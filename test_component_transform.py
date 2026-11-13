import math
import unittest
from component_transform import rotate, component_point, transformed_pad_points


class ComponentTransformTests(unittest.TestCase):
    def test_rotation_quarter_turn(self):
        x, y = rotate((4, 0), 90)
        self.assertAlmostEqual(x, 0)
        self.assertAlmostEqual(y, 4)

    def test_translation_rotation(self):
        part = {'x': 100, 'y': 200, 'rotation_deg': 90, 'shape_transform_tokens': []}
        x, y = component_point(part, (3, 7))
        self.assertAlmostEqual(x, 93)
        self.assertAlmostEqual(y, 203)

    def test_mirror_before_rotation(self):
        part = {'x': 100, 'y': 200, 'rotation_deg': 90,
                'shape_transform_tokens': ['FLIP', 'MIRRORY']}
        x, y = component_point(part, (3, 7))
        self.assertAlmostEqual(x, 93)
        self.assertAlmostEqual(y, 197)

    def test_double_rotation_of_pad_and_component(self):
        part = {'x': 10, 'y': 20, 'rotation_deg': 90, 'shape_transform_tokens': []}
        pin = {'x_local': 2, 'y_local': 0, 'rotation_deg': 90}
        entry = {'rotation': 0}
        pad = {'geometry': [{'type': 'rectangle', 'x': 0, 'y': 0, 'width': 4, 'height': 2}]}
        points = transformed_pad_points(part, pin, entry, pad)
        self.assertEqual(len(points), 4)
        self.assertAlmostEqual(min(p[0] for p in points), 6)
        self.assertAlmostEqual(max(p[0] for p in points), 10)
        self.assertAlmostEqual(min(p[1] for p in points), 20)
        self.assertAlmostEqual(max(p[1] for p in points), 22)

    def test_reflection_is_involution(self):
        part = {'x': 0, 'y': 0, 'rotation_deg': 0, 'shape_transform_tokens': ['MIRRORY']}
        self.assertEqual(component_point(part, (3, -7)), (-3.0, -7.0))


if __name__ == '__main__':
    unittest.main()
