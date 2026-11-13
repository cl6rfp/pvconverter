"""Inventory source graphics and mechanical records without inferring a silkscreen."""
import argparse
import json
from collections import Counter
from pathlib import Path
from gencad_parser import parse_file


def audit_source(path):
    data, _ = parse_file(str(path))
    artworks = data['board_artworks']
    comps = data['components']
    sections = data['raw_sections']
    declared = [x['name'] for x in data['layers']]
    silk = [name for name in declared if 'SILK' in name.upper() or 'LEGEND' in name.upper()]
    return {
        'source_file': Path(path).name,
        'silkscreen': {
            'explicit_layer_names': silk,
            'status': 'explicit layer present' if silk else 'not explicitly identified',
            'note': 'Artwork on TOP/BOTTOM is not automatically classified as silkscreen.'
        },
        'board_artwork': {
            'groups': len(artworks),
            'by_layer': dict(sorted(Counter(a['layer'] for a in artworks).items())),
            'primitive_types': dict(sorted(Counter(g['type'] for a in artworks for g in a['geometry']).items())),
            'artworks_section_records': len(sections.get('$ARTWORKS', [])),
        },
        'mechanical': {
            'holes': len(data['mechanical_holes']),
            'holes_source': '$MECH',
            'holes_data': data['mechanical_holes'],
            'explicit_board_outline': 'not identified',
        },
        'components': {
            'total': len(comps),
            'by_layer': dict(sorted(Counter(c.get('layer', 'UNSPECIFIED') for c in comps).items())),
            'rotation_degrees': dict(sorted(Counter(str(c.get('rotation',0)) for c in comps).items())),
            'shape_transform_tokens': dict(sorted(Counter(token for c in comps for token in c.get('shape_extra', [])).items())),
        },
    }


def main():
    p=argparse.ArgumentParser(description='Inventory artwork, silkscreen markers, holes and component transforms')
    p.add_argument('cad'); p.add_argument('--out')
    args=p.parse_args()
    content=json.dumps(audit_source(args.cad), indent=2, ensure_ascii=False)
    if args.out: Path(args.out).write_text(content+'\n',encoding='utf-8')
    else: print(content)


if __name__ == '__main__': main()
