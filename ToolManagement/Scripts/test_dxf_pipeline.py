#!/usr/bin/env python3
"""
Test DXF pipeline to debug extrusion_vector issue
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from DXF.extractor import DXFExtractor
from DXF.parser import DXFParser
from ProcessingEngine.workpiece_rotator import WorkpieceRotator
from ProcessingEngine.machine_positioner import MachinePositioner
from ProcessingEngine.drill_point_grouper import DrillPointGrouper

def check_drill_points(points, stage):
    """Check if drill points have required fields"""
    print(f"\n--- {stage} ---")
    print(f"Number of points: {len(points)}")
    if points:
        first_point = points[0]
        print(f"Fields in first point: {list(first_point.keys())}")
        has_extrusion = 'extrusion_vector' in first_point
        has_direction = 'direction' in first_point
        print(f"Has extrusion_vector: {has_extrusion}")
        print(f"Has direction: {has_direction}")
        if has_extrusion:
            print(f"Extrusion vector: {first_point['extrusion_vector']}")
            # Show all unique extrusion vectors
            vectors = set()
            for p in points:
                if 'extrusion_vector' in p:
                    vectors.add(p['extrusion_vector'])
            print(f"Unique extrusion vectors: {sorted(vectors)}")

def main():
    dxf_file = "Tests/TestData/DXF/complex_case_8mm.dxf"
    
    print("Testing DXF Pipeline...")
    
    # Step 1: Parse
    parser = DXFParser()
    success, msg, parse_data = parser.parse(dxf_file)
    if not success:
        print(f"Parse failed: {msg}")
        return
    print("Parse SUCCESS")
    
    # Step 2: Extract
    extractor = DXFExtractor()
    success, msg, extract_data = extractor.process(parse_data["document"])
    if not success:
        print(f"Extract failed: {msg}")
        return
    print("Extract SUCCESS")
    check_drill_points(extract_data["drill_points"], "After Extraction")
    
    # Step 3: Rotate
    rotator = WorkpieceRotator()
    rotation_input = {
        "workpiece": extract_data["workpiece"],
        "drill_points": extract_data["drill_points"]
    }
    success, msg, rotate_data = rotator.transform_drilling_data(rotation_input)
    if not success:
        print(f"Rotate failed: {msg}")
        return
    print("Rotate SUCCESS")
    check_drill_points(rotate_data["drill_points"], "After Rotation")
    
    # Step 4: Position
    positioner = MachinePositioner()
    success, msg, position_data = positioner.position_for_top_left_machine(rotate_data)
    if not success:
        print(f"Position failed: {msg}")
        return
    print("Position SUCCESS")
    check_drill_points(position_data["drill_points"], "After Positioning")
    
    # Step 5: Group
    grouper = DrillPointGrouper()
    success, msg, group_data = grouper.group_drilling_points(position_data)
    if not success:
        print(f"Group failed: {msg}")
        return
    print("Group SUCCESS")
    check_drill_points(group_data["drill_points"], "After Grouping")

if __name__ == "__main__":
    main()