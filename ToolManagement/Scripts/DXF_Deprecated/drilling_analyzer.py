"""
Module for analyzing drilling points by tool requirements.

This module takes drilling points and classifies them by their tool requirements
and edge directions, focusing on providing proper categorization for CNC operations.

Classes:
    DrillPointAnalyzer: Analyzes drilling points for tool group classification
    DrillPointClassifier: Classifies drilling points by edge and operation type
"""

import math
from typing import List, Dict, Any, Tuple, Set, Union
import numpy as np

# Import from Utils package
from Utils.logging_utils import setup_logger, log_exception
from Utils.error_utils import ErrorHandler, BaseError, ValidationError, ErrorSeverity, ErrorCategory

# Setup logger
logger = setup_logger(__name__)


class DrillPointAnalyzer:
    """
    Analyzes drilling points to determine tool requirements.
    
    This class groups drilling points by diameter, edge, and other parameters
    to identify which tools will be needed for machining operations.
    """
    
    def __init__(self):
        """Initialize the drill point analyzer."""
        self.precision = 1  # Decimal precision for rounding
        logger.info("DrillPointAnalyzer initialized")
    
    def vector_to_string(self, vector: Tuple[float, float, float]) -> str:
        """Convert a vector to a readable string format."""
        if vector is None:
            return "None"
        return f"({vector[0]:.1f}, {vector[1]:.1f}, {vector[2]:.1f})"
    
    def round_vector(self, vector: Tuple[float, float, float], precision: int = 1) -> Tuple[float, float, float]:
        """Round vector components to specified precision."""
        if vector is None:
            return None
        return (round(vector[0], precision), round(vector[1], precision), round(vector[2], precision))
    
    def detect_edge(self, vector: Tuple[float, float, float]) -> str:
        """
        Detect which edge a drilling operation is for based on its direction vector.
        
        Args:
            vector: Direction vector (x, y, z)
            
        Returns:
            Edge name: "VERTICAL", "LEFT", "RIGHT", "FRONT", "BACK", or "UNKNOWN"
        """
        if vector is None:
            return "UNKNOWN"
        
        # Use a tolerance for comparing vector components
        tolerance = 0.1
        
        # Normalize the vector
        magnitude = math.sqrt(vector[0]**2 + vector[1]**2 + vector[2]**2)
        if magnitude < 0.0001:  # Prevent division by zero
            return "UNKNOWN"
        
        x = vector[0] / magnitude
        y = vector[1] / magnitude
        z = vector[2] / magnitude
        
        # Check if it's a vertical drilling (Z direction)
        if abs(z - 1.0) < tolerance and abs(x) < tolerance and abs(y) < tolerance:
            return "VERTICAL"
        
        # Detect edge based on primary direction
        # For horizontal drilling, one component will be dominant
        if abs(x) > abs(y) and abs(x) > abs(z):
            return "RIGHT" if x > 0 else "LEFT"
        elif abs(y) > abs(x) and abs(y) > abs(z):
            return "BACK" if y > 0 else "FRONT"
        else:
            return "UNKNOWN"
    
    def group_by_tool(self, drilling_points: List[Any]) -> Dict[str, Any]:
        """
        Group drilling points by tool requirements (edge and diameter).
        
        For horizontal drilling, the edge (front/back/left/right) is the primary 
        grouping factor since different tools are needed for different edges.
        
        Args:
            drilling_points: List of drilling point objects with position, vector and diameter
            
        Returns:
            Dictionary with tool groups, organized by tool characteristics
        """
        logger.info(f"Grouping {len(drilling_points)} drilling points by edge and diameter")
        
        # Initialize results
        tool_groups = {}
        
        # Process each drilling point
        for point in drilling_points:
            # Extract key parameters
            position = getattr(point, 'position', None)
            diameter = round(getattr(point, 'diameter', 0), self.precision)  # Round to specified decimal places
            depth = round(getattr(point, 'depth', 0), self.precision)  # Round to specified decimal places
            vector = getattr(point, 'extrusion_vector', None)
            layer = getattr(point, 'layer_name', '')
            
            # Skip invalid points
            if position is None or diameter <= 0:
                logger.warning(f"Skipping invalid point: {point}")
                continue
            
            # Round vector components for consistent grouping
            rounded_vector = self.round_vector(vector, self.precision)
            
            # Determine edge from vector
            edge = self.detect_edge(vector)
            
            # Create a key combining edge and diameter
            # For horizontal drilling, edge is critical because different tools
            # are needed for different edges
            key = (edge, diameter)
            
            # Create new group if needed
            if key not in tool_groups:
                tool_groups[key] = {
                    'edge': edge,
                    'diameter': diameter,
                    'points': [],
                    'depths': set(),
                    'layers': set(),
                    'vectors': set(),  # Track unique vectors in this group
                    'is_vertical': edge == "VERTICAL"
                }
            
            # Add point to its group
            tool_groups[key]['points'].append(point)
            tool_groups[key]['depths'].add(depth)
            tool_groups[key]['layers'].add(layer)
            
            # Store the vector as a tuple to be hashable for the set
            if rounded_vector is not None:
                tool_groups[key]['vectors'].add(rounded_vector)
        
        # Add count information and finalize each group
        for key, group in tool_groups.items():
            group['count'] = len(group['points'])
            group['depths'] = sorted(list(group['depths']))
            
            # Convert vectors set to list for easier handling
            vectors_list = list(group['vectors'])
            group['vectors'] = vectors_list
            
            # Add a representative vector for display
            if vectors_list:
                group['primary_vector'] = vectors_list[0]
                group['primary_vector_str'] = self.vector_to_string(vectors_list[0])
            else:
                group['primary_vector'] = None
                group['primary_vector_str'] = "None"
        
        # Sort groups: first by type (vertical/horizontal), then by edge, then by diameter
        sorted_keys = sorted(tool_groups.keys(), 
                            key=lambda k: (0 if tool_groups[k]['is_vertical'] else 1,
                                            tool_groups[k]['edge'], 
                                            tool_groups[k]['diameter']))
        
        sorted_groups = {k: tool_groups[k] for k in sorted_keys}
        
        logger.info(f"Found {len(sorted_groups)} tool groups")
        return sorted_groups
    
    def analyze_drilling_data(self, drilling_points: List[Any]) -> Tuple[bool, str, Dict]:
        """
        Analyze drilling points and group them by tool requirements.
        
        Args:
            drilling_points: List of drilling point objects
            
        Returns:
            Tuple of (success, message, details)
        """
        if not drilling_points:
            warning_msg = "No drilling points to analyze"
            logger.warning(warning_msg)
            return ErrorHandler.create_success_response(
                message=warning_msg,
                data={
                    'tool_groups': {},
                    'statistics': {'total_points': 0}
                }
            )
        
        try:
            # Group points by tool requirements
            tool_groups = self.group_by_tool(drilling_points)
            
            # Calculate statistics
            vertical_groups = [group for group in tool_groups.values() if group['is_vertical']]
            horizontal_groups = [group for group in tool_groups.values() if not group['is_vertical']]
            
            statistics = {
                'total_points': len(drilling_points),
                'total_groups': len(tool_groups),
                'vertical_groups': len(vertical_groups),
                'horizontal_groups': len(horizontal_groups),
                'vertical_points': sum(group['count'] for group in vertical_groups),
                'horizontal_points': sum(group['count'] for group in horizontal_groups),
            }
            
            # Count points by edge
            edge_counts = {'VERTICAL': 0, 'FRONT': 0, 'BACK': 0, 'LEFT': 0, 'RIGHT': 0, 'UNKNOWN': 0}
            for group in tool_groups.values():
                edge_counts[group['edge']] += group['count']
            
            statistics['edge_counts'] = edge_counts
            
            # Create results dictionary
            results = {
                'tool_groups': tool_groups,
                'statistics': statistics
            }
            
            # Create details dictionary with specific information for each edge
            edge_details = {}
            for edge in ["VERTICAL", "FRONT", "BACK", "LEFT", "RIGHT"]:
                edge_groups = [group for group in tool_groups.values() if group['edge'] == edge]
                if edge_groups:
                    edge_details[edge] = {
                        'group_count': len(edge_groups),
                        'point_count': sum(group['count'] for group in edge_groups),
                        'diameters': sorted(set(group['diameter'] for group in edge_groups))
                    }
            
            success_msg = (f"Analysis complete: {statistics['total_groups']} tool groups "
                         f"({statistics['vertical_groups']} vertical, {statistics['horizontal_groups']} horizontal)")
            logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    'results': results,
                    'statistics': statistics,
                    'edge_details': edge_details,
                    'group_count': len(tool_groups),
                    'edge_summary': edge_counts
                }
            )
            
        except Exception as e:
            error_msg = f"Error during drilling analysis: {str(e)}"
            log_exception(logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={
                        "error_type": "Exception",
                        "error": str(e),
                        "points_count": len(drilling_points)
                    }
                )
            )


