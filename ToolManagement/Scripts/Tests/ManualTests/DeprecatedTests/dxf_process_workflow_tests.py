"""
Complete workflow test script demonstrating the DXF processing pipeline.

This script shows the full workflow:
1. Load a DXF file
2. Extract workpiece information
3. Extract drilling points
4. Analyze and classify drilling points
5. Transform coordinates

Usage:
    python dxf_process_workflow_tests.py
"""

import os
import sys
import platform

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import project modules
from DXF.file_loader import DxfLoader
from DXF.workpiece_extractor import WorkpieceExtractor
from DXF.drilling_extractor import DrillingExtractor
from DXF.drilling_analyzer import DrillPointAnalyzer, DrillPointClassifier
from DXF.coordinate_transformer import CoordinateTransformer
from Utils.ui_utils import UIUtils
from Utils.logging_utils import setup_logger

# Set up logger
logger = setup_logger(__name__)

# Set up path to test data
test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")
dxf_dir = os.path.join(test_data_dir, "DXF")


class WorkflowDisplay:
    """Handles display of workpiece and drilling information."""
    
    @staticmethod
    def format_point(point):
        """Format coordinate point for display."""
        return f"({point[0]:.1f}, {point[1]:.1f})"
    
    @staticmethod
    def format_point_3d(point):
        """Format 3D coordinate point for display."""
        return f"({point[0]:.1f}, {point[1]:.1f}, {point[2]:.1f})"
    
    @staticmethod
    def display_workpiece_info(workpiece_info):
        """Display extracted workpiece information."""
        dimensions = workpiece_info.get('dimensions', {})
        orientation = workpiece_info.get('orientation', {})
        reference_points = workpiece_info.get('reference_points', {})
        
        print("\n=== Workpiece Information ===")
        print(f"Width: {dimensions.get('width', 0):.1f}mm")
        print(f"Height: {dimensions.get('height', 0):.1f}mm")
        print(f"Thickness: {dimensions.get('depth', 0):.1f}mm")
        print(f"Origin Aligned: {orientation.get('origin_aligned', False)}")
        print(f"Axis Aligned: {orientation.get('axis_aligned', False)}")
        
        print("\n=== Reference Points ===")
        print(f"Corner BL: {WorkflowDisplay.format_point(reference_points.get('corner_bl', (0, 0)))}")
        print(f"Corner BR: {WorkflowDisplay.format_point(reference_points.get('corner_br', (0, 0)))}")
        print(f"Corner TR: {WorkflowDisplay.format_point(reference_points.get('corner_tr', (0, 0)))}")
        print(f"Corner TL: {WorkflowDisplay.format_point(reference_points.get('corner_tl', (0, 0)))}")
        print(f"Center: {WorkflowDisplay.format_point(reference_points.get('center', (0, 0)))}")
    
    @staticmethod
    def display_corners(rotator, title="Current Corner Points"):
        """Display corner points in a readable format."""
        success, corners, details = rotator.get_current_corners()
        if not success:
            print(f"Error: {details.get('error', 'Could not get corner points')}")
            return
            
        rotation_angle = details.get('rotation_angle', 0)
        orientation = details.get('orientation', 'Unknown')
        
        success, dimensions, _ = rotator.calculate_dimensions()
        if success:
            width, height = dimensions
        else:
            width, height = 0, 0
        
        print(f"\n=== {title} (Rotation: {rotation_angle}°) ===")
        print(f"Workpiece orientation: {orientation}")
        print(f"Corner A: {WorkflowDisplay.format_point(corners.get('corner_point_a', (0, 0)))}")
        print(f"Corner B: {WorkflowDisplay.format_point(corners.get('corner_point_b', (0, 0)))}")
        print(f"Corner C: {WorkflowDisplay.format_point(corners.get('corner_point_c', (0, 0)))}")
        print(f"Corner D: {WorkflowDisplay.format_point(corners.get('corner_point_d', (0, 0)))}")
        print(f"Current dimensions: {width:.1f} x {height:.1f}")
    
    @staticmethod
    def display_drilling_points(drilling_points, title="Drilling Points"):
        """Display drilling points in a readable format."""
        print(f"\n=== {title} ===")
        if not drilling_points:
            print("No drilling points available")
            return
            
        for i, drill in enumerate(drilling_points):  # Show all points
            coords = drill.position
            drill_type = getattr(drill, 'drill_type', None)
            edge = getattr(drill, 'edge', None)
            
            print(f"Drill {i+1}: {WorkflowDisplay.format_point_3d(coords)} "
                  f"(Ø{drill.diameter:.1f}mm, depth:{drill.depth:.1f}mm, "
                  f"Type:{drill_type or 'unknown'}, Edge:{edge or 'unknown'})")
    
    @staticmethod
    def display_transformed_points(points, title="Transformed Points"):
        """Display transformed drilling points."""
        print(f"\n=== {title} ===")
        if not points:
            print("No points available")
            return
            
        transformed_count = 0
        for i, point in enumerate(points):  # Show all points
            # Get original and machine positions
            orig_pos = point.position
            mach_pos = getattr(point, 'machine_position', None)
            edge = getattr(point, 'edge', 'Unknown')
            
            if mach_pos:
                transformed_count += 1
                orig_str = WorkflowDisplay.format_point_3d(orig_pos)
                mach_str = WorkflowDisplay.format_point_3d(mach_pos)
                print(f"Point {i+1}: {orig_str} → {mach_str} (Edge: {edge})")
            else:
                print(f"Point {i+1}: {WorkflowDisplay.format_point_3d(orig_pos)} (Not transformed)")
                
        print(f"\nTotal transformed points: {transformed_count} of {len(points)}")


