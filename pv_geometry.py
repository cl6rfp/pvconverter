"""Geometry inspection and SVG preview for PVF 1.0.

The SVG is a diagnostic view, not a fabrication export. Source coordinates and
ambiguous arc directions remain unchanged in the PV file. For display only,
ambiguous arcs use the CCW candidate and are counted in the report.
"""
from __future__ import annotations
import argparse, base64, hashlib, html, json, math
from pathlib import Path
from pvf import read_pvf, PVFError

LAYER_COLORS = {
    'TOP': '#d84a38', 'INNER_1': '#3b82c4', 'INNER_2': '#2b9b75',
    'BOTTOM': '#8b5cf6', 'ALL': '#888888'
}



def _arc_extrema_points(g, sweep_deg=None):
    """Return exact axis-aligned extrema points for a circular SVG arc."""
    sx, sy = map(float, g['start'])
    ex, ey = map(float, g['end'])
    cx, cy = map(float, g['center'])
    r1 = math.hypot(sx-cx, sy-cy)
    r2 = math.hypot(ex-cx, ey-cy)
    radius = (r1+r2)/2.0
    if radius <= 1e-12:
        return [(sx, sy), (ex, ey)]
    sweep = float(sweep_deg if sweep_deg is not None else g.get('arc_sweep_ccw_deg', 0.0))
    start = math.atan2(sy-cy, sx-cx)
    end = math.atan2(ey-cy, ex-cx)
    if abs(sweep) < 1e-9:
        sweep = math.degrees((end-start) % (2*math.pi))
    points = [(sx, sy), (ex, ey)]
    direction = 1.0 if sweep >= 0 else -1.0
    span = abs(math.radians(sweep))
    for angle in (0.0, math.pi/2, math.pi, 3*math.pi/2):
        delta = ((angle-start) % (2*math.pi)) if direction > 0 else ((start-angle) % (2*math.pi))
        if delta <= span + 1e-10:
            point = (cx + radius*math.cos(angle), cy + radius*math.sin(angle))
            if all(math.dist(point, existing) > 1e-10 for existing in points):
                points.append(point)
    return points


def _xy_bounds(points):
    pts=[(float(x),float(y)) for x,y in points if x is not None and y is not None]
    if not pts: return (-1.0,-1.0,1.0,1.0)
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    dx=max(xs)-min(xs); dy=max(ys)-min(ys)
    pad=max(dx,dy,1.0)*0.025
    return min(xs)-pad,min(ys)-pad,max(xs)+pad,max(ys)+pad


def _arc_path(g):
    sx,sy=g['start']; ex,ey=g['end']; cx,cy=g['center']
    r1=math.hypot(sx-cx,sy-cy); r2=math.hypot(ex-cx,ey-cy)
    r=(r1+r2)/2
    sweep=float(g.get('display_sweep_deg',g.get('arc_sweep_ccw_deg',0.0)))
    large=1 if abs(sweep)>180.0+1e-7 else 0
    # The parent SVG group flips Y. SVG's sweep=1 is clockwise in its
    # native y-down coordinate system; the reflection makes it CCW in the
    # original GenCAD y-up coordinate system. Therefore the mapping is
    # intentionally the opposite of the untransformed SVG mapping.
    svg_sweep=1 if sweep >= 0 else 0
    return f'M {sx:.6f},{sy:.6f} A {r:.6f},{r:.6f} 0 {large} {svg_sweep} {ex:.6f},{ey:.6f}'


def _unit(v):
    n=math.hypot(v[0],v[1])
    return (v[0]/n,v[1]/n) if n>1e-12 else None


def _arc_tangent(g, at_start, ccw):
    x,y=(g['start'] if at_start else g['end'])
    cx,cy=g['center']; rx=x-cx; ry=y-cy
    return _unit((-ry,rx) if ccw else (ry,-rx))