class DrillPointClassifier:
    """
    Classifies drilling points by edge and operation type.
    
    This class processes analyzed drilling points and updates them with
    classification information needed for coordinate transformation.
    """
    
    def __init__(self):
        """Initialize the drill point classifier."""
        # Analyzer used for tool grouping
        self.analyzer = DrillPointAnalyzer()
        logger.info("DrillPointClassifier initialized")
    
    def classify_points(self, drilling_points: List[Any]) -> Tuple[bool, str, Dict]:
        """
        Classify drilling points by edge and operation type.
        
        Adds edge and drill_type properties to each drilling point object.
        
        Args:
            drilling_points: List of drilling point objects
            
        Returns:
            Tuple of (success, message, details)
        """
        if not drilling_points:
            warning_msg = "No drilling points to classify"
            logger.warning(warning_msg)
            return ErrorHandler.create_success_response(
                message=warning_msg,
                data={
                    "points": [],
                    "classified_count": 0
                }
            )
        
        logger.info(f"Classifying {len(drilling_points)} drilling points")
        
        try:
            # First analyze the drilling data to group points
            success, message, analysis_details = self.analyzer.analyze_drilling_data(drilling_points)
            
            if not success:
                error_msg = f"Error analyzing drilling points: {message}"
                logger.error(error_msg)
                return ErrorHandler.from_exception(
                    BaseError(
                        message=error_msg,
                        severity=ErrorSeverity.ERROR,
                        category=ErrorCategory.PROCESSING,
                        details={"analysis_error": message, "details": analysis_details}
                    )
                )
            
            # Extract the tool_groups from the results
            results = analysis_details.get('results', {})
            tool_groups = results.get('tool_groups', {})
            
            # Statistics for tracking classification
            classification_stats = {
                "vertical_count": 0,
                "horizontal_count": 0,
                "unknown_count": 0,
                "by_edge": {}
            }
            
            # Initialize edge counters
            for edge in ["VERTICAL", "FRONT", "BACK", "LEFT", "RIGHT", "UNKNOWN"]:
                classification_stats["by_edge"][edge] = 0
            
            # Update each drilling point with its classification
            for key, group in tool_groups.items():
                edge, diameter = key
                
                # Process each point in this group
                for point in group['points']:
                    # Set edge property on the drilling point object
                    point.edge = edge
                    classification_stats["by_edge"][edge] += 1
                    
                    # Set type property (vertical or horizontal)
                    if edge == "VERTICAL":
                        point.drill_type = "vertical"
                        classification_stats["vertical_count"] += 1
                    elif edge in ["FRONT", "BACK", "LEFT", "RIGHT"]:
                        point.drill_type = "horizontal"
                        classification_stats["horizontal_count"] += 1
                    else:
                        point.drill_type = "unknown"
                        classification_stats["unknown_count"] += 1
                    
                    # Set primary vector if available
                    if "primary_vector" in group and group["primary_vector"] is not None:
                        point.primary_vector = group["primary_vector"]
            
            success_msg = (f"Classification complete: {classification_stats['vertical_count']} vertical, "
                         f"{classification_stats['horizontal_count']} horizontal points")
            logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    "points": drilling_points,
                    "classified_count": len(drilling_points),
                    "stats": classification_stats,
                    "analysis_results": results
                }
            )
            
        except Exception as e:
            error_msg = f"Error during drilling classification: {str(e)}"
            log_exception(logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={
                        "error_type": "Exception",
                        "error": str(e),
                        "points_count": len(drilling_points)
                    }
                )
            )
    
    def get_points_by_edge(self, drilling_points: List[Any]) -> Dict[str, List[Any]]:
        """
        Group drilling points by edge for easier access.
        
        Args:
            drilling_points: List of classified drilling point objects
            
        Returns:
            Dictionary with points grouped by edge
        """
        # Create edge groups dictionary
        edge_groups = {
            "VERTICAL": [],
            "FRONT": [],
            "BACK": [],
            "LEFT": [],
            "RIGHT": [],
            "UNKNOWN": []
        }
        
        # Sort points into edge groups
        for point in drilling_points:
            edge = getattr(point, 'edge', "UNKNOWN")
            if edge in edge_groups:
                edge_groups[edge].append(point)
            else:
                edge_groups["UNKNOWN"].append(point)
        
        return edge_groups


