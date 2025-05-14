"""
Unit tests for the Machine Positioner module.

This module tests the functionality of the MachinePositioner class
which calculates and applies offsets to workpiece coordinates.
"""

import os
import sys
import unittest
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Path setup for imports
current_dir = Path(__file__).parent.absolute()
scripts_dir = current_dir.parent.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import module to test
from ProcessingEngine.machine_positioner import MachinePositioner


class TestMachinePositioner(unittest.TestCase):
    """Test cases for the MachinePositioner class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.positioner = MachinePositioner()
        
        # Sample workpiece data - a rectangular workpiece with corners in Q1
        self.q1_workpiece = {
            "width": 500,
            "height": 300,
            "thickness": 20,
            "corner_points": [
                (0, 0, 0),           # Origin
                (0, 300, 0),         # Height edge
                (500, 300, 0),       # Point C (opposite)
                (500, 0, 0)          # Width edge
            ]
        }
        
        # Sample workpiece with corners in Q2
        self.q2_workpiece = {
            "width": 500,
            "height": 300,
            "thickness": 20,
            "corner_points": [
                (0, 0, 0),           # Origin
                (-500, 0, 0),        # Width edge
                (-500, 300, 0),      # Point C (opposite)
                (0, 300, 0)          # Height edge
            ]
        }
        
        # Sample workpiece with corners in Q3
        self.q3_workpiece = {
            "width": 500,
            "height": 300,
            "thickness": 20,
            "corner_points": [
                (0, 0, 0),           # Origin
                (-500, 0, 0),        # Width edge
                (-500, -300, 0),     # Point C (opposite)
                (0, -300, 0)         # Height edge
            ]
        }
        
        # Sample workpiece with corners in Q4
        self.q4_workpiece = {
            "width": 500,
            "height": 300,
            "thickness": 20,
            "corner_points": [
                (0, 0, 0),           # Origin
                (500, 0, 0),         # Width edge
                (500, -300, 0),      # Point C (opposite)
                (0, -300, 0)         # Height edge
            ]
        }
        
        # Sample drill points
        self.drill_points = [
            {
                "position": (100, 100, 0),
                "extrusion_vector": (0, 0, 1),
                "diameter": 8.0
            },
            {
                "position": (400, 200, 0),
                "extrusion_vector": (1, 0, 0),
                "diameter": 10.0
            }
        ]
    
    def test_determine_offset_q1(self):
        """Test offset calculation for Q1 (x>0, y>0)."""
        point_c = (500, 300, 0)
        offset_x, offset_y = self.positioner._determine_offset(point_c[0], point_c[1])
        
        # Q1 rule: Apply (0, -y_c)
        self.assertEqual(offset_x, 0)
        self.assertEqual(offset_y, -300)
    
    def test_determine_offset_q2(self):
        """Test offset calculation for Q2 (x<0, y>0)."""
        point_c = (-500, 300, 0)
        offset_x, offset_y = self.positioner._determine_offset(point_c[0], point_c[1])
        
        # Q2 rule: Apply (-x_c, -y_c)
        self.assertEqual(offset_x, 500)
        self.assertEqual(offset_y, -300)
    
    def test_determine_offset_q3(self):
        """Test offset calculation for Q3 (x<0, y<0)."""
        point_c = (-500, -300, 0)
        offset_x, offset_y = self.positioner._determine_offset(point_c[0], point_c[1])
        
        # Q3 rule: Apply (-x_c, 0)
        self.assertEqual(offset_x, 500)
        self.assertEqual(offset_y, 0)
    
    def test_determine_offset_q4(self):
        """Test offset calculation for Q4 (x>0, y<0)."""
        point_c = (500, -300, 0)
        offset_x, offset_y = self.positioner._determine_offset(point_c[0], point_c[1])
        
        # Q4 rule: Apply (0, 0)
        self.assertEqual(offset_x, 0)
        self.assertEqual(offset_y, 0)
    
    def test_apply_offset_to_coordinates(self):
        """Test applying offset to coordinates."""
        # Test with positive offset
        coords = (100, 100, 0)
        offset = (50, 50)
        new_coords = self.positioner._apply_offset_to_coordinates(coords, offset)
        
        self.assertEqual(new_coords, (150.0, 150.0, 0))
        
        # Test with negative offset
        coords = (100, 100, 0)
        offset = (-50, -50)
        new_coords = self.positioner._apply_offset_to_coordinates(coords, offset)
        
        self.assertEqual(new_coords, (50.0, 50.0, 0))
        
        # Test with zero offset
        coords = (100, 100, 0)
        offset = (0, 0)
        new_coords = self.positioner._apply_offset_to_coordinates(coords, offset)
        
        self.assertEqual(new_coords, (100.0, 100.0, 0))
        
        # Test with decimal values
        coords = (100.5, 100.5, 0)
        offset = (0.5, 0.5)
        new_coords = self.positioner._apply_offset_to_coordinates(coords, offset)
        
        # Should be rounded to 0.1mm precision
        self.assertEqual(new_coords, (101.0, 101.0, 0))
    
    def test_validate_workpiece_data(self):
        """Test workpiece data validation."""
        # Test valid workpiece
        success, message, _ = self.positioner._validate_workpiece_data(self.q1_workpiece)
        self.assertTrue(success)
        
        # Test empty workpiece
        success, message, _ = self.positioner._validate_workpiece_data({})
        self.assertFalse(success)
        
        # Test missing corner_points
        invalid_workpiece = {"width": 500, "height": 300}
        success, message, _ = self.positioner._validate_workpiece_data(invalid_workpiece)
        self.assertFalse(success)
    
    def test_position_for_top_left_machine_q1(self):
        """Test positioning with workpiece in Q1."""
        test_data = {
            "workpiece": self.q1_workpiece,
            "drill_points": self.drill_points
        }
        
        success, message, result = self.positioner.position_for_top_left_machine(test_data)
        
        # Check success and result structure
        self.assertTrue(success)
        self.assertIn("workpiece", result)
        self.assertIn("drill_points", result)
        self.assertIn("machine_corner_points", result)
        self.assertIn("offset", result)
        
        # Check offset calculation
        self.assertEqual(result["offset"], (0, -300))
        
        # Check corner points transformation
        machine_corners = result["machine_corner_points"]
        self.assertEqual(len(machine_corners), 4)
        
        # Check that the third corner (top-left) is now at origin
        self.assertEqual(machine_corners[1], (0, 0, 0))
        
        # Check drill points transformation
        machine_drill_points = result["drill_points"]
        self.assertEqual(len(machine_drill_points), 2)
        
        # First drill point should be offset by (0, -300)
        self.assertEqual(machine_drill_points[0]["machine_position"], (100, -200, 0))
        
        # Second drill point should be offset by (0, -300)
        self.assertEqual(machine_drill_points[1]["machine_position"], (400, -100, 0))
    
    def test_position_for_top_left_machine_q2(self):
        """Test positioning with workpiece in Q2."""
        test_data = {
            "workpiece": self.q2_workpiece,
            "drill_points": self.drill_points
        }
        
        success, message, result = self.positioner.position_for_top_left_machine(test_data)
        
        # Check success and result structure
        self.assertTrue(success)
        
        # Check offset calculation
        self.assertEqual(result["offset"], (500, -300))
        
        # Check that the height edge (top-left) is now at origin
        machine_corners = result["machine_corner_points"]
        self.assertEqual(machine_corners[3], (500, 0, 0))
    
    def test_position_for_top_left_machine_q3(self):
        """Test positioning with workpiece in Q3."""
        test_data = {
            "workpiece": self.q3_workpiece,
            "drill_points": self.drill_points
        }
        
        success, message, result = self.positioner.position_for_top_left_machine(test_data)
        
        # Check success and result structure
        self.assertTrue(success)
        
        # Check offset calculation
        self.assertEqual(result["offset"], (500, 0))
        
        # Check that the height edge (top-left) is now at origin
        machine_corners = result["machine_corner_points"]
        self.assertEqual(machine_corners[3], (500, -300, 0))
    
    def test_position_for_top_left_machine_q4(self):
        """Test positioning with workpiece in Q4."""
        test_data = {
            "workpiece": self.q4_workpiece,
            "drill_points": self.drill_points
        }
        
        success, message, result = self.positioner.position_for_top_left_machine(test_data)
        
        # Check success and result structure
        self.assertTrue(success)
        
        # Check offset calculation
        self.assertEqual(result["offset"], (0, 0))
        
        # Check that the height edge (top-left) is now at origin
        machine_corners = result["machine_corner_points"]
        self.assertEqual(machine_corners[3], (0, -300, 0))
    
    def test_invalid_input(self):
        """Test behavior with invalid input."""
        # Test with no data
        success, message, _ = self.positioner.position_for_top_left_machine(None)
        self.assertFalse(success)
        
        # Test with empty data
        success, message, _ = self.positioner.position_for_top_left_machine({})
        self.assertFalse(success)
        
        # Test with missing workpiece
        success, message, _ = self.positioner.position_for_top_left_machine({"drill_points": []})
        self.assertFalse(success)
        
        # Test with insufficient corner points
        invalid_workpiece = {
            "corner_points": [(0, 0, 0), (1, 0, 0), (1, 1, 0)]  # Only 3 points
        }
        success, message, _ = self.positioner.position_for_top_left_machine({
            "workpiece": invalid_workpiece,
            "drill_points": []
        })
        self.assertFalse(success)
        
        # Test with drill point missing position
        invalid_drill_point = {"diameter": 8.0}
        success, message, _ = self.positioner.position_for_top_left_machine({
            "workpiece": self.q1_workpiece,
            "drill_points": [invalid_drill_point]
        })
        self.assertFalse(success)
    
    def test_get_orientation_name(self):
        """Test orientation name detection."""
        # Test Q1
        self.assertEqual(self.positioner.get_orientation_name((300, 200, 0)), "bottom-left")
        
        # Test Q2
        self.assertEqual(self.positioner.get_orientation_name((-300, 200, 0)), "bottom-right")
        
        # Test Q3
        self.assertEqual(self.positioner.get_orientation_name((-300, -200, 0)), "top-right")
        
        # Test Q4
        self.assertEqual(self.positioner.get_orientation_name((300, -200, 0)), "top-left")
        
        # Test on axis
        self.assertEqual(self.positioner.get_orientation_name((0, 0, 0)), "unknown")


if __name__ == "__main__":
    unittest.main()