class DxfWorkflowTester:
    """Main class to run the DXF workflow test."""
    
    def __init__(self):
        """Initialize the workflow tester."""
        # Create instances of all needed components
        self.loader = DxfLoader()
        self.workpiece_extractor = WorkpieceExtractor()
        self.drilling_extractor = DrillingExtractor()
        self.analyzer = DrillPointAnalyzer()
        self.classifier = DrillPointClassifier()
        self.transformer = CoordinateTransformer()
        
        # State variables
        self.dxf_doc = None
        self.workpiece_info = None
        self.drilling_points = []
        self.current_drilling_points = []
        
        logger.info("DxfWorkflowTester initialized")
    
    def run_workflow(self, dxf_file_path=None):
        """
        Run the complete workflow test.
        
        Args:
            dxf_file_path: Optional path to DXF file. If None, user will be prompted to select one.
        """
        print(f"\n=== DXF Processing Workflow Test ===")
        print(f"Running on {platform.system()} platform")
        
        # Step 1: Load DXF File
        if not self._load_dxf_file(dxf_file_path):
            return
        
        # Step 2: Extract Workpiece Information
        if not self._extract_workpiece_info():
            return
        
        # Step 3: Extract Drilling Points
        self._extract_drilling_points()
        
        # Step 4: Analyze and Classify Drilling Points
        if not self._analyze_and_classify_drilling_points():
            return
        
        # Step 5: Run Interactive Transformation
        self._run_interactive_transformation()
        
        print("\nWorkflow test completed successfully!")
    
    def _load_dxf_file(self, dxf_file_path):
        """Load the DXF file."""
        print("\n--- STEP 1: LOADING DXF FILE ---")
        
        # Let user select a DXF file if not provided
        if dxf_file_path is None:
            dxf_file_path = UIUtils.select_dxf_file(dxf_dir)
            if not dxf_file_path:
                print("No DXF file selected. Exiting.")
                return False
        
        print(f"Using DXF file: {os.path.basename(dxf_file_path)}")
        
        # Load DXF file
        success, doc, message = self.loader.load_dxf(dxf_file_path)
        if not success:
            print(f"Error loading DXF: {message}")
            return False
        
        self.dxf_doc = doc
        print(f"DXF file loaded successfully: {message}")
        return True
    
    def _extract_workpiece_info(self):
        """Extract workpiece information from DXF."""
        print("\n--- STEP 2: EXTRACTING WORKPIECE INFORMATION ---")
        
        success, workpiece_info, message = self.workpiece_extractor.extract_workpiece_info(self.dxf_doc)
        if not success:
            print(f"Error extracting workpiece info: {message}")
            return False
        
        self.workpiece_info = workpiece_info
        print(f"Workpiece information extracted: {message}")
        
        # Display workpiece information
        WorkflowDisplay.display_workpiece_info(self.workpiece_info)
        return True
    
    def _extract_drilling_points(self):
        """Extract drilling points from DXF."""
        print("\n--- STEP 3: EXTRACTING DRILLING POINTS ---")
        
        success, drilling_info, message = self.drilling_extractor.extract_all_drilling_info(self.dxf_doc)
        if not success:
            print(f"Warning: Could not extract drilling points: {message}")
            print("Proceeding with empty drilling points list")
            drilling_points = []
        else:
            drilling_points = drilling_info.get('points', [])
            print(f"Extracted {len(drilling_points)} drilling points")
        
        self.drilling_points = drilling_points
        self.current_drilling_points = drilling_points.copy()
        
        # Display the drilling points
        WorkflowDisplay.display_drilling_points(self.drilling_points, "Original Drilling Points")
        return True
    
    def _analyze_and_classify_drilling_points(self):
        """Analyze and classify the drilling points."""
        print("\n--- STEP 4: ANALYZING AND CLASSIFYING DRILLING POINTS ---")
        
        # Skip if no drilling points
        if not self.drilling_points:
            print("No drilling points to analyze")
            return True
        
        # Analyze drilling points
        success, analysis_results, details = self.analyzer.analyze_drilling_data(self.drilling_points)
        if not success:
            print(f"Warning: Could not analyze drilling points: {details.get('error', 'Unknown error')}")
            print("Proceeding without analysis")
            return True
        
        print(f"Analysis successful: Found {analysis_results['statistics']['total_groups']} tool groups")
        
        # Classify the drilling points
        success, classified_points, class_details = self.classifier.classify_points(self.drilling_points)
        if not success:
            print(f"Warning: Could not classify drilling points: {class_details.get('error', 'Unknown error')}")
            print("Proceeding without classification")
            return True
        
        print(f"Classification successful: {class_details['classified_count']} points classified")
        self.drilling_points = classified_points
        self.current_drilling_points = classified_points.copy()
        
        # Show some classification statistics
        stats = class_details.get('stats', {})
        print(f"Vertical points: {stats.get('vertical_count', 0)}")
        print(f"Horizontal points: {stats.get('horizontal_count', 0)}")
        
        # Display the classified drilling points
        WorkflowDisplay.display_drilling_points(self.drilling_points, "Classified Drilling Points")
        
        # Set up the transformer with workpiece info and classifier
        success, message, details = self.transformer.set_from_workpiece_info(self.workpiece_info, self.classifier)
        if not success:
            print(f"Error setting up coordinate transformer: {message}")
            return False
        
        print(f"Coordinate transformer initialized: {message}")
        
        # Display rotator information
        WorkflowDisplay.display_corners(self.transformer.rotator, "Original Corner Points")
        return True
    
    def _run_interactive_transformation(self):
        """Run the interactive transformation loop."""
        print("\n--- STEP 5: COORDINATE TRANSFORMATION ---")
        
        # Skip if no drilling points
        if not self.current_drilling_points:
            print("No drilling points to transform")
            return True
        
        # Interactive transformation loop
        while True:
            print("\n=== Transformation Options ===")
            print("1. Apply full transformation pipeline")
            print("2. Rotate 90° clockwise")
            print("3. Reset to original position")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ")
            
            if choice == "1":
                self._apply_full_transformation()
            elif choice == "2":
                self._rotate_90_degrees()
            elif choice == "3":
                self._reset_to_original()
            elif choice == "4":
                print("\nExiting transformation loop...")
                break
            else:
                print("\nInvalid choice, please try again.")
    
    def _apply_full_transformation(self):
        """Apply the full transformation pipeline."""
        print("\n--- APPLYING FULL TRANSFORMATION PIPELINE ---")
        
        success, transformed_points, details = self.transformer.transform_drilling_points(
            self.current_drilling_points, 
            rotation=False,  # We handle rotation separately
            edge=True,       # Apply edge transformation
            offset=True      # Apply origin offset
        )
        
        if success:
            print(f"Transformation successful: {details.get('message', '')}")
            self.current_drilling_points = transformed_points
            
            # Display transformed points
            WorkflowDisplay.display_transformed_points(
                self.current_drilling_points,
                "Transformed Drilling Points"
            )
        else:
            print(f"Error during transformation: {details.get('error', 'Unknown error')}")
    
    def _rotate_90_degrees(self):
        """Rotate the workpiece and drilling points 90 degrees clockwise."""
        success, corners, details = self.transformer.rotator.rotate_90_clockwise()
        if not success:
            print(f"Error rotating: {details.get('error', 'Unknown error')}")
            return
        
        WorkflowDisplay.display_corners(self.transformer.rotator)
        
        # Rotate drilling points
        success, rotated_points, rot_details = self.transformer.rotator.rotate_drilling_points(
            self.current_drilling_points
        )
        
        if success:
            self.current_drilling_points = rotated_points
            print(f"Rotated {rot_details.get('successful_rotations', 0)} drilling points")
            
            # Display rotated drilling points
            WorkflowDisplay.display_drilling_points(
                self.current_drilling_points, 
                f"Drilling Points (Rotated {details.get('rotation_angle', 90)}°)"
            )
        else:
            print(f"Error rotating drilling points: {rot_details.get('error', 'Unknown error')}")
    
    def _reset_to_original(self):
        """Reset the workpiece and drilling points to their original position."""
        success, corners, details = self.transformer.rotator.reset_to_original()
        if not success:
            print(f"Error resetting: {details.get('error', 'Unknown error')}")
            return
        
        WorkflowDisplay.display_corners(self.transformer.rotator)
        
        # Reset drilling points to original
        self.current_drilling_points = self.drilling_points.copy()
        WorkflowDisplay.display_drilling_points(
            self.current_drilling_points,
            "Drilling Points (Reset to Original)"
        )


# Main entry point
if __name__ == "__main__":
    # Create tester and run workflow
    tester = DxfWorkflowTester()
    tester.run_workflow()
    
    # Keep terminal open
    UIUtils.keep_terminal_open("DXF workflow test completed.")