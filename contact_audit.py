"""Candidatos de contacto pista-vía y referencias pin-red en un archivo PV.

Las coincidencias de posición no se convierten en conexiones eléctricas.
El informe conserva los identificadores para inspección posterior.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from connectivity_audit import _Endpoints, _point
from pvf import read_pvf


def analyze_contacts(blocks, tolerance=1e-4, top=20):
    """Cruza extremos de pistas con vías de su ROUT y comprueba enlaces NETS/PINS.

    No calcula un grafo eléctrico ni aplica transformaciones de componentes.
    """
    if (not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool)
            or not math.isfinite(tolerance) or tolerance < 0):
        raise ValueError('tolerance must be finite and nonnegative')
    if not isinstance(top, int) or isinstance(top, bool) or top < 0:
        raise ValueError('top must be a nonnegative integer')

    segments = {s['id']: s for s in blocks['SEGS']}
    vias = {v['id']: v for v in blocks['VIAS']}
    stacks = {s['id']: s for s in blocks.get('PSTK', [])}
    pins = {p['id']: p for p in blocks.get('PINS', [])}
    nets = {n['id']: n for n in blocks.get('NETS', [])}
    primitives = blocks['PRIM']
    counts = Counter()
    examples = []

    for route in blocks['ROUT']:
        start, count = route.get('primitive_start'), route.get('primitive_count')
        if (not isinstance(start, int) or not isinstance(count, int)
                or count < 0 or (count and (start < 1 or start - 1 + count > len(primitives)))
                or (not count and start not in (0, None))):
            counts['invalid_ranges'] += 1
            continue
        if not count:
            continue
        index = _Endpoints(tolerance)
        via_items = []
        for item in primitives[start - 1:start - 1 + count]:
            kind, ref = item.get('kind'), item.get('ref_id')
            if kind == 'segment':
                seg = segments.get(ref)
                if not seg or seg.get('route_id') != route['id']:
                    counts['invalid_segment_refs'] += 1
                    continue
                if seg.get('type') == 'line':
                    ends = (seg.get('p1'), seg.get('p2'))
                elif seg.get('type') == 'arc':
                    ends = (seg.get('start'), seg.get('end'))
                else:
                    counts['unsupported_segments'] += 1
                    continue
                if not seg.get('layer_id'):
                    counts['segments_without_layer'] += 1
                    continue
                for endpoint in ends:
                    point = _point(endpoint)
                    if point is None:
                        counts['invalid_segment_points'] += 1
                        continue
                    index.add(seg['layer_id'], point, seg['id'])
            elif kind == 'via':
                via = vias.get(ref)
                if not via or via.get('route_id') != route['id']:
                    counts['invalid_via_refs'] += 1
                else:
                    via_items.append(via)
            else:
                counts['unknown_primitives'] += 1

        for via in via_items:
            counts['vias_checked'] += 1
            point = _point([via.get('x'), via.get('y')])
            if point is None:
                counts['invalid_via_points'] += 1
                continue
            stack = stacks.get(via.get('padstack_id'))
            layer_ids = {p.get('layer_id') for p in stack.get('pads', []) if p.get('layer_id')} if stack else set()
            if not layer_ids:
                counts['vias_without_known_pad_layers'] += 1
                continue
            touched = defaultdict(set)
            for layer in layer_ids:
                for other, seg_id in index.candidates(layer, point):
                    if math.dist(point, other) <= tolerance:
                        touched[layer].add(seg_id)
            if touched:
                counts['vias_with_endpoint_candidates'] += 1
                counts['layer_endpoint_matches'] += sum(len(items) for items in touched.values())
                if len(touched) > 1:
                    counts['vias_with_multiple_layer_candidates'] += 1
                if len(examples) < top:
                    examples.append({'route_id': route['id'], 'net_id': route.get('net_id'),
                                     'via_id': via['id'], 'position': list(point),
                                     'matching_layers': [{'layer_id': layer, 'segment_ids': sorted(ids)}
                                                         for layer, ids in sorted(touched.items())]})
            else:
                counts['vias_without_endpoint_candidates'] += 1

    for net in blocks.get('NETS', []):
        counts['nets_checked'] += 1
        for connection in net.get('connections', []):
            counts['net_pin_references'] += 1
            if connection.get('pin_id') not in pins:
                counts['missing_net_pin_references'] += 1
    for route in blocks['ROUT']:
        if route.get('net_id') not in nets:
            counts['routes_without_known_net'] += 1

    return {
        'scope': 'Via-to-segment endpoint candidates within one ROUT; NETS-to-PINS reference checks.',
        'tolerance_source_units': tolerance,
        'routes_checked': len(blocks['ROUT']),
        'totals': dict(counts),
        'examples': examples,
        'limitations': [
            'A matching endpoint is a geometric candidate, not verified electrical continuity.',
            'Padstack layers identify listed pad layers; via spans and plated-through behavior are not inferred.',
            'Interior T-junctions, crossings, traces in other ROUT records and copper regions are excluded.',
            'Pin positions require confirmed board transforms; pin-to-trace geometry is not evaluated.',
            'Existing NETS pin references are validated, not reconstructed from geometry.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    parser.add_argument('--tolerance', type=float, default=1e-4)
    parser.add_argument('--top', type=int, default=20)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = analyze_contacts({k: v['data'] for k, v in read_pvf(args.file)['blocks'].items()},
                              tolerance=args.tolerance, top=args.top)
    report = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding='utf-8')
    else:
        print(report, end='')


if __name__ == '__main__':
    main()
