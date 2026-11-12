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


def audit_conversion_integrity(data, tolerance=1e-4, max_examples=20):
    """Report source route and geometry ambiguities without modifying them."""
    counts = {'blocking_errors': 0, 'warnings': 0, 'informational': 0, 'ambiguous': 0}
    issues = []
    route_counts = {
        'routes_checked': len(data['routes']),
        'primitive_records_checked': 0,
        'adjacent_primitive_pairs_checked': 0,
        'connected_pairs': 0,
        'disconnected_pairs': 0,
        'via_transitions_checked': 0,
        'via_transitions_connected': 0,
        'vias_without_layer_context': 0,
        'layer_changes_without_adjacent_via': 0,
        'arc_line_transitions': 0,
        'route_arcs_without_explicit_direction': 0,
        'duplicate_route_geometries': 0,
        'routes_with_empty_primitive_stream': 0,
    }

    def report(severity, code, entity, key, value, message):
        counts[severity] += 1
        if len(issues) < max_examples:
            issues.append({'severity': severity, 'code': code, 'entity': entity,
                           'key': key, 'value': value, 'message': message})

    def finite(value):
        try:
            return value is not None and math.isfinite(float(value))
        except (TypeError, ValueError, OverflowError):
            return False

    def primitive_geometry(route, primitive):
        if primitive.get('kind') == 'segment':
            index = primitive.get('index')
            if not isinstance(index, int) or not 0 <= index < len(route['segments']):
                return None
            geometry = route['segments'][index]
            if geometry.get('type') == 'line':
                return geometry.get('p1'), geometry.get('p2'), geometry
            if geometry.get('type') == 'arc':
                return geometry.get('start'), geometry.get('end'), geometry
        elif primitive.get('kind') == 'via':
            index = primitive.get('index')
            if not isinstance(index, int) or not 0 <= index < len(route['vias']):
                return None
            via = route['vias'][index]
            if via.get('x') is not None and via.get('y') is not None:
                point = [via['x'], via['y']]
                return point, point, via
        return None

    def check_numeric(entity, key, field, value, positive=False,
                      nonnegative=False, optional=False):
        if optional and value is None:
            return True
        valid = finite(value)
        if valid:
            number = float(value)
            if positive and number <= 0:
                valid = False
            if nonnegative and number < 0:
                valid = False
        if not valid:
            requirement = ('finite positive' if positive else
                           'finite non-negative' if nonnegative else 'finite')
            report('blocking_errors', 'invalid_numeric_value', entity,
                   key, field, f'{entity} {field} must be a {requirement} number')
        return valid

    def check_point(entity, key, field, point, optional=False):
        if optional and point is None:
            return True
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            report('blocking_errors', 'invalid_numeric_value', entity,
                   key, field, f'{entity} {field} must contain exactly two finite coordinates')
            return False
        results = [
            check_numeric(entity, key, f'{field}[{axis}]', value)
            for axis, value in zip(('x', 'y'), point)
        ]
        return all(results)

    for record_index, track in enumerate(data['tracks']):
        check_numeric('track', track.get('id', record_index), 'width',
                      track.get('width'), positive=True)

    for shape_index, shape in enumerate(data['shapes']):
        for pin_index, pin in enumerate(shape.get('pins', [])):
            key = f"{shape.get('name', shape_index)}:{pin.get('number', pin_index)}"
            check_numeric('shape_pin', key, 'x', pin.get('x'))
            check_numeric('shape_pin', key, 'y', pin.get('y'))
            check_numeric('shape_pin', key, 'rotation', pin.get('rotation'), optional=True)

    for record_index, hole in enumerate(data['mechanical_holes']):
        key = hole.get('id', record_index)
        check_numeric('mechanical_hole', key, 'x', hole.get('x'))
        check_numeric('mechanical_hole', key, 'y', hole.get('y'))
        check_numeric('mechanical_hole', key, 'diameter', hole.get('diameter'), positive=True)

    for record_index, component in enumerate(data['components']):
        key = component.get('reference', record_index)
        if 'position' in component:
            check_point('component', key, 'position', component.get('position'))
        check_numeric('component', key, 'rotation', component.get('rotation'), optional=True)

    for stack_index, stack in enumerate(data['padstacks']):
        key = stack.get('name', stack_index)
        check_numeric('padstack', key, 'drill', stack.get('drill'),
                      nonnegative=True, optional=True)
        for entry_index, entry in enumerate(stack.get('pads', [])):
            check_numeric('padstack_pad', f'{key}:{entry_index}', 'rotation',
                          entry.get('rotation'), optional=True)

    for group_type, groups in (('board_artwork', data['board_artworks']),
                               ('pad_geometry', data['pads'])):
        for group_index, group in enumerate(groups):
            group_key = group.get('name', group_index)
            for geometry_index, geometry in enumerate(group.get('geometry', [])):
                geometry_key = f'{group_key}:{geometry_index}'
                geometry_type = geometry.get('type')
                if geometry_type == 'line':
                    check_point(group_type, geometry_key, 'p1',
                                geometry.get('p1'), optional=True)
                    check_point(group_type, geometry_key, 'p2',
                                geometry.get('p2'), optional=True)
                elif geometry_type == 'arc':
                    arc_points = [
                        check_point(group_type, geometry_key, field,
                                    geometry.get(field), optional=True)
                        for field in ('start', 'end', 'center')
                    ]
                    if all(arc_points):
                        radius_start = math.dist(geometry['start'], geometry['center'])
                        radius_end = math.dist(geometry['end'], geometry['center'])
                        if radius_start <= tolerance or radius_end <= tolerance:
                            report('blocking_errors', 'invalid_numeric_value',
                                   group_type, geometry_key, 'radius',
                                   f'{group_type} arc radius must be greater than the geometry tolerance')
                elif geometry_type == 'circle':
                    check_point(group_type, geometry_key, 'center',
                                geometry.get('center'), optional=True)
                    check_numeric(group_type, geometry_key, 'radius',
                                  geometry.get('radius'), positive=True, optional=True)
                elif geometry_type == 'rectangle':
                    for field in ('x', 'y'):
                        check_numeric(group_type, geometry_key, field,
                                      geometry.get(field), optional=True)
                    for field in ('width', 'height'):
                        check_numeric(group_type, geometry_key, field,
                                      geometry.get(field), positive=True, optional=True)

    duplicate_geometry = {}
    seen_vias = 0
    for route_index, route in enumerate(data['routes']):
        primitives = route.get('primitives', [])
        segments = route.get('segments', [])
        vias = route.get('vias', [])
        route_name = route.get('net', route_index)
        route_counts['primitive_records_checked'] += len(primitives)
        if not primitives:
            route_counts['routes_with_empty_primitive_stream'] += 1

        if len(primitives) != len(segments) + len(vias):
            report('blocking_errors', 'primitive_count_mismatch', 'route',
                   route_name, len(primitives),
                   'Primitive stream does not reference every segment and via exactly once')

        seen_segments = set()
        seen_route_vias = set()
        for order, primitive in enumerate(primitives):
            kind = primitive.get('kind')
            index = primitive.get('index')
            target = segments if kind == 'segment' else vias if kind == 'via' else ()
            seen = seen_segments if kind == 'segment' else seen_route_vias
            if (not isinstance(index, int) or not 0 <= index < len(target)
                    or index in seen):
                report('blocking_errors', 'invalid_primitive_reference', 'route',
                       route_name, {'order': order, 'kind': kind, 'index': index},
                       'Primitive has an invalid or duplicate source-record reference')
                continue
            seen.add(index)
            source_order = target[index].get('source_order')
            if source_order != order:
                report('blocking_errors', 'primitive_source_order_mismatch', 'route',
                       route_name, {'order': order, 'source_order': source_order},
                       'Primitive order differs from the original route record order')
            if kind == 'via':
                seen_vias += 1
                if target[index].get('layer_context') is None:
                    route_counts['vias_without_layer_context'] += 1
                if not finite(target[index].get('x')) or not finite(target[index].get('y')):
                    report('blocking_errors', 'invalid_via_position', 'route',
                           route_name, order,
                           'Via coordinates must be finite numeric values')

        if seen_segments != set(range(len(segments))) or seen_route_vias != set(range(len(vias))):
            report('blocking_errors', 'unreferenced_route_record', 'route',
                   route_name, {'segments': len(segments), 'vias': len(vias)},
                   'Route contains segments or vias missing from its primitive stream')

        resolved = [primitive_geometry(route, primitive) for primitive in primitives]
        for index, (left, right) in enumerate(zip(primitives, primitives[1:])):
            route_counts['adjacent_primitive_pairs_checked'] += 1
            left_geom, right_geom = resolved[index], resolved[index + 1]
            if left_geom is None or right_geom is None:
                continue
            left_points = left_geom[:2]
            right_points = right_geom[:2]
            distances = [
                math.dist(a, b)
                for a in left_points for b in right_points
                if a is not None and b is not None
                and len(a) == 2 and len(b) == 2
                and all(math.isfinite(float(value)) for value in (*a, *b))
            ]
            if not distances:
                continue
            gap = min(distances)
            left_is_via = left.get('kind') == 'via'
            right_is_via = right.get('kind') == 'via'
            if left_is_via or right_is_via:
                route_counts['via_transitions_checked'] += 1
                if gap <= tolerance:
                    route_counts['via_transitions_connected'] += 1
                else:
                    report('warnings', 'via_transition_gap', 'route',
                           route_name, {'order': index, 'distance': gap},
                           'Adjacent route geometry does not terminate at the via center')
            elif gap <= tolerance:
                route_counts['connected_pairs'] += 1
            else:
                route_counts['disconnected_pairs'] += 1
                report('warnings', 'route_discontinuity', 'route',
                       route_name, {'order': index, 'distance': gap},
                       'Adjacent source primitives do not share an endpoint; route fragments are preserved')

            if (not left_is_via and not right_is_via
                    and left_geom[2].get('layer') != right_geom[2].get('layer')
                    and gap <= tolerance):
                route_counts['layer_changes_without_adjacent_via'] += 1
                report('ambiguous', 'connected_layer_change_without_via', 'route',
                       route_name, {'order': index,
                                    'from_layer': left_geom[2].get('layer'),
                                    'to_layer': right_geom[2].get('layer')},
                       'Connected primitives change layer without an intervening VIA record')

            if ((left_geom[2].get('type') == 'arc' and right_geom[2].get('type') == 'line')
                    or (left_geom[2].get('type') == 'line' and right_geom[2].get('type') == 'arc')):
                route_counts['arc_line_transitions'] += 1

        for segment in segments:
            if segment.get('type') not in ('line', 'arc'):
                continue
            if segment.get('type') == 'arc' and not segment.get('direction'):
                route_counts['route_arcs_without_explicit_direction'] += 1
            points = ((segment.get('p1'), segment.get('p2'))
                      if segment['type'] == 'line'
                      else (segment.get('start'), segment.get('end'), segment.get('center')))
            if not all(point is not None and len(point) == 2
                       and all(finite(value) for value in point)
                       for point in points):
                report('blocking_errors', 'invalid_route_geometry', 'route',
                       route_name, segment.get('source_order'),
                       'Route primitive coordinates must be finite numeric pairs')
                continue
            if segment['type'] == 'line':
                if math.dist(*points) <= tolerance:
                    report('blocking_errors', 'zero_length_route_segment', 'route',
                           route_name, segment.get('source_order'),
                           'Route line has coincident endpoints')
                endpoints = tuple(sorted(tuple(float(v) for v in point) for point in points))
                key = (route_name, segment.get('layer'), 'line', endpoints)
            else:
                start, end, center = points
                radius_start = math.dist(start, center)
                radius_end = math.dist(end, center)
                if radius_start <= tolerance or radius_end <= tolerance:
                    report('blocking_errors', 'degenerate_route_arc', 'route',
                           route_name, segment.get('source_order'),
                           'Route arc has a zero or near-zero radius')
                    continue
                if abs(radius_start-radius_end) > max(
                        1e-6, max(radius_start, radius_end)*1e-4):
                    report('warnings', 'route_arc_radius_mismatch', 'route',
                           route_name, segment.get('source_order'),
                           'Route arc endpoint radii differ; source geometry is retained')
                endpoints = tuple(sorted((tuple(float(v) for v in start),
                                          tuple(float(v) for v in end))))
                key = (route_name, segment.get('layer'), 'arc', endpoints,
                       tuple(float(v) for v in center))
            if key in duplicate_geometry:
                route_counts['duplicate_route_geometries'] += 1
                report('warnings', 'duplicate_route_geometry', 'route',
                       route_name, segment.get('source_order'),
                       'Exact route geometry is repeated on the same net and layer')
            else:
                duplicate_geometry[key] = segment.get('source_order')

    if seen_vias:
        report('ambiguous', 'via_layer_span_interpretation', 'via',
               'source', seen_vias,
               'Via layer spans are preserved from GenCAD; physical transitions are not inferred')

    if route_counts['vias_without_layer_context']:
        report('ambiguous', 'via_layer_context_missing', 'via', 'routes',
               route_counts['vias_without_layer_context'],
               'Via layer context is absent; the source span and padstack are retained')
    if route_counts['route_arcs_without_explicit_direction']:
        report('ambiguous', 'arc_direction_not_explicit', 'arc', 'routes',
               route_counts['route_arcs_without_explicit_direction'],
               'Route arc direction is not explicit in the parsed source')

    transformed = [component for component in data['components']
                   if component.get('shape_extra')]
    if transformed:
        report('ambiguous', 'component_transform_semantics', 'component',
               'shape_transform_tokens', len(transformed),
               'Component transformation tokens are preserved; their source semantics are not validated')

    for stack in data['padstacks']:
        inner_entries = sum(entry.get('layer') == 'INNER'
                            for entry in stack.get('pads', []))
        if inner_entries > 1:
            report('informational', 'repeated_inner_layers_normalized', 'padstack',
                   stack.get('name'), inner_entries,
                   'Repeated INNER entries are distinguished by source order in PV')

    return {
        'status': 'review_required' if any(counts.values()) else 'clear',
        'tolerance_source_units': tolerance,
        'counts': counts,
        'route_summary': route_counts,
        'issues': issues,
        'issues_truncated': sum(counts.values()) > len(issues),
        'source_geometry_modified': False,
    }



