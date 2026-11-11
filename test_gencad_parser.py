from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from gencad_parser import parse_file


class GenCADParserTests(unittest.TestCase):
    def test_shape_pin_without_optional_mirror_is_parsed(self):
        source = """$SHAPES
SHAPE TEST_PACKAGE
PIN 1 PST_1 1.25 2.50 TOP 90
$END
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "minimal.cad"
            path.write_text(source, encoding="latin-1")
            data, _ = parse_file(str(path))

        self.assertEqual(len(data["shapes"]), 1)
        self.assertEqual(len(data["shapes"][0]["pins"]), 1)
        pin = data["shapes"][0]["pins"][0]
        self.assertEqual(pin["number"], "1")
        self.assertEqual(pin["padstack"], "PST_1")
        self.assertEqual((pin["x"], pin["y"]), (1.25, 2.50))
        self.assertEqual(pin["layer"], "TOP")
        self.assertEqual(pin["rotation"], 90.0)
        self.assertEqual(pin["extra"], [])

    def test_shape_pin_preserves_optional_extra_tokens(self):
        source = """$SHAPES
SHAPE TEST_PACKAGE
PIN 2 PST_2 0 0 BOTTOM 180 MIRRORY FLIP
$END
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "minimal.cad"
            path.write_text(source, encoding="latin-1")
            data, _ = parse_file(str(path))

        pin = data["shapes"][0]["pins"][0]
        self.assertEqual(pin["extra"], ["MIRRORY", "FLIP"])


if __name__ == "__main__":
    unittest.main()
