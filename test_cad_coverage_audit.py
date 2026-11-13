import tempfile
import subprocess
import sys
import unittest
from pathlib import Path

from cad_coverage_audit import audit_file


class CoverageAuditTests(unittest.TestCase):
    def _audit(self, body):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'sample.cad'
            source.write_text(body, encoding='latin-1')
            return audit_file(source)

    def test_known_records(self):
        result = self._audit('$BOARD\nARTWORK OUT TOP\nLINE 0 0 1 1\n$END\n')
        self.assertEqual(result['unsupported_records'], 0)
        self.assertEqual(result['malformed_records'], 0)
        self.assertEqual(result['sections']['$BOARD']['types']['LINE'], 1)

    def test_unknown_instruction_is_reported(self):
        result = self._audit('$BOARD\nARTWORK OUT TOP\nSPLINE 0 0 1 1\n$END\n')
        self.assertEqual(result['unsupported_records'], 1)
        self.assertIn('SPLINE', result['sections']['$BOARD']['unsupported_examples'][0]['record'])

    def test_missing_coordinates_are_reported(self):
        result = self._audit('$ROUTES\nROUTE N1\nLINE 0 0 4\n$END\n')
        self.assertEqual(result['malformed_records'], 1)

    def test_partial_source_semantics(self):
        result = self._audit('$SHAPES\nSHAPE P1\nINSERT DECORATION\n$END\n')
        self.assertEqual(result['partial_records'], 1)
        self.assertEqual(result['unsupported_records'], 0)

    def test_strict_conversion_rejects_unrecognized_record(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'sample.cad'
            target = Path(directory) / 'sample.pv'
            source.write_text('$BOARD\nARTWORK A TOP\nSPLINE 0 0 1 1\n$END\n', encoding='latin-1')
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('build_pv.py')),
                                     str(source), str(target), '--strict-source'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('cad_coverage_audit.py', result.stderr)
            self.assertFalse(target.exists())

    def test_empty_section(self):
        result = self._audit('$TESTPINS\n$END\n')
        self.assertEqual(result['sections']['$TESTPINS']['records'], 0)


if __name__ == '__main__':
    unittest.main()

# CLI contract is checked separately: strict mode must refuse unknown instructions
# before a PV file can be written.