def validate_references(data):
    """Validate semantic references before assigning PV identifiers.

    Missing optional metadata is reported as a warning. A reference that would
    otherwise be encoded as ID 0 is an error and blocks conversion.
    """
    issues = []
    def issue(severity, code, entity, key, value, message):
        issues.append({'severity':severity,'code':code,'entity':entity,
                       'key':key,'value':value,'message':message})
    def index(items, key, label):
        result = {}
        for pos, item in enumerate(items):
            value = item.get(key)
            if value is None or value == '':
                issue('error','empty_identifier',label, key, value,
                      f'{label} at index {pos} has no {key}')
            elif value in result:
                issue('error','duplicate_identifier',label,key,value,
                      f'{label} identifier {value!r} is duplicated')
            else:
                result[value] = item
        return result

    shapes = index(data['shapes'], 'name', 'shape')
    pads = index(data['pads'], 'name', 'pad')
    stacks = index(data['padstacks'], 'name', 'padstack')
    components = index(data['components'], 'reference', 'component')
    signals = index(data['signals'], 'name', 'signal')
    tracks = index(data['tracks'], 'id', 'track')

    # A named component shape is a hard dependency; an omitted shape is allowed
    # for source records that intentionally describe an unplaced/unfootprinted part.
    for c in data['components']:
        ref, shape = c.get('reference'), c.get('shape')
        if not shape:
            issue('warning','component_without_shape','component',ref,None,
                  'Component has no SHAPE declaration; no pins can be generated')
        elif shape not in shapes:
            issue('error','missing_component_shape','component',ref,shape,
                  'Referenced shape does not exist')

    for sh in data['shapes']:
        pin_numbers = set()
        for pin in sh.get('pins', []):
            number = pin.get('number')
            if number in pin_numbers:
                issue('error','duplicate_shape_pin','shape',sh.get('name'),number,
                      'Pin number is duplicated within this shape; pin lookup would be ambiguous')
            pin_numbers.add(number)
            stack = pin.get('padstack')
            if not stack or stack not in stacks:
                issue('error','missing_pin_padstack','shape_pin',
                      f"{sh.get('name')}:{number}",stack,
                      'Pin references a padstack that does not exist')

    for st in data['padstacks']:
        for entry in st.get('pads', []):
            pad = entry.get('pad')
            if not pad or pad not in pads:
                issue('error','missing_pad_geometry','padstack',
                      st.get('name'),pad,
                      'Padstack entry references a pad definition that does not exist')

    # Component/pin connectivity must resolve to one unique generated pin.
    for sig in data['signals']:
        for node in sig.get('nodes', []):
            cref, pnum = node.get('component'), node.get('pin')
            comp = components.get(cref)
            if comp is None:
                issue('error','missing_node_component','signal',sig.get('name'),cref,
                      f'Node references missing component {cref!r}')
                continue
            sh = shapes.get(comp.get('shape'))
            if sh is None or not any(x.get('number') == pnum for x in sh.get('pins', [])):
                issue('error','missing_node_pin','signal',sig.get('name'),
                      f'{cref}:{pnum}',
                      'Node pin cannot be resolved through the component shape')

    for route in data['routes']:
        net = route.get('net')
        if not net or net not in signals:
            issue('error','missing_route_net','route',net,net,
                  'Route references a signal/net that does not exist')
        for seg in route.get('segments', []):
            tid = seg.get('track_id')
            if tid is not None and tid not in tracks:
                issue('warning','missing_track_definition','route_segment',
                      route.get('net'),tid,
                      'Track definition is missing; segment width cannot be resolved')
            if seg.get('layer') is None:
                issue('warning','segment_without_layer','route_segment',
                      route.get('net'),seg.get('source_order'),
                      'Segment has no explicit layer context')
            if seg.get('type') == 'line':
                pts = (seg.get('p1'), seg.get('p2'))
                if any(not pt or len(pt) != 2 or any(v is None for v in pt) for pt in pts):
                    issue('error','invalid_line_geometry','route_segment',
                          route.get('net'),seg.get('source_order'),
                          'Line is missing valid numeric endpoints')
            elif seg.get('type') == 'arc':
                pts = (seg.get('start'), seg.get('end'), seg.get('center'))
                if any(not pt or len(pt) != 2 or any(v is None for v in pt) for pt in pts):
                    issue('error','invalid_arc_geometry','route_segment',
                          route.get('net'),seg.get('source_order'),
                          'Arc is missing valid numeric start/end/center')
                else:
                    r1=math.dist(seg['start'],seg['center'])
                    r2=math.dist(seg['end'],seg['center'])
                    if r1 == 0 or r2 == 0:
                        issue('error','degenerate_arc','route_segment',
                              route.get('net'),seg.get('source_order'),
                              'Arc radius is zero')
                    elif abs(r1-r2) > max(1e-6, max(r1,r2)*1e-4):
                        issue('warning','arc_radius_mismatch','route_segment',
                              route.get('net'),seg.get('source_order'),
                              'Arc endpoint radii differ; source geometry is retained')
            else:
                issue('error','unknown_route_primitive','route_segment',
                      route.get('net'),seg.get('type'),
                      'Unsupported route segment geometry type')
        for via in route.get('vias', []):
            stack = via.get('padstack')
            if stack and stack not in stacks:
                issue('error','missing_via_padstack','via',route.get('net'),stack,
                      'Via references a padstack that does not exist')
            if via.get('x') is None or via.get('y') is None:
                issue('error','invalid_via_position','via',route.get('net'),via.get('raw'),
                      'Via is missing numeric coordinates')

    # Source layer declarations must be unique; inferred route/component layers
    # are added later and remain explicitly marked as source-derived.
    index(data['layers'], 'name', 'layer')
    # Geometry records with malformed numeric data are retained only when the
    # source type is unknown; known primitives must be structurally complete.
    for group_name, groups in (('board_artwork',data['board_artworks']),
                               ('pad_geometry',data['pads'])):
        for group in groups:
            for gi,g in enumerate(group.get('geometry', [])):
                t=g.get('type')
                required = (('p1','p2') if t=='line' else
                            ('start','end','center') if t=='arc' else
                            ('center','radius') if t=='circle' else
                            ('x','y','width','height') if t=='rectangle' else ())
                for field in required:
                    value=g.get(field)
                    if isinstance(value,list):
                        valid=len(value)==2 and all(v is not None for v in value)
                    else:
                        valid=value is not None
                    if not valid:
                        issue('error','invalid_geometry_record',group_name,
                              group.get('name'),f'{gi}:{field}',
                              f'Known geometry primitive is missing valid {field}')
                if t=='arc' and all(g.get(k) and all(v is not None for v in g[k])
                                    for k in ('start','end','center')):
                    r1=math.dist(g['start'],g['center'])
                    r2=math.dist(g['end'],g['center'])
                    if r1 == 0 or r2 == 0:
                        issue('error','degenerate_arc',group_name,group.get('name'),gi,
                              'Arc radius is zero')
                    elif abs(r1-r2) > max(1e-6,max(r1,r2)*1e-4):
                        issue('warning','arc_radius_mismatch',group_name,group.get('name'),gi,
                              'Arc endpoint radii differ; source geometry is retained')

    errors = sum(x['severity']=='error' for x in issues)
    warnings = sum(x['severity']=='warning' for x in issues)
    integrity = audit_conversion_integrity(data)
    integrity_errors = integrity['counts']['blocking_errors']
    return {'status':'failed' if errors or integrity_errors else 'passed',
            'error_count':errors + integrity_errors,
            'warning_count':warnings + integrity['counts']['warnings'],
            'checked_reference_domains':['shapes','padstacks','pads','components',
                'signals','nodes','routes','tracks','vias','layers','geometry'],
            'issues':issues,'integrity_diagnostics':integrity}



