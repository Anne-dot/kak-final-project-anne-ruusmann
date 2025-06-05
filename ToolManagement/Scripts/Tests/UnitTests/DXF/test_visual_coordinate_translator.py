"""
Unit tests for the Visual Coordinate Translator module.

This module tests the functionality of the VisualCoordinateTranslator class
which transforms DXF coordinates to physical workpiece coordinates.
"""

import sys
import unittest
from pathlib import Path

# Path setup for imports
current_dir = Path(__file__).parent.absolute()
scripts_dir = current_dir.parent.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import module to test
from DXF.visual_coordinate_translator import VisualCoordinateTranslator


class TestVisualCoordinateTranslator(unittest.TestCase):
    """Test cases for the VisualCoordinateTranslator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.translator = VisualCoordinateTranslator()

        # Sample workpiece data
        self.workpiece = {
            "width": 555.0,
            "height": 570.0,
            "thickness": 22.5,
            "corner_points": [(0, 0, 0), (555, 0, 0), (555, 570, 0), (0, 570, 0)],
        }

        # Sample X-direction drill points
        self.x_direction_points = [
            {
                "position": (542.0, -9.5, 0.0),
                "diameter": 8.0,
                "depth": 21.5,
                "direction": (1.0, 0.0, 0.0),
                "layer": "EDGE.DRILL_D8.0_P21.5",
            },
            {
                "position": (-542.0, -9.5, -555.0),
                "diameter": 8.0,
                "depth": 21.5,
                "direction": (-1.0, 0.0, 0.0),
                "layer": "EDGE.DRILL_D8.0_P21.5",
            },
        ]

        # Sample Y-direction drill points
        self.y_direction_points = [
            {
                "position": (-517.5, -9.5, 0.0),
                "diameter": 8.0,
                "depth": 21.5,
                "direction": (0.0, 1.0, 0.0),
                "layer": "EDGE.DRILL_D8.0_P21.5",
            },
            {
                "position": (517.5, -9.5, -555.0),
                "diameter": 8.0,
                "depth": 21.5,
                "direction": (0.0, -1.0, 0.0),
                "layer": "EDGE.DRILL_D8.0_P21.5",
            },
        ]

        # Expected translation results for X-direction points
        self.expected_x_translations = [
            (0.0, 28.0, 13.0),  # translated from (542.0, -9.5, 0.0)
            (555.0, 28.0, 13.0),  # translated from (-542.0, -9.5, -555.0)
        ]

        # Expected translation results for Y-direction points
        self.expected_y_translations = [
            (37.5, 0.0, 13.0),  # translated from (-517.5, -9.5, 0.0)
            (37.5, 555.0, 13.0),  # translated from (517.5, -9.5, -555.0)
        ]

    def test_validate_workpiece(self):
        """Test workpiece validation."""
        # Test valid workpiece
        success, message, dimensions = self.translator._validate_workpiece(self.workpiece)
        self.assertTrue(success)
        self.assertEqual(dimensions["width"], 555.0)
        self.assertEqual(dimensions["height"], 570.0)
        self.assertEqual(dimensions["thickness"], 22.5)

        # Test missing dimensions
        invalid_workpiece = {"width": 100.0}
        success, message, _ = self.translator._validate_workpiece(invalid_workpiece)
        self.assertFalse(success)

        # Test negative dimensions
        negative_workpiece = {"width": -100.0, "height": 100.0, "thickness": 10.0}
        success, message, _ = self.translator._validate_workpiece(negative_workpiece)
        self.assertFalse(success)

    def test_has_required_fields(self):
        """Test drill point validation."""
        # Test valid point
        point = self.x_direction_points[0]
        self.assertTrue(self.translator._has_required_fields(point))

        # Test missing field
        invalid_point = {"position": (0, 0, 0), "diameter": 8.0}
        self.assertFalse(self.translator._has_required_fields(invalid_point))

        # Test invalid position format
        invalid_point = {
            "position": [0, 0],  # Missing Z coordinate
            "diameter": 8.0,
            "depth": 10.0,
            "direction": (1.0, 0.0, 0.0),
        }
        self.assertFalse(self.translator._has_required_fields(invalid_point))

        # Test invalid direction format
        invalid_point = {
            "position": (0, 0, 0),
            "diameter": 8.0,
            "depth": 10.0,
            "direction": (1.0, 0.0),  # Missing Z component
        }
        self.assertFalse(self.translator._has_required_fields(invalid_point))

    def test_is_x_direction_drilling(self):
        """Test X-direction drilling detection."""
        # Test positive X direction
        self.assertTrue(self.translator._is_x_direction_drilling((1.0, 0.0, 0.0)))

        # Test negative X direction
        self.assertTrue(self.translator._is_x_direction_drilling((-1.0, 0.0, 0.0)))

        # Test not X direction
        self.assertFalse(self.translator._is_x_direction_drilling((0.0, 1.0, 0.0)))
        self.assertFalse(self.translator._is_x_direction_drilling((0.0, 0.0, 1.0)))
        self.assertFalse(self.translator._is_x_direction_drilling((0.5, 0.5, 0.0)))

    def test_is_y_direction_drilling(self):
        """Test Y-direction drilling detection."""
        # Test positive Y direction
        self.assertTrue(self.translator._is_y_direction_drilling((0.0, 1.0, 0.0)))

        # Test negative Y direction
        self.assertTrue(self.translator._is_y_direction_drilling((0.0, -1.0, 0.0)))

        # Test not Y direction
        self.assertFalse(self.translator._is_y_direction_drilling((1.0, 0.0, 0.0)))
        self.assertFalse(self.translator._is_y_direction_drilling((0.0, 0.0, 1.0)))
        self.assertFalse(self.translator._is_y_direction_drilling((0.5, 0.5, 0.0)))

    def test_translate_x_direction(self):
        """Test X-direction coordinate translation."""
        # Test positive X direction
        point = self.x_direction_points[0]
        translated = self.translator._translate_x_direction(
            point, point["position"], self.workpiece["height"], self.workpiece["thickness"]
        )

        self.assertEqual(translated["position"], self.expected_x_translations[0])

        # Test negative X direction
        point = self.x_direction_points[1]
        translated = self.translator._translate_x_direction(
            point, point["position"], self.workpiece["height"], self.workpiece["thickness"]
        )

        self.assertEqual(translated["position"], self.expected_x_translations[1])

    def test_translate_y_direction(self):
        """Test Y-direction coordinate translation."""
        # Test positive Y direction
        point = self.y_direction_points[0]
        translated = self.translator._translate_y_direction(
            point, point["position"], self.workpiece["width"], self.workpiece["thickness"]
        )

        self.assertEqual(translated["position"], self.expected_y_translations[0])

        # Test negative Y direction
        point = self.y_direction_points[1]
        translated = self.translator._translate_y_direction(
            point, point["position"], self.workpiece["width"], self.workpiece["thickness"]
        )

        self.assertEqual(translated["position"], self.expected_y_translations[1])

    def test_translate_coordinates(self):
        """Test the main coordinate translation function."""
        # Test with X-direction points
        success, message, result = self.translator.translate_coordinates(
            self.x_direction_points, self.workpiece
        )

        self.assertTrue(success)
        self.assertEqual(len(result["drill_points"]), 2)

        # Check translated positions
        for i, point in enumerate(result["drill_points"]):
            self.assertEqual(point["position"], self.expected_x_translations[i])

        # Test with Y-direction points
        success, message, result = self.translator.translate_coordinates(
            self.y_direction_points, self.workpiece
        )

        self.assertTrue(success)
        self.assertEqual(len(result["drill_points"]), 2)

        # Check translated positions
        for i, point in enumerate(result["drill_points"]):
            self.assertEqual(point["position"], self.expected_y_translations[i])

        # Test with mixed X and Y direction points
        mixed_points = self.x_direction_points + self.y_direction_points
        success, message, result = self.translator.translate_coordinates(
            mixed_points, self.workpiece
        )

        self.assertTrue(success)
        self.assertEqual(len(result["drill_points"]), 4)

        # Test with invalid workpiece
        invalid_workpiece = {"width": -100.0}
        success, message, result = self.translator.translate_coordinates(
            self.x_direction_points, invalid_workpiece
        )

        self.assertFalse(success)

        # Test with no valid points
        invalid_points = [
            {
                "position": (0, 0, 0),
                "diameter": 8.0,
                "depth": 10.0,
                "direction": (0.0, 0.0, 1.0),
            }  # Vertical direction
        ]
        success, message, result = self.translator.translate_coordinates(
            invalid_points, self.workpiece
        )

        self.assertFalse(success)


if __name__ == "__main__":
    unittest.main()
