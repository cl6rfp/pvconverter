from __future__ import annotations

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pvf
from build_pv import audit_conversion_integrity, validate_references
from pv_geometry import geometry_report


def valid_source():
    return {
        'components': [{'reference':'U1','shape':'PKG1'}],
        'shapes': [{'name':'PKG1','pins':[
            {'number':'1','padstack':'PST1','x':0.0,'y':0.0}
        ]}],
        'pads': [{'name':'PAD1'}],
        'padstacks': [{'name':'PST1','pads':[{'pad':'PAD1','layer':'TOP'}]}],
        'signals': [{'name':'GND','nodes':[{'component':'U1','pin':'1'}]}],
        'tracks': [{'id':'T1','width':0.25}],
        'routes': [{'net':'GND','segments':[
            {'type':'line','p1':[0.0,0.0],'p2':[1.0,0.0],
             'track_id':'T1','layer':'TOP','source_order':0}
        ],'vias':[],'primitives':[{'kind':'segment','index':0}]}],
        'layers': [{'name':'TOP','type':'copper'}],
        'board_artworks': [],
        'mechanical_holes': [],
    }


class ReferenceValidationTests(unittest.TestCase):
    def test_valid_cross_references_pass(self):
        report = validate_references(valid_source())
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['error_count'], 0)

    def test_missing_padstack_is_a_blocking_error(self):
        data = valid_source()
        data['shapes'][0]['pins'][0]['padstack'] = 'DOES_NOT_EXIST'
        report = validate_references(data)
        self.assertEqual(report['status'], 'failed')
        self.assertTrue(any(x['code'] == 'missing_pin_padstack'
                            for x in report['issues']))

    def test_duplicate_component_identifier_is_blocking(self):
        data = valid_source()
        data['components'].append({'reference':'U1','shape':'PKG1'})
        report = validate_references(data)
        self.assertTrue(any(x['code'] == 'duplicate_identifier'
                            and x['entity'] == 'component'
                            for x in report['issues']))

    def test_unresolved_signal_pin_is_blocking(self):
        data = valid_source()
        data['signals'][0]['nodes'][0]['pin'] = '99'
        report = validate_references(data)
        self.assertTrue(any(x['code'] == 'missing_node_pin'
                            for x in report['issues']))

    def test_unresolved_route_net_is_blocking(self):
        data = valid_source()
        data['routes'][0]['net'] = 'NO_NET'
        report = validate_references(data)
        self.assertTrue(any(x['code'] == 'missing_route_net'
                            for x in report['issues']))

    def test_missing_track_definition_is_warning_not_silent_zero(self):
        data = valid_source()
        data['routes'][0]['segments'][0]['track_id'] = 'NO_TRACK'
        report = validate_references(data)
        self.assertEqual(report['error_count'], 0)
        self.assertTrue(any(x['code'] == 'missing_track_definition'
                            and x['severity'] == 'warning'
                            for x in report['issues']))


