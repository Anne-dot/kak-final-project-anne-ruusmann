"""
Unit tests for the ToolMatcher module.

This module tests the functionality of the ToolMatcher class
which matches drilling operations to appropriate tools.
"""

import os
import sys
import unittest
from pathlib import Path
from typing import Dict, List, Tuple, Any
from unittest.mock import patch, MagicMock

# Path setup for imports
current_dir = Path(__file__).parent.absolute()
scripts_dir = current_dir.parent.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import module to test
from GCodeGenerator.tool_matcher import ToolMatcher


class TestToolMatcher(unittest.TestCase):
    """Test cases for the ToolMatcher class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock CSV data for testing instead of relying on external file
        self.mock_csv_data = {
            "rows": [
                {
                    "tool_number": "1",
                    "tool_type": "VerticalDrill",
                    "tool_direction": "5",
                    "diameter": "8.0",
                    "in_spindle": "1",
                    "description": "Vertical Drill 8mm"
                },
                {
                    "tool_number": "2",
                    "tool_type": "HorizontalDrill",
                    "tool_direction": "1",
                    "diameter": "10.0",
                    "in_spindle": "0",
                    "description": "Horizontal Drill 10mm X+"
                },
                {
                    "tool_number": "3",
                    "tool_type": "HorizontalDrill",
                    "tool_direction": "2",
                    "diameter": "10.0",
                    "in_spindle": "1",
                    "description": "Horizontal Drill 10mm X-"
                },
                {
                    "tool_number": "4",
                    "tool_type": "HorizontalDrill",
                    "tool_direction": "3",
                    "diameter": "12.0",
                    "in_spindle": "0",
                    "description": "Horizontal Drill 12mm Y+"
                }
            ]
        }
        
        # Sample group keys for testing
        self.group_keys = [
            (8.0, (0.0, 0.0, 1.0)),    # 8mm vertical (direction 5)
            (10.0, (1.0, 0.0, 0.0)),   # 10mm horizontal X+ (direction 1)
            (10.0, (-1.0, 0.0, 0.0)),  # 10mm horizontal X- (direction 2)
            (12.0, (0.0, 1.0, 0.0)),   # 12mm horizontal Y+ (direction 3)
            (6.0, (0.0, 0.0, 1.0)),    # 6mm vertical - no match
        ]
    
    @patch('GCodeGenerator.tool_matcher.FileUtils.read_csv')
    def test_match_tool_to_group_success(self, mock_read_csv):
        """Test successful tool matching cases."""
        # Setup mock
        mock_read_csv.return_value = (True, "Success", self.mock_csv_data)
        
        # Create matcher with mock tool data
        matcher = ToolMatcher("mock_path")
        
        # Test vertical drill match
        success, message, result = matcher.match_tool_to_group(self.group_keys[0])
        self.assertTrue(success)
        self.assertEqual(result["tool_number"], 1)
        self.assertEqual(result["diameter"], 8.0)
        self.assertEqual(result["direction"], 5)
        
        # Test horizontal X+ drill match
        success, message, result = matcher.match_tool_to_group(self.group_keys[1])
        self.assertTrue(success)
        self.assertEqual(result["tool_number"], 2)
        self.assertEqual(result["diameter"], 10.0)
        self.assertEqual(result["direction"], 1)
        
        # Test horizontal X- drill match
        success, message, result = matcher.match_tool_to_group(self.group_keys[2])
        self.assertTrue(success)
        self.assertEqual(result["tool_number"], 3)
        self.assertEqual(result["diameter"], 10.0)
        self.assertEqual(result["direction"], 2)
        
        # Test horizontal Y+ drill match
        success, message, result = matcher.match_tool_to_group(self.group_keys[3])
        self.assertTrue(success)
        self.assertEqual(result["tool_number"], 4)
        self.assertEqual(result["diameter"], 12.0)
        self.assertEqual(result["direction"], 3)
    
    @patch('GCodeGenerator.tool_matcher.FileUtils.read_csv')
    def test_match_tool_to_group_no_match(self, mock_read_csv):
        """Test case where no matching tool is found."""
        # Setup mock
        mock_read_csv.return_value = (True, "Success", self.mock_csv_data)
        
        # Create matcher with mock tool data
        matcher = ToolMatcher("mock_path")
        
        # Test with diameter that doesn't exist in tool data
        success, message, _ = matcher.match_tool_to_group(self.group_keys[4])
        self.assertFalse(success)
        self.assertIn("No exact diameter match found", message)
    
    @patch('GCodeGenerator.tool_matcher.FileUtils.read_csv')
    def test_invalid_direction_vector(self, mock_read_csv):
        """Test with invalid direction vector."""
        # Setup mock
        mock_read_csv.return_value = (True, "Success", self.mock_csv_data)
        
        # Create matcher with mock tool data
        matcher = ToolMatcher("mock_path")
        
        # Test with direction vector that doesn't map to a valid code
        success, message, _ = matcher.match_tool_to_group((8.0, (0.5, 0.5, 0.0)))
        self.assertFalse(success)
        self.assertIn("Unsupported direction vector", message)
    
    @patch('GCodeGenerator.tool_matcher.FileUtils.read_csv')
    def test_invalid_group_key(self, mock_read_csv):
        """Test with invalid group key format."""
        # Setup mock
        mock_read_csv.return_value = (True, "Success", self.mock_csv_data)
        
        # Create matcher with mock tool data
        matcher = ToolMatcher("mock_path")
        
        # Test with invalid group key (string instead of tuple)
        success, message, _ = matcher.match_tool_to_group("invalid")
        self.assertFalse(success)
        self.assertIn("Invalid group key format", message)
    
    @patch('GCodeGenerator.tool_matcher.FileUtils.read_csv')
    def test_csv_read_error(self, mock_read_csv):
        """Test handling of CSV read error."""
        # Setup mock to return failure
        mock_read_csv.return_value = (False, "Failed to read CSV", {})
        
        # Create matcher with mock tool data
        matcher = ToolMatcher("mock_path")
        
        # Test with valid group key but CSV read fails
        success, message, _ = matcher.match_tool_to_group(self.group_keys[0])
        self.assertFalse(success)
        self.assertIn("Failed to read tool data", message)
    
    def test_convert_vector_to_direction_code(self):
        """Test direction vector conversion."""
        matcher = ToolMatcher("mock_path")
        
        # Test all valid vectors
        self.assertEqual(matcher._convert_vector_to_direction_code((1.0, 0.0, 0.0)), 1)
        self.assertEqual(matcher._convert_vector_to_direction_code((-1.0, 0.0, 0.0)), 2)
        self.assertEqual(matcher._convert_vector_to_direction_code((0.0, 1.0, 0.0)), 3)
        self.assertEqual(matcher._convert_vector_to_direction_code((0.0, -1.0, 0.0)), 4)
        self.assertEqual(matcher._convert_vector_to_direction_code((0.0, 0.0, 1.0)), 5)
        
        # Test invalid vector
        self.assertIsNone(matcher._convert_vector_to_direction_code((0.5, 0.5, 0.0)))
    
    @patch('GCodeGenerator.tool_matcher.FileUtils.read_csv')
    def test_prepare_tool_data_for_response(self, mock_read_csv):
        """Test formatting of tool data response."""
        # Create a raw tool record
        raw_tool = {
            "tool_number": "5",
            "tool_type": "VerticalDrill",
            "tool_direction": "5",
            "diameter": "8.5",
            "tool_length": "100.0",
            "max_working_length": "150.0",
            "tool_holder_z_offset": "0.0",
            "in_spindle": "1",
            "rotation_direction": "CW",
            "description": "Special Vertical Drill",
            "notes": "For special applications"
        }
        
        # Create matcher
        matcher = ToolMatcher("mock_path")
        
        # Call the method
        formatted = matcher._prepare_tool_data_for_response(raw_tool)
        
        # Verify conversion of numeric fields
        self.assertEqual(formatted["tool_number"], 5)
        self.assertEqual(formatted["diameter"], 8.5)
        self.assertEqual(formatted["tool_length"], 100.0)
        self.assertEqual(formatted["max_working_length"], 150.0)
        self.assertEqual(formatted["tool_holder_z_offset"], 0.0)
        
        # Verify boolean conversion
        self.assertTrue(formatted["in_spindle"])
        
        # Verify string fields preserved
        self.assertEqual(formatted["description"], "Special Vertical Drill")
        self.assertEqual(formatted["notes"], "For special applications")


if __name__ == "__main__":
    unittest.main()