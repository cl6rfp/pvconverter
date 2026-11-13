"""Check that a PV conversion retains the GenCAD records used by the importer.

This is a source-to-container audit, not a geometry or PCB fabrication check.
Comparisons use stored coordinates and source tokens; no visual transforms are
applied.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

from gencad_parser import parse_file
from pvf import read_pvf


def audit(source, pv, max_examples=20):
    data, raw = parse_file(source)
    doc = read_pvf(pv)
    b = {name: entry['data'] for name, entry in doc['blocks'].items()}
    checks = 0
    errors = []
    error_count = 0
    counts = {}

    def check(where, actual, expected):
        nonlocal checks, error_count
        checks += 1
        if actual != expected:
            error_count += 1
        if actual != expected and len(errors) < max_examples:
            errors.append({'field': where, 'expected': expected, 'actual': actual})
        return actual == expected

    src_hash = hashlib.sha256(raw).hexdigest()
    check('META.source_sha256', b['META'].get('source_sha256'), src_hash)
    stored_source = b.get('SRCE', {})
    if stored_source.get('encoding') == 'base64-latin-1':
        try:
            embedded = base64.b64decode(stored_source['data'], validate=True)
            check('SRCE.data', hashlib.sha256(embedded).hexdigest(), src_hash)
            check('SRCE.byte_length', len(embedded), len(raw))
        except (KeyError, ValueError) as exc:
            error_count += 1
            errors.append({'field': 'SRCE.data', 'issue': str(exc)})
    else:
        error_count += 1
        errors.append({'field': 'SRCE.encoding', 'issue': 'Source is not embedded as base64-latin-1'})

    count_sources = {
        'COMP': len(data['components']), 'SHAP': len(data['shapes']),
        'PADS': len(data['pads']), 'PSTK': len(data['padstacks']),
        'NETS': len(data['signals']), 'ROUT': len(data['routes']),
        'SEGS': sum(len(r['segments']) for r in data['routes']),
        'VIAS': sum(len(r['vias']) for r in data['routes']),
        'PRIM': sum(len(r['primitives']) for r in data['routes']),
        'PINS': sum(len(next(s for s in data['shapes'] if s['name'] == c['shape'])['pins'])
                    for c in data['components']),
        'HOLE': len(data['mechanical_holes']), 'TRKS': len(data['tracks']),
        'ARTW': len(data['board_artworks']), 'DEVS': len(data['devices'])
    }
    for key, expected in count_sources.items():
        actual = len(b.get(key, []))
        check(f'{key}.count', actual, expected)
        counts[key] = actual

    shape_by_id = {s['id']: s for s in b['SHAP']}
    for idx, (src, converted) in enumerate(zip(data['components'], b['COMP']), 1):
        name = f'COMP[{idx}]'
        for a, c in (('reference', 'reference'), ('layer', 'source_layer'),
                     ('rotation', 'rotation_deg'), ('device', 'device')):
            check(f'{name}.{c}', converted.get(c), src.get(a))
        check(f'{name}.position', [converted.get('x'), converted.get('y')], src.get('position'))
        check(f'{name}.shape', shape_by_id.get(converted['shape_id'], {}).get('name'), src.get('shape'))
        check(f'{name}.tokens', converted.get('shape_transform_tokens', []), src.get('shape_extra', []))

    for idx, (src, converted) in enumerate(zip(data['mechanical_holes'], b.get('HOLE', [])), 1):
        for field in ('x', 'y', 'diameter', 'raw'):
            check(f'HOLE[{idx}].{field}', converted.get(field), src.get(field))

    src_prims = ((route, prim) for route in data['routes'] for prim in route['primitives'])
    segments = {s['id']: s for s in b.get('SEGS', [])}
    vias = {v['id']: v for v in b.get('VIAS', [])}
    for idx, ((route, source_prim), converted_prim) in enumerate(zip(src_prims, b.get('PRIM', [])), 1):
        where = f'PRIM[{idx}]'
        check(f'{where}.kind', converted_prim['kind'], source_prim['kind'])
        if source_prim['kind'] == 'segment':
            src = route['segments'][source_prim['index']]
            conv = segments.get(converted_prim['ref_id'], {})
            for field, mapped in (('type', 'type'), ('track_id', 'track_id'),
                                  ('layer', 'source_layer'), ('raw', 'source_raw')):
                check(f'{where}.{mapped}', conv.get(mapped), src.get(field))
            for field in ('p1', 'p2', 'start', 'end', 'center'):
                if field in src:
                    check(f'{where}.{field}', conv.get(field), src[field])
        elif source_prim['kind'] == 'via':
            src = route['vias'][source_prim['index']]
            conv = vias.get(converted_prim['ref_id'], {})
            for field, mapped in (('padstack', 'padstack_name'), ('x', 'x'), ('y', 'y'),
                                  ('span', 'span'), ('offset', 'offset'), ('name', 'name'),
                                  ('raw', 'source_raw')):
                check(f'{where}.{mapped}', conv.get(mapped), src.get(field))

    for idx, (src, conv) in enumerate(zip(data['board_artworks'], b.get('ARTW', [])), 1):
        check(f'ARTW[{idx}].name', conv.get('name'), src.get('name'))
        check(f'ARTW[{idx}].source_layer', conv.get('source_layer'), src.get('layer'))
        for geom_idx, (source_geom, pv_geom) in enumerate(zip(src['geometry'], conv['geometry']), 1):
            for field in ('type', 'raw', 'p1', 'p2', 'start', 'end', 'center',
                          'radius', 'x', 'y', 'width', 'height'):
                if field in source_geom:
                    check(f'ARTW[{idx}].geometry[{geom_idx}].{field}',
                          pv_geom.get(field), source_geom[field])

    return {'source': Path(source).name, 'pv': Path(pv).name,
            'checks': checks, 'error_count': error_count, 'errors': errors,
            'records': counts, 'scope': 'source fields and route order; not independent geometric correctness'}


def main():
    parser = argparse.ArgumentParser(description='Compare original GenCAD records to PVF output')
    parser.add_argument('cad', type=Path)
    parser.add_argument('pv', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = audit(args.cad, args.pv)
    output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding='utf-8')
    print(output)
    if result['error_count']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
