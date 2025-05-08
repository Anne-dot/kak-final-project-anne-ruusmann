#!/usr/bin/env python3
"""
Interactive test for drilling point extraction and analysis.

This test script:
1. Allows selection of a DXF file using terminal UI
2. Extracts drilling points based on named layers
3. Analyzes drilling points by direction (edge)
4. Groups points by tool compatibility
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import modules
from DXF.file_loader import DxfLoader
from DXF.workpiece_extractor import WorkpieceExtractor
from DXF.drilling_extractor import DrillingExtractor
from DXF.drilling_analyzer import DrillPointAnalyzer, DrillPointClassifier
from Utils.ui_utils import UIUtils
from Utils.logging_utils import setup_logger

# Set up logger
logger = setup_logger(__name__)

# Set up path to test data
test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")
dxf_dir = os.path.join(test_data_dir, "DXF")

def display_drilling_points_summary(drilling_info):
    """Display summary of extracted drilling points."""
    UIUtils.print_separator("DRILLING POINTS SUMMARY")
    
    points = drilling_info.get('points', [])
    count = len(points)
    
    print(f"\n[DRILLING POINTS] Found {count} drilling points")
    
    # Group points by layer for display
    layers = {}
    for point in points:
        layer = point.layer_name
        if layer not in layers:
            layers[layer] = []
        layers[layer].append(point)
    
    # Display layer breakdown
    print("\n[LAYER BREAKDOWN]")
    for layer, layer_points in layers.items():
        print(f"  {layer}: {len(layer_points)} points")
    
    # Display ALL points
    print("\n[ALL DRILLING POINTS]")
    for i, point in enumerate(points):
        print(f"  Point {i+1}:")
        print(f"    Position: ({point.position[0]:.2f}, {point.position[1]:.2f}, {point.position[2]:.2f})")
        print(f"    Layer: {point.layer_name}")
        print(f"    Diameter: {point.diameter:.2f}mm")
        print(f"    Depth: {point.depth:.2f}mm")
        if point.extrusion_vector:
            x, y, z = point.extrusion_vector
            print(f"    Extrusion Vector: ({x:.2f}, {y:.2f}, {z:.2f})")
        else:
            print("    Extrusion Vector: None")

def display_analysis_results(analysis_details):
    """Display drilling point analysis results."""
    UIUtils.print_separator("DRILLING ANALYSIS RESULTS")
    
    # Get statistics
    stats = analysis_details.get('statistics', {})
    edge_details = analysis_details.get('edge_details', {})
    
    print("\n[OVERALL STATISTICS]")
    print(f"  Total Points: {stats.get('total_points', 0)}")
    print(f"  Total Tool Groups: {stats.get('total_groups', 0)}")
    print(f"  Vertical Groups: {stats.get('vertical_groups', 0)}")
    print(f"  Horizontal Groups: {stats.get('horizontal_groups', 0)}")
    
    # Display edge counts
    print("\n[POINTS BY EDGE]")
    edge_counts = stats.get('edge_counts', {})
    for edge, count in edge_counts.items():
        if count > 0:
            print(f"  {edge}: {count} points")
    
    # Display detailed edge information
    if edge_details:
        print("\n[EDGE DETAILS]")
        for edge, details in edge_details.items():
            group_count = details.get('group_count', 0)
            point_count = details.get('point_count', 0)
            diameters = details.get('diameters', [])
            
            print(f"  {edge}:")
            print(f"    Groups: {group_count}")
            print(f"    Points: {point_count}")
            print(f"    Diameters: {', '.join(f'{d:.1f}mm' for d in diameters)}")

def display_classification_results(classification_details):
    """Display drilling point classification results."""
    UIUtils.print_separator("DRILLING CLASSIFICATION RESULTS")
    
    # Get classification statistics
    stats = classification_details.get('stats', {})
    
    print("\n[CLASSIFICATION SUMMARY]")
    print(f"  Vertical Points: {stats.get('vertical_count', 0)}")
    print(f"  Horizontal Points: {stats.get('horizontal_count', 0)}")
    print(f"  Unknown Points: {stats.get('unknown_count', 0)}")
    
    # Get points by edge
    points = classification_details.get('points', [])
    classifier = DrillPointClassifier()
    points_by_edge = classifier.get_points_by_edge(points)
    
    # Display points by edge
    print("\n[POINTS BY EDGE]")
    for edge, edge_points in points_by_edge.items():
        if edge_points:
            print(f"\n  {edge} EDGE: {len(edge_points)} points")
            
            # Group by diameter for this edge
            diameters = {}
            for point in edge_points:
                diameter = round(point.diameter, 1)
                if diameter not in diameters:
                    diameters[diameter] = []
                diameters[diameter].append(point)
            
            # Display diameter groups
            for diameter, diameter_points in diameters.items():
                print(f"    Diameter {diameter:.1f}mm: {len(diameter_points)} points")
                
                # Show ALL points
                for i, point in enumerate(diameter_points):
                    x, y, z = point.position
                    print(f"      Point {i+1}: ({x:.1f}, {y:.1f}, {z:.1f})")

def main():
    """Run the interactive drilling point extraction and analysis test."""
    print("=== Drilling Point Extraction and Analysis Test ===")
    print("This test extracts and analyzes drilling points from a DXF file\n")
    
    # Initialize objects
    loader = DxfLoader()
    extractor = DrillingExtractor()
    analyzer = DrillPointAnalyzer()
    classifier = DrillPointClassifier()
    
    # Let user select a DXF file
    print(f"Looking for DXF files in: {dxf_dir}")
    dxf_file_path = UIUtils.select_dxf_file(dxf_dir)
    if not dxf_file_path:
        print("No DXF file selected. Exiting.")
        UIUtils.keep_terminal_open("Test aborted - no file selected.")
        sys.exit(1)
    
    print(f"\nSelected DXF file: {os.path.basename(dxf_file_path)}")
    
    # Step 1: Load the DXF file
    print("\nStep 1: Loading DXF file...")
    success, message, details = loader.load_dxf(dxf_file_path)
    
    if not success:
        print(f"Error loading DXF: {message}")
        UIUtils.keep_terminal_open("Test failed at DXF loading stage.")
        sys.exit(1)
    
    print(f"SUCCESS: DXF loaded successfully")
    dxf_doc = details.get('document')
    
    # Step 2: Extract drilling information
    print("\nStep 2: Extracting drilling points...")
    success, message, drilling_info = extractor.extract_all_drilling_info(dxf_doc)
    
    if not success:
        print(f"Error extracting drilling info: {message}")
        UIUtils.keep_terminal_open("Test failed at drilling extraction stage.")
        sys.exit(1)
    
    print(f"SUCCESS: {message}")
    
    # Display drilling points summary
    display_drilling_points_summary(drilling_info)
    
    # Skip analysis if no drilling points found
    drill_points = drilling_info.get('points', [])
    if not drill_points:
        print("\nNo drilling points found to analyze.")
        UIUtils.keep_terminal_open("Test completed with no drilling points to analyze.")
        sys.exit(0)
    
    # Step 3: Analyze drilling points
    print("\nStep 3: Analyzing drilling points...")
    success, message, analysis_details = analyzer.analyze_drilling_data(drill_points)
    
    if not success:
        print(f"Error analyzing drilling points: {message}")
        UIUtils.keep_terminal_open("Test failed at drilling analysis stage.")
        sys.exit(1)
    
    print(f"SUCCESS: {message}")
    
    # Display analysis results
    display_analysis_results(analysis_details)
    
    # Step 4: Classify drilling points
    print("\nStep 4: Classifying drilling points...")
    success, message, classification_details = classifier.classify_points(drill_points)
    
    if not success:
        print(f"Error classifying drilling points: {message}")
        UIUtils.keep_terminal_open("Test failed at drilling classification stage.")
        sys.exit(1)
    
    print(f"SUCCESS: {message}")
    
    # Display classification results
    display_classification_results(classification_details)
    
    # Keep the terminal open until user presses Enter
    UIUtils.keep_terminal_open("Drilling extraction and analysis test completed successfully.")

if __name__ == "__main__":
    main()