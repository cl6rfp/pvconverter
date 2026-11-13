"""Non-destructive per-route adjacency diagnostics from an existing PVF file.

This is NOT electrical connectivity proof: routes may contain branches,
nonconsecutive fragments, and implied contacts that the event stream does not
represent as adjacent endpoints. Coordinates are preserved, never repaired.
"""
from __future__ import annotations
import argparse
import json
import math
from collections import Counter
from pathlib import Path
from pvf import read_pvf


def _ends(record):
    if record is None:
        return None
    if record.get('type') == 'line':
        return record.get('p1'), record.get('p2')
    if record.get('type') == 'arc':
        return record.get('start'), record.get('end')
    if 'x' in record and 'y' in record:
        point = [record['x'], record['y']]
        return point, point
    return None


def analyze_routes(blocks, tolerance=1e-4, top=20):
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError('tolerance must be finite and nonnegative')
    seg = {x['id']: x for x in blocks['SEGS']}
    vias = {x['id']: x for x in blocks['VIAS']}
    primitives = blocks['PRIM']
    results = []
    summary = Counter()
    for route in blocks['ROUT']:
        start = route['primitive_start'] - 1
        count = route['primitive_count']
        stream = primitives[start:start + count]
        local = Counter()
        if len(stream) != count:
            local['invalid_ranges'] += 1
        prev = None
        for item in stream:
            table = seg if item.get('kind') == 'segment' else vias if item.get('kind') == 'via' else {}
            current = _ends(table.get(item.get('ref_id')))
            if prev is not None and current is not None:
                try:
                    gap = min(math.dist(a, b) for a in prev for b in current)
                except (ValueError, TypeError):
                    local['invalid_coordinates'] += 1
                else:
                    if gap > tolerance:
                        local['adjacent_gaps'] += 1
                    else:
                        local['adjacent_contacts'] += 1
            prev = current
        summary.update(local)
        if local['adjacent_gaps'] or local['invalid_ranges'] or local['invalid_coordinates']:
            results.append({'route_id': route['id'],
                            'net_id': route.get('net_id'),
                            'primitive_count': count,
                            'adjacent_gaps': local['adjacent_gaps'],
                            'invalid_ranges': local['invalid_ranges'],
                            'invalid_coordinates': local['invalid_coordinates']})
    results.sort(key=lambda x: (-x['adjacent_gaps'], x['route_id']))
    return {'interpretation': 'geometric adjacency only; NOT verified electrical continuity',
            'tolerance_source_units': tolerance,
            'routes_checked': len(blocks['ROUT']),
            'routes_with_gaps_or_invalid_data': len(results),
            'totals': dict(summary),
            'worst_routes': results[:top]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    parser.add_argument('--tolerance', type=float, default=1e-4)
    parser.add_argument('--top', type=int, default=20)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.top < 0:
        parser.error('--top must be nonnegative')
    result = analyze_routes({k: v['data'] for k, v in read_pvf(args.file)['blocks'].items()}, args.tolerance, args.top)
    data = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data + '\n', encoding='utf-8')
    else:
        print(data)


if __name__ == '__main__':
    main()
