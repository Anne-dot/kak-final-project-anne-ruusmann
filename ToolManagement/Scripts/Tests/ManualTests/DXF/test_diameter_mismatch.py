"""
Test for diameter mismatch detection in DrillPointExtractor.

This script creates a temporary DXF file with intentional mismatches
between circle diameters and layer name specifications, then verifies
that the extractor correctly identifies and reports these mismatches.
"""

import os
import sys
import tempfile
from pathlib import Path

# Path setup for imports
current_dir = Path(__file__).parent.absolute()
scripts_dir = current_dir.parent.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import ezdxf for DXF creation and our modules
import ezdxf

from DXF.extractor import DrillPointExtractor
from DXF.parser import DXFParser


def create_test_dxf():
    """Create a test DXF file with diameter mismatches."""
    print("\nCreating test DXF file with diameter mismatches...")

    # Create a new DXF file
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Add various circles with intentional mismatches

    # Case 1: Perfect match (control case)
    msp.add_circle(center=(0, 0, 0), radius=4.0, dxfattribs={"layer": "EDGE.DRILL_D8.0_P21.5"})
    print("  Added circle: 8.0mm diameter on layer EDGE.DRILL_D8.0_P21.5")

    # Case 2: Small mismatch (under threshold)
    msp.add_circle(center=(20, 0, 0), radius=4.05, dxfattribs={"layer": "EDGE.DRILL_D8.0_P15.0"})
    print("  Added circle: 8.1mm diameter on layer EDGE.DRILL_D8.0_P15.0 (1.25% difference)")

    # Case 3: Significant mismatch (above threshold)
    msp.add_circle(center=(40, 0, 0), radius=5.0, dxfattribs={"layer": "EDGE.DRILL_D8.0_P18.0"})
    print("  Added circle: 10.0mm diameter on layer EDGE.DRILL_D8.0_P18.0 (25% difference)")

    # Case 4: Extreme mismatch
    msp.add_circle(center=(60, 0, 0), radius=8.0, dxfattribs={"layer": "EDGE.DRILL_D8.0_P10.0"})
    print("  Added circle: 16.0mm diameter on layer EDGE.DRILL_D8.0_P10.0 (100% difference)")

    # Save to a temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix=".dxf", delete=False)
    doc.saveas(temp_file.name)
    print(f"  Saved test file to: {temp_file.name}")

    return temp_file.name


def run_test():
    """Run diameter mismatch detection test."""
    print("\nDiameter Mismatch Detection Test")
    print("=" * 30)

    # Create test file
    test_file = create_test_dxf()

    # Step 1: Parse the DXF file
    parser = DXFParser()
    success, message, result = parser.parse(test_file)

    if not success:
        print(f"Failed to parse DXF file: {message}")
        os.unlink(test_file)  # Clean up
        return

    print(f"DXF parsing: {message}")

    # Step 2: Extract drill points
    document = result["document"]
    extractor = DrillPointExtractor()
    success, message, extract_result = extractor.extract(document)

    # Step 3: Display results
    print(f"Drill extraction: {message}")

    if success:
        drill_points = extract_result.get("drill_points", [])
        print(f"Found {len(drill_points)} drill points")

        # Print all drill points in a simple tabular format
        if drill_points:
            # Print header
            print("\nDrill Points Table:")
            print(f"{'#':<4} {'Position':<24} {'Spec Ø':<8} {'Geom Ø':<8} {'Diff %':<8} {'Layer'}")
            print("-" * 80)

            # Print each point as a row
            for i, point in enumerate(drill_points):
                pos = point.get("position", (0, 0, 0))
                pos_str = f"({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})"
                layer = point.get("layer", "")

                # Get diameter info (new format)
                diameter_geometry = point.get("diameter_geometry", 0)
                diameter_specification = point.get("diameter_specification", None)

                # Format diameter values
                spec_str = (
                    f"{diameter_specification:.2f}" if diameter_specification is not None else "N/A"
                )

                # Format the difference percentage
                mismatch = point.get("diameter_mismatch", None)
                diff_str = f"{mismatch['percent']:.1f}%" if mismatch else "N/A"

                # Highlight significant mismatches
                if mismatch and mismatch.get("is_significant", False):
                    diff_str = f"!{diff_str}!"

                print(
                    f"{i + 1:<4} {pos_str:<24} "
                    f"{spec_str:<8} "
                    f"{diameter_geometry:.2f}  "
                    f"{diff_str:<8} "
                    f"{layer}"
                )

            # Print total count
            print("-" * 80)
            print(f"Total drill points found: {len(drill_points)}")
        else:
            print("No drill points found.")
    else:
        print(f"Error: {message}")

    # Clean up
    os.unlink(test_file)
    print(f"\nTest file {test_file} has been removed")


if __name__ == "__main__":
    run_test()