def _primitive_ends(item, seg_by, via_by):
    if item.get('kind')=='segment':
        g=seg_by.get(item.get('ref_id'))
        if not g: return None,None
        if g.get('type')=='line': return tuple(g['p1']),tuple(g['p2'])
        if g.get('type')=='arc': return tuple(g['start']),tuple(g['end'])
    elif item.get('kind')=='via':
        v=via_by.get(item.get('ref_id'))
        if v and v.get('x') is not None and v.get('y') is not None:
            q=(float(v['x']),float(v['y'])); return q,q
    return None,None


def _line_tangent_at_connection(item, seg_by, point, entering):
    """Return the line direction at a connected endpoint, oriented along travel."""
    if not item or item.get('kind') != 'segment':
        return None
    g=seg_by.get(item.get('ref_id'))
    if not g or g.get('type') != 'line':
        return None
    p1=tuple(g['p1']); p2=tuple(g['p2'])
    if math.dist(p2, point) <= 1e-4:
        v=(p2[0]-p1[0],p2[1]-p1[1]) if entering else (p1[0]-p2[0],p1[1]-p2[1])
    elif math.dist(p1, point) <= 1e-4:
        v=(p1[0]-p2[0],p1[1]-p2[1]) if entering else (p2[0]-p1[0],p2[1]-p1[1])
    else:
        return None
    return _unit(v)


def _resolve_route_arc_sweeps(routes, prims, segs, vias, tolerance=1e-4):
    """Resolve display sweep using route continuity in either traversal direction.

    GenCAD stores geometric start/end points, but route order may traverse an
    arc from end to start. Evaluate both endpoint orientations and both arc
    loci. The selected sweep is always expressed from the stored start to end,
    because that is the direction consumed by the SVG path renderer.
    """
    seg_by={x['id']:x for x in segs}; via_by={x['id']:x for x in vias}
    chosen={}; resolved=0; unresolved=0; no_neighbors=0; reverse_traversals=0
    for route in routes:
        stream=prims[route['primitive_start']-1:route['primitive_start']-1+route['primitive_count']]
        for i,item in enumerate(stream):
            if item.get('kind')!='segment': continue
            arc=seg_by.get(item.get('ref_id'))
            if not arc or arc.get('type')!='arc': continue
            a1=math.atan2(arc['start'][1]-arc['center'][1],arc['start'][0]-arc['center'][0])
            a2=math.atan2(arc['end'][1]-arc['center'][1],arc['end'][0]-arc['center'][0])
            ccw=math.degrees((a2-a1)%(2*math.pi))
            candidates=[ccw, ccw-360.0 if ccw else -360.0]
            prev=stream[i-1] if i>0 else None
            nxt=stream[i+1] if i+1<len(stream) else None
            scores=[]
            # forward=True means route travels stored start -> end.
            for sweep in candidates:
                ccw_dir=sweep>=0
                for forward in (True,False):
                    entry=arc['start'] if forward else arc['end']
                    exit_point=arc['end'] if forward else arc['start']
                    incoming=_line_tangent_at_connection(prev,seg_by,tuple(entry),True)
                    outgoing=_line_tangent_at_connection(nxt,seg_by,tuple(exit_point),False)
                    entry_tangent=_arc_tangent(arc,forward,ccw_dir)
                    exit_tangent=_arc_tangent(arc,not forward,ccw_dir)
                    # Reversing route traversal reverses both geometric tangents.
                    if not forward:
                        entry_tangent=tuple(-v for v in entry_tangent)
                        exit_tangent=tuple(-v for v in exit_tangent)
                    score=0.0; evidence=0
                    if incoming and entry_tangent:
                        score += sum(x*y for x,y in zip(incoming,entry_tangent)); evidence += 1
                    if outgoing and exit_tangent:
                        score += sum(x*y for x,y in zip(exit_tangent,outgoing)); evidence += 1
                    scores.append((score,evidence,sweep,forward))
            scores.sort(key=lambda z:z[0],reverse=True)
            if scores[0][1] and scores[0][0]-scores[1][0] > 0.15:
                chosen[arc['id']]=scores[0][2]; resolved+=1
                if not scores[0][3]: reverse_traversals+=1
            else:
                # No source direction is fabricated when neighboring geometry
                # cannot distinguish the candidates.
                minor=ccw if ccw<=180.0 else ccw-360.0
                chosen[arc['id']]=minor if abs(minor)>1e-7 else 180.0
                unresolved+=1
                if not any(s[1] for s in scores): no_neighbors+=1
    return chosen, {'arcs_direction_inferred_from_continuity':resolved,
                    'arcs_direction_ambiguous_display_fallback':unresolved,
                    'arcs_without_connected_line_tangent':no_neighbors,
                    'arcs_route_traversed_end_to_start':reverse_traversals}


