from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pvf
from build_pv import validate_references


def valid_source():
    return {
        'components': [{'reference':'U1','shape':'PKG1'}],
        'shapes': [{'name':'PKG1','pins':[
            {'number':'1','padstack':'PST1'}
        ]}],
        'pads': [{'name':'PAD1'}],
        'padstacks': [{'name':'PST1','pads':[{'pad':'PAD1','layer':'TOP'}]}],
        'signals': [{'name':'GND','nodes':[{'component':'U1','pin':'1'}]}],
        'tracks': [{'id':'T1','width':0.25}],
        'routes': [{'net':'GND','segments':[
            {'type':'line','p1':[0.0,0.0],'p2':[1.0,0.0],
             'track_id':'T1','layer':'TOP','source_order':0}
        ],'vias':[]}],
        'layers': [{'name':'TOP','type':'copper'}],
        'board_artworks': [],
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


    def test_non_finite_track_width_is_blocking(self):
        data = valid_source()
        data['tracks'][0]['width'] = float('nan')
        report = validate_references(data)
        self.assertTrue(any(x['code'] == 'invalid_track_width'
                            for x in report['issues']))

    def test_zero_length_route_line_is_blocking(self):
        data = valid_source()
        data['routes'][0]['segments'][0]['p2'] = [0.0, 0.0]
        report = validate_references(data)
        self.assertTrue(any(x['code'] == 'degenerate_line'
                            for x in report['issues']))

    def test_non_finite_shape_pin_coordinate_is_blocking(self):
        data = valid_source()
        data['shapes'][0]['pins'][0]['x'] = float('inf')
        report = validate_references(data)
        self.assertTrue(any(x['code'] == 'invalid_shape_pin_position'
                            for x in report['issues']))

    def test_non_positive_pad_geometry_is_blocking(self):
        data = valid_source()
        data['pads'][0]['geometry'] = [
            {'type':'circle','center':[0.0,0.0],'radius':-1.0}
        ]
        report = validate_references(data)
        self.assertTrue(any(x['code'] == 'invalid_circle_radius'
                            for x in report['issues']))

    def test_missing_track_definition_is_warning_not_silent_zero(self):
        data = valid_source()
        data['routes'][0]['segments'][0]['track_id'] = 'NO_TRACK'
        report = validate_references(data)
        self.assertEqual(report['error_count'], 0)
        self.assertTrue(any(x['code'] == 'missing_track_definition'
                            and x['severity'] == 'warning'
                            for x in report['issues']))


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
