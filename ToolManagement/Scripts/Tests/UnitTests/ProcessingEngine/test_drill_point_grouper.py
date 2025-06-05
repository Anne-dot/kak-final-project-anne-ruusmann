"""
Unit tests for the Drill Point Grouper module.

This module tests the functionality of the DrillPointGrouper class
which groups drill points by diameter and direction.
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
from ProcessingEngine.drill_point_grouper import DrillPointGrouper


class TestDrillPointGrouper(unittest.TestCase):
    """Test cases for the DrillPointGrouper class."""

    def setUp(self):
        """Set up test fixtures."""
        self.grouper = DrillPointGrouper()

        # Sample drill points with different diameters and directions
        self.drill_points = [
            {
                "position": (100, 50, 0),
                "extrusion_vector": (0, 0, 1),  # Z+
                "diameter": 8.0,
            },
            {
                "position": (200, 100, 0),
                "extrusion_vector": (0, 0, 1),  # Z+
                "diameter": 8.0,
            },
            {
                "position": (300, 150, 0),
                "extrusion_vector": (1, 0, 0),  # X+
                "diameter": 8.0,
            },
            {
                "position": (400, 200, 0),
                "extrusion_vector": (1, 0, 0),  # X+
                "diameter": 10.0,
            },
            {
                "position": (500, 250, 0),
                "extrusion_vector": (0, 1, 0),  # Y+
                "diameter": 10.0,
            },
        ]

        # Test data
        self.test_data = {
            "drill_points": self.drill_points,
            "workpiece": {"width": 600, "height": 400, "thickness": 20},
        }

    def test_group_drilling_points(self):
        """Test the main grouping function."""
        # Group the points
        success, message, result = self.grouper.group_drilling_points(self.test_data)

        # Verify success
        self.assertTrue(success)

        # Verify result structure
        self.assertIn("grouped_points", result)

        # Get the grouped points
        groups = result["grouped_points"]

        # Verify expected number of groups (3 groups: 8mm Z+, 8mm X+, 10mm X+, 10mm Y+)
        self.assertEqual(len(groups), 4)

        # Check each expected group
        # Group 1: 8mm Z+
        group_key = (8.0, (0, 0, 1))
        self.assertIn(group_key, groups)
        self.assertEqual(len(groups[group_key]), 2)

        # Group 2: 8mm X+
        group_key = (8.0, (1, 0, 0))
        self.assertIn(group_key, groups)
        self.assertEqual(len(groups[group_key]), 1)

        # Group 3: 10mm X+
        group_key = (10.0, (1, 0, 0))
        self.assertIn(group_key, groups)
        self.assertEqual(len(groups[group_key]), 1)

        # Group 4: 10mm Y+
        group_key = (10.0, (0, 1, 0))
        self.assertIn(group_key, groups)
        self.assertEqual(len(groups[group_key]), 1)

        # Verify all points have group_key added
        for point in result["drill_points"]:
            self.assertIn("group_key", point)

    def test_missing_drill_points(self):
        """Test behavior with missing drill points."""
        # Test with empty data
        success, message, _ = self.grouper.group_drilling_points({})
        self.assertFalse(success)

        # Test with empty drill points list
        success, message, _ = self.grouper.group_drilling_points({"drill_points": []})
        self.assertFalse(success)

    def test_missing_diameter(self):
        """Test behavior with drill points missing diameter."""
        # Create a point missing diameter
        invalid_data = {
            "drill_points": [
                {
                    "position": (100, 50, 0),
                    "extrusion_vector": (0, 0, 1),
                    # Missing diameter
                }
            ]
        }

        success, message, _ = self.grouper.group_drilling_points(invalid_data)
        self.assertFalse(success)

    def test_missing_direction(self):
        """Test behavior with drill points missing direction."""
        # Create a point missing direction
        invalid_data = {
            "drill_points": [
                {
                    "position": (100, 50, 0),
                    "diameter": 8.0,
                    # Missing extrusion_vector/direction
                }
            ]
        }

        success, message, _ = self.grouper.group_drilling_points(invalid_data)
        self.assertFalse(success)

    def test_direction_formats(self):
        """Test various forms of direction vectors."""
        # Test with both extrusion_vector and direction names
        mixed_data = {
            "drill_points": [
                {"position": (100, 50, 0), "extrusion_vector": (0, 0, 1), "diameter": 8.0},
                {"position": (200, 100, 0), "direction": (0, 0, 1), "diameter": 8.0},
            ]
        }

        success, message, result = self.grouper.group_drilling_points(mixed_data)
        self.assertTrue(success)

        # Both should be in the same group
        groups = result["grouped_points"]
        self.assertEqual(len(groups), 1)

        group_key = (8.0, (0, 0, 1))
        self.assertIn(group_key, groups)
        self.assertEqual(len(groups[group_key]), 2)


if __name__ == "__main__":
    unittest.main()
