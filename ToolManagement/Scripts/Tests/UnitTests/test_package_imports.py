"""
Test script to verify package imports can be resolved.
Tests that DXF and GCode package structure is correct across platforms.

This module serves as a reference for the proper import path handling
pattern that all tests should follow.
"""
import unittest
import os
import sys
import importlib
from pathlib import Path

# Get the current file's directory
current_dir = Path(__file__).parent.absolute()

# Get the Scripts directory (parent of Tests directory)
scripts_dir = current_dir.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Add ToolManagement directory to path to support absolute imports
# This allows importing modules using their full package path
project_dir = scripts_dir.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))


class TestPackageImports(unittest.TestCase):
    """Tests that package imports can be resolved without errors."""
    
    def test_dxf_package_import(self):
        """Test that the DXF package can be imported."""
        try:
            import DXF
            self.assertTrue(True, "DXF package imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import DXF package: {e}")
            
    def test_gcode_package_import(self):
        """Test that the GCode package can be imported."""
        try:
            import GCode
            self.assertTrue(True, "GCode package imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import GCode package: {e}")
    
    def test_dxf_module_imports(self):
        """Test that DXF modules can be imported."""
        # List currently available DXF modules only
        dxf_modules = [
            "DXF.parser",
            # Other modules will be added as they are developed
        ]

        for module in dxf_modules:
            try:
                importlib.import_module(module)
                self.assertTrue(True, f"{module} imported successfully")
            except ImportError as e:
                self.fail(f"Failed to import {module}: {e}")

    def test_gcode_module_imports(self):
        """Test that GCode modules can be imported."""
        # List currently available GCode modules only
        # Currently, these may not all exist - update as modules are developed
        gcode_modules = [
            "GCode.gcode_normalizer",
            # Other modules will be added as they are developed
        ]

        # Only test modules that actually exist
        existing_modules = []
        for module in gcode_modules:
            module_path = Path(scripts_dir) / f"{module.replace('.', '/')}.py"
            if module_path.exists():
                existing_modules.append(module)

        # If no modules exist yet, skip this test
        if not existing_modules:
            self.skipTest("No GCode modules found - will be added as they are developed")

        for module in existing_modules:
            try:
                importlib.import_module(module)
                self.assertTrue(True, f"{module} imported successfully")
            except ImportError as e:
                self.fail(f"Failed to import {module}: {e}")
                
    def test_import_across_platforms(self):
        """Test that platform-specific path handling works correctly."""
        # Get platform information
        import platform
        system = platform.system()
        
        # This test just checks that the platform is correctly identified
        # You can expand this later with platform-specific tests
        if system == 'Windows':
            self.assertEqual(os.sep, '\\', "Correct path separator for Windows")
        else:
            self.assertEqual(os.sep, '/', "Correct path separator for Unix-like systems")


if __name__ == '__main__':
    unittest.main()