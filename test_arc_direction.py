from pv_geometry import _arc_path, _resolve_route_arc_sweeps

# Arc from (1,0) to (0,1) around origin. A preceding horizontal line
# entering at the start points east, which favors the CCW tangent (north).
segs = [
    {'id': 1, 'type': 'line', 'p1': [0, 0], 'p2': [1, 0]},
    {'id': 2, 'type': 'arc', 'start': [1, 0], 'end': [0, 1], 'center': [0, 0]},
    {'id': 3, 'type': 'line', 'p1': [0, 1], 'p2': [-1, 1]},
]
prims = [
    {'route_id': 1, 'order': 0, 'kind': 'segment', 'ref_id': 1},
    {'route_id': 1, 'order': 1, 'kind': 'segment', 'ref_id': 2},
    {'route_id': 1, 'order': 2, 'kind': 'segment', 'ref_id': 3},
]
routes = [{'id': 1, 'primitive_start': 1, 'primitive_count': 3}]
chosen, report = _resolve_route_arc_sweeps(routes, prims, segs, [])
assert chosen[2] == 90.0, chosen
assert report['arcs_direction_inferred_from_continuity'] == 1
assert report['arcs_direction_ambiguous_display_fallback'] == 0

# Verify SVG sweep flags differ for opposite source directions under Y flip.
ccw = _arc_path({'start': [1, 0], 'end': [0, 1], 'center': [0, 0], 'display_sweep_deg': 90})
cw = _arc_path({'start': [1, 0], 'end': [0, 1], 'center': [0, 0], 'display_sweep_deg': -270})
assert ccw.split()[-3:-1] == ['0', '0']
assert cw.split()[-3:-1] == ['1', '1']
print('ARC DIRECTION UNIT TESTS PASSED')
