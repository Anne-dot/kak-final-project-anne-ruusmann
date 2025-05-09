#!/usr/bin/env python3
"""
Simplified unit tests for the drilling_extractor module.

This approach uses the existing DXF file in TestData/DXF instead of
creating mock objects or generating test files.
"""

import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import modules to test
from DXF.drilling_extractor import DrillingExtractor
from DXF.file_loader import DxfLoader

class TestDrillingExtractorSimple(unittest.TestCase):
    """Test drilling point extraction using an existing DXF file."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        # Initialize extractors
        cls.extractor = DrillingExtractor()
        cls.loader = DxfLoader()
        
        # Define test data directory
        cls.test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'TestData', 'DXF'))
        
        # Find available DXF file in the test directory
        cls.dxf_files = []
        if os.path.exists(cls.test_dir):
            cls.dxf_files = [f for f in os.listdir(cls.test_dir) if f.lower().endswith('.dxf')]
        
        # Pre-load DXF document for efficiency
        cls.doc = None
        cls.dxf_file = None
        
        if cls.dxf_files:
            cls.dxf_file = os.path.join(cls.test_dir, cls.dxf_files[0])
            success, message, details = cls.loader.load_dxf(cls.dxf_file)
            if success:
                cls.doc = details.get('document')
            else:
                print(f"Failed to load test file: {message}")
    
    def setUp(self):
        """Set up for each test."""
        # Skip all tests if no DXF file is available
        if not self.doc:
            self.skipTest("No valid DXF file available in TestData/DXF directory")
    
    def test_file_loading(self):
        """Verify that the test file loaded correctly."""
        self.assertIsNotNone(self.doc)
        self.assertTrue(self.dxf_file.endswith('.dxf'))
        
        # Print file info for debugging
        success, message, details = self.loader.get_dxf_info(self.doc)
        self.assertTrue(success, f"Failed to get DXF info: {message}")
        info = details
        
        print(f"\nLoaded test file: {os.path.basename(self.dxf_file)}")
        print(f"  Version: {info['dxf_version']}")
        print(f"  Total entities: {info['total_entities']}")
        
        # Print layer info for better debugging
        print("\nLayers:")
        for layer_name in info['layers']:
            print(f"  - {layer_name}")
        
        # Print entity counts
        print("\nEntity types:")
        for entity_type, count in info['entity_counts'].items():
            print(f"  - {entity_type}: {count}")
    
    def test_find_drilling_points(self):
        """Test extraction of drilling points from the test file."""
        # Extract drilling points
        success, message, details = self.extractor.find_drilling_points(self.doc)
        
        # Print results for debugging
        print(f"\nDrilling point extraction: {'Success' if success else 'Failed'}")
        print(f"Message: {message}")
        
        if success:
            drill_points = details.get('drill_points', [])
            print(f"Found {len(drill_points)} drilling points")
            
            # Print some details about the first few points
            if drill_points:
                print("\nSample drilling points:")
                for i, point in enumerate(drill_points[:3]):  # Just show first 3
                    print(f"  {i+1}. Position: {point.position}, Diameter: {point.diameter}, Depth: {point.depth}")
        
        # Basic assertions
        self.assertTrue(success, f"Failed to find drilling points: {message}")
        self.assertIsNotNone(details)
        self.assertIn('drill_points', details)
        self.assertIn('count', details)
    
    def test_extract_parameters(self):
        """Test extraction of drilling parameters."""
        # First get drilling points
        success, message, details = self.extractor.find_drilling_points(self.doc)
        if not success:
            self.skipTest(f"Could not extract drilling points: {message}")
        
        drill_points = details.get('drill_points', [])
        
        # Extract parameters
        success, message, details = self.extractor.extract_drilling_parameters(drill_points)
        
        # Print results for debugging
        print(f"\nParameter extraction: {'Success' if success else 'Failed'}")
        print(f"Message: {message}")
        
        if success:
            parameters = details.get('parameters', [])
            print(f"Extracted parameters for {len(parameters)} points")
            
            # Display sample parameters
            if parameters:
                print("\nSample parameters:")
                for i, param in enumerate(parameters[:3]):  # Just show first 3
                    print(f"  {i+1}. Position: {param.get('position')}, Diameter: {param.get('diameter')}, Depth: {param.get('depth')}")
        
        # Basic assertions
        self.assertTrue(success, f"Failed to extract parameters: {message}")
        self.assertIsNotNone(details)
        self.assertIn('parameters', details)
        self.assertIn('count', details)
    
    def test_extract_all_drilling_info(self):
        """Test complete extraction of drilling info."""
        # Extract all info in one call
        success, message, details = self.extractor.extract_all_drilling_info(self.doc)
        
        # Print results for debugging
        print(f"\nAll drilling info extraction: {'Success' if success else 'Failed'}")
        print(f"Message: {message}")
        
        if success:
            print(f"Found {details.get('count', 0)} drilling points")
            points = details.get('points', [])
            parameters = details.get('parameters', [])
            
            print(f"Points: {len(points)}")
            print(f"Parameters: {len(parameters)}")
        else:
            print(f"Error: {message}")
            print(f"Error details: {details}")
        
        # Basic assertions
        self.assertTrue(success, f"Failed to extract all drilling info: {message}")
        self.assertIsNotNone(details)
        self.assertIn('points', details)
        self.assertIn('parameters', details)
        self.assertIn('count', details)

if __name__ == '__main__':
    unittest.main()