def _geom_svg(g, color, width=1.0):
    typ=g.get('type')
    if typ=='line':
        x1,y1=g['p1']; x2,y2=g['p2']
        return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" />'
    if typ=='arc':
        return f'<path d="{_arc_path(g)}" fill="none" stroke="{color}" stroke-width="{width}" />'
    if typ=='circle':
        x,y=g['center']; r=float(g['radius'])
        return f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{color}" stroke-width="{width}" />'
    if typ=='rectangle':
        x,y,w,h=map(float,(g['x'],g['y'],g['width'],g['height']))
        # GenCAD RECTANGLE stores the lower-left corner followed by width and height.
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{color}" stroke-width="{width}" />'
    return ''


def geometry_report(pv_path):
    doc=read_pvf(pv_path); b={k:v['data'] for k,v in doc['blocks'].items()}
    required=('META','LAYR','COMP','SHAP','PINS','PADS','PSTK','NETS','SEGS','VIAS','PRIM','ROUT','HOLE','TRKS','ARTW')
    missing=[x for x in required if x not in b]
    if missing: raise PVFError('Missing required blocks: '+', '.join(missing))
    segs=b['SEGS']; vias=b['VIAS']; routes=b['ROUT']; prims=b['PRIM']
    arcs=sum(1 for s in segs if s.get('type')=='arc')
    arcs+=sum(1 for p in b['PADS'] for g in p.get('geometry',[]) if g.get('type')=='arc')
    arcs+=sum(1 for a in b['ARTW'] for g in a.get('geometry',[]) if g.get('type')=='arc')
    all_arc_records=[s for s in segs if s.get('type')=='arc']
    all_arc_records += [g for p in b['PADS'] for g in p.get('geometry',[]) if g.get('type')=='arc']
    all_arc_records += [g for a in b['ARTW'] for g in a.get('geometry',[]) if g.get('type')=='arc']
    direction_not_explicit=sum(1 for g in all_arc_records if 'direction_not_explicit' in g.get('arc_sweep_status',''))
    semicircle_arcs=sum(1 for g in all_arc_records if abs(abs(float(g.get('arc_sweep_ccw_deg',0.0)))-180.0)<1e-6)
    source_block=b.get('SRCE',{})
    source_hash_ok=None
    if source_block.get('encoding')=='base64-latin-1':
        source_bytes=base64.b64decode(source_block['data'])
        source_hash_ok=hashlib.sha256(source_bytes).hexdigest()==b['META'].get('source_sha256')==source_block.get('sha256')
    validation_data=b.get('VALD',{})
    ref_errors=[]
    seg_by={x['id']:x for x in segs}; via_by={x['id']:x for x in vias}
    for r in routes:
        stream=prims[r['primitive_start']-1:r['primitive_start']-1+r['primitive_count']]
        if len(stream)!=r['primitive_count']:
            ref_errors.append(f"route {r['id']}: primitive range length mismatch"); continue
        for order,item in enumerate(stream):
            if item.get('route_id')!=r['id'] or item.get('order')!=order:
                ref_errors.append(f"route {r['id']}: primitive order mismatch at {order}"); break
            table=seg_by if item.get('kind')=='segment' else via_by if item.get('kind')=='via' else {}
            obj=table.get(item.get('ref_id'))
            if obj is None or obj.get('route_id')!=r['id'] or obj.get('route_order')!=order:
                ref_errors.append(f"route {r['id']}: broken {item.get('kind')} reference at {order}"); break
    return {
      'version':doc['version'],'file_size':doc['file_size'],'blocks':len(doc['blocks']),
      'components':len(b['COMP']),'shapes':len(b['SHAP']),'pins':len(b['PINS']),
      'nets':len(b['NETS']),'routes':len(routes),'segments':len(segs),'vias':len(vias),
      'route_primitives':len(prims),'artwork_groups':len(b['ARTW']),'mechanical_holes':len(b['HOLE']),
      'arc_records':arcs,'arc_direction_not_explicit':direction_not_explicit,
      'semicircle_arcs_with_equal_sweep_candidates':semicircle_arcs,
      'source_sha256_matches':source_hash_ok,
      'route_reference_errors':ref_errors,'valid':not ref_errors and source_hash_ok is not False,
      'pv_validation_status':validation_data.get('status'),
      'integrity_diagnostics':validation_data.get('integrity_diagnostics')
    }


