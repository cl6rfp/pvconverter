from __future__ import annotations
import argparse, hashlib, json, re, base64
from pathlib import Path
import math
from gencad_parser import parse_file
from pvf import write_pvf


def enrich_geometry(g):
    # Keep source geometry and add non-destructive arc diagnostics/candidates.
    out=dict(g)
    if g.get('type')=='arc':
        start=g['start']; end=g['end']; center=g['center']
        a1=math.atan2(start[1]-center[1],start[0]-center[0])
        a2=math.atan2(end[1]-center[1],end[0]-center[0])
        ccw=math.degrees(a2-a1)%360.0
        r1=math.dist(start,center); r2=math.dist(end,center)
        out.update({'arc_sweep_ccw_deg':ccw,
                    'arc_sweep_cw_deg':ccw-360.0 if ccw else -360.0,
                    'arc_sweep_status':'direction_not_explicit_in_parsed_source; both_candidates_retained',
                    'radius_start':r1,'radius_end':r2,'arc_radius_error':abs(r1-r2)})
    return out


def build_model(data, raw):
    # Stable IDs are assigned in source order. Source names remain available.
    comps=data['components']; shapes=data['shapes']; pads=data['pads']; stacks=data['padstacks']; signals=data['signals']; routes=data['routes']
    shape_ids={s['name']:i+1 for i,s in enumerate(shapes)}
    pad_ids={p['name']:i+1 for i,p in enumerate(pads)}
    stack_ids={p['name']:i+1 for i,p in enumerate(stacks)}
    comp_ids={c['reference']:i+1 for i,c in enumerate(comps)}
    net_ids={n['name']:i+1 for i,n in enumerate(signals)}
    track_widths={t['id']:t['width'] for t in data['tracks']}
    # Build a physical copper stack from source evidence. The header declares four
    # routing layers and padstacks consistently list TOP, INNER, INNER, BOTTOM.
    # Keep the original label while giving the two repeated INNER entries distinct IDs.
    layer_specs=[]
    def add_layer(name, kind='unspecified', source_name=None, stack_order=None):
        if not name or any(x['name']==name for x in layer_specs): return
        layer_specs.append({'name':name,'source_name':source_name or name,'type':kind,'stack_order':stack_order})
    add_layer('TOP','copper','TOP',1)
    add_layer('INNER_1','copper','INNER',2)
    add_layer('INNER_2','copper','INNER',3)
    add_layer('BOTTOM','copper','BOTTOM',4)
    for l in data['layers']: add_layer(l['name'],l['type'],l['name'],None)
    add_layer('ALL','all_layers','ALL',None)
    for c in comps: add_layer(c.get('layer'))
    for r in routes:
        for seg in r['segments']: add_layer(seg.get('layer'))
    layer_ids={x['name']:i+1 for i,x in enumerate(layer_specs)}
    layers=[dict(x,id=layer_ids[x['name']]) for x in layer_specs]

    component_records=[]; pin_records=[]; pin_lookup={}; pin_id=1
    for c in comps:
        cid=comp_ids[c['reference']]
        sid=shape_ids.get(c.get('shape'),0)
        component_records.append({'id':cid,'reference':c['reference'],'x':c.get('position',[None,None])[0], 'y':c.get('position',[None,None])[1], 'layer_id':layer_ids.get(c.get('layer'),0),'source_layer':c.get('layer'),'rotation_deg':c.get('rotation'),'shape_id':sid,'device':c.get('device'),'shape_transform_tokens':c.get('shape_extra',[]),'source_extra':c.get('other',[])})
        shape=next((s for s in shapes if s['name']==c.get('shape')),None)
        if shape:
            for idx,p in enumerate(shape['pins']):
                rec={'id':pin_id,'component_id':cid,'shape_id':sid,'shape_pin_index':idx,'number':p['number'],'padstack_id':stack_ids.get(p['padstack'],0),'x_local':p['x'],'y_local':p['y'],'layer_id':layer_ids.get(p['layer'],0),'source_layer':p['layer'],'rotation_deg':p['rotation'],'extra':p.get('extra',[])}
                pin_records.append(rec)
                pin_lookup[(c['reference'],p['number'])]=pin_id
                pin_id+=1

    net_records=[]
    for n in signals:
        con=[]
        for node in n['nodes']:
            pid=pin_lookup.get((node['component'],node['pin']),0)
            con.append({'pin_id':pid,'component_ref':node['component'],'pin_number':node['pin']})
        net_records.append({'id':net_ids[n['name']],'name':n['name'],'connections':con})

    # Store segments and vias in their own blocks, but also emit PRIM to preserve
    # their exact interleaved source order inside each ROUTE.
    seg_records=[]; via_records=[]; route_records=[]; primitive_records=[]
    segid=1; viaid=1; routeid=1
    for r in routes:
        nid=net_ids.get(r['net'],0); first_s=segid; first_v=viaid
        first_prim=len(primitive_records)+1
        seg_ids={}; via_ids={}
        for primitive in r.get('primitives',[]):
            if primitive['kind']=='segment':
                s=r['segments'][primitive['index']]
                rec={'id':segid,'route_id':routeid,'route_order':s['source_order'],'net_id':nid,
                     'type':s['type'],'track_id':s.get('track_id'),
                     'width_source':track_widths.get(s.get('track_id')),
                     'layer_id':layer_ids.get(s.get('layer'),0),'source_layer':s.get('layer'),
                     'source_raw':s.get('raw')}
                if s['type']=='line':
                    rec['p1']=s.get('p1'); rec['p2']=s.get('p2')
                else:
                    import math
                    rec['start']=s['start']; rec['end']=s['end']; rec['center']=s['center']
                    a1=math.atan2(s['start'][1]-s['center'][1],s['start'][0]-s['center'][0])
                    a2=math.atan2(s['end'][1]-s['center'][1],s['end'][0]-s['center'][0])
                    ccw=(math.degrees(a2-a1)%360.0)
                    rec['arc_sweep_ccw_deg']=ccw
                    rec['arc_sweep_cw_deg']=ccw-360.0 if ccw else -360.0
                    rec['arc_sweep_status']='direction_not_explicit_in_parsed_source; both_candidates_retained'
                    rec['radius_start']=math.dist(s['start'],s['center'])
                    rec['radius_end']=math.dist(s['end'],s['center'])
                    rec['arc_radius_error']=abs(rec['radius_start']-rec['radius_end'])
                seg_records.append(rec); seg_ids[primitive['index']]=segid
                primitive_records.append({'route_id':routeid,'order':s['source_order'],'kind':'segment','ref_id':segid})
                segid+=1
            elif primitive['kind']=='via':
                v=r['vias'][primitive['index']]
                via_records.append({'id':viaid,'route_id':routeid,'route_order':v['source_order'],
                    'net_id':nid,'padstack_id':stack_ids.get(v.get('padstack'),0),
                    'padstack_name':v.get('padstack'),'x':v.get('x'),'y':v.get('y'),
                    'span':v.get('span'),'offset':v.get('offset'),'name':v.get('name'),
                    'track_context':v.get('track_context'),'source_layer_context':v.get('layer_context'),
                    'source_raw':v.get('raw')})
                via_ids[primitive['index']]=viaid
                primitive_records.append({'route_id':routeid,'order':v['source_order'],'kind':'via','ref_id':viaid})
                viaid+=1
        route_records.append({'id':routeid,'net_id':nid,'net_name':r['net'],
            'segment_start_id':first_s if segid>first_s else 0,'segment_count':segid-first_s,
            'via_start_id':first_v if viaid>first_v else 0,'via_count':viaid-first_v,
            'primitive_start':first_prim if len(primitive_records)>=first_prim else 0,
            'primitive_count':len(primitive_records)-first_prim+1 if len(primitive_records)>=first_prim else 0,
            'other':r.get('other',[])})
        routeid+=1

    # Geometry and pad definitions retain source coordinates as parsed plus raw token arrays.
    shape_records=[{'id':shape_ids[s['name']],'name':s['name'],'pin_count':len(s['pins']),'pins':s['pins'],'inserts':s['inserts'],'other':s['other']} for s in shapes]
    pad_records=[{'id':pad_ids[p['name']],'name':p['name'],'pad_type':p['pad_type'],'attributes':p['attributes'],'geometry':[enrich_geometry(g) for g in p['geometry']]} for p in pads]
    stack_records=[]
    for st in stacks:
        inner_index=0; stack_pads=[]
        for entry in st['pads']:
            source_layer=entry.get('layer')
            if source_layer=='INNER':
                inner_index+=1
                normalized_layer=f'INNER_{inner_index}'
            else:
                normalized_layer=source_layer
            stack_pads.append(dict(entry,pad_id=pad_ids.get(entry['pad'],0),
                layer_id=layer_ids.get(normalized_layer,0),normalized_layer=normalized_layer,
                source_layer=source_layer))
        stack_records.append({'id':stack_ids[st['name']],'name':st['name'],'drill':st['drill'],
            'pads':stack_pads,'attributes':st['attributes'],
            'inner_layer_entries':inner_index,'source_pad_order_preserved':True})
    artwork_records=[]
    for i,a in enumerate(data['board_artworks'],1): artwork_records.append({'id':i,'name':a['name'],'layer_id':layer_ids.get(a['layer'],0),'source_layer':a['layer'],'geometry':[enrich_geometry(g) for g in a['geometry']]})
    meta=dict(data['meta'])
    meta.update({'pv_core_schema':'0.1','coordinate_storage':'source_user_units_as_decimal_values','coordinate_conversion':'not_applied','units_interpretation':'unconfirmed; original GenCAD USER 1000 retained','copper_stack_interpretation':'4 routing layers declared; repeated INNER padstack entries normalized by occurrence order to INNER_1 and INNER_2; source labels retained','bottom_component_transform':'source SHAPE tokens retained verbatim; MIRRORY FLIP semantics not applied until verified','source_sha256':hashlib.sha256(raw).hexdigest()})
    blocks=[
      {'id':'META','data':meta,'record_count':1,'flags':1},
      {'id':'LAYR','data':layers,'record_count':len(layers)},
      {'id':'COMP','data':component_records,'record_count':len(component_records)},
      {'id':'SHAP','data':shape_records,'record_count':len(shape_records)},
      {'id':'PINS','data':pin_records,'record_count':len(pin_records)},
      {'id':'PADS','data':pad_records,'record_count':len(pad_records)},
      {'id':'PSTK','data':stack_records,'record_count':len(stack_records)},
      {'id':'NETS','data':net_records,'record_count':len(net_records)},
      {'id':'SEGS','data':seg_records,'record_count':len(seg_records)},
      {'id':'VIAS','data':via_records,'record_count':len(via_records)},
      {'id':'PRIM','data':primitive_records,'record_count':len(primitive_records),'flags':1},
      {'id':'ROUT','data':route_records,'record_count':len(route_records)},
      {'id':'HOLE','data':data['mechanical_holes'],'record_count':len(data['mechanical_holes'])},
      {'id':'TRKS','data':data['tracks'],'record_count':len(data['tracks'])},
      {'id':'DEVS','data':data['devices'],'record_count':len(data['devices'])},
      {'id':'ARTW','data':artwork_records,'record_count':len(artwork_records)},
      {'id':'SRCE','data':{'encoding':'base64-latin-1','sha256':hashlib.sha256(raw).hexdigest(),'data':base64.b64encode(raw).decode('ascii')},'record_count':1,'flags':0},
    ]
    return blocks


def main():
    ap=argparse.ArgumentParser(description='Build a PVF prototype from GenCAD 1.4')
    ap.add_argument('input'); ap.add_argument('output')
    args=ap.parse_args()
    data,raw=parse_file(args.input)
    print('Source validation:')
    print(json.dumps(data['validation'],indent=2))
    blocks=build_model(data,raw)
    info=write_pvf(args.output,blocks)
    print('\nPVF created:')
    print(json.dumps(info,indent=2))

if __name__=='__main__': main()
