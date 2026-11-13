"""Tests for the standalone diagnostic preview and layer metadata."""
import tempfile
import unittest
from pathlib import Path
from pv_geometry import _layer_group, _layer_names, export_browser_preview


class LayerPreviewTests(unittest.TestCase):
    def test_layers_include_declared_and_referenced(self):
        blocks = {'LAYR': [{'name': 'TOP'}, {'name': 'INNER_1'}, {'name': 'BOTTOM'}],
                  'SEGS': [{'source_layer': 'BOTTOM'}, {'source_layer': 'INNER_3'}]}
        self.assertEqual(_layer_names(blocks), ['TOP', 'INNER_1', 'BOTTOM', 'INNER_3'])

    def test_group_escapes_source_layer(self):
        self.assertIn('data-layer="A&amp;B"', _layer_group('A&B', ['<line/>'], 'routes'))

    def test_browser_preview_controls_and_svg(self):
        with tempfile.TemporaryDirectory() as temp:
            svg = Path(temp)/'board.svg'
            page = Path(temp)/'board.html'
            svg.write_text('<svg xmlns="http://www.w3.org/2000/svg">'
                           '<g data-layer="TOP" data-kind="routes"><line/></g>'
                           '<g data-layer="BOTTOM" data-kind="routes"><line/></g></svg>')
            report = export_browser_preview(svg, page)
            output = page.read_text()
            self.assertEqual(report['layers'], ['TOP', 'BOTTOM'])
            self.assertIn('data-name="TOP"', output)
            self.assertIn('data-name="BOTTOM"', output)
            self.assertIn('data-kind="vias"', output)
            self.assertIn('function sync()', output)
            self.assertIn("board.addEventListener('wheel'", output)
            self.assertIn("board.addEventListener('pointerdown'", output)
            self.assertIn("event.button !== 2", output)
            self.assertIn("board.addEventListener('contextmenu'", output)
            self.assertIn('getScreenCTM()', output)
            self.assertIn('reset-view', output)
            self.assertIn('passive:false', output)


if __name__ == '__main__':
    unittest.main()
