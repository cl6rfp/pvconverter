from __future__ import annotations
import sys, json
from pathlib import Path
from pv_geometry import geometry_report, export_svg

pv=Path(sys.argv[1] if len(sys.argv)>1 else 'MS-7B79_test.pv')
r=geometry_report(pv)
assert r['valid'],r
assert r['source_sha256_matches'] is True
assert r['components']==2693
assert r['segments']==94146
assert r['vias']==7149
assert r['route_primitives']==101295
assert r['arc_records']==27729
assert r['route_reference_errors']==[]
out=pv.with_name(pv.stem+'_geometry_test.svg')
result=export_svg(pv,out,'ALL',False)
assert out.exists() and out.stat().st_size>10000
print(json.dumps(r,indent=2))
print('SVG_PREVIEW_OK',out.stat().st_size,'bytes')
print('ALL GEOMETRY TESTS PASSED')