# Backwards compatibility functions for existing code
def analyze_drilling_data(drilling_points: List[Any]) -> Tuple[bool, str, Dict]:
    """Legacy function that calls the DrillPointAnalyzer class method."""
    analyzer = DrillPointAnalyzer()
    return analyzer.analyze_drilling_data(drilling_points)

def classify_drilling_points(drilling_points: List[Any]) -> Tuple[bool, str, Dict]:
    """Legacy function that calls the DrillPointClassifier class method."""
    classifier = DrillPointClassifier()
    return classifier.classify_points(drilling_points)


# Example usage if run directly
if __name__ == "__main__":
    import os
    import sys
    from DXF.file_loader import DxfLoader
    from DXF.drilling_extractor import DrillingExtractor
    from Utils.ui_utils import UIUtils
    
    # Create analyzer and classifier
    analyzer = DrillPointAnalyzer()
    classifier = DrillPointClassifier()
    
    # Set up path to test data
    test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Tests", "TestData")
    dxf_dir = os.path.join(test_data_dir, "DXF")
    
    # Let user select a DXF file
    dxf_file_path = UIUtils.select_dxf_file(dxf_dir)
    if not dxf_file_path:
        print("No DXF file selected. Exiting.")
        UIUtils.keep_terminal_open("Test aborted - no file selected.")
        sys.exit(1)
    
    print(f"Using test DXF file: {dxf_file_path}")
    
    # Load DXF file
    UIUtils.print_separator("Loading DXF File")
    loader = DxfLoader()
    success, message, details = loader.load_dxf(dxf_file_path)
    
    if success:
        print(f"SUCCESS: {message}")
        
        # Get the document from details
        doc = details.get('document')
        
        # Extract drilling points
        UIUtils.print_separator("Extracting Drilling Points")
        extractor = DrillingExtractor()
        success, message, drilling_details = extractor.extract_all_drilling_info(doc)
        
        if success:
            print(f"SUCCESS: {message}")
            
            # Get drilling points from details
            drilling_points = drilling_details.get('points', [])
            
            # Analyze drilling points
            UIUtils.print_separator("Analyzing Drilling Points")
            success, message, analysis_details = analyzer.analyze_drilling_data(drilling_points)
            
            if success:
                print(f"SUCCESS: {message}")
                
                # Get analysis results from details
                results = analysis_details.get('results', {})
                statistics = results.get('statistics', {}) if 'statistics' in results else analysis_details.get('statistics', {})
                group_count = statistics.get('total_groups', 0)
                print(f"Found {group_count} tool groups")
                
                # Classify drilling points
                UIUtils.print_separator("Classifying Drilling Points")
                success, message, classification_details = classifier.classify_points(drilling_points)
                
                if success:
                    print(f"SUCCESS: {message}")
                    
                    # Get classified points from details
                    classified_points = classification_details.get('points', drilling_points)
                    
                    # Get points by edge
                    points_by_edge = classifier.get_points_by_edge(classified_points)
                    
                    # Show results
                    UIUtils.print_separator("Classification Results")
                    stats = classification_details.get('stats', {})
                    print(f"Vertical points: {stats.get('vertical_count', 0)}")
                    print(f"Horizontal points: {stats.get('horizontal_count', 0)}")
                    
                    # Show points by edge
                    for edge, points in points_by_edge.items():
                        if points:
                            print(f"\n{edge} Edge: {len(points)} points")
                            for i, point in enumerate(points[:3]):  # Show first 3 points
                                position = getattr(point, 'position', None)
                                if position:
                                    pos_str = f"({position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f})"
                                    print(f"  {i+1}. {pos_str}, Ø{getattr(point, 'diameter', 0):.1f}mm")
                            
                            if len(points) > 3:
                                print(f"  ...and {len(points) - 3} more")
                else:
                    print(f"Classification failed: {message}")
                    if 'details' in classification_details:
                        print(f"Details: {classification_details.get('details')}")
            else:
                print(f"Analysis failed: {message}")
                if 'details' in analysis_details:
                    print(f"Details: {analysis_details.get('details')}")
        else:
            print(f"Extraction failed: {message}")
            if 'details' in drilling_details:
                print(f"Details: {drilling_details.get('details')}")
    else:
        print(f"Loading failed: {message}")
        if 'details' in details:
            print(f"Details: {details.get('details')}")
        
    # Keep terminal open
    UIUtils.keep_terminal_open("Drilling analysis completed.")