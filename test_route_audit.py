import unittest
from route_audit import analyze_routes

class RouteAuditTests(unittest.TestCase):
    def test_connected_and_gapped_routes(self):
        b = {
            'SEGS': [
                {'id': 1, 'type': 'line', 'p1': [0,0], 'p2': [1,0]},
                {'id': 2, 'type': 'line', 'p1': [2,0], 'p2': [3,0]},
                {'id': 3, 'type': 'line', 'p1': [3,0], 'p2': [4,0]}],
            'VIAS': [],
            'ROUT': [{'id': 1, 'net_id': 9, 'primitive_start': 1, 'primitive_count': 3}],
            'PRIM': [{'kind': 'segment', 'ref_id': 1}, {'kind': 'segment', 'ref_id': 2}, {'kind': 'segment', 'ref_id': 3}]
        }
        result = analyze_routes(b)
        self.assertEqual(result['totals']['adjacent_gaps'], 1)
        self.assertEqual(result['totals']['adjacent_contacts'], 1)
        self.assertEqual(result['worst_routes'][0]['net_id'], 9)

    def test_empty_route(self):
        b = {'SEGS': [], 'VIAS': [], 'ROUT': [{'id': 1, 'primitive_start': 1, 'primitive_count': 0}], 'PRIM': []}
        self.assertEqual(analyze_routes(b)['routes_with_gaps_or_invalid_data'], 0)

if __name__ == '__main__':
    unittest.main()
