from __future__ import annotations
import sys, json, hashlib, base64
from pathlib import Path
from pvf import read_pvf

p=Path(sys.argv[1])
r=read_pvf(p)
b=r['blocks']
get=lambda name: b[name]['data']
components=get('COMP'); shapes=get('SHAP'); pins=get('PINS'); pads=get('PADS')
padstacks=get('PSTK'); nets=get('NETS'); segs=get('SEGS'); vias=get('VIAS')
prims=get('PRIM'); routes=get('ROUT'); layers=get('LAYR'); artworks=get('ARTW')
checks={
 'components':len(components), 'shapes':len(shapes), 'pins':len(pins),
 'pads':len(pads), 'padstacks':len(padstacks), 'nets':len(nets),
 'route_segments':len(segs), 'vias':len(vias), 'route_primitives':len(prims),
 'routes':len(routes), 'board_artworks':len(get('ARTW')),
 'mechanical_holes':len(get('HOLE')),
 'inner_layers_present':all(x in {l['name'] for l in layers} for x in ('INNER_1','INNER_2')),
 'bottom_transform_tokens_preserved':sum(1 for c in components if c.get('shape_transform_tokens')==['MIRRORY','FLIP']),
 'inner_pad_layers_distinguished':sum(1 for st in padstacks for x in st['pads'] if x.get('source_layer')=='INNER' and x.get('normalized_layer') in ('INNER_1','INNER_2')),
}
source=base64.b64decode(get('SRCE')['data'])
checks['source_bytes']=len(source)
checks['source_sha256_matches']=hashlib.sha256(source).hexdigest()==get('META')['source_sha256']
# Validate the route event stream and all cross-block references.
seg_by_id={x['id']:x for x in segs}; via_by_id={x['id']:x for x in vias}
route_order_ok=True
for route in routes:
 start=route['primitive_start']; count=route['primitive_count']
 stream=prims[start-1:start-1+count] if count else []
 if len(stream)!=count: route_order_ok=False; break
 for expected_order,item in enumerate(stream):
  if item['route_id']!=route['id'] or item['order']!=expected_order:
   route_order_ok=False; break
  table=seg_by_id if item['kind']=='segment' else via_by_id if item['kind']=='via' else {}
  obj=table.get(item['ref_id'])
  if obj is None or obj['route_id']!=route['id'] or obj['route_order']!=expected_order:
   route_order_ok=False; break
 if not route_order_ok: break
checks['route_primitive_order_valid']=route_order_ok
# Every track ID referenced by a segment must have a definition.
track_ids={x['id'] for x in get('TRKS')}
checks['missing_track_definitions']=sum(1 for x in segs if x.get('track_id') not in track_ids)
arc_records=[x for x in segs if x['type']=='arc']
arc_records += [g for pad in pads for g in pad['geometry'] if g['type']=='arc']
arc_records += [g for art in artworks for g in art['geometry'] if g['type']=='arc']
checks['all_arcs_have_endpoints_center_and_candidates']=all(all(k in x for k in ('start','end','center','arc_sweep_ccw_deg','arc_sweep_cw_deg','arc_radius_error')) for x in arc_records)
checks['arc_records_checked']=len(arc_records)
checks['blocks']=list(b)
print(json.dumps({'version':r['version'],'file_size':r['file_size'],'checks':checks},indent=2))
assert checks['components']==2693
assert checks['shapes']==112
assert checks['pins']==11104
assert checks['pads']==347
assert checks['padstacks']==228
assert checks['nets']==1997
assert checks['route_segments']==94146
assert checks['vias']==7149
assert checks['route_primitives']==101295
assert checks['routes']==1997
assert checks['inner_layers_present']
assert checks['bottom_transform_tokens_preserved']==243
assert checks['inner_pad_layers_distinguished']==194
assert checks['source_sha256_matches']
assert checks['route_primitive_order_valid']
assert checks['missing_track_definitions']==0
assert checks['all_arcs_have_endpoints_center_and_candidates']
assert checks['arc_records_checked']==27729
print('ALL TESTS PASSED')
