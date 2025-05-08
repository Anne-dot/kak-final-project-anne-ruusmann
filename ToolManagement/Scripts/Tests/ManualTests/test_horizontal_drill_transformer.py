"""
Test script for the horizontal drilling point transformation pipeline.

This script tests the new HorizontalDrillTransformer implementation, which:
1. Filters out vertical drilling points
2. Transforms horizontal drilling points to machine coordinates
3. Demonstrates workpiece rotation capabilities (automatic and manual)
"""

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from DXF.file_loader import DxfLoader
from DXF.drilling_extractor import DrillingExtractor
from DXF.drilling_analyzer import DrillPointAnalyzer, DrillPointClassifier
from DXF.horizontal_drill_transformer import HorizontalDrillTransformer
from DXF.workpiece_extractor import WorkpieceExtractor


def select_dxf_file(auto_select_index=0):
    """Display a simple selection menu for DXF files."""
    # Set up path to test data
    test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")
    dxf_dir = os.path.join(test_data_dir, "DXF")
    
    print(f"Looking for DXF files in: {dxf_dir}")
    print("\nAvailable DXF files:")
    
    dxf_files = [f for f in os.listdir(dxf_dir) if f.lower().endswith('.dxf')]
    for i, file in enumerate(dxf_files):
        print(f"{i+1}. {file}")
    
    # Non-interactive mode (for automated testing)
    selected_index = auto_select_index
    if selected_index < 0 or selected_index >= len(dxf_files):
        selected_index = 0  # Default to first file
    
    selected_file = dxf_files[selected_index]
    print(f"\nSelected DXF file: {selected_file}")
    
    return os.path.join(dxf_dir, selected_file)


