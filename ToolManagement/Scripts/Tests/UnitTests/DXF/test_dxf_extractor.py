"""
Unit tests for the DXF extractor module.

This module contains comprehensive unit tests for the extractor classes:
- DrillPointExtractor
- WorkpieceExtractor
- DXFExtractor

Tests cover normal operation, edge cases, and error handling.
"""

import unittest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Path setup for both running the test directly and through run_tests.py
# Get the current file's directory
current_dir = Path(__file__).parent.absolute()

# Get the Scripts directory (parent of Tests directory)
scripts_dir = current_dir.parent.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import testing requirements
import ezdxf
from DXF.parser import DXFParser
from DXF.extractor import DrillPointExtractor, WorkpieceExtractor, DXFExtractor
from Utils.error_utils import ValidationError, ErrorSeverity


class TestDXFExtractor(unittest.TestCase):
    """Tests for the DXFExtractor class."""
    
    def setUp(self):
        """Set up test environment before each test method."""
        # Initialize DXF extractor
        self.extractor = DXFExtractor()
        
        # Create temporary test files
        self.test_files = []
        
        # Create test file with valid data
        self.valid_file = self._create_valid_file()
        self.test_files.append(self.valid_file)
        
        # Create test file with missing workpiece
        self.missing_workpiece_file = self._create_missing_workpiece_file()
        self.test_files.append(self.missing_workpiece_file)
        
        # Create test file with missing drill points
        self.missing_drills_file = self._create_missing_drills_file()
        self.test_files.append(self.missing_drills_file)
        
        # Parse the test files
        self.parser = DXFParser()
        self.documents = {}
        
        for file_path in self.test_files:
            success, _, result = self.parser.parse(file_path)
            if success:
                self.documents[file_path] = result["document"]
    
    def tearDown(self):
        """Clean up test environment after each test method."""
        # Remove test files
        for file_path in self.test_files:
            if os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except:
                    pass
    
    def _create_valid_file(self):
        """Create a test file with both workpiece and drill points."""
        # Create a new DXF file
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        
        # Add a valid workpiece
        points = [(0, 0), (500, 0), (500, 400), (0, 400), (0, 0)]
        msp.add_lwpolyline(points, dxfattribs={"layer": "PANEL_Egger22mm"})
        
        # Add valid drill points
        msp.add_circle(center=(100, 100, 0), radius=4.0, dxfattribs={"layer": "EDGE.DRILL_D8.0_P15.0"})
        msp.add_circle(center=(200, 100, 0), radius=5.0, dxfattribs={"layer": "EDGE.DRILL_D10.0_P20.0"})
        
        # Save to a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.dxf', delete=False)
        doc.saveas(temp_file.name)
        return temp_file.name
    
    def _create_missing_workpiece_file(self):
        """Create a test file with drill points but no workpiece."""
        # Create a new DXF file
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        
        # Add only drill points
        msp.add_circle(center=(100, 100, 0), radius=4.0, dxfattribs={"layer": "EDGE.DRILL_D8.0_P15.0"})
        msp.add_circle(center=(200, 100, 0), radius=5.0, dxfattribs={"layer": "EDGE.DRILL_D10.0_P20.0"})
        
        # Save to a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.dxf', delete=False)
        doc.saveas(temp_file.name)
        return temp_file.name
    
    def _create_missing_drills_file(self):
        """Create a test file with workpiece but no drill points."""
        # Create a new DXF file
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        
        # Add only a workpiece
        points = [(0, 0), (500, 0), (500, 400), (0, 400), (0, 0)]
        msp.add_lwpolyline(points, dxfattribs={"layer": "PANEL_Egger22mm"})
        
        # Save to a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.dxf', delete=False)
        doc.saveas(temp_file.name)
        return temp_file.name
    
    def test_process_valid_file(self):
        """Test processing a valid DXF file with both workpiece and drill points."""
        document = self.documents.get(self.valid_file)
        self.assertIsNotNone(document, "Failed to parse test file")
        
        # Process the document
        success, message, result = self.extractor.process(document)
        
        # Check extraction succeeded
        self.assertTrue(success)
        self.assertIn("Extraction complete", message)
        
        # Validate workpiece
        self.assertIn("workpiece", result)
        workpiece = result["workpiece"]
        self.assertEqual(workpiece["width"], 500.0)
        self.assertEqual(workpiece["height"], 400.0)
        self.assertEqual(workpiece["thickness"], 22.0)
        
        # Validate drill points
        self.assertIn("drill_points", result)
        drill_points = result["drill_points"]
        self.assertEqual(len(drill_points), 2)
    
    def test_missing_workpiece(self):
        """Test that extraction fails when workpiece is missing."""
        document = self.documents.get(self.missing_workpiece_file)
        self.assertIsNotNone(document, "Failed to parse test file")
        
        # Process the document
        success, message, _ = self.extractor.process(document)
        
        # Check extraction failed
        self.assertFalse(success)
        self.assertIn("workpiece", message.lower())
    
    def test_missing_drill_points(self):
        """Test that extraction fails when drill points are missing."""
        document = self.documents.get(self.missing_drills_file)
        self.assertIsNotNone(document, "Failed to parse test file")
        
        # Process the document
        success, message, _ = self.extractor.process(document)
        
        # Check extraction failed
        self.assertFalse(success)
        self.assertIn("drill point", message.lower())
    
    def test_skipped_points_reporting(self):
        """Test that skipped drill points are properly reported."""
        # Create a mock document
        doc = MagicMock()
        
        # Mock the WorkpieceExtractor.extract method
        mock_wp_result = {
            "workpiece": {
                "width": 500.0,
                "height": 400.0,
                "thickness": 22.0,
                "corner_points": [(0, 0, 0), (500, 0, 0), (500, 400, 0), (0, 400, 0)],
                "layer": "PANEL_Egger22mm"
            }
        }
        wp_success = True
        wp_message = "Workpiece extraction succeeded"
        
        # Mock the DrillPointExtractor.extract method with skipped points
        mock_drill_result = {
            "drill_points": [
                {"position": (100, 100, 0), "diameter": 8.0, "depth": 15.0},
                {"position": (200, 100, 0), "diameter": 10.0, "depth": 20.0}
            ],
            "skipped_count": 3,
            "issues": [
                {"entity_type": "CIRCLE", "layer": "EDGE.DRILL_D8.0", "position": "(300, 100, 0)"},
                {"entity_type": "CIRCLE", "layer": "EDGE.DRILL_D0.0_P15.0", "position": "(400, 100, 0)"},
                {"entity_type": "CIRCLE", "layer": "EDGE.DRILL_D8.0_P0.0", "position": "(500, 100, 0)"}
            ]
        }
        drill_success = True
        drill_message = "Drill extraction succeeded with warnings"
        
        # Patch the extract methods
        with patch.object(self.extractor.workpiece_extractor, 'extract', return_value=(wp_success, wp_message, mock_wp_result)):
            with patch.object(self.extractor.drill_extractor, 'extract', return_value=(drill_success, drill_message, mock_drill_result)):
                # Process the document
                success, message, result = self.extractor.process(doc)
                
                # Check extraction succeeded with warning
                self.assertTrue(success)
                self.assertIn("3 points skipped", message)
                
                # Check that issues were included in result
                self.assertEqual(result["skipped_drill_points"], 3)
                self.assertEqual(len(result["issues"]), 3)


if __name__ == "__main__":
    unittest.main()