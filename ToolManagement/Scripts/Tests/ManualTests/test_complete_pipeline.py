#!/usr/bin/env python3
"""
Test script for the complete horizontal drilling transformation pipeline.

This script demonstrates the full pipeline from filtering to positioning:
1. Filter out vertical drilling points
2. Transform horizontal drilling points to machine coordinates
3. Rotate workpiece if needed (auto/manual)
4. Position workpiece at the desired location
"""

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from DXF.file_loader import DxfLoader
from DXF.drilling_extractor import DrillingExtractor
from DXF.drilling_analyzer import DrillPointAnalyzer, DrillPointClassifier
from DXF.horizontal_drill_transformer import HorizontalDrillTransformer
from DXF.workpiece_extractor import WorkpieceExtractor


def select_dxf_file():
    """Display a simple selection menu for DXF files."""
    # Set up path to test data
    test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")
    dxf_dir = os.path.join(test_data_dir, "DXF")
    
    print(f"Looking for DXF files in: {dxf_dir}")
    print("\nAvailable DXF files:")
    
    dxf_files = [f for f in os.listdir(dxf_dir) if f.lower().endswith('.dxf')]
    for i, file in enumerate(dxf_files):
        print(f"{i+1}. {file}")
    
    # Non-interactive selection - choose first file
    selected_index = 0
    selected_file = dxf_files[selected_index]
    print(f"\nSelected DXF file: {selected_file}")
    
    return os.path.join(dxf_dir, selected_file)


def calc_bounding_box(points):
    """Calculate bounding box of points."""
    if not points:
        return {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0, "width": 0, "height": 0}
    
    min_x = min(p.machine_position[0] for p in points if hasattr(p, 'machine_position'))
    max_x = max(p.machine_position[0] for p in points if hasattr(p, 'machine_position'))
    min_y = min(p.machine_position[1] for p in points if hasattr(p, 'machine_position'))
    max_y = max(p.machine_position[1] for p in points if hasattr(p, 'machine_position'))
    
    return {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "width": max_x - min_x,
        "height": max_y - min_y
    }