class IntegrityAuditTests(unittest.TestCase):
    def test_connected_route_has_no_integrity_findings(self):
        report = audit_conversion_integrity(valid_source())
        self.assertEqual(report['counts']['blocking_errors'], 0)
        self.assertEqual(report['counts']['warnings'], 0)
        self.assertEqual(report['route_summary']['connected_pairs'], 0)
        self.assertFalse(report['source_geometry_modified'])

    def test_route_gap_is_reported_without_repairing_geometry(self):
        data = valid_source()
        data['routes'][0]['segments'].append({
            'type':'line','p1':[2.0,0.0],'p2':[3.0,0.0],
            'track_id':'T1','layer':'TOP','source_order':1
        })
        data['routes'][0]['primitives'].append({'kind':'segment','index':1})
        original = deepcopy(data)

        report = audit_conversion_integrity(data)

        self.assertEqual(data, original)
        self.assertEqual(report['route_summary']['disconnected_pairs'], 1)
        self.assertTrue(any(issue['code'] == 'route_discontinuity'
                            and issue['severity'] == 'warnings'
                            for issue in report['issues']))

    def test_layer_change_without_via_is_marked_ambiguous(self):
        data = valid_source()
        data['routes'][0]['segments'].append({
            'type':'line','p1':[1.0,0.0],'p2':[2.0,0.0],
            'track_id':'T1','layer':'BOTTOM','source_order':1
        })
        data['routes'][0]['primitives'].append({'kind':'segment','index':1})

        report = audit_conversion_integrity(data)

        self.assertEqual(report['route_summary']['layer_changes_without_adjacent_via'], 1)
        self.assertTrue(any(issue['code'] == 'connected_layer_change_without_via'
                            and issue['severity'] == 'ambiguous'
                            for issue in report['issues']))

    def test_via_transition_and_missing_source_layer_context_are_reported(self):
        data = valid_source()
        route = data['routes'][0]
        route['segments'][0]['p2'] = [1.0, 0.0]
        route['segments'][0]['source_order'] = 0
        route['vias'] = [{'x':1.0,'y':0.0,'layer_context':None,'source_order':1}]
        route['segments'].append({
            'type':'line','p1':[1.0,0.0],'p2':[2.0,0.0],
            'track_id':'T1','layer':'BOTTOM','source_order':2
        })
        route['primitives'] = [
            {'kind':'segment','index':0},
            {'kind':'via','index':0},
            {'kind':'segment','index':1},
        ]

        report = audit_conversion_integrity(data)

        self.assertEqual(report['route_summary']['via_transitions_checked'], 2)
        self.assertEqual(report['route_summary']['via_transitions_connected'], 2)
        self.assertEqual(report['route_summary']['vias_without_layer_context'], 1)
        codes = {issue['code'] for issue in report['issues']}
        self.assertIn('via_layer_context_missing', codes)
        self.assertIn('via_layer_span_interpretation', codes)

    def test_invalid_primitive_reference_is_blocking(self):
        data = valid_source()
        data['routes'][0]['primitives'][0]['index'] = 12

        report = audit_conversion_integrity(data)

        self.assertGreater(report['counts']['blocking_errors'], 0)
        self.assertTrue(any(issue['code'] == 'invalid_primitive_reference'
                            for issue in report['issues']))

    def test_duplicate_geometry_is_reported(self):
        data = valid_source()
        data['routes'][0]['segments'].append(deepcopy(data['routes'][0]['segments'][0]))
        data['routes'][0]['segments'][1]['source_order'] = 1
        data['routes'][0]['primitives'].append({'kind':'segment','index':1})

        report = audit_conversion_integrity(data)

        self.assertEqual(report['route_summary']['duplicate_route_geometries'], 1)
        self.assertTrue(any(issue['code'] == 'duplicate_route_geometry'
                            for issue in report['issues']))

    def test_arc_line_transition_is_counted_as_ambiguous_direction(self):
        data = valid_source()
        route = data['routes'][0]
        route['segments'][0] = {
            'type':'arc','start':[1.0,0.0],'end':[0.0,1.0],
            'center':[0.0,0.0],'track_id':'T1','layer':'TOP','source_order':0
        }
        route['segments'].append({
            'type':'line','p1':[0.0,1.0],'p2':[-1.0,1.0],
            'track_id':'T1','layer':'TOP','source_order':1
        })
        route['primitives'].append({'kind':'segment','index':1})

        report = audit_conversion_integrity(data)

        self.assertEqual(report['route_summary']['arc_line_transitions'], 1)
        self.assertEqual(report['route_summary']['route_arcs_without_explicit_direction'], 1)
        self.assertTrue(any(issue['code'] == 'arc_direction_not_explicit'
                            and issue['severity'] == 'ambiguous'
                            for issue in report['issues']))

    def test_non_positive_track_width_is_a_blocking_diagnostic(self):
        data = valid_source()
        data['tracks'][0]['width'] = 0

        validation = validate_references(data)

        self.assertEqual(validation['status'], 'failed')
        self.assertTrue(any(issue['code'] == 'invalid_numeric_value'
                            and issue['entity'] == 'track'
                            for issue in validation['integrity_diagnostics']['issues']))


    def test_non_finite_component_position_is_blocking(self):
        data = valid_source()
        data['components'][0]['position'] = [float('nan'), 0.0]
        validation = validate_references(data)
        self.assertEqual(validation['status'], 'failed')
        self.assertTrue(any(issue['code'] == 'invalid_numeric_value'
                            and issue['entity'] == 'component'
                            for issue in validation['integrity_diagnostics']['issues']))

    def test_non_finite_component_rotation_is_blocking(self):
        data = valid_source()
        data['components'][0]['rotation'] = float('inf')
        validation = validate_references(data)
        self.assertEqual(validation['status'], 'failed')
        self.assertTrue(any(issue['code'] == 'invalid_numeric_value'
                            and issue['entity'] == 'component'
                            and issue['value'] == 'rotation'
                            for issue in validation['integrity_diagnostics']['issues']))

    def test_negative_padstack_drill_is_blocking(self):
        data = valid_source()
        data['padstacks'][0]['drill'] = -0.2
        validation = validate_references(data)
        self.assertEqual(validation['status'], 'failed')
        self.assertTrue(any(issue['code'] == 'invalid_numeric_value'
                            and issue['entity'] == 'padstack'
                            and issue['value'] == 'drill'
                            for issue in validation['integrity_diagnostics']['issues']))

    def test_zero_padstack_drill_is_allowed(self):
        data = valid_source()
        data['padstacks'][0]['drill'] = 0.0
        validation = validate_references(data)
        self.assertEqual(validation['status'], 'passed')

    def test_non_finite_padstack_pad_rotation_is_blocking(self):
        data = valid_source()
        data['padstacks'][0]['pads'][0]['rotation'] = float('inf')
        validation = validate_references(data)
        self.assertEqual(validation['status'], 'failed')
        self.assertTrue(any(issue['code'] == 'invalid_numeric_value'
                            and issue['entity'] == 'padstack_pad'
                            for issue in validation['integrity_diagnostics']['issues']))

    def test_non_positive_pad_geometry_dimensions_are_blocking(self):
        data = valid_source()
        data['pads'][0]['geometry'] = [{
            'type': 'rectangle', 'x': 0.0, 'y': 0.0,
            'width': -1.0, 'height': 2.0,
        }]
        validation = validate_references(data)
        self.assertEqual(validation['status'], 'failed')
        self.assertTrue(any(issue['code'] == 'invalid_numeric_value'
                            and issue['entity'] == 'pad_geometry'
                            and issue['value'] == 'width'
                            for issue in validation['integrity_diagnostics']['issues']))

    def test_non_finite_artwork_coordinates_are_blocking(self):
        data = valid_source()
        data['board_artworks'] = [{
            'name': 'ART1', 'layer': 'TOP',
            'geometry': [{
                'type': 'line', 'p1': [0.0, 0.0],
                'p2': [float('inf'), 1.0],
            }],
        }]
        validation = validate_references(data)
        self.assertEqual(validation['status'], 'failed')
        self.assertTrue(any(issue['code'] == 'invalid_numeric_value'
                            and issue['entity'] == 'board_artwork'
                            for issue in validation['integrity_diagnostics']['issues']))


