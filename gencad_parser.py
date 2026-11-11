from __future__ import annotations
import json, re, hashlib
from pathlib import Path
from collections import defaultdict

NUM = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?'

def tokens(line: str):
    # GenCAD values are whitespace separated; quoted strings stay intact.
    import shlex
    try: return shlex.split(line, posix=True)
    except ValueError: return line.split()

def fnum(s):
    try: return float(s)
    except Exception: return None

def parse_file(path: str):
    raw = Path(path).read_bytes()
    text = raw.decode('latin-1')
    lines = text.splitlines()
    sections = defaultdict(list)
    sec = None
    for line in lines:
        s = line.strip()
        if s.startswith('$') and not s.startswith('$END'):
            sec = s
            sections[sec]  # ensure section exists
        elif s.startswith('$END'):
            sec = None
        elif sec is not None and s:
            sections[sec].append(s)

    out = {
        'meta': {'format':'GenCAD 1.4', 'source_name':Path(path).name,
                 'source_size':len(raw), 'source_sha256':hashlib.sha256(raw).hexdigest(),
                 'raw_header':sections.get('$HEADER',[])},
        'board_artworks':[], 'pads':[], 'padstacks':[], 'shapes':[],
        'components':[], 'devices':[], 'signals':[], 'tracks':[],
        'layers':[], 'routes':[], 'mechanical_holes':[],
        'raw_sections':{k:v for k,v in sections.items()}
    }
    # Header interpretation
    for l in sections.get('$HEADER',[]):
        t=tokens(l)
        if not t: continue
        if t[0]=='UNITS' and len(t)>=3: out['meta']['units']={'kind':t[1],'value':fnum(t[2])}
        elif t[0]=='ORIGIN' and len(t)>=3: out['meta']['origin']=[fnum(t[1]),fnum(t[2])]
        elif t[0]=='ATTRIBUTE' and len(t)>=4: out['meta'].setdefault('attributes',[]).append(t[1:])
        elif t[0] in ('DRAWING','REVISION','USER','INTERTRACK','GENCAD'):
            out['meta'].setdefault('header_fields',[]).append(t)

    # Generic geometry parser used in board artwork and pad definitions.
    def geom_record(t):
        typ=t[0].upper()
        if typ=='LINE' and len(t)>=5:
            return {'type':'line','p1':[fnum(t[1]),fnum(t[2])],'p2':[fnum(t[3]),fnum(t[4])],'raw':t}
        if typ=='ARC' and len(t)>=7:
            return {'type':'arc','start':[fnum(t[1]),fnum(t[2])], 'end':[fnum(t[3]),fnum(t[4])], 'center':[fnum(t[5]),fnum(t[6])], 'raw':t}
        if typ=='CIRCLE' and len(t)>=4:
            return {'type':'circle','center':[fnum(t[1]),fnum(t[2])],'radius':fnum(t[3]),'raw':t}
        if typ=='RECTANGLE' and len(t)>=5:
            return {'type':'rectangle','x':fnum(t[1]),'y':fnum(t[2]),'width':fnum(t[3]),'height':fnum(t[4]),'raw':t}
        return {'type':'unknown','raw':t}

    # $BOARD artwork groups
    current=None
    for l in sections.get('$BOARD',[]):
        t=tokens(l)
        if not t: continue
        if t[0]=='ARTWORK' and len(t)>=3:
            current={'name':t[1],'layer':t[2],'geometry':[]}; out['board_artworks'].append(current)
        elif current is not None:
            current['geometry'].append(geom_record(t))

    # $PADS
    current=None
    for l in sections.get('$PADS',[]):
        t=tokens(l)
        if not t: continue
        if t[0]=='PAD' and len(t)>=2:
            current={'name':t[1],'pad_type':t[2] if len(t)>2 else None,'attributes':t[3:],'geometry':[]}; out['pads'].append(current)
        elif current is not None:
            current['geometry'].append(geom_record(t))

    # $PADSTACKS
    current=None
    for l in sections.get('$PADSTACKS',[]):
        t=tokens(l)
        if not t: continue
        if t[0]=='PADSTACK' and len(t)>=2:
            current={'name':t[1],'drill':fnum(t[2]) if len(t)>2 else None,'pads':[],'attributes':[]}; out['padstacks'].append(current)
        elif current is not None and t[0]=='PAD' and len(t)>=2:
            current['pads'].append({'pad':t[1],'layer':t[2] if len(t)>2 else None,'rotation':fnum(t[3]) if len(t)>3 else None,'mirror':t[4] if len(t)>4 else None,'raw':t})
        elif current is not None and t[0]=='ATTRIBUTE': current['attributes'].append(t[1:])

    # $SHAPES
    current=None
    for l in sections.get('$SHAPES',[]):
        t=tokens(l)
        if not t: continue
        if t[0]=='SHAPE' and len(t)>=2:
            current={'name':t[1],'pins':[],'inserts':[],'other':[]}; out['shapes'].append(current)
        elif current is not None and t[0]=='PIN' and len(t)>=7:
            # PIN number padstack x y layer rotation [mirror]
            current['pins'].append({'number':t[1],'padstack':t[2],'x':fnum(t[3]),'y':fnum(t[4]),'layer':t[5],'rotation':fnum(t[6]),'extra':t[7:]})
        elif current is not None and t[0]=='INSERT': current['inserts'].append(t[1:])
        elif current is not None: current['other'].append(t)

    # $COMPONENTS
    current=None
    for l in sections.get('$COMPONENTS',[]):
        t=tokens(l)
        if not t: continue
        if t[0]=='COMPONENT' and len(t)>=2:
            current={'reference':t[1]}; out['components'].append(current)
        elif current is not None:
            if t[0]=='PLACE' and len(t)>=3: current['position']=[fnum(t[1]),fnum(t[2])]
            elif t[0]=='LAYER' and len(t)>=2: current['layer']=t[1]
            elif t[0]=='ROTATION' and len(t)>=2: current['rotation']=fnum(t[1])
            elif t[0]=='SHAPE' and len(t)>=2: current['shape']=t[1]; current['shape_extra']=t[2:]
            elif t[0]=='DEVICE' and len(t)>=2: current['device']=t[1]
            else: current.setdefault('other',[]).append(t)

    # $DEVICES
    current=None
    for l in sections.get('$DEVICES',[]):
        t=tokens(l)
        if not t: continue
        if t[0]=='DEVICE' and len(t)>=2:
            current={'name':t[1],'parts':[],'other':[]}; out['devices'].append(current)
        elif current is not None and t[0]=='PART': current['parts'].append(t[1:])
        elif current is not None: current['other'].append(t)

    # $SIGNALS
    current=None
    for l in sections.get('$SIGNALS',[]):
        t=tokens(l)
        if not t: continue
        if t[0]=='SIGNAL' and len(t)>=2:
            current={'name':t[1],'nodes':[]}; out['signals'].append(current)
        elif current is not None and t[0]=='NODE' and len(t)>=3:
            current['nodes'].append({'component':t[1],'pin':t[2]})
        elif current is not None: current.setdefault('other',[]).append(t)

    # $TRACKS and $LAYERS
    for l in sections.get('$TRACKS',[]):
        t=tokens(l)
        if t and t[0]=='TRACK' and len(t)>=3: out['tracks'].append({'id':t[1],'width':fnum(t[2]),'raw':t})
    for l in sections.get('$LAYERS',[]):
        t=tokens(l)
        if t and t[0]=='DEFINE' and len(t)>=3: out['layers'].append({'name':t[1],'type':t[2],'raw':t})

    # $ROUTES: preserve the exact order of LINE/ARC/VIA primitives as well as context.
    # This matters because vias are interleaved with track segments in the source.
    current=None; active_track=None; active_layer=None
    for l in sections.get('$ROUTES',[]):
        t=tokens(l)
        if not t: continue
        if t[0]=='ROUTE' and len(t)>=2:
            current={'net':t[1],'segments':[],'vias':[],'primitives':[],'other':[]}
            out['routes'].append(current); active_track=None; active_layer=None
        elif current is not None and t[0]=='TRACK' and len(t)>=2:
            active_track=t[1]
        elif current is not None and t[0]=='LAYER' and len(t)>=2:
            active_layer=t[1]
        elif current is not None and t[0] in ('LINE','ARC'):
            g=geom_record(t)
            g.update({'track_id':active_track,'layer':active_layer,'source_order':len(current['primitives'])})
            idx=len(current['segments']); current['segments'].append(g)
            current['primitives'].append({'kind':'segment','index':idx})
        elif current is not None and t[0]=='VIA':
            v={'padstack':t[1] if len(t)>1 else None,'x':fnum(t[2]) if len(t)>2 else None,
               'y':fnum(t[3]) if len(t)>3 else None,'span':t[4] if len(t)>4 else None,
               'offset':t[5] if len(t)>5 else None,'name':t[6] if len(t)>6 else None,
               'raw':t,'layer_context':active_layer,'track_context':active_track,
               'source_order':len(current['primitives'])}
            idx=len(current['vias']); current['vias'].append(v)
            current['primitives'].append({'kind':'via','index':idx})
        elif current is not None:
            current['other'].append(t)

    for l in sections.get('$MECH',[]):
        t=tokens(l)
        if t and t[0]=='HOLE' and len(t)>=4: out['mechanical_holes'].append({'x':fnum(t[1]),'y':fnum(t[2]),'diameter':fnum(t[3]),'raw':t})

    # Cross-reference / consistency checks
    shape_names={x['name'] for x in out['shapes']}
    pad_names={x['name'] for x in out['pads']}
    stack_names={x['name'] for x in out['padstacks']}
    comp_names={x['reference'] for x in out['components']}
    shape_by_name={x['name']:x for x in out['shapes']}
    missing_shape=[c['reference'] for c in out['components'] if c.get('shape') not in shape_names]
    missing_stack=[]
    for sh in out['shapes']:
        for pin in sh['pins']:
            if pin['padstack'] not in stack_names: missing_stack.append((sh['name'],pin['number'],pin['padstack']))
    missing_pad=[]
    for ps in out['padstacks']:
        for p in ps['pads']:
            if p['pad'] not in pad_names: missing_pad.append((ps['name'],p['pad']))
    missing_node_components=[]; missing_node_pins=[]; node_count=0
    for sig in out['signals']:
        for n in sig['nodes']:
            node_count+=1
            if n['component'] not in comp_names: missing_node_components.append((sig['name'],n))
            else:
                c=next((x for x in out['components'] if x['reference']==n['component']),None)
                sh=shape_by_name.get(c.get('shape')) if c else None
                if sh and not any(p['number']==n['pin'] for p in sh['pins']): missing_node_pins.append((sig['name'],n))
    track_ids={x['id'] for x in out['tracks']}
    used_track_ids={s.get('track_id') for r in out['routes'] for s in r['segments']}
    missing_route_tracks=sorted(x for x in used_track_ids if x is not None and x not in track_ids)
    route_arcs=[s for r in out['routes'] for s in r['segments'] if s['type']=='arc']
    board_arcs=[g for a in out['board_artworks'] for g in a['geometry'] if g['type']=='arc']
    all_arcs=route_arcs+board_arcs
    arc_radius_errors=[]; arc_180_count=0
    for arc in all_arcs:
        c=arc['center']; start=arc.get('start'); end=arc.get('end')
        r1=((start[0]-c[0])**2+(start[1]-c[1])**2)**0.5
        r2=((end[0]-c[0])**2+(end[1]-c[1])**2)**0.5
        arc_radius_errors.append(abs(r1-r2))
        a1=__import__('math').atan2(start[1]-c[1],start[0]-c[0])
        a2=__import__('math').atan2(end[1]-c[1],end[0]-c[0])
        delta=(a2-a1)%(2*__import__('math').pi)
        if abs(delta-__import__('math').pi)<1e-5: arc_180_count+=1
    out['validation']={
        'component_count':len(out['components']), 'shape_count':len(out['shapes']),
        'pin_definition_count':sum(len(s['pins']) for s in out['shapes']),
        'pad_count':len(out['pads']), 'padstack_count':len(out['padstacks']),
        'signal_count':len(out['signals']), 'node_count':node_count,
        'route_count':len(out['routes']), 'route_line_count':sum(1 for r in out['routes'] for s in r['segments'] if s['type']=='line'),
        'route_arc_count':len(route_arcs), 'route_via_count':sum(len(r['vias']) for r in out['routes']),
        'route_primitive_count':sum(len(r['primitives']) for r in out['routes']),
        'track_definition_count':len(out['tracks']), 'used_track_id_count':len(used_track_ids),
        'missing_route_track_definitions':len(missing_route_tracks),
        'board_artwork_count':len(out['board_artworks']),
        'board_line_count':sum(1 for a in out['board_artworks'] for g in a['geometry'] if g['type']=='line'),
        'board_arc_count':len(board_arcs), 'arc_radius_error_max':max(arc_radius_errors,default=0),
        'arcs_with_180_degree_ambiguity':arc_180_count,
        'mechanical_hole_count':len(out['mechanical_holes']),
        'missing_component_shapes':len(missing_shape), 'missing_pin_padstacks':len(missing_stack),
        'missing_pad_geometry_refs':len(missing_pad), 'missing_node_components':len(missing_node_components),
        'missing_node_pins':len(missing_node_pins),
        'missing_route_track_examples':missing_route_tracks[:10],
        'missing_examples':{'shapes':missing_shape[:10],'stacks':missing_stack[:10],'pads':missing_pad[:10], 'node_components':missing_node_components[:10], 'node_pins':missing_node_pins[:10]}
    }
    return out, raw

if __name__=='__main__':
    import sys
    data, raw=parse_file(sys.argv[1])
    print(json.dumps(data['validation'],indent=2))
