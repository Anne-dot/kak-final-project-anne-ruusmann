#!/usr/bin/env python3
"""
DXF to G-code CLI - Simple command line version for testing

Usage:
    python3 dxf_to_gcode_cli.py [dxf_file] [output_file]
    
If no arguments provided, will prompt for input.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all required modules
from DXF.extractor import DXFExtractor
from DXF.parser import DXFParser
from GCodeGenerator.gcode_program_generator import GCodeProgramGenerator
from ProcessingEngine.drill_point_grouper import DrillPointGrouper
from ProcessingEngine.machine_positioner import MachinePositioner
from ProcessingEngine.workpiece_rotator import WorkpieceRotator
from ProcessingEngine.drill_point_filter import DrillPointFilter
from GCodeProcessor.preprocessor import GCodePreprocessor
from Utils.logging_utils import setup_logger


def process_dxf_to_gcode(dxf_file: str, output_file: str) -> bool:
    """Process DXF file through complete pipeline."""
    print(f"\n{'='*60}")
    print(f"DXF to G-code Conversion")
    print(f"{'='*60}\n")
    
    try:
        # Step 1: Parse DXF
        print("Step 1/8: Parsing DXF file...")
        parser = DXFParser()
        success, message, parse_data = parser.parse(dxf_file)
        if not success:
            print(f"ERROR: {message}")
            return False
        print("SUCCESS")
        
        # Step 2: Extract drilling data
        print("\nStep 2/8: Extracting drilling information...")
        extractor = DXFExtractor()
        success, message, extract_data = extractor.process(parse_data["document"])
        if not success:
            print(f"ERROR: {message}")
            return False
        print(f"SUCCESS - Found {len(extract_data['drill_points'])} drill points")
        
        # Step 3: Rotate workpiece
        print("\nStep 3/8: Processing workpiece orientation...")
        rotator = WorkpieceRotator()
        # Combine workpiece and drill points for the rotator
        rotation_input = {
            "workpiece": extract_data["workpiece"],
            "drill_points": extract_data["drill_points"]
        }
        success, message, rotate_data = rotator.transform_drilling_data(rotation_input)
        if not success:
            print(f"ERROR: {message}")
            return False
        print("SUCCESS")
        
        # Step 4: Position for machine
        print("\nStep 4/8: Calculating machine positions...")
        positioner = MachinePositioner()
        success, message, position_data = positioner.position_for_top_left_machine(rotate_data)
        if not success:
            print(f"ERROR: {message}")
            return False
            
        # Step 5: Filter for horizontal drilling (MVP)
        print("\nStep 5/8: Filtering for horizontal drilling...")
        filter = DrillPointFilter()
        success, message, filter_data = filter.filter_for_horizontal_drilling(position_data)
        if not success:
            print(f"ERROR: {message}")
            return False
        
        # Show filtering statistics
        stats = filter_data.get("filtering_stats", {})
        if stats.get("vertical_removed"):
            print(f"Filtered out {stats['vertical_count']} vertical drilling points")
        print(f"Processing {stats.get('horizontal_count', 0)} horizontal drilling points")
        print("SUCCESS")
            
        # Step 6: Group drill points
        print("\nStep 6/8: Grouping drill points by tool requirements...")
        grouper = DrillPointGrouper()
        success, message, group_data = grouper.group_drilling_points(filter_data)
        if not success:
            print(f"ERROR: {message}")
            return False
        print("SUCCESS")
        
        # Step 7: Generate G-code
        print("\nStep 7/8: Generating G-code program...")
        generator_input = {
            "workpiece": filter_data["workpiece"],
            "drill_points": filter_data["drill_points"],
            "grouped_points": group_data["grouped_points"]
        }
        generator = GCodeProgramGenerator()
        success, message, gen_data = generator.generate_program(generator_input)
        if not success:
            print(f"ERROR: {message}")
            return False
        print("SUCCESS")
        
        # Step 8: Add line numbers
        print("\nStep 8/8: Adding line numbers...")
        gcode_lines = gen_data.get("gcode_lines", [])
        gcode_content = '\n'.join(gcode_lines)
        
        # Use preprocessor to add line numbers
        preprocessor = GCodePreprocessor()
        final_gcode = preprocessor.add_line_numbers(gcode_content)
        print("SUCCESS")
        
        # Save to file
        with open(output_file, "w") as f:
            f.write(final_gcode)
        
        print(f"\n{'='*60}")
        print(f"SUCCESS! G-code saved to: {output_file}")
        print(f"Total lines: {final_gcode.count(chr(10)) + 1}")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return False


def main():
    """Main entry point."""
    # Set up logging
    logger = setup_logger("dxf_to_gcode_cli")
    
    # Get file paths
    if len(sys.argv) >= 2:
        dxf_file = sys.argv[1]
    else:
        # List available test files
        test_dir = Path(__file__).parent / "Tests" / "TestData" / "DXF"
        if test_dir.exists():
            dxf_files = list(test_dir.glob("*.dxf"))
            if dxf_files:
                print("\nAvailable test DXF files:")
                for i, f in enumerate(dxf_files):
                    print(f"{i+1}. {f.name}")
                choice = input("\nEnter number or full path to DXF file: ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(dxf_files):
                    dxf_file = str(dxf_files[int(choice)-1])
                else:
                    dxf_file = choice
            else:
                dxf_file = input("Enter path to DXF file: ").strip()
        else:
            dxf_file = input("Enter path to DXF file: ").strip()
    
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # Auto-generate output filename
        base_name = Path(dxf_file).stem
        output_file = str(Path(dxf_file).parent / f"{base_name}_gcode.txt")
        use_default = input(f"Output file [{output_file}]: ").strip()
        if use_default:
            output_file = use_default
    
    # Process the file
    if process_dxf_to_gcode(dxf_file, output_file):
        print("Conversion completed successfully!")
    else:
        print("Conversion failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()