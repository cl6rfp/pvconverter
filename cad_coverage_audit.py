"""Inventario reproducible de cobertura del importador GenCAD.

No valida fidelidad geométrica por comparación con otro CAD. Señala instrucciones
no reconocidas y datos que el importador conserva sin convertir en entidades.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from gencad_parser import parse_file, tokens

# Registros que el parser interpreta como entidades o propiedades.
INTERPRETED = {
    '$HEADER': {'UNITS', 'ORIGIN', 'ATTRIBUTE', 'DRAWING', 'REVISION', 'USER', 'INTERTRACK', 'GENCAD'},
    '$BOARD': {'ARTWORK', 'LINE', 'ARC', 'CIRCLE', 'RECTANGLE'},
    '$PADS': {'PAD', 'LINE', 'ARC', 'CIRCLE', 'RECTANGLE'},
    '$PADSTACKS': {'PADSTACK', 'PAD', 'ATTRIBUTE'},
    '$SHAPES': {'SHAPE', 'PIN', 'INSERT'},
    '$COMPONENTS': {'COMPONENT', 'PLACE', 'LAYER', 'ROTATION', 'SHAPE', 'DEVICE'},
    '$DEVICES': {'DEVICE', 'PART'},
    '$SIGNALS': {'SIGNAL', 'NODE'},
    '$TRACKS': {'TRACK'},
    '$LAYERS': {'DEFINE'},
    '$ROUTES': {'ROUTE', 'TRACK', 'LAYER', 'LINE', 'ARC', 'VIA'},
    '$MECH': {'HOLE'},
}

# El parser sí guarda estos tokens, pero no les asigna semántica completa.
PARTIAL = {
    '$HEADER': {'ATTRIBUTE', 'DRAWING', 'REVISION', 'USER', 'INTERTRACK', 'GENCAD'},
    '$SHAPES': {'INSERT'},
    '$PADSTACKS': {'ATTRIBUTE'},
    '$DEVICES': {'PART'},
}


def summarize(data, max_examples=12):
    result = {'source': data['meta']['source_name'], 'sha256': data['meta']['source_sha256'],
              'sections': {}, 'unsupported_records': 0, 'partial_records': 0,
              'malformed_records': 0, 'notes': []}
    # Required field counts catch malformed lines that the parser silently skips.
    required = {
        ('$BOARD', 'ARTWORK'): 3, ('$BOARD', 'LINE'): 5, ('$BOARD', 'ARC'): 7,
        ('$PADS', 'PAD'): 2, ('$PADS', 'LINE'): 5, ('$PADS', 'ARC'): 7,
        ('$PADS', 'CIRCLE'): 4, ('$PADS', 'RECTANGLE'): 5,
        ('$SHAPES', 'PIN'): 7, ('$COMPONENTS', 'PLACE'): 3,
        ('$SIGNALS', 'NODE'): 3, ('$TRACKS', 'TRACK'): 3,
        ('$LAYERS', 'DEFINE'): 3, ('$ROUTES', 'LINE'): 5,
        ('$ROUTES', 'ARC'): 7, ('$ROUTES', 'VIA'): 4, ('$MECH', 'HOLE'): 4,
    }
    for section, lines in data['raw_sections'].items():
        counts = Counter()
        unknown = []
        partial = []
        malformed = []
        for line_number, line in enumerate(lines, 1):
            fields = tokens(line)
            if not fields:
                continue
            key = fields[0].upper()
            counts[key] += 1
            if key not in INTERPRETED.get(section, set()):
                result['unsupported_records'] += 1
                if len(unknown) < max_examples:
                    unknown.append({'line_in_section': line_number, 'record': line})
            elif key in PARTIAL.get(section, set()):
                result['partial_records'] += 1
                if len(partial) < max_examples:
                    partial.append({'line_in_section': line_number, 'record': line})
            if len(fields) < required.get((section, key), 1):
                result['malformed_records'] += 1
                if len(malformed) < max_examples:
                    malformed.append({'line_in_section': line_number, 'record': line})
        result['sections'][section] = {'records': sum(counts.values()), 'types': dict(sorted(counts.items())),
                                       'unsupported_examples': unknown, 'partial_examples': partial,
                                       'malformed_examples': malformed}
    result['notes'] = [
        'Los registros parciales se conservan en la fuente; no prueban una representación completa en PV.',
        'Un conteo de instrucciones reconocidas no certifica orientación, dimensiones ni conectividad.',
        'El contorno mecánico y la serigrafía no se deducen de grupos de arte arbitrarios.',
    ]
    return result


def audit_file(source):
    model, _ = parse_file(str(source))
    return summarize(model)


def main():
    cli = argparse.ArgumentParser(description='Cobertura de instrucciones GenCAD')
    cli.add_argument('source', type=Path)
    cli.add_argument('--output', type=Path)
    args = cli.parse_args()
    report = audit_file(args.source)
    output = json.dumps(report, indent=2, ensure_ascii=False) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding='utf-8')
    else:
        print(output, end='')
    if report['unsupported_records'] or report['malformed_records']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
