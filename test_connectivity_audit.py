import copy
import unittest

from connectivity_audit import analyze_connectivity


def fixture(segments, primitives=None, vias=None):
    if primitives is None:
        primitives = [{'kind': 'segment', 'ref_id': s['id']} for s in segments]
    return {'SEGS': segments, 'VIAS': vias or [], 'PRIM': primitives,
            'ROUT': [{'id': 1, 'net_id': 7, 'primitive_start': 1,
                      'primitive_count': len(primitives)}]}


def line(id, a, b, layer=1):
    return {'id': id, 'route_id': 1, 'type': 'line',
            'p1': a, 'p2': b, 'layer_id': layer}


class ConnectivityAuditTests(unittest.TestCase):
    def test_branch_out_of_source_order_is_one_group(self):
        b = fixture([line(1, [0, 0], [1, 0]),
                     line(2, [2, 1], [1, 0]),
                     line(3, [1, 0], [1, 1])])
        result = analyze_connectivity(b)
        self.assertEqual(result['totals']['endpoint_groups'], 1)
        self.assertEqual(result['totals']['endpoint_joins'], 2)
        self.assertEqual(result['routes_needing_review'], 0)

    def test_different_layers_not_joined(self):
        b = fixture([line(1, [0, 0], [1, 0], 1),
                     line(2, [1, 0], [2, 0], 2)])
        self.assertEqual(analyze_connectivity(b)['totals']['endpoint_groups'], 2)

    def test_crossing_interiors_not_joined(self):
        b = fixture([line(1, [-1, 0], [1, 0]), line(2, [0, -1], [0, 1])])
        self.assertEqual(analyze_connectivity(b)['totals']['endpoint_groups'], 2)

    def test_tolerance_nearby_and_exact(self):
        b = fixture([line(1, [0, 0], [1, 0]), line(2, [1.00005, 0], [2, 0])])
        self.assertEqual(analyze_connectivity(b)['totals']['endpoint_groups'], 1)
        self.assertEqual(analyze_connectivity(b, tolerance=0)['totals']['endpoint_groups'], 2)

    def test_via_does_not_create_implicit_bridge(self):
        b = fixture([line(1, [0, 0], [1, 0]), line(2, [1, 0], [2, 0], 2)],
                    [{'kind': 'segment', 'ref_id': 1},
                     {'kind': 'via', 'ref_id': 3},
                     {'kind': 'segment', 'ref_id': 2}],
                    [{'id': 3, 'x': 1, 'y': 0}])
        out = analyze_connectivity(b)
        self.assertEqual(out['totals']['endpoint_groups'], 2)
        self.assertEqual(out['totals']['vias_not_joined'], 1)

    def test_missing_references_reported(self):
        b = fixture([line(1, [0, 0], [1, 0])],
                    [{'kind': 'segment', 'ref_id': 1},
                     {'kind': 'segment', 'ref_id': 99}])
        self.assertEqual(analyze_connectivity(b)['totals']['missing_or_foreign_segment_refs'], 1)

    def test_invalid_range_not_sliced_from_end(self):
        b = fixture([])
        b['ROUT'][0]['primitive_start'] = 0
        b['ROUT'][0]['primitive_count'] = 1
        self.assertEqual(analyze_connectivity(b)['totals']['invalid_ranges'], 1)

    def test_invalid_coordinate_is_skipped(self):
        b = fixture([line(1, [0, 0], [float('nan'), 0])])
        self.assertEqual(analyze_connectivity(b)['totals']['invalid_segment_coordinates'], 1)

    def test_source_not_mutated(self):
        b = fixture([line(1, [0, 0], [1, 0])])
        before = copy.deepcopy(b)
        analyze_connectivity(b)
        self.assertEqual(b, before)

    def test_invalid_options(self):
        b = fixture([])
        for tolerance in (-1, float('inf'), float('nan')):
            with self.subTest(tolerance=tolerance):
                with self.assertRaises(ValueError):
                    analyze_connectivity(b, tolerance=tolerance)
        with self.assertRaises(ValueError):
            analyze_connectivity(b, top=-1)


if __name__ == '__main__':
    unittest.main()
