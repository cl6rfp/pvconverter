import copy
import unittest

from contact_audit import analyze_contacts


def sample(segments=None, vias=None, stack_layers=(1, 2)):
    segments = segments or []
    vias = vias or []
    prim = ([{'kind': 'segment', 'ref_id': s['id']} for s in segments]
            + [{'kind': 'via', 'ref_id': v['id']} for v in vias])
    return {
        'SEGS': segments, 'VIAS': vias, 'PRIM': prim,
        'PSTK': [{'id': 3, 'pads': [{'layer_id': x} for x in stack_layers]}],
        'PINS': [{'id': 11}],
        'NETS': [{'id': 7, 'connections': [{'pin_id': 11}]}],
        'ROUT': [{'id': 1, 'net_id': 7, 'primitive_start': 1, 'primitive_count': len(prim)}],
    }


def segment(id, a, b, layer):
    return {'id': id, 'route_id': 1, 'type': 'line', 'p1': a, 'p2': b, 'layer_id': layer}


def via(id=4, x=1, y=0):
    return {'id': id, 'route_id': 1, 'x': x, 'y': y, 'padstack_id': 3}


class ContactAuditTests(unittest.TestCase):
    def test_two_layer_endpoints_are_candidates(self):
        data = sample([segment(1, [0, 0], [1, 0], 1),
                       segment(2, [1, 0], [2, 0], 2)], [via()])
        result = analyze_contacts(data)
        self.assertEqual(result['totals']['vias_with_multiple_layer_candidates'], 1)
        self.assertEqual(result['totals']['layer_endpoint_matches'], 2)
        self.assertEqual(result['examples'][0]['matching_layers'][0]['segment_ids'], [1])

    def test_layer_not_in_padstack_does_not_match(self):
        data = sample([segment(1, [0, 0], [1, 0], 3)], [via()])
        self.assertEqual(analyze_contacts(data)['totals']['vias_without_endpoint_candidates'], 1)

    def test_intersection_inside_segment_not_endpoint(self):
        data = sample([segment(1, [0, 0], [2, 0], 1)], [via()])
        self.assertEqual(analyze_contacts(data)['totals']['vias_without_endpoint_candidates'], 1)

    def test_tolerance_and_immutability(self):
        data = sample([segment(1, [0, 0], [1.00005, 0], 1)], [via()])
        before = copy.deepcopy(data)
        self.assertEqual(analyze_contacts(data)['totals']['vias_with_endpoint_candidates'], 1)
        self.assertEqual(analyze_contacts(data, tolerance=0)['totals']['vias_without_endpoint_candidates'], 1)
        self.assertEqual(data, before)

    def test_invalid_references_and_positions(self):
        data = sample(vias=[via(x=None)])
        data['NETS'][0]['connections'].append({'pin_id': 999})
        result = analyze_contacts(data)
        self.assertEqual(result['totals']['invalid_via_points'], 1)
        self.assertEqual(result['totals']['missing_net_pin_references'], 1)

    def test_absent_padstack_unknown(self):
        data = sample(vias=[via()])
        data['PSTK'] = []
        self.assertEqual(analyze_contacts(data)['totals']['vias_without_known_pad_layers'], 1)

    def test_invalid_ranges(self):
        data = sample([segment(1, [0, 0], [1, 0], 1)])
        data['ROUT'][0]['primitive_start'] = -1
        self.assertEqual(analyze_contacts(data)['totals']['invalid_ranges'], 1)

    def test_options(self):
        for value in (-1, float('inf'), float('nan')):
            with self.assertRaises(ValueError):
                analyze_contacts(sample(), tolerance=value)
        with self.assertRaises(ValueError):
            analyze_contacts(sample(), top=-1)


if __name__ == '__main__':
    unittest.main()
