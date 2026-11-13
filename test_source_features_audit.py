"""Source inventory must not infer mechanical geometry or silkscreen."""
import tempfile
import unittest
from pathlib import Path
from source_features_audit import audit_source


class SourceFeatureTests(unittest.TestCase):
    def test_mechanical_and_artwork_are_separate(self):
        cad = '''$HEADER\nGENCAD 1.4\n$ENDHEADER\n$BOARD\nARTWORK text1 TOP\nLINE 0 0 1 1\n$ENDBOARD\n$MECH\nHOLE 1 2 3\n$ENDMECH\n'''
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'sample.cad'
            path.write_text(cad)
            report = audit_source(path)
        self.assertEqual(report['board_artwork']['groups'], 1)
        self.assertEqual(report['mechanical']['holes'], 1)
        self.assertEqual(report['silkscreen']['status'], 'not explicitly identified')
        self.assertEqual(report['mechanical']['explicit_board_outline'], 'not identified')

    def test_explicit_silk_layer_is_reported(self):
        cad='$LAYERS\nDEFINE SILK_TOP SILKSCREEN\n$ENDLAYERS\n'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'sample.cad'
            path.write_text(cad)
            report = audit_source(path)
        self.assertEqual(report['silkscreen']['explicit_layer_names'], ['SILK_TOP'])

if __name__ == '__main__': unittest.main()