def _convex_hull(points):
    """Return a monotone-chain hull for a clearly marked estimated envelope."""
    pts=sorted(set((float(x),float(y)) for x,y in points))
    if len(pts)<3: return pts
    def cross(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[]
    for q in pts:
        while len(lower)>=2 and cross(lower[-2],lower[-1],q)<=0: lower.pop()
        lower.append(q)
    upper=[]
    for q in reversed(pts):
        while len(upper)>=2 and cross(upper[-2],upper[-1],q)<=0: upper.pop()
        upper.append(q)
    return lower[:-1]+upper[:-1]


def _pad_local_extents(padrec):
    xs=[]; ys=[]
    for g in padrec.get('geometry',[]):
        typ=g.get('type')
        if typ=='circle':
            x,y=g.get('center',[0,0]); r=float(g.get('radius') or 0)
            xs.extend([float(x)-r,float(x)+r]); ys.extend([float(y)-r,float(y)+r])
        elif typ=='rectangle':
            x,y,w,h=map(float,(g['x'],g['y'],g['width'],g['height']))
            xs.extend([x,x+w]); ys.extend([y,y+h])
        else:
            for k in ('p1','p2','start','end'):
                q=g.get(k)
                if q: xs.append(float(q[0])); ys.append(float(q[1]))
    return (min(xs),min(ys),max(xs),max(ys)) if xs and ys else (-5,-5,5,5)


def export_svg(pv_path, svg_path, layer='ALL', show_components=False):
    doc=read_pvf(pv_path); b={k:v['data'] for k,v in doc['blocks'].items()}
    route_sweeps, arc_direction_report = _resolve_route_arc_sweeps(
        b.get('ROUT',[]), b.get('PRIM',[]), b.get('SEGS',[]), b.get('VIAS',[]))
    display_segs=[]
    for seg in b.get('SEGS',[]):
        item=dict(seg)
        if item.get('type')=='arc':
            item['display_sweep_deg']=route_sweeps.get(item.get('id'),item.get('arc_sweep_ccw_deg',0.0))
        display_segs.append(item)
    points=[]
    def addp(p):
        if p and len(p)>=2 and p[0] is not None and p[1] is not None: points.append(p)
    # Bounds use visible geometry, not arc centers (which are not rendered points).
    for seg in display_segs:
        if seg.get('type') == 'line':
            addp(seg.get('p1')); addp(seg.get('p2'))
        elif seg.get('type') == 'arc':
            for point in _arc_extrema_points(seg, seg.get('display_sweep_deg')):
                addp(point)
    for artwork in b.get('ARTW',[]):
        for geom in artwork.get('geometry',[]):
            if geom.get('type') == 'line':
                addp(geom.get('p1')); addp(geom.get('p2'))
            elif geom.get('type') == 'arc':
                for point in _arc_extrema_points(geom):
                    addp(point)
            elif geom.get('type') == 'circle':
                cx, cy = geom['center']; radius = float(geom['radius'])
                addp((cx-radius, cy-radius)); addp((cx+radius, cy+radius))
            elif geom.get('type') == 'rectangle':
                x, y, w, h = map(float, (geom['x'], geom['y'], geom['width'], geom['height']))
                addp((x,y)); addp((x+w,y+h))
    for v in b.get('VIAS',[]): addp((v.get('x'),v.get('y')))
    for h in b.get('HOLE',[]): addp((h.get('x'),h.get('y')))
    # Resolve model lookup tables once; the PV references are authoritative.
    shapes={x['id']:x for x in b.get('SHAP',[])}
    stacks={x['id']:x for x in b.get('PSTK',[])}
    pads={x['id']:x for x in b.get('PADS',[])}
    pins_by_component={}
    for pin in b.get('PINS',[]): pins_by_component.setdefault(pin['component_id'],[]).append(pin)
    # Include footprint pin locations in view bounds using source component coordinates.
    for c in b.get('COMP',[]):
        if c.get('x') is None or c.get('y') is None: continue
        ang=math.radians(float(c.get('rotation_deg') or 0))
        mirror=bool(c.get('shape_transform_tokens') and 'MIRRORY' in c.get('shape_transform_tokens'))
        for pin in pins_by_component.get(c.get('id'),[]):
            px=float(pin.get('x_local') or 0); py=float(pin.get('y_local') or 0)
            if mirror: px=-px
            rx=px*math.cos(ang)-py*math.sin(ang); ry=px*math.sin(ang)+py*math.cos(ang)
            addp((c['x']+rx,c['y']+ry))
    xmin,ymin,xmax,ymax=_xy_bounds(points)
    width=xmax-xmin; height=ymax-ymin
    target_w,target_h=1800,1300
    pad=max(width,height)*0.035
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{target_w}" height="{target_h}" viewBox="{xmin-pad} {-ymax-pad} {width+2*pad} {height+2*pad}">',
           '<rect x="-1000000" y="-1000000" width="2000000" height="2000000" fill="#10151d"/>',
           '<g transform="scale(1,-1)" fill="none" stroke-linecap="round" stroke-linejoin="round">']
    def allowed(src): return layer=='ALL' or src==layer
    # No board-edge primitive is present in this source. Do not invent an
    # outline from routed copper or component positions: that hull is not a
    # physical board boundary and can visually mislead repair work.
    # Existing board artwork (kept distinct from an asserted board outline).
    for a in b.get('ARTW',[]):
        if not allowed(a.get('source_layer')): continue
        color=LAYER_COLORS.get(a.get('source_layer'),'#a0a0a0')
        for g in a.get('geometry',[]):
            item=_geom_svg(g,color,1.5)
            if item: parts.append(item)
    track_width={t['id']:float(t.get('width') or 1.0) for t in b.get('TRKS',[])}
    for seg in display_segs:
        if not allowed(seg.get('source_layer')): continue
        color=LAYER_COLORS.get(seg.get('source_layer'),'#b5b5b5')
        w=max(0.5,min(track_width.get(seg.get('track_id'),1.0),50.0))
        if seg.get('type')=='line':
            x1,y1=seg['p1']; x2,y2=seg['p2']
            parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}"/>')
        elif seg.get('type')=='arc': parts.append(f'<path d="{_arc_path(seg)}" stroke="{color}" stroke-width="{w}" fill="none"/>')
    # Footprints: draw actual pad geometry through component -> shape pin -> padstack -> pad.
    # The bottom-side MIRRORY token is applied as an X reflection of local footprint coordinates;
    # the original token remains preserved in the PV and this display transform is explicitly visual.
    pad_color='#e6b85c'
    # Text labels are collected in board coordinates and emitted outside the
    # mirrored geometry group. This prevents the global Y flip and component
    # mirror/rotation transforms from flipping or relocating the text itself.
    label_parts=[]
    for c in b.get('COMP',[]):
        if c.get('x') is None or c.get('y') is None: continue
        if not allowed(c.get('source_layer')): continue
        cx,cy=float(c['x']),float(c['y'])
        angle=float(c.get('rotation_deg') or 0)
        mirror=bool(c.get('shape_transform_tokens') and 'MIRRORY' in c.get('shape_transform_tokens'))
        shape_pins=pins_by_component.get(c.get('id'),[])
        if show_components:
            parts.append(f'<g transform="translate({cx},{cy}) rotate({angle}) scale({-1 if mirror else 1},1)">')
            # Approximate body silhouette from the actual footprint pad extents.
            # It is intentionally dashed: GenCAD SHAPES contains pin placements,
            # not a manufacturer-accurate package body outline.
            body_pts=[]
            for bp in shape_pins:
                bst=stacks.get(bp.get('padstack_id'),{})
                side='BOTTOM' if c.get('source_layer')=='BOTTOM' else 'TOP'
                be=next((e for e in bst.get('pads',[]) if e.get('normalized_layer')==side),None)
                if be is None: be=next((e for e in bst.get('pads',[]) if e.get('normalized_layer') in ('TOP','BOTTOM','INNER_1','INNER_2')),None)
                brec=pads.get(be.get('pad_id'),{}) if be else {}
                bx0,by0,bx1,by1=_pad_local_extents(brec)
                px=float(bp.get('x_local') or 0); py=float(bp.get('y_local') or 0)
                pr=math.radians(float(bp.get('rotation_deg') or 0)+(float(be.get('rotation') or 0) if be else 0))
                for xx,yy in ((bx0,by0),(bx0,by1),(bx1,by0),(bx1,by1)):
                    body_pts.append((px+xx*math.cos(pr)-yy*math.sin(pr),py+xx*math.sin(pr)+yy*math.cos(pr)))
            if body_pts:
                bx0=min(q[0] for q in body_pts); bx1=max(q[0] for q in body_pts)
                by0=min(q[1] for q in body_pts); by1=max(q[1] for q in body_pts)
                span=max(bx1-bx0,by1-by0,8.0); margin=max(8.0,span*0.06)
                parts.append(f'<rect x="{bx0-margin:.4f}" y="{by0-margin:.4f}" width="{bx1-bx0+2*margin:.4f}" height="{by1-by0+2*margin:.4f}" rx="{margin*0.7:.4f}" fill="#94a3b8" fill-opacity="0.07" stroke="#cbd5e1" stroke-width="2.2" stroke-dasharray="8 5"/>')
            for pin in shape_pins:
                px=float(pin.get('x_local') or 0); py=float(pin.get('y_local') or 0)
                stack=stacks.get(pin.get('padstack_id'),{})
                # Prefer copper pad on the component side; fall back to first copper entry.
                entries=stack.get('pads',[])
                side='BOTTOM' if c.get('source_layer')=='BOTTOM' else 'TOP'
                entry=next((e for e in entries if e.get('normalized_layer')==side),None)
                if entry is None: entry=next((e for e in entries if e.get('normalized_layer') in ('TOP','BOTTOM','INNER_1','INNER_2')),None)
                padrec=pads.get(entry.get('pad_id'),{}) if entry else {}
                prot=float(pin.get('rotation_deg') or 0)+(float(entry.get('rotation') or 0) if entry else 0)
                parts.append(f'<g transform="translate({px},{py}) rotate({prot})">')
                for geom in padrec.get('geometry',[]):
                    # Pad definitions are local to the pin origin. Render copper fill for easy recognition.
                    typ=geom.get('type')
                    if typ=='circle':
                        x,y=geom.get('center',[0,0]); r=float(geom.get('radius') or 0)
                        parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{pad_color}" fill-opacity="0.88" stroke="#ffe4a3" stroke-width="1.2"/>')
                    elif typ=='rectangle':
                        x,y,w,h=map(float,(geom['x'],geom['y'],geom['width'],geom['height']))
                        # GenCAD RECTANGLE x/y are the lower-left corner, not the center.
                        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{pad_color}" fill-opacity="0.88" stroke="#ffe4a3" stroke-width="1.2"/>')
                    elif typ in ('line','arc'):
                        item=_geom_svg(geom,'#ffe4a3',1.4)
                        if item: parts.append(item)
                drill=stack.get('drill')
                if drill and float(drill)>0:
                    parts.append(f'<circle cx="0" cy="0" r="{float(drill)/2}" fill="#10151d" stroke="#d7dce3" stroke-width="1.2"/>')
                if pin.get('number') not in (None,''):
                    # Place the pin number just outside the pad instead of over
                    # its copper. The offset is derived from the actual pad
                    # footprint, then transformed with pad, pin and component.
                    # This keeps the label beside the pin on rotated/mirrored parts.
                    ext_x=ext_y=0.0
                    for geom in padrec.get('geometry',[]):
                        typ=geom.get('type')
                        if typ=='circle':
                            gx,gy=geom.get('center',[0,0]); rr=float(geom.get('radius') or 0)
                            ext_x=max(ext_x,abs(float(gx))+rr)
                            ext_y=max(ext_y,abs(float(gy))+rr)
                        elif typ=='rectangle':
                            gx,gy,gw,gh=map(float,(geom['x'],geom['y'],geom['width'],geom['height']))
                            ext_x=max(ext_x,abs(gx),abs(gx+gw))
                            ext_y=max(ext_y,abs(gy),abs(gy+gh))
                        elif typ in ('line','arc'):
                            for key in ('p1','p2','start','end','center'):
                                q=geom.get(key)
                                if q and len(q)>=2:
                                    ext_x=max(ext_x,abs(float(q[0])))
                                    ext_y=max(ext_y,abs(float(q[1])))
                    if ext_x==0.0 and ext_y==0.0:
                        ext_x=ext_y=7.0
                    # A small clearance beyond the pad edge; never anchor the
                    # number directly on the copper center.
                    ox,oy=ext_x+4.0,ext_y+4.0
                    par=math.radians(prot)
                    ox,oy=ox*math.cos(par)-oy*math.sin(par),ox*math.sin(par)+oy*math.cos(par)
                    lx,ly=px+ox,py+oy
                    if mirror: lx=-lx
                    ar=math.radians(angle)
                    wx=cx + lx*math.cos(ar) - ly*math.sin(ar)
                    wy=cy + lx*math.sin(ar) + ly*math.cos(ar)
                    label_parts.append(f'<g transform="translate({wx},{-wy})"><text fill="#f4f1e8" stroke="none" font-size="10">{html.escape(str(pin["number"]))}</text></g>')
                parts.append('</g>')
            # Component reference uses the transformed component origin.
            ref=html.escape(str(c.get('reference','')))
            label_parts.append(f'<g transform="translate({cx},{-cy-16})"><text fill="#f3f4f6" stroke="none" font-size="18" text-anchor="middle">{ref}</text></g>')
            parts.append('</g>')
    # Vias and mechanical holes remain visible on every selected copper view.
    for v in b.get('VIAS',[]):
        x,y=v.get('x'),v.get('y')
        if x is not None and y is not None:
            parts.append(f'<circle cx="{x}" cy="{y}" r="9" stroke="#f5d76e" stroke-width="2" fill="#10151d"/>')
    for h in b.get('HOLE',[]):
        x,y,d=h['x'],h['y'],h['diameter']
        parts.append(f'<circle cx="{x}" cy="{y}" r="{d/2}" stroke="#e5e7eb" stroke-width="2" fill="none" stroke-dasharray="8 5"/>')
    parts.append('</g>')
    parts.extend(label_parts)
    parts.append('</svg>')
    Path(svg_path).write_text('\n'.join(parts),encoding='utf-8')
    return {'svg_path':str(svg_path),'bounds_source_units':[xmin,ymin,xmax,ymax],'layer':layer,
            'components_shown':show_components,'footprints_rendered':sum(1 for c in b.get('COMP',[]) if c.get('shape_id') in shapes),
            **arc_direction_report, 'outline_status':'not rendered; source contains no explicit mechanical board edge', 'component_silhouettes':'estimated from transformed pad extents; dashed to distinguish from true package outlines'}


def main():
    ap=argparse.ArgumentParser(description='PVF reader and geometry preview')
    ap.add_argument('pv'); ap.add_argument('--report',action='store_true')
    ap.add_argument('--svg'); ap.add_argument('--layer',default='ALL',choices=['ALL','TOP','INNER_1','INNER_2','BOTTOM'])
    ap.add_argument('--components',action='store_true')
    a=ap.parse_args()
    if a.report or not a.svg: print(json.dumps(geometry_report(a.pv),indent=2))
    if a.svg: print(json.dumps(export_svg(a.pv,a.svg,a.layer,a.components),indent=2))

if __name__=='__main__': main()