def main(auto_select_index=0, manual_rotation=0):
    """Main test function."""
    print("=== Horizontal Drilling Point Transformation Test ===")
    print("This test demonstrates the new horizontal drilling point transformation pipeline\n")
    
    # Step 1: Select and load a DXF file
    dxf_file_path = select_dxf_file(auto_select_index)
    
    # Create required objects
    loader = DxfLoader()
    extractor = DrillingExtractor()
    analyzer = DrillPointAnalyzer()
    classifier = DrillPointClassifier()
    workpiece_extractor = WorkpieceExtractor()
    transformer = HorizontalDrillTransformer()
    
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
    
    # Step 5: Configure and run the transformer
    print("\nStep 5: Configuring horizontal drill transformer...")
    
    # Configure the transformer with workpiece info
    success, message, details = transformer.set_from_workpiece_info(workpiece_info)
    
    if not success:
        print(f"Error configuring transformer: {message}")
        return
    
    print(f"SUCCESS: Transformer configured with workpiece info")
    print(f"  Workpiece dimensions: {details['width']:.1f} x {details['height']:.1f} x {details['thickness']:.1f}mm")
    print(f"  Boundaries: X=({details['boundaries']['min_x']:.1f}, {details['boundaries']['max_x']:.1f}), "
          f"Y=({details['boundaries']['min_y']:.1f}, {details['boundaries']['max_y']:.1f})")
    
    # Step 6: Transform drilling points
    print("\nStep 6: Transforming drilling points...")
    success, message, transform_details = transformer.transform_points(drilling_points)
    
    if not success:
        print(f"Error transforming drilling points: {message}")
        return
    
    print(f"SUCCESS: {message}")
    
    # Print transformation results
    horizontal_points = transform_details.get('transformed_points', [])
    vertical_points = transform_details.get('vertical_points', [])
    error_points = transform_details.get('error_points', [])
    stats = transform_details.get('stats', {})
    
    # Summary
    print("\n=== TRANSFORMATION RESULTS ===")
    print(f"Total drilling points: {stats.get('total_points', 0)}")
    print(f"Horizontal drilling points: {stats.get('horizontal_points', 0)}")
    print(f"Vertical drilling points (skipped): {stats.get('vertical_points', 0)}")
    print(f"Successfully transformed: {stats.get('successfully_transformed', 0)}")
    print(f"Transformation errors: {stats.get('errors', 0)}")
    
    # By edge
    print("\nResults by edge:")
    by_edge = stats.get('by_edge', {})
    for edge, edge_stats in by_edge.items():
        print(f"  {edge}: {edge_stats.get('total', 0)} points, "
              f"{edge_stats.get('transformed', 0)} transformed")
    
    # Step 7: Display transformed points
    print("\n=== DRILLING POINTS BEFORE AND AFTER TRANSFORMATION ===")
    
    # Group points by edge for clean display
    edge_groups = {}
    for point in horizontal_points:
        edge = getattr(point, 'edge', 'UNKNOWN')
        if edge not in edge_groups:
            edge_groups[edge] = []
        edge_groups[edge].append(point)
    
    # Print each edge group
    for edge, points in edge_groups.items():
        print(f"\n{edge} EDGE DRILLING POINTS ({len(points)} points):")
        
        for i, point in enumerate(points):
            # Get transformation details
            result = getattr(point, 'transformation_result', {})
            original = result.get('original_position', (-1, -1, -1))
            transformed = result.get('transformed_position', (-1, -1, -1))
            
            # Print point info
            print(f"  Point {i+1}:")
            print(f"    Original DXF: ({original[0]:.1f}, {original[1]:.1f}, {original[2]:.1f})")
            print(f"    Machine: ({transformed[0]:.1f}, {transformed[1]:.1f}, {transformed[2]:.1f})")
    
    # Print vertical points (skipped)
    if vertical_points:
        print(f"\nVERTICAL DRILLING POINTS (SKIPPED) ({len(vertical_points)} points):")
        for i, point in enumerate(vertical_points[:5]):  # Show just first 5
            position = getattr(point, 'position', (-1, -1, -1))
            print(f"  Point {i+1}: ({position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f})")
        
        if len(vertical_points) > 5:
            print(f"  ... and {len(vertical_points) - 5} more")
    
    # Print error points if any
    if error_points:
        print(f"\nPOINTS WITH TRANSFORMATION ERRORS ({len(error_points)} points):")
        for i, point in enumerate(error_points):
            position = getattr(point, 'position', (-1, -1, -1))
            error = getattr(point, 'transformation_error', 'Unknown error')
            print(f"  Point {i+1}: ({position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f})")
            print(f"    Error: {error}")
    
    # Add enumerated list of machine coordinates grouped by edge and diameter
    print("\n=== MACHINE COORDINATES BY EDGE AND DIAMETER ===")
    
    # Organize horizontal points by edge and diameter
    edge_diameter_points = {}
    for point in horizontal_points:
        edge = getattr(point, 'edge', 'UNKNOWN')
        diameter = getattr(point, 'diameter', 0.0)
        
        # Create key for grouping
        key = f"{edge}_{diameter:.1f}"
        if key not in edge_diameter_points:
            edge_diameter_points[key] = []
            
        edge_diameter_points[key].append(point)
    
    # Print each group
    for key, points in sorted(edge_diameter_points.items()):
        edge, diameter = key.split('_')
        print(f"\n{edge} EDGE - {diameter}mm DIAMETER: ({len(points)} points)")
        
        # Sort the points based on edge type
        sorted_points = []
        if edge in ["LEFT", "RIGHT"]:
            # Sort by Y coordinate for LEFT and RIGHT edges (ascending)
            sorted_points = sorted(points, key=lambda p: p.machine_position[1] if hasattr(p, 'machine_position') else 0)
        elif edge in ["FRONT", "BACK"]:
            # Sort by X coordinate for FRONT and BACK edges (ascending)
            sorted_points = sorted(points, key=lambda p: p.machine_position[0] if hasattr(p, 'machine_position') else 0)
        else:
            # Default sorting if edge is unknown
            sorted_points = points
        
        # Print enumerated coordinates
        for i, point in enumerate(sorted_points):
            if hasattr(point, 'machine_position') and point.machine_position:
                x, y, z = point.machine_position
                print(f"  {i+1}: ({x:.1f}, {y:.1f}, {z:.1f})")
    
    # Step 8: Test manual rotation capabilities
    print("\n=== STEP 8: TESTING MANUAL ROTATION CAPABILITIES ===")
    print("This step demonstrates manual rotation of already transformed points.")
    
    print("\nCurrent workpiece dimensions:")
    print(f"  Width: {transformer.width:.1f}mm")
    print(f"  Height: {transformer.height:.1f}mm")
    print(f"  Thickness: {transformer.thickness:.1f}mm")
    
    # Set manual rotation value from parameter (for non-interactive mode)
    rotation_count = manual_rotation
    print(f"\nUsing manual rotation: {rotation_count * 90}° rotation")
    
    # Apply manual rotation if requested
    if rotation_count > 0:
        print(f"\nApplying {rotation_count * 90}° manual rotation...")
        
        # Make a copy of the transformed points for rotation
        success, message, rotation_details = transformer.apply_manual_rotation(horizontal_points, rotation_count)
        
        if not success:
            print(f"Error applying manual rotation: {message}")
        else:
            print(f"SUCCESS: {message}")
            print("\nRotated workpiece dimensions:")
            print(f"  Width: {rotation_details['dimensions']['width']:.1f}mm")
            print(f"  Height: {rotation_details['dimensions']['height']:.1f}mm")
            
            # Print the rotated coordinates
            print("\n=== ROTATED MACHINE COORDINATES BY EDGE AND DIAMETER ===")
            
            # Reorganize points by edge and diameter after rotation
            edge_diameter_points = {}
            for point in horizontal_points:
                edge = getattr(point, 'edge', 'UNKNOWN')
                diameter = getattr(point, 'diameter', 0.0)
                
                # Create key for grouping
                key = f"{edge}_{diameter:.1f}"
                if key not in edge_diameter_points:
                    edge_diameter_points[key] = []
                    
                edge_diameter_points[key].append(point)
            
            # Print each group
            for key, points in sorted(edge_diameter_points.items()):
                edge, diameter = key.split('_')
                print(f"\n{edge} EDGE - {diameter}mm DIAMETER: ({len(points)} points)")
                
                # Sort the points based on edge type
                sorted_points = []
                if edge in ["LEFT", "RIGHT"]:
                    # Sort by Y coordinate for LEFT and RIGHT edges (ascending)
                    sorted_points = sorted(points, key=lambda p: p.machine_position[1] if hasattr(p, 'machine_position') else 0)
                elif edge in ["FRONT", "BACK"]:
                    # Sort by X coordinate for FRONT and BACK edges (ascending)
                    sorted_points = sorted(points, key=lambda p: p.machine_position[0] if hasattr(p, 'machine_position') else 0)
                else:
                    # Default sorting if edge is unknown
                    sorted_points = points
                
                # Print enumerated coordinates
                for i, point in enumerate(sorted_points):
                    if hasattr(point, 'machine_position') and point.machine_position:
                        x, y, z = point.machine_position
                        print(f"  {i+1}: ({x:.1f}, {y:.1f}, {z:.1f})")
    
    # Step 9: Test automatic rotation with a tall workpiece
    print("\n=== STEP 9: TESTING AUTOMATIC ROTATION FOR TALL WORKPIECE ===")
    print("This step simulates a tall workpiece that exceeds 800mm in height.")
    
    # Create a test workpiece with height > 800mm
    print("\nCreating test workpiece with height > 800mm")
    tall_workpiece_info = {
        'dimensions': {
            'width': 500.0,
            'height': 950.0,  # Height exceeds 800mm threshold
            'depth': 20.0
        }
    }
    
    # Configure transformer with tall workpiece
    transformer_tall = HorizontalDrillTransformer()
    
    # Force auto rotation to be enabled
    transformer_tall.auto_rotation_enabled = True
    
    # Set parameters
    success, message, details = transformer_tall.set_from_workpiece_info(tall_workpiece_info)
    
    if not success:
        print(f"Error configuring transformer: {message}")
    else:
        print(f"SUCCESS: Transformer configured with tall workpiece")
        print(f"  Workpiece dimensions: {details['width']:.1f} x {details['height']:.1f} x {details['thickness']:.1f}mm")
        
        print("\nTransforming drilling points with auto rotation...")
        # Use the same drilling points we already processed
        success, message, transform_details = transformer_tall.transform_points(drilling_points)
        
        if not success:
            print(f"Error transforming points: {message}")
        else:
            print(f"SUCCESS: {message}")
            
            # Display the rotator state directly
            rotator_state = transformer_tall.rotator.get_current_dimensions()
            rotation_angle = rotator_state.get('rotation_angle', 0)
            
            if rotation_angle > 0:
                print(f"\nAutomatic rotation applied: {rotation_angle}°")
                print(f"  Original dimensions: {tall_workpiece_info['dimensions']['width']:.1f} x {tall_workpiece_info['dimensions']['height']:.1f}mm")
                print(f"  After rotation: {rotator_state['width']:.1f} x {rotator_state['height']:.1f}mm")
                
                # Show the rotation stats from the transform details
                stats = transform_details.get('stats', {})
                print("\nRotation statistics:")
                print(f"  Rotation applied: {stats.get('rotation_applied', False)}")
                print(f"  Rotation angle: {stats.get('rotation_angle', 0)}°")
            else:
                print("\nNo automatic rotation was applied.")
                print("  This could be because:")
                print("  1. Auto-rotation is disabled")
                print("  2. Height threshold isn't being triggered")
                print("  3. Rotation isn't being applied correctly")
                
                # Print workpiece rotator state for debugging
                print("\nWorkpiece rotator state:")
                print(f"  Auto-rotation enabled: {transformer_tall.auto_rotation_enabled}")
                print(f"  Height threshold: {transformer_tall.rotator.max_height_threshold}mm")
                print(f"  Current height: {transformer_tall.height}mm")
                print(f"  Auto-rotation needed: {transformer_tall.rotator.check_auto_rotation_needed()}")
            
            horizontal_points_tall = transform_details.get('transformed_points', [])
            print(f"\nSuccessfully transformed {len(horizontal_points_tall)} horizontal drilling points")
    
    print("\n=== Test completed successfully ===")


if __name__ == "__main__":
    try:
        # Default parameters for non-interactive run
        # auto_select_index=0: Use first DXF file
        # manual_rotation=1: Apply 90° rotation
        main(auto_select_index=0, manual_rotation=1)
    except Exception as e:
        print(f"Error running test: {str(e)}")
        import traceback
        traceback.print_exc()