def test_full_pipeline():
    """Test the complete transformation pipeline with various options."""
    print("=== COMPLETE HORIZONTAL DRILLING TRANSFORMATION PIPELINE TEST ===")
    print("This test demonstrates the full pipeline from filtering to positioning")
    
    # Step 1: Select and load a DXF file
    dxf_file_path = select_dxf_file()
    
    # Create required objects
    loader = DxfLoader()
    extractor = DrillingExtractor()
    analyzer = DrillPointAnalyzer()
    classifier = DrillPointClassifier()
    workpiece_extractor = WorkpieceExtractor()
    
    print("\nStep 1: Loading DXF file...")
    success, message, details = loader.load_dxf(dxf_file_path)
    
    if not success:
        print(f"Error loading DXF: {message}")
        return
    
    print(f"SUCCESS: DXF loaded successfully")
    doc = details.get('document')
    
    # Step 2: Extract workpiece information
    print("\nStep 2: Extracting workpiece information...")
    success, message, workpiece_info = workpiece_extractor.extract_workpiece_info(doc)
    
    if not success:
        print(f"Error extracting workpiece info: {message}")
        return
    
    print(f"SUCCESS: Workpiece information extracted")
    print(f"  Dimensions: {workpiece_info['dimensions']['width']:.2f} x "
          f"{workpiece_info['dimensions']['height']:.2f} x "
          f"{workpiece_info['dimensions']['depth']:.2f}mm")
    
    # Step 3: Extract drilling points
    print("\nStep 3: Extracting drilling points...")
    success, message, drill_details = extractor.extract_all_drilling_info(doc)
    
    if not success:
        print(f"Error extracting drilling info: {message}")
        return
    
    drilling_points = drill_details.get('points', [])
    print(f"SUCCESS: Found {len(drilling_points)} drilling points")
    
    # Step 4: Classify drilling points
    print("\nStep 4: Classifying drilling points...")
    success, message, classification_details = classifier.classify_points(drilling_points)
    
    if not success:
        print(f"Error classifying drilling points: {message}")
        return
    
    print(f"SUCCESS: {message}")
    
    # Get points by edge
    points_by_edge = classifier.get_points_by_edge(drilling_points)
    
    # Print classification summary
    print("\n=== DRILLING POINT CLASSIFICATION ===")
    for edge, points in points_by_edge.items():
        print(f"  {edge}: {len(points)} points")
    
    # Run tests for different pipeline configurations
    pipeline_tests = [
        {
            "name": "Default - Transform + Rotate + Position to top-left",
            "rotation": True,
            "positioning": True,
            "target_position": "top-left"
        },
        {
            "name": "Transform only (no rotation, no positioning)",
            "rotation": False,
            "positioning": False,
            "target_position": None
        },
        {
            "name": "Transform + Manual rotation (90°) + Position to top-left",
            "rotation": False,  # No auto rotation
            "positioning": True,
            "target_position": "top-left",
            "manual_rotation": 1  # 90° rotation
        },
        {
            "name": "Transform + Position to bottom-right (placeholder)",
            "rotation": True,
            "positioning": True,
            "target_position": "bottom-right"
        }
    ]
    
    # Run each pipeline test
    for test in pipeline_tests:
        print(f"\n\n=== TEST: {test['name']} ===")
        
        # Create a new transformer for each test
        transformer = HorizontalDrillTransformer(
            auto_rotation_enabled=test["rotation"],
            target_position=test.get("target_position", "top-left")
        )
        
        # Configure transformer
        success, message, details = transformer.set_from_workpiece_info(workpiece_info)
        if not success:
            print(f"Error configuring transformer: {message}")
            continue
        
        print(f"Transformer configured with workpiece dimensions: "
              f"{details['width']:.1f} x {details['height']:.1f} x {details['thickness']:.1f}mm")
        
        # Run the transformation
        success, message, transform_details = transformer.transform_points(
            drilling_points,
            apply_rotation=test["rotation"],
            apply_positioning=test["positioning"]
        )
        
        if not success:
            print(f"Error in pipeline: {message}")
            continue
        
        print(f"SUCCESS: {message}")
        
        # If manual rotation specified, apply it
        if test.get("manual_rotation") and not test["rotation"]:
            horizontal_points = transform_details.get('transformed_points', [])
            print(f"Applying manual {test['manual_rotation'] * 90}° rotation...")
            
            success, message, rotation_details = transformer.apply_manual_rotation(
                horizontal_points, 
                rotations=test["manual_rotation"]
            )
            
            if not success:
                print(f"Error applying manual rotation: {message}")
                continue
                
            print(f"SUCCESS: {message}")
            
            # If positioning is needed after manual rotation
            if test["positioning"]:
                print(f"Positioning workpiece to {test.get('target_position', 'top-left')}...")
                
                success, message, pos_details = transformer.position_workpiece(
                    horizontal_points,
                    target_position=test.get('target_position')
                )
                
                if not success:
                    print(f"Error positioning workpiece: {message}")
                    continue
                    
                print(f"SUCCESS: {message}")
        
        # Get stats
        stats = transform_details.get('stats', {})
        
        # Print summary
        print("\n=== PIPELINE RESULTS ===")
        print(f"Total drilling points: {stats.get('total_points', 0)}")
        print(f"Horizontal drilling points: {stats.get('horizontal_points', 0)}")
        print(f"Vertical drilling points (skipped): {stats.get('vertical_points', 0)}")
        print(f"Successfully transformed: {stats.get('successfully_transformed', 0)}")
        
        # Rotation info
        if test["rotation"] or test.get("manual_rotation"):
            print(f"Rotation applied: {transform_details.get('rotation_applied', False)}")
            print(f"Rotation angle: {transform_details.get('rotation_angle', 0)}°")
        
        # Positioning info
        if test["positioning"]:
            print(f"Positioning applied: {transform_details.get('positioning_applied', False)}")
            
            if "stats" in transform_details and "positioning_offset" in stats:
                print(f"Positioning offset: {stats.get('positioning_offset', (0, 0))}")
            
            if "stats" in transform_details and "positioning_target" in stats:
                print(f"Target position: {stats.get('positioning_target', 'unknown')}")
        
        # Get the transformed and positioned points
        horizontal_points = transform_details.get('transformed_points', [])
        
        # Calculate and print the bounding box
        bbox = calc_bounding_box(horizontal_points)
        print(f"\nBounding box of final points:")
        print(f"  X range: {bbox['min_x']:.1f} to {bbox['max_x']:.1f} (width: {bbox['width']:.1f}mm)")
        print(f"  Y range: {bbox['min_y']:.1f} to {bbox['max_y']:.1f} (height: {bbox['height']:.1f}mm)")
    
    print("\n=== All pipeline tests completed successfully ===")


if __name__ == "__main__":
    try:
        test_full_pipeline()
    except Exception as e:
        print(f"Error running test: {str(e)}")
        import traceback
        traceback.print_exc()