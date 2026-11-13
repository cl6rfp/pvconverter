"""Diagnóstico de contactos entre extremos de pistas de una misma ruta.

No reconstruye una red eléctrica: solo compara extremos de segmentos en la
misma capa y dentro de una tolerancia. Los cruces interiores, las vías y los
pads requieren análisis independiente.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from pvf import read_pvf


def _point(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    try:
        x, y = float(value[0]), float(value[1])
    except (TypeError, ValueError, OverflowError):
        return None
    return (x, y) if math.isfinite(x) and math.isfinite(y) else None


class _Groups:
    def __init__(self, count):
        self.parent = list(range(count))
        self.size = [1] * count

    def root(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def join(self, x, y):
        a, b = self.root(x), self.root(y)
        if a == b:
            return False
        if self.size[a] < self.size[b]:
            a, b = b, a
        self.parent[b] = a
        self.size[a] += self.size[b]
        return True


class _Endpoints:
    """Índice espacial limitado a una ruta y capa; no mezcla redes."""
    def __init__(self, tolerance):
        self.tolerance = tolerance
        self.cells = defaultdict(list)

    def candidates(self, layer, point):
        if self.tolerance == 0:
            yield from self.cells[(layer, point[0], point[1])]
            return
        x, y = (math.floor(v / self.tolerance) for v in point)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                yield from self.cells[(layer, x + dx, y + dy)]

    def add(self, layer, point, index):
        if self.tolerance == 0:
            key = (layer, point[0], point[1])
        else:
            key = (layer, math.floor(point[0] / self.tolerance),
                   math.floor(point[1] / self.tolerance))
        self.cells[key].append((point, index))


def analyze_connectivity(blocks, tolerance=1e-4, top=20):
    """Agrupa segmentos por contactos de extremos, sin modificar los bloques.

    Un grupo aislado no implica un circuito abierto. Un contacto encontrado
    tampoco verifica continuidad eléctrica: depende del origen, las capas y
    de la exactitud del modelo exportado.
    """
    if not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError('tolerance must be finite and nonnegative')
    if not isinstance(top, int) or top < 0:
        raise ValueError('top must be a nonnegative integer')

    segments = {s['id']: s for s in blocks['SEGS']}
    vias = {v['id']: v for v in blocks['VIAS']}
    primitives = blocks['PRIM']
    problems = []
    totals = Counter()

    for route in blocks['ROUT']:
        route_id = route['id']
        start, count = route.get('primitive_start'), route.get('primitive_count')
        invalid_range = (not isinstance(start, int) or not isinstance(count, int)
                         or count < 0 or (count == 0 and not 0 <= start <= len(primitives) + 1)
                         or (count > 0 and (start < 1 or start - 1 + count > len(primitives))))
        if invalid_range:
            totals['invalid_ranges'] += 1
            problems.append({'route_id': route_id, 'net_id': route.get('net_id'),
                             'invalid_range': True})
            continue

        records = []
        skipped = Counter()
        via_count = 0
        for item in primitives[start - 1:start - 1 + count]:
            kind, ref = item.get('kind'), item.get('ref_id')
            if kind == 'via':
                if ref not in vias:
                    skipped['missing_via_refs'] += 1
                via_count += 1
                continue
            if kind != 'segment':
                skipped['unknown_primitive_kinds'] += 1
                continue
            seg = segments.get(ref)
            if seg is None or seg.get('route_id') != route_id:
                skipped['missing_or_foreign_segment_refs'] += 1
                continue
            if seg.get('type') == 'line':
                ends = (_point(seg.get('p1')), _point(seg.get('p2')))
            elif seg.get('type') == 'arc':
                ends = (_point(seg.get('start')), _point(seg.get('end')))
            else:
                skipped['unsupported_segment_types'] += 1
                continue
            if None in ends:
                skipped['invalid_segment_coordinates'] += 1
                continue
            layer = seg.get('layer_id')
            if layer is None:
                skipped['missing_layers'] += 1
                continue
            records.append((layer, ends))

        groups = _Groups(len(records))
        index = _Endpoints(tolerance)
        contacts = 0
        for i, (layer, ends) in enumerate(records):
            for endpoint in ends:
                for previous, other in index.candidates(layer, endpoint):
                    if (math.dist(previous, endpoint) <= tolerance
                            and groups.join(i, other)):
                        contacts += 1
                index.add(layer, endpoint, i)

        components = len({groups.root(i) for i in range(len(records))})
        totals['segments_checked'] += len(records)
        totals['vias_not_joined'] += via_count
        totals['endpoint_joins'] += contacts
        totals['endpoint_groups'] += components
        totals.update(skipped)
        if len(records) > 1 and components > 1:
            totals['routes_with_multiple_endpoint_groups'] += 1
        if components > 1 or skipped:
            problems.append({'route_id': route_id, 'net_id': route.get('net_id'),
                             'segments_checked': len(records),
                             'endpoint_groups': components,
                             'vias_not_joined': via_count,
                             'skipped': dict(skipped)})

    problems.sort(key=lambda x: (-x.get('endpoint_groups', 0), x['route_id']))
    return {
        'interpretation': ('Same-route, same-layer segment endpoint contacts only. '
                           'Not proof of electrical continuity or open circuits.'),
        'tolerance_source_units': tolerance,
        'routes_checked': len(blocks['ROUT']),
        'totals': dict(totals),
        'routes_needing_review': len(problems),
        'worst_routes': problems[:top],
        'excluded': ['via bridging between layers', 'pad/pin contact',
                     'interior crossings and T junctions', 'copper polygons',
                     'contacts between separate ROUT records'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    parser.add_argument('--tolerance', type=float, default=1e-4)
    parser.add_argument('--top', type=int, default=20)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.top < 0:
        parser.error('--top must be nonnegative')
    result = analyze_connectivity(
        {k: v['data'] for k, v in read_pvf(args.file)['blocks'].items()},
        args.tolerance, args.top,
    )
    data = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data, encoding='utf-8')
    else:
        print(data, end='')


if __name__ == '__main__':
    main()
