"""Regression tests for BOARD artwork provenance diagnostics."""
import tempfile
import unittest
from pathlib import Path
from artwork_audit import closed_line_chain, geometry_bounds, inspect_artwork
from pv_geometry import export_browser_preview


class ArtworkAuditTests(unittest.TestCase):
    def test_closed_four_line_rectangle_is_not_automatically_board_edge(self):
        corners = [[0, 0], [20, 0], [20, 10], [0, 10]]
        shapes = [{'type': 'line', 'p1': corners[i], 'p2': corners[(i + 1) % 4]}
                  for i in range(4)]
        report = inspect_artwork([{'id': 7, 'name': 'artwork7', 'source_layer': 'TOP',
                                   'geometry': shapes}])
        self.assertEqual(report['closed_line_chains'], 1)
        self.assertEqual(report['items'][0]['bbox'], [0, 0, 20, 10])
        self.assertFalse(report['items'][0]['board_edge_verified'])

    def test_disjoint_cycles_are_not_a_single_contour(self):
        lines = []
        for x in (0, 10):
            for a, b in [([x, 0], [x+1, 0]), ([x+1, 0], [x+1, 1]),
                         ([x+1, 1], [x, 1]), ([x, 1], [x, 0])]:
                lines.append({'type': 'line', 'p1': a, 'p2': b})
        self.assertFalse(closed_line_chain(lines))

    def test_open_chain_and_empty_geometry(self):
        self.assertFalse(closed_line_chain([{'type': 'line', 'p1': [0, 0], 'p2': [1, 0]}]))
        self.assertIsNone(geometry_bounds([]))

    def test_preview_exposes_artwork_selector(self):
        with tempfile.TemporaryDirectory() as directory:
            svg = Path(directory) / 'test.svg'
            page = Path(directory) / 'test.html'
            svg.write_text('<svg><g data-kind="artwork" data-layer="TOP">'
                           '<g data-artwork="42" data-artwork-name="artwork42">'
                           '<line/></g></g></svg>', encoding='utf-8')
            export_browser_preview(svg, page)
            rendered = page.read_text(encoding='utf-8')
            self.assertIn('artwork42 (#42)', rendered)
            self.assertIn('id="artwork-select"', rendered)


if __name__ == '__main__':
    unittest.main()
