"""Component-coordinate helpers and a non-destructive transform audit.

Coordinates are in GenCAD source units. MIRRORY is currently displayed as an
X reflection in component-local space; this remains a preview convention until
its source semantics can be verified against an independent reference.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

from pvf import read_pvf


def rotate(point, degrees):
    a = math.radians(float(degrees or 0))
    x, y = map(float, point)
    return (x * math.cos(a) - y * math.sin(a),
            x * math.sin(a) + y * math.cos(a))


def component_point(component, point):
    """Map a local point to board space using the current SVG convention."""
    x, y = map(float, point)
    tokens = component.get('shape_transform_tokens') or []
    if 'MIRRORY' in tokens:
        x = -x
    rx, ry = rotate((x, y), component.get('rotation_deg'))
    return float(component['x']) + rx, float(component['y']) + ry


def pad_box_points(pin, pad_entry, pad):
    """Conservative pad bounds from its local axis-aligned envelope.

    Rotating all envelope corners may overestimate a pad; it must never be used
    as an exact footprint outline or a manufacturing dimension.
    """
    from pv_geometry import _pad_local_extents
    x0, y0, x1, y1 = _pad_local_extents(pad)
    angle = float(pin.get('rotation_deg') or 0) + float(pad_entry.get('rotation') or 0)
    px, py = float(pin.get('x_local') or 0), float(pin.get('y_local') or 0)
    return [(px + rx, py + ry) for rx, ry in (
        rotate((x, y), angle) for x, y in
        ((x0, y0), (x0, y1), (x1, y0), (x1, y1)))]


def transformed_pad_points(component, pin, entry, pad):
    return [component_point(component, p) for p in pad_box_points(pin, entry, pad)]


def _is_number(value):
    try:
        return math.isfinite(float(value))
    except (ValueError, TypeError):
        return False


def audit_pv(pv_path, example_limit=12):
    blocks = {key: block['data'] for key, block in read_pvf(pv_path)['blocks'].items()}
    components = blocks.get('COMP', [])
    stacks = {item['id']: item for item in blocks.get('PSTK', [])}
    pads = {item['id']: item for item in blocks.get('PADS', [])}
    pins_by_component = {}
    for pin in blocks.get('PINS', []):
        pins_by_component.setdefault(pin['component_id'], []).append(pin)
    tokens = Counter()
    invalid = []
    bounds = []
    transformed_pins = 0
    pins_without_pad = 0
    for comp in components:
        for token in comp.get('shape_transform_tokens') or []:
            tokens[token] += 1
        if comp.get('x') is None or comp.get('y') is None:
            invalid.append({'component': comp.get('reference'), 'reason': 'missing origin'})
            continue
        for pin in pins_by_component.get(comp['id'], []):
            position = component_point(comp, (pin.get('x_local') or 0, pin.get('y_local') or 0))
            if not all(math.isfinite(value) for value in position):
                invalid.append({'component': comp.get('reference'), 'pin': pin.get('number'), 'reason': 'non-finite coordinate'})
                continue
            transformed_pins += 1
            stack = stacks.get(pin.get('padstack_id'), {})
            entries = stack.get('pads', [])
            side = 'BOTTOM' if comp.get('source_layer') == 'BOTTOM' else 'TOP'
            entry = next((item for item in entries if item.get('normalized_layer') == side), None)
            if entry is None:
                entry = next((item for item in entries if item.get('normalized_layer') in
                              ('TOP', 'BOTTOM', 'INNER_1', 'INNER_2')), None)
            pad = pads.get(entry.get('pad_id')) if entry else None
            if pad is None:
                pins_without_pad += 1
                bounds.append(position)
            else:
                bounds.extend(transformed_pad_points(comp, pin, entry, pad))
    supported = {'MIRRORY', 'FLIP'}
    numeric_metadata = {name: count for name, count in tokens.items()
                        if _is_number(name)}
    unknown = {name: count for name, count in tokens.items()
               if name not in supported and name not in numeric_metadata}
    return {
        'components': len(components), 'pins_transformed': transformed_pins,
        'pins_without_pad_geometry': pins_without_pad,
        'transform_tokens': dict(sorted(tokens.items())),
        'numeric_shape_metadata_not_interpreted': numeric_metadata,
        'unrecognized_transform_tokens': unknown,
        'invalid_count': len(invalid), 'invalid_examples': invalid[:example_limit],
        'pad_envelope_bounds': ([min(p[0] for p in bounds), min(p[1] for p in bounds),
                                 max(p[0] for p in bounds), max(p[1] for p in bounds)]
                                if bounds else None),
        'interpretation': 'SVG display convention, not independently verified GenCAD mirror semantics',
    }


def main():
    parser = argparse.ArgumentParser(description='Audit component transforms in a PVF file')
    parser.add_argument('pv', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = audit_pv(args.pv)
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + '\n', encoding='utf-8')
    print(encoded)
    if report['invalid_count'] or report['unrecognized_transform_tokens']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
