"""Inspect GenCAD BOARD artwork without interpreting it as a board outline."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from pvf import read_pvf


def geometry_bounds(geometry):
    """Return axis-aligned bounds of lines, circles and conservative arc extents."""
    points = []
    for item in geometry:
        kind = item.get('type')
        if kind == 'line':
            points.extend((item['p1'], item['p2']))
        elif kind == 'rectangle':
            x, y, w, h = (float(item[k]) for k in ('x', 'y', 'width', 'height'))
            points.extend(((x, y), (x + w, y + h)))
        elif kind in ('circle', 'arc'):
            x, y = map(float, item['center'])
            r = float(item['radius']) if kind == 'circle' else math.dist((x, y), item['start'])
            # Conservative for an arc with unresolved direction; no implied outline.
            points.extend(((x - r, y - r), (x + r, y + r)))
    if not points:
        return None
    return [min(float(p[0]) for p in points), min(float(p[1]) for p in points),
            max(float(p[0]) for p in points), max(float(p[1]) for p in points)]


def closed_line_chain(geometry, tolerance=1e-4):
    """Check whether line endpoints form a single cycle (not whether it is a PCB edge)."""
    if not geometry or any(item.get('type') != 'line' for item in geometry):
        return False
    points = {}
    for item in geometry:
        p, q = item['p1'], item['p2']
        if math.dist(p, q) <= tolerance:
            return False
        for endpoint in (p, q):
            key = (round(float(endpoint[0]) / tolerance), round(float(endpoint[1]) / tolerance))
            points.setdefault(key, []).append(item)
    if not points or any(len(edges) != 2 for edges in points.values()):
        return False
    # Degree two alone can describe several disjoint cycles.
    adjacency = {}
    for item in geometry:
        a, b = ((round(float(p[0]) / tolerance), round(float(p[1]) / tolerance))
                for p in (item['p1'], item['p2']))
        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)
    pending = [next(iter(adjacency))]
    visited = set()
    while pending:
        node = pending.pop()
        if node not in visited:
            visited.add(node)
            pending.extend(adjacency[node] - visited)
    return len(visited) == len(adjacency)


def inspect_artwork(groups):
    records = []
    for item in groups:
        geometry = item.get('geometry') or []
        box = geometry_bounds(geometry)
        records.append({
            'id': item.get('id'), 'name': item.get('name'), 'layer': item.get('source_layer'),
            'primitives': len(geometry),
            'types': {k: sum(g.get('type') == k for g in geometry)
                      for k in sorted({g.get('type') for g in geometry})},
            'bbox': box,
            'closed_line_chain': closed_line_chain(geometry),
            'board_edge_verified': False,
        })
    return {
        'groups': len(records),
        'closed_line_chains': sum(x['closed_line_chain'] for x in records),
        'note': 'Closed artwork is not sufficient evidence of a physical PCB boundary.',
        'items': records,
    }


def main():
    p = argparse.ArgumentParser(description='BOARD artwork provenance and geometry')
    p.add_argument('pv')
    p.add_argument('--output', help='Save JSON report')
    args = p.parse_args()
    doc = read_pvf(args.pv)
    result = inspect_artwork(doc['blocks']['ARTW']['data'])
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(encoded + '\n', encoding='utf-8')
    else:
        print(encoded)


if __name__ == '__main__':
    main()