class GeometryReportValidationTests(unittest.TestCase):
    @staticmethod
    def write_minimal_pv(path, status, error_count=0, blocking_errors=0):
        empty_blocks = {
            'LAYR': [], 'COMP': [], 'SHAP': [], 'PINS': [], 'PADS': [],
            'PSTK': [], 'NETS': [], 'SEGS': [], 'VIAS': [], 'PRIM': [],
            'ROUT': [], 'HOLE': [], 'TRKS': [], 'ARTW': [],
        }
        blocks = [
            {'id': 'META', 'data': {}, 'record_count': 1},
            {'id': 'VALD', 'data': {
                'status': status,
                'error_count': error_count,
                'integrity_diagnostics': {
                    'counts': {'blocking_errors': blocking_errors}
                },
            }, 'record_count': 0},
        ]
        blocks.extend(
            {'id': block_id, 'data': data, 'record_count': len(data)}
            for block_id, data in empty_blocks.items()
        )
        pvf.write_pvf(path, blocks)

    def test_report_is_invalid_when_validation_block_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'failed.pv'
            self.write_minimal_pv(path, 'failed', error_count=1)
            report = geometry_report(path)

        self.assertFalse(report['valid'])
        self.assertTrue(report['pv_validation_failed'])
        self.assertEqual(report['pv_validation_error_count'], 1)

    def test_report_is_invalid_when_integrity_has_blocking_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'blocked.pv'
            self.write_minimal_pv(path, 'passed', blocking_errors=2)
            report = geometry_report(path)

        self.assertFalse(report['valid'])
        self.assertTrue(report['pv_validation_failed'])
        self.assertEqual(report['pv_validation_blocking_errors'], 2)

    def test_report_remains_valid_when_validation_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'valid.pv'
            self.write_minimal_pv(path, 'passed')
            report = geometry_report(path)

        self.assertTrue(report['valid'])
        self.assertFalse(report['pv_validation_failed'])


class AtomicWriteTests(unittest.TestCase):
    def test_failed_replace_preserves_previous_file_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'board.pvf'
            target.write_bytes(b'previous-valid-file')
            blocks = [{'id':'TEST','data':{'ok':True},'record_count':1}]
            with patch.object(pvf, '_zstd_compress', side_effect=lambda data, level=9: data):
                with patch.object(pvf.os, 'replace', side_effect=OSError('simulated replace failure')):
                    with self.assertRaises(OSError):
                        pvf.write_pvf(target, blocks)
            self.assertEqual(target.read_bytes(), b'previous-valid-file')
            self.assertEqual(list(Path(tmp).glob('*.tmp')), [])


if __name__ == '__main__':
    unittest.main()
