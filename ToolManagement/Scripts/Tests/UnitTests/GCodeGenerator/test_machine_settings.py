"""
Unit tests for the MachineSettings module.

This module tests the functionality of the MachineSettings class
which provides machine-specific settings for G-code generation.
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
from GCodeGenerator.machine_settings import MachineSettings
from Utils.config import AppConfig


class TestMachineSettings(unittest.TestCase):
    """Test cases for the MachineSettings class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create machine settings with default configuration
        self.settings = MachineSettings()

        # Test data
        self.test_workpiece_small = {"width": 400.0, "height": 500.0, "thickness": 18.0}
        self.test_workpiece_large = {"width": 400.0, "height": 700.0, "thickness": 18.0}
        self.test_vectors = [
            (1.0, 0.0, 0.0),  # X+
            (-1.0, 0.0, 0.0),  # X-
            (0.0, 1.0, 0.0),  # Y+
            (0.0, -1.0, 0.0),  # Y-
            (0.5, 0.5, 0.0),  # Invalid
        ]

    def test_initialization_with_defaults(self):
        """Test initialization with default settings."""
        # Verify default settings are loaded correctly
        self.assertEqual(
            self.settings.settings["drilling_feed_rate"], AppConfig.gcode.DRILLING_FEED_RATE
        )
        self.assertEqual(
            self.settings.settings["approach_distance"], AppConfig.gcode.SAFE_APPROACH_DISTANCE
        )
        self.assertEqual(
            self.settings.settings["decimal_precision"], AppConfig.gcode.DECIMAL_PRECISION
        )

    def test_initialization_with_custom_settings(self):
        """Test initialization with custom settings."""
        # Create settings with custom values
        custom_settings = {
            "drilling_feed_rate": 150.0,
            "approach_distance": 15.0,
            "decimal_precision": 4,
        }

        custom_machine_settings = MachineSettings(custom_settings)

        # Verify custom settings are applied
        self.assertEqual(custom_machine_settings.settings["drilling_feed_rate"], 150.0)
        self.assertEqual(custom_machine_settings.settings["approach_distance"], 15.0)
        self.assertEqual(custom_machine_settings.settings["decimal_precision"], 4)

        # Verify other settings remain at defaults
        self.assertEqual(
            custom_machine_settings.settings["rapid_feed_rate"],
            AppConfig.gcode.RAPID_POSITIONING_FEED_RATE,
        )

    def test_get_feed_rate(self):
        """Test retrieval of feed rates."""
        # Test known operation types
        self.assertEqual(
            self.settings.get_feed_rate("drilling"), AppConfig.gcode.DRILLING_FEED_RATE
        )
        self.assertEqual(
            self.settings.get_feed_rate("rapid"), AppConfig.gcode.RAPID_POSITIONING_FEED_RATE
        )
        self.assertEqual(
            self.settings.get_feed_rate("retraction"), AppConfig.gcode.RETRACTION_FEED_RATE
        )

        # Test unknown operation type (should default to drilling)
        self.assertEqual(self.settings.get_feed_rate("unknown"), AppConfig.gcode.DRILLING_FEED_RATE)

    def test_get_approach_and_clearance_distance(self):
        """Test retrieval of approach and clearance distances."""
        self.assertEqual(
            self.settings.get_approach_distance(), AppConfig.gcode.SAFE_APPROACH_DISTANCE
        )
        self.assertEqual(
            self.settings.get_clearance_distance(), AppConfig.gcode.SAFE_CLEARANCE_DISTANCE
        )

    def test_get_positioning_commands(self):
        """Test retrieval of positioning commands."""
        commands = self.settings.get_positioning_commands()

        # Verify expected commands are present
        self.assertIn("safe_z_positioning", commands)
        self.assertIn("tooltip_positioning", commands)

        # Verify command values
        self.assertEqual(commands["safe_z_positioning"], "M151")
        self.assertEqual(commands["tooltip_positioning"], "M152")

    def test_get_vector_axis_info(self):
        """Test mapping of direction vectors to axis information."""
        # Test valid vectors
        x_pos_info = self.settings.get_vector_axis_info((1.0, 0.0, 0.0))
        self.assertEqual(x_pos_info["axis"], "X")
        self.assertEqual(x_pos_info["direction"], 1)
        self.assertEqual(x_pos_info["description"], "X+")

        x_neg_info = self.settings.get_vector_axis_info((-1.0, 0.0, 0.0))
        self.assertEqual(x_neg_info["axis"], "X")
        self.assertEqual(x_neg_info["direction"], -1)
        self.assertEqual(x_neg_info["description"], "X-")

        y_pos_info = self.settings.get_vector_axis_info((0.0, 1.0, 0.0))
        self.assertEqual(y_pos_info["axis"], "Y")
        self.assertEqual(y_pos_info["direction"], 1)
        self.assertEqual(y_pos_info["description"], "Y+")

        y_neg_info = self.settings.get_vector_axis_info((0.0, -1.0, 0.0))
        self.assertEqual(y_neg_info["axis"], "Y")
        self.assertEqual(y_neg_info["direction"], -1)
        self.assertEqual(y_neg_info["description"], "Y-")

        # Test invalid vector
        invalid_info = self.settings.get_vector_axis_info((0.5, 0.5, 0.0))
        self.assertEqual(invalid_info["axis"], "?")
        self.assertEqual(invalid_info["direction"], 0)
        self.assertEqual(invalid_info["description"], "Unknown")

    def test_get_coordinate_system(self):
        """Test coordinate system selection based on workpiece dimensions."""
        # Test small workpiece
        small_cs = self.settings.get_coordinate_system(self.test_workpiece_small)
        self.assertEqual(small_cs["command"], AppConfig.gcode.COORDINATE_SYSTEM_SMALL)

        # Test large workpiece
        large_cs = self.settings.get_coordinate_system(self.test_workpiece_large)
        self.assertEqual(large_cs["command"], AppConfig.gcode.COORDINATE_SYSTEM_LARGE)

        # Test with empty workpiece dimensions (should default to small)
        empty_cs = self.settings.get_coordinate_system({})
        self.assertEqual(empty_cs["command"], AppConfig.gcode.COORDINATE_SYSTEM_SMALL)

    def test_format_coordinate(self):
        """Test coordinate formatting."""
        # Test with default precision (3)
        self.assertEqual(self.settings.format_coordinate(10.1234), "10.123")
        self.assertEqual(self.settings.format_coordinate(10.0), "10.000")

        # Test with custom precision
        custom_settings = MachineSettings({"decimal_precision": 4})
        self.assertEqual(custom_settings.format_coordinate(10.12345), "10.1235")

    def test_format_comment(self):
        """Test comment formatting."""
        self.assertEqual(self.settings.format_comment("Test"), "(Test)")
        self.assertEqual(self.settings.format_comment(""), "()")

    def test_get_line_number(self):
        """Test line number generation."""
        # Test with default increment (1)
        self.assertEqual(self.settings.get_line_number(0), "N1")
        self.assertEqual(self.settings.get_line_number(1), "N2")
        self.assertEqual(self.settings.get_line_number(10), "N11")

        # Test with custom increment
        custom_settings = MachineSettings({"line_number_increment": 5})
        self.assertEqual(custom_settings.get_line_number(0), "N1")
        self.assertEqual(custom_settings.get_line_number(1), "N6")
        self.assertEqual(custom_settings.get_line_number(2), "N11")

        # Test with line numbers disabled
        disabled_settings = MachineSettings({"use_line_numbers": False})
        self.assertEqual(disabled_settings.get_line_number(0), "")
        self.assertEqual(disabled_settings.get_line_number(1), "")

    def test_get_default_gcode_header(self):
        """Test G-code header generation."""
        # Test header for small workpiece
        small_header = self.settings.get_default_gcode_header(self.test_workpiece_small)

        # Verify header contains expected commands
        self.assertEqual(small_header[0]["command"], "(")
        self.assertTrue("Program name:" in small_header[0]["comment"])

        self.assertEqual(small_header[1]["command"], "(")
        self.assertTrue("Workpiece dimensions:" in small_header[1]["comment"])

        self.assertEqual(small_header[2]["command"], AppConfig.gcode.DEFAULT_UNITS)
        self.assertEqual(small_header[3]["command"], AppConfig.gcode.DEFAULT_POSITIONING)
        self.assertEqual(small_header[4]["command"], AppConfig.gcode.DEFAULT_PLANE)
        self.assertEqual(small_header[5]["command"], AppConfig.gcode.DEFAULT_FEEDRATE_MODE)
        self.assertEqual(small_header[6]["command"], AppConfig.gcode.COORDINATE_SYSTEM_SMALL)
        self.assertEqual(small_header[7]["command"], "M00")

        # Test header for large workpiece
        large_header = self.settings.get_default_gcode_header(self.test_workpiece_large)
        self.assertEqual(large_header[6]["command"], AppConfig.gcode.COORDINATE_SYSTEM_LARGE)

        # Verify workpiece dimensions are formatted correctly (1 decimal place)
        self.assertTrue("400.0 x 500.0 x 18.0 mm" in small_header[1]["comment"])
        self.assertTrue("400.0 x 700.0 x 18.0 mm" in large_header[1]["comment"])

        # Test with custom program name
        custom_header = self.settings.get_default_gcode_header(
            self.test_workpiece_small, "test_program.nc"
        )
        self.assertTrue("test_program.nc" in custom_header[0]["comment"])

    def test_header_requires_valid_workpiece_dimensions(self):
        """Test that header generation requires valid workpiece dimensions."""
        # Should raise ValueError for missing dimensions
        with self.assertRaises(ValueError):
            self.settings.get_default_gcode_header({})

        with self.assertRaises(ValueError):
            self.settings.get_default_gcode_header({"width": 400.0, "height": 500.0})

        with self.assertRaises(ValueError):
            self.settings.get_default_gcode_header({"height": 500.0, "thickness": 18.0})

    def test_workpiece_dimension_rounding(self):
        """Test that workpiece dimensions are properly rounded to 1 decimal place."""
        # Test with dimensions that need rounding
        detailed_dimensions = {"width": 400.123, "height": 500.567, "thickness": 18.999}

        header = self.settings.get_default_gcode_header(detailed_dimensions)

        # Verify dimensions are rounded to 1 decimal place in the header
        self.assertTrue("400.1 x 500.6 x 19.0 mm" in header[1]["comment"])

    def test_get_default_gcode_footer(self):
        """Test G-code footer generation."""
        footer = self.settings.get_default_gcode_footer()

        # Verify footer contains expected commands
        self.assertEqual(footer[0]["command"], "M09")  # Coolant off
        self.assertEqual(footer[1]["command"], "M05")  # Spindle off
        self.assertEqual(footer[2]["command"], "T0")  # Select tool 0
        self.assertEqual(footer[3]["command"], "M30")  # Program end


if __name__ == "__main__":
    unittest.main()