def build_model(data, raw):
    # Validate semantic links before assigning IDs; never encode unresolved references as ID 0.
    reference_validation = validate_references(data)
    if reference_validation['error_count']:
        raise ValueError('PV build blocked by reference validation: ' + json.dumps(reference_validation, ensure_ascii=False))
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
    # Include every layer referenced by shape pins and padstack entries before
    # assigning IDs. Repeated INNER entries are normalized per padstack.
    for sh in shapes:
        for pin in sh.get('pins',[]):
            add_layer(pin.get('layer'))
    for st in stacks:
        inner_count=0
        for entry in st.get('pads',[]):
            source_layer=entry.get('layer')
            if source_layer=='INNER':
                inner_count+=1
                add_layer(f'INNER_{inner_count}','copper','INNER',None)
            elif source_layer:
                add_layer(source_layer,'unspecified',source_layer,None)
    for l in data['layers']: add_layer(l['name'],l['type'],l['name'],None)
    add_layer('ALL','all_layers','ALL',None)
    for c in comps: add_layer(c.get('layer'))
    for artwork in data['board_artworks']: add_layer(artwork.get('layer'))
    for r in routes:
        for seg in r['segments']: add_layer(seg.get('layer'))
    layer_ids={x['name']:i+1 for i,x in enumerate(layer_specs)}
    layers=[dict(x,id=layer_ids[x['name']]) for x in layer_specs]

    component_records=[]; pin_records=[]; pin_lookup={}; pin_id=1
    for c in comps:
        cid=comp_ids[c['reference']]
        sid=shape_ids[c['shape']] if c.get('shape') else 0
        component_records.append({'id':cid,'reference':c['reference'],'x':c.get('position',[None,None])[0], 'y':c.get('position',[None,None])[1], 'layer_id':layer_ids[c['layer']] if c.get('layer') else 0,'source_layer':c.get('layer'),'rotation_deg':c.get('rotation'),'shape_id':sid,'device':c.get('device'),'shape_transform_tokens':c.get('shape_extra',[]),'source_extra':c.get('other',[])})
        shape=next((s for s in shapes if s['name']==c.get('shape')),None)
        if shape:
            for idx,p in enumerate(shape['pins']):
                rec={'id':pin_id,'component_id':cid,'shape_id':sid,'shape_pin_index':idx,'number':p['number'],'padstack_id':stack_ids[p['padstack']],'x_local':p['x'],'y_local':p['y'],'layer_id':layer_ids[p['layer']],'source_layer':p['layer'],'rotation_deg':p['rotation'],'extra':p.get('extra',[])}
                pin_records.append(rec)
                pin_lookup[(c['reference'],p['number'])]=pin_id
                pin_id+=1

    net_records=[]
    for n in signals:
        con=[]
        for node in n['nodes']:
            pid=pin_lookup[(node['component'],node['pin'])]
            con.append({'pin_id':pid,'component_ref':node['component'],'pin_number':node['pin']})
        net_records.append({'id':net_ids[n['name']],'name':n['name'],'connections':con})

    # Store segments and vias in their own blocks, but also emit PRIM to preserve
    # their exact interleaved source order inside each ROUTE.
    seg_records=[]; via_records=[]; route_records=[]; primitive_records=[]
    segid=1; viaid=1; routeid=1
    for r in routes:
        nid=net_ids[r['net']]; first_s=segid; first_v=viaid
        first_prim=len(primitive_records)+1
        seg_ids={}; via_ids={}
        for primitive in r.get('primitives',[]):
            if primitive['kind']=='segment':
                s=r['segments'][primitive['index']]
                rec={'id':segid,'route_id':routeid,'route_order':s['source_order'],'net_id':nid,
                     'type':s['type'],'track_id':s.get('track_id'),
                     'width_source':track_widths.get(s.get('track_id')),
                     'layer_id':layer_ids[s['layer']] if s.get('layer') else 0,'source_layer':s.get('layer'),
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
                    'net_id':nid,'padstack_id':stack_ids[v['padstack']] if v.get('padstack') else 0,
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
            stack_pads.append(dict(entry,pad_id=pad_ids[entry['pad']],
                layer_id=layer_ids[normalized_layer] if normalized_layer else 0,normalized_layer=normalized_layer,
                source_layer=source_layer))
        stack_records.append({'id':stack_ids[st['name']],'name':st['name'],'drill':st['drill'],
            'pads':stack_pads,'attributes':st['attributes'],
            'inner_layer_entries':inner_index,'source_pad_order_preserved':True})
    artwork_records=[]
    for i,a in enumerate(data['board_artworks'],1): artwork_records.append({'id':i,'name':a['name'],'layer_id':layer_ids[a['layer']],'source_layer':a['layer'],'geometry':[enrich_geometry(g) for g in a['geometry']]})
    meta=dict(data['meta'])
    meta.update({'reference_validation':reference_validation,'pv_core_schema':'0.1','coordinate_storage':'source_user_units_as_decimal_values','coordinate_conversion':'not_applied','units_interpretation':'unconfirmed; original GenCAD USER 1000 retained','copper_stack_interpretation':'4 routing layers declared; repeated INNER padstack entries normalized by occurrence order to INNER_1 and INNER_2; source labels retained','bottom_component_transform':'source SHAPE tokens retained verbatim; MIRRORY FLIP semantics not applied until verified','source_sha256':hashlib.sha256(raw).hexdigest()})
    blocks=[
      {'id':'META','data':meta,'record_count':1,'flags':1},
      {'id':'VALD','data':reference_validation,'record_count':len(reference_validation['issues'])},
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
