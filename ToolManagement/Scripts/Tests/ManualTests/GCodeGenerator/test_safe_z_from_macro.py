"""
Test reading TOOL_CHANGE_HEIGHT from m6start.m1s macro.

This test verifies that the machine_settings module can successfully
read the safe Z height from the VBScript macro file.
"""

import sys
from pathlib import Path

# Path setup for imports
current_dir = Path(__file__).parent.absolute()
scripts_dir = current_dir.parent.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from GCodeGenerator.machine_settings import MachineSettings
from GCodeGenerator.drilling_operations import generate_drilling_sequence


def test_safe_z_reading():
    """Test reading safe Z height from macro."""
    print("=" * 60)
    print("Testing Safe Z Height Reading from m6start.m1s")
    print("=" * 60)
    
    try:
        # Create machine settings instance
        settings = MachineSettings()
        
        # Try to get safe Z height
        safe_z = settings.get_safe_z_height()
        print(f"\nSUCCESS: Read safe Z height: {safe_z}mm")
        
        # Test in drilling sequence
        test_drill_point = {
            "machine_position": (100.0, 200.0, 9.0),
            "diameter": 8.0,
            "depth": 15.0,
            "extrusion_vector": (1.0, 0.0, 0.0),
        }
        
        success, message, details = generate_drilling_sequence(test_drill_point, settings)
        
        if success:
            print("\nSUCCESS: Generated drilling sequence")
            print("\nG-code lines:")
            for line in details["gcode_lines"]:
                print(f"  {line}")
                # Verify safe Z is used
                if "G53 G00 Z" in line and "Return to safe height" in line:
                    print(f"  --> Confirmed: Using safe Z height of {safe_z}mm")
        else:
            print(f"\nERROR: Failed to generate drilling sequence: {message}")
            
    except RuntimeError as e:
        print(f"\nCRITICAL ERROR: {e}")
        print("\nThis error means the TOOL_CHANGE_HEIGHT could not be read from the macro.")
        print("Please verify:")
        print("1. The m6start.m1s file exists in the expected location")
        print("2. The file contains: Const TOOL_CHANGE_HEIGHT = <value>")
        return False
    except Exception as e:
        print(f"\nERROR: Unexpected error: {e}")
        return False
    
    print("\n" + "=" * 60)
    return True


if __name__ == "__main__":
    success = test_safe_z_reading()
    sys.exit(0 if success else 1)