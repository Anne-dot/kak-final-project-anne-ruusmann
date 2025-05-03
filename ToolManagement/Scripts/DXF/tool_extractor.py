"""
Module for extracting tool requirements from DXF files.

This module identifies and extracts tool requirements from DXF files,
focusing on the tools needed for drilling operations. It translates
drilling information into tool requirements without duplicating analysis.

References:
    - MRFP-80: DXF to G-code Generation Epic
    - MRFP-128: Implement DXF Package Modules
"""

import os
from typing import List, Dict, Tuple, Optional, Any, Union

# Import from Utils package
from Utils.logging_utils import setup_logger, log_exception
from Utils.file_utils import FileUtils
from Utils.error_utils import ErrorHandler, BaseError, ValidationError, FileError, ErrorSeverity, ErrorCategory

# Import from DXF package
from DXF.drilling_extractor import DrillingExtractor


class ToolRequirementExtractor:
    """
    Class for extracting tool requirements from DXF files.
    
    This class analyzes DXF files to determine what tools are needed
    for machining operations, particularly focusing on drilling.
    """
    
    def __init__(self):
        """Initialize the tool requirement extractor."""
        # Set up logger for this class
        self.logger = setup_logger(__name__)
        
        # Tolerance for grouping similar diameters (in mm)
        self.diameter_tolerance = 0.1
        
        # Dictionary to store requirements
        self.requirements = {
            'vertical_drills': [],
            'horizontal_drills': [],
            'all_diameters': set()
        }
        
        self.logger.info("ToolRequirementExtractor initialized")
    
    def extract_tool_requirements(self, dxf_doc, drilling_info=None) -> Tuple[bool, str, Dict]:
        """
        Extract all tool requirements from a DXF document.
        
        Args:
            dxf_doc: ezdxf document object
            drilling_info: Optional pre-extracted drilling information
            
        Returns:
            Tuple of (success, message, details)
        """
        if dxf_doc is None:
            error_msg = "No DXF document provided"
            self.logger.error(error_msg)
            return ErrorHandler.from_exception(
                ValidationError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    details={"error": "missing_document"}
                )
            )
        
        self.logger.info("Extracting tool requirements")
        
        try:
            # If drilling_info not provided, we need to get it
            if drilling_info is None:
                drilling_extractor = DrillingExtractor()
                success, message, drilling_details = drilling_extractor.extract_all_drilling_info(dxf_doc)
                
                if not success:
                    error_msg = f"Failed to extract drilling information: {message}"
                    self.logger.error(error_msg)
                    return ErrorHandler.from_exception(
                        BaseError(
                            message=error_msg,
                            severity=ErrorSeverity.ERROR,
                            category=ErrorCategory.PROCESSING,
                            details={"error_source": "drilling_extractor", "original_message": message}
                        )
                    )
                    
                drilling_info = drilling_details
            
            # Reset requirements dictionary
            self.requirements = {
                'vertical_drills': [],
                'horizontal_drills': [],
                'all_diameters': set()
            }
            
            # Convert drilling info into tool requirements
            success, message, result_details = self._convert_drilling_to_requirements(drilling_info)
            if not success:
                return ErrorHandler.from_exception(
                    BaseError(
                        message=message,
                        severity=ErrorSeverity.ERROR,
                        category=ErrorCategory.PROCESSING,
                        details={"error_source": "convert_drilling_to_requirements", "error": message}
                    )
                )
            
            # Group requirements by operation
            success, message, grouped_details = self._group_requirements_by_operation()
            if not success:
                self.logger.warning(f"Warning grouping requirements: {message}")
            else:
                self.requirements['grouped'] = grouped_details
            
            # Add summary information
            self.requirements['summary'] = {
                'vertical_drill_count': len(self.requirements['vertical_drills']),
                'horizontal_drill_count': len(self.requirements['horizontal_drills']),
                'total_drill_count': len(self.requirements['vertical_drills']) + len(self.requirements['horizontal_drills']),
                'unique_diameters': len(self.requirements['all_diameters']),
                'diameter_list': sorted(list(self.requirements['all_diameters']))
            }
            
            # Create human-readable summary
            success, message, summary_details = self._format_requirements_summary()
            if success and summary_details:
                self.requirements['readable_summary'] = summary_details
            
            success_msg = "Tool requirements extracted successfully"
            self.logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data=self.requirements
            )
            
        except Exception as e:
            error_msg = f"Error extracting tool requirements: {str(e)}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )
    
    def _convert_drilling_to_requirements(self, drilling_info) -> Tuple[bool, str, Dict]:
        """
        Convert drilling information into tool requirements.
        
        Args:
            drilling_info: Dict containing drilling information from DrillingExtractor
            
        Returns:
            Tuple of (success, message, details)
        """
        if not drilling_info:
            error_msg = "No drilling information provided"
            self.logger.error(error_msg)
            return ErrorHandler.from_exception(
                ValidationError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    details={"error": "missing_drilling_info"}
                )
            )
        
        self.logger.info("Converting drilling info to tool requirements")
        
        try:
            # Process vertical drilling points
            vertical_parameters = drilling_info.get('parameters', {}).get('vertical', [])
            for params in vertical_parameters:
                requirement = {
                    'type': 'vertical_drill',
                    'diameter': params.get('diameter', 0.0),
                    'depth': params.get('depth', 0.0),
                    'position': params.get('position', (0, 0, 0)),
                    'layer': params.get('layer', '')
                }
                
                self.requirements['vertical_drills'].append(requirement)
                
                # Add to all diameters set (rounded to 1 decimal place for grouping)
                if requirement['diameter'] > 0:
                    self.requirements['all_diameters'].add(round(requirement['diameter'], 1))
            
            # Process horizontal drilling points
            horizontal_parameters = drilling_info.get('parameters', {}).get('horizontal', [])
            for params in horizontal_parameters:
                requirement = {
                    'type': 'horizontal_drill',
                    'diameter': params.get('diameter', 0.0),
                    'depth': params.get('depth', 0.0),
                    'edge': params.get('edge', 'UNKNOWN'),
                    'direction': params.get('direction', (0, 0, 0)),
                    'position': params.get('position', (0, 0, 0)),
                    'layer': params.get('layer', '')
                }
                
                self.requirements['horizontal_drills'].append(requirement)
                
                # Add to all diameters set (rounded to 1 decimal place for grouping)
                if requirement['diameter'] > 0:
                    self.requirements['all_diameters'].add(round(requirement['diameter'], 1))
            
            success_msg = f"Converted {len(vertical_parameters)} vertical and {len(horizontal_parameters)} horizontal drilling points to tool requirements"
            self.logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    "vertical_count": len(vertical_parameters),
                    "horizontal_count": len(horizontal_parameters),
                    "requirements": self.requirements
                }
            )
            
        except Exception as e:
            error_msg = f"Error converting drilling info to requirements: {str(e)}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )
    
    def _group_requirements_by_operation(self) -> Tuple[bool, str, Dict]:
        """
        Group similar requirements by operation type.
        
        Returns:
            Tuple of (success, message, details)
        """
        self.logger.info("Grouping requirements by operation")
        
        try:
            # Create grouped requirements dictionary
            grouped = {
                'vertical_drills': {},  # Grouped by diameter
                'horizontal_drills': {}  # Grouped by diameter and edge
            }
            
            # Group vertical drilling operations by diameter
            for req in self.requirements.get('vertical_drills', []):
                diameter = round(req.get('diameter', 0.0), 1)
                if diameter <= 0:
                    continue
                
                diameter_key = f"D{diameter:.1f}"
                
                if diameter_key not in grouped['vertical_drills']:
                    grouped['vertical_drills'][diameter_key] = []
                
                grouped['vertical_drills'][diameter_key].append(req)
            
            # Group horizontal drilling operations by diameter and edge
            for req in self.requirements.get('horizontal_drills', []):
                diameter = round(req.get('diameter', 0.0), 1)
                edge = req.get('edge', 'UNKNOWN')
                if diameter <= 0:
                    continue
                
                group_key = f"D{diameter:.1f}_{edge}"
                
                if group_key not in grouped['horizontal_drills']:
                    grouped['horizontal_drills'][group_key] = []
                
                grouped['horizontal_drills'][group_key].append(req)
            
            # Calculate statistics
            stats = {
                "vertical_groups": len(grouped['vertical_drills']),
                "horizontal_groups": len(grouped['horizontal_drills']),
                "total_groups": len(grouped['vertical_drills']) + len(grouped['horizontal_drills'])
            }
            
            success_msg = f"Grouped requirements into {stats['vertical_groups']} vertical and {stats['horizontal_groups']} horizontal operation types"
            self.logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data=grouped
            )
            
        except Exception as e:
            error_msg = f"Error grouping requirements: {str(e)}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )
    
    def _format_requirements_summary(self) -> Tuple[bool, str, str]:
        """
        Create a human-readable summary of tool requirements.
        
        Returns:
            Tuple of (success, message, summary)
        """
        self.logger.info("Creating human-readable requirements summary")
        
        try:
            # Create summary lines
            summary_lines = []
            
            # Add header
            summary_lines.append("TOOL REQUIREMENTS SUMMARY")
            summary_lines.append("=========================")
            
            # Add vertical drill information
            vertical_count = len(self.requirements.get('vertical_drills', []))
            summary_lines.append(f"\nVertical Drilling: {vertical_count} operations")
            
            vert_groups = self.requirements.get('grouped', {}).get('vertical_drills', {})
            for group_key, operations in vert_groups.items():
                summary_lines.append(f"  {group_key}: {len(operations)} holes")
            
            # Add horizontal drill information
            horizontal_count = len(self.requirements.get('horizontal_drills', []))
            summary_lines.append(f"\nHorizontal Drilling: {horizontal_count} operations")
            
            horz_groups = self.requirements.get('grouped', {}).get('horizontal_drills', {})
            for group_key, operations in horz_groups.items():
                summary_lines.append(f"  {group_key}: {len(operations)} holes")
            
            # Add required diameter summary
            all_diameters = sorted(list(self.requirements.get('all_diameters', set())))
            summary_lines.append(f"\nRequired Tool Diameters: {len(all_diameters)} unique sizes")
            
            # Format diameters in clean groups of 5
            diameter_chunks = [all_diameters[i:i+5] for i in range(0, len(all_diameters), 5)]
            for chunk in diameter_chunks:
                summary_lines.append(f"  {', '.join([f'{d:.1f}mm' for d in chunk])}")
            
            # Join all lines into a single string
            summary = "\n".join(summary_lines)
            
            success_msg = "Created human-readable requirements summary"
            self.logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data=summary
            )
            
        except Exception as e:
            error_msg = f"Error creating requirements summary: {str(e)}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )


class ToolSelector:
    """
    Class for selecting appropriate tools based on requirements.
    
    This class matches tool requirements to available tools in the
    tool database, selecting the best tools for each operation.
    It handles direction-specific tool selection for horizontal drilling.
    """
    
    def __init__(self):
        """Initialize the tool selector."""
        # Set up logger for this class
        self.logger = setup_logger(__name__)
        
        # Tolerance for diameter matching (in mm)
        self.diameter_tolerance = 0.1
        
        # Direction codes from tool data
        self.direction_codes = {
            1: "X+",  # RIGHT edge
            2: "X-",  # LEFT edge
            3: "Y+",  # FRONT edge
            4: "Y-",  # BACK edge
            5: "Z-",  # VERTICAL (down)
            6: "MILL" # Mill (all directions)
        }
        
        # Edge to direction code mapping
        self.edge_to_direction = {
            "FRONT": 3,  # Y+
            "BACK": 4,   # Y-
            "LEFT": 2,   # X-
            "RIGHT": 1   # X+
        }
        
        # Tool data cache
        self.tool_data = None
        
        self.logger.info("ToolSelector initialized")
    
    def select_tools(self, requirements, tool_data_path=None) -> Tuple[bool, str, Dict]:
        """
        Select appropriate tools based on requirements.
        
        Args:
            requirements: Dict containing tool requirements
            tool_data_path: Optional path to tool data CSV file
            
        Returns:
            Tuple of (success, message, details)
        """
        if not requirements:
            error_msg = "No tool requirements provided"
            self.logger.error(error_msg)
            return ErrorHandler.from_exception(
                ValidationError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    details={"error": "missing_requirements"}
                )
            )
        
        self.logger.info("Selecting tools based on requirements")
        
        try:
            # Load tool data if not already loaded
            if self.tool_data is None:
                success, message, tool_data_details = self._load_tool_data(tool_data_path)
                if not success:
                    return ErrorHandler.from_exception(
                        BaseError(
                            message=f"Failed to load tool data: {message}",
                            severity=ErrorSeverity.ERROR,
                            category=ErrorCategory.PROCESSING,
                            details={"error_source": "load_tool_data", "original_message": message}
                        )
                    )
                self.tool_data = tool_data_details
            
            # Create selections dictionary
            selections = {
                'vertical_drills': {},
                'horizontal_drills': {},
                'all_selections': []
            }
            
            # Process vertical drilling requirements
            vert_success, vert_message, vert_details = self._select_vertical_drill_tools(
                requirements.get('vertical_drills', [])
            )
            if vert_success:
                selections['vertical_drills'] = vert_details
            else:
                self.logger.warning(f"Warning selecting vertical drill tools: {vert_message}")
            
            # Process horizontal drilling requirements
            horz_success, horz_message, horz_details = self._select_horizontal_drill_tools(
                requirements.get('horizontal_drills', [])
            )
            if horz_success:
                selections['horizontal_drills'] = horz_details
            else:
                self.logger.warning(f"Warning selecting horizontal drill tools: {horz_message}")
            
            # Combine all selections
            for tool_type, tool_selections in selections.items():
                if tool_type != 'all_selections':
                    selections['all_selections'].extend(tool_selections.values() if isinstance(tool_selections, dict) else tool_selections)
            
            # Add summary information
            selections['summary'] = {
                'vertical_drill_count': len(selections.get('vertical_drills', {})),
                'horizontal_drill_count': len(selections.get('horizontal_drills', {})),
                'total_selections': len(selections.get('all_selections', []))
            }
            
            # Create human-readable summary
            summary_success, summary_message, summary_details = self._format_selections_summary(selections)
            if summary_success:
                selections['readable_summary'] = summary_details
            
            success_msg = f"Selected {len(selections['all_selections'])} tools successfully"
            self.logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data=selections
            )
            
        except Exception as e:
            error_msg = f"Error selecting tools: {str(e)}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )
    
    def _load_tool_data(self, tool_data_path=None) -> Tuple[bool, str, Dict]:
        """
        Load tool data from CSV file.
        
        Args:
            tool_data_path: Path to tool data CSV file, defaults to standard location
            
        Returns:
            Tuple of (success, message, details)
        """
        self.logger.info("Loading tool data from CSV")
        
        try:
            # Default path if not provided
            if tool_data_path is None:
                from Utils.path_utils import PathUtils
                data_dir = PathUtils.get_data_dir()
                tool_data_path = os.path.join(data_dir, "tool-data.csv")
            
            # Use FileUtils to read CSV file
            success, message, details = FileUtils.read_csv(tool_data_path)
            
            if not success:
                error_msg = f"Failed to read tool data CSV: {message}"
                self.logger.error(error_msg)
                return ErrorHandler.from_exception(
                    FileError(
                        message=error_msg,
                        file_path=tool_data_path,
                        severity=ErrorSeverity.ERROR,
                        details={"original_message": message}
                    )
                )
            
            # Extract rows from result
            result = details.get('data', {})
            if isinstance(result, dict) and 'rows' in result:
                rows = result['rows']
            else:
                rows = result
            
            # Process tool data into usable format
            tool_data = self._process_tool_data(rows)
            
            success_msg = f"Loaded data for {len(tool_data)} tools"
            self.logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data=tool_data
            )
            
        except Exception as e:
            error_msg = f"Error loading tool data: {str(e)}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                FileError(
                    message=error_msg,
                    file_path=str(tool_data_path) if tool_data_path else "default path",
                    severity=ErrorSeverity.ERROR,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )
    
    def _process_tool_data(self, rows):
        """
        Process raw CSV data into tool data dictionary.
        
        Args:
            rows: List of CSV row dictionaries
            
        Returns:
            dict: Processed tool data indexed by tool number
        """
        tools = {}
        
        for row in rows:
            try:
                # Convert tool number to integer
                tool_number = int(row.get('tool_number', 0))
                if tool_number <= 0:
                    continue
                
                # Skip empty tool slots
                if row.get('tool_type', '').strip().lower() == 'empty':
                    continue
                
                # Process tool direction
                direction_code = 0
                try:
                    direction_code = int(row.get('tool_direction', 0))
                except (ValueError, TypeError):
                    direction_code = 0
                
                # Convert any string diameters to float
                diameter = 0.0
                try:
                    diameter = float(row.get('diameter', 0.0))
                except (ValueError, TypeError):
                    diameter = 0.0
                
                # Create tool data entry
                tools[tool_number] = {
                    'tool_number': tool_number,
                    'tool_type': row.get('tool_type', '').strip(),
                    'direction': direction_code,
                    'direction_name': self.direction_codes.get(direction_code, 'UNKNOWN'),
                    'diameter': diameter,
                    'in_spindle': row.get('in_spindle', '0').strip() == '1'
                }
                
            except Exception as e:
                self.logger.warning(f"Error processing tool row: {str(e)}")
                continue
        
        return tools
    
    def _select_vertical_drill_tools(self, requirements) -> Tuple[bool, str, Dict]:
        """
        Select appropriate tools for vertical drilling operations.
        
        Args:
            requirements: List of vertical drilling requirements
            
        Returns:
            Tuple of (success, message, details)
        """
        if not requirements:
            return ErrorHandler.create_success_response(
                message="No vertical drilling requirements",
                data={}
            )
        
        self.logger.info(f"Selecting tools for {len(requirements)} vertical drilling operations")
        
        try:
            # Create selections dictionary
            selections = {}
            
            # Group requirements by diameter for efficient selection
            diameter_groups = {}
            for req in requirements:
                diameter = round(req.get('diameter', 0.0), 1)
                if diameter <= 0:
                    continue
                
                if diameter not in diameter_groups:
                    diameter_groups[diameter] = []
                
                diameter_groups[diameter].append(req)
            
            # For each diameter group, find matching tool
            for diameter, reqs in diameter_groups.items():
                # Find vertical drill tools with matching diameter
                matching_tools = []
                for tool_number, tool in self.tool_data.items():
                    # Check if it's a vertical drill (direction code 5)
                    if tool.get('direction') != 5:
                        continue
                    
                    # Check if diameter matches within tolerance
                    tool_diameter = round(tool.get('diameter', 0.0), 1)
                    if abs(tool_diameter - diameter) <= self.diameter_tolerance:
                        matching_tools.append(tool)
                
                # Select best matching tool (prioritize exact match)
                selected_tool = None
                if matching_tools:
                    # Sort by diameter difference (smallest first)
                    matching_tools.sort(key=lambda t: abs(round(t.get('diameter', 0.0), 1) - diameter))
                    selected_tool = matching_tools[0]
                
                # Add to selections
                group_key = f"D{diameter:.1f}"
                if selected_tool:
                    selections[group_key] = {
                        'tool_number': selected_tool.get('tool_number'),
                        'diameter': selected_tool.get('diameter'),
                        'type': 'vertical_drill',
                        'direction': selected_tool.get('direction'),
                        'direction_name': selected_tool.get('direction_name'),
                        'operations': len(reqs)
                    }
                else:
                    self.logger.warning(f"No matching tool found for {group_key}")
                    selections[group_key] = {
                        'tool_number': None,
                        'diameter': diameter,
                        'type': 'vertical_drill',
                        'direction': 5,  # Vertical Z-
                        'direction_name': 'Z-',
                        'operations': len(reqs),
                        'missing': True
                    }
            
            success_msg = f"Selected tools for {len(selections)} vertical drilling diameter groups"
            self.logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data=selections
            )
            
        except Exception as e:
            error_msg = f"Error selecting vertical drill tools: {str(e)}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )
    
    def _select_horizontal_drill_tools(self, requirements) -> Tuple[bool, str, Dict]:
        """
        Select appropriate tools for horizontal drilling operations.
        
        Args:
            requirements: List of horizontal drilling requirements
            
        Returns:
            Tuple of (success, message, details)
        """
        if not requirements:
            return ErrorHandler.create_success_response(
                message="No horizontal drilling requirements",
                data={}
            )
        
        self.logger.info(f"Selecting tools for {len(requirements)} horizontal drilling operations")
        
        try:
            # Create selections dictionary
            selections = {}
            
            # Group requirements by diameter and edge for efficient selection
            edge_diameter_groups = {}
            for req in requirements:
                diameter = round(req.get('diameter', 0.0), 1)
                edge = req.get('edge', 'UNKNOWN')
                if diameter <= 0 or edge == 'UNKNOWN':
                    continue
                
                group_key = f"{edge}_{diameter}"
                if group_key not in edge_diameter_groups:
                    edge_diameter_groups[group_key] = []
                
                edge_diameter_groups[group_key].append(req)
            
            # For each diameter-edge group, find matching tool
            for group_key, reqs in edge_diameter_groups.items():
                edge, diameter_str = group_key.split('_')
                diameter = float(diameter_str)
                
                # Get direction code for this edge
                direction_code = self.edge_to_direction.get(edge, 0)
                
                # Find horizontal drill tools with matching diameter and direction
                matching_tools = []
                for tool_number, tool in self.tool_data.items():
                    # Check if direction matches
                    if tool.get('direction') != direction_code:
                        continue
                    
                    # Check if diameter matches within tolerance
                    tool_diameter = round(tool.get('diameter', 0.0), 1)
                    if abs(tool_diameter - diameter) <= self.diameter_tolerance:
                        matching_tools.append(tool)
                
                # Select best matching tool (prioritize exact match)
                selected_tool = None
                if matching_tools:
                    # Sort by diameter difference (smallest first)
                    matching_tools.sort(key=lambda t: abs(round(t.get('diameter', 0.0), 1) - diameter))
                    selected_tool = matching_tools[0]
                
                # Add to selections
                selection_key = f"D{diameter:.1f}_{edge}"
                if selected_tool:
                    selections[selection_key] = {
                        'tool_number': selected_tool.get('tool_number'),
                        'diameter': selected_tool.get('diameter'),
                        'type': 'horizontal_drill',
                        'edge': edge,
                        'direction': selected_tool.get('direction'),
                        'direction_name': selected_tool.get('direction_name'),
                        'operations': len(reqs)
                    }
                else:
                    self.logger.warning(f"No matching tool found for {selection_key}")
                    selections[selection_key] = {
                        'tool_number': None,
                        'diameter': diameter,
                        'type': 'horizontal_drill',
                        'edge': edge,
                        'direction': direction_code,
                        'direction_name': self.direction_codes.get(direction_code, 'UNKNOWN'),
                        'operations': len(reqs),
                        'missing': True
                    }
            
            success_msg = f"Selected tools for {len(selections)} horizontal drilling edge-diameter groups"
            self.logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data=selections
            )
            
        except Exception as e:
            error_msg = f"Error selecting horizontal drill tools: {str(e)}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )
    
    def _format_selections_summary(self, selections) -> Tuple[bool, str, str]:
        """
        Create a human-readable summary of tool selections.
        
        Args:
            selections: Dict containing tool selections
            
        Returns:
            Tuple of (success, message, summary)
        """
        self.logger.info("Creating human-readable selections summary")
        
        try:
            # Create summary lines
            summary_lines = []
            
            # Add header
            summary_lines.append("TOOL SELECTION SUMMARY")
            summary_lines.append("=====================")
            
            # Add vertical drill information
            vertical_selections = selections.get('vertical_drills', {})
            summary_lines.append(f"\nVertical Drilling: {len(vertical_selections)} tools required")
            
            for group_key, selection in vertical_selections.items():
                tool_status = f"Tool #{selection['tool_number']}" if selection.get('tool_number') else "NO TOOL FOUND"
                summary_lines.append(f"  {group_key}: {tool_status} - {selection['operations']} operations")
            
            # Add horizontal drill information
            horizontal_selections = selections.get('horizontal_drills', {})
            summary_lines.append(f"\nHorizontal Drilling: {len(horizontal_selections)} tools required")
            
            for group_key, selection in horizontal_selections.items():
                tool_status = f"Tool #{selection['tool_number']}" if selection.get('tool_number') else "NO TOOL FOUND"
                summary_lines.append(f"  {group_key}: {tool_status} - {selection['operations']} operations")
            
            # Add missing tools warning if any
            missing_tools = [s for s in selections.get('all_selections', []) if s.get('missing', False)]
            if missing_tools:
                summary_lines.append(f"\nWARNING: {len(missing_tools)} required tools not found in tool database")
                for tool in missing_tools:
                    if tool.get('type') == 'vertical_drill':
                        summary_lines.append(f"  Missing: {tool.get('diameter', 0.0):.1f}mm vertical drill")
                    else:
                        summary_lines.append(f"  Missing: {tool.get('diameter', 0.0):.1f}mm {tool.get('edge', '')} edge drill")
            
            # Join all lines into a single string
            summary = "\n".join(summary_lines)
            
            success_msg = "Created human-readable selections summary"
            self.logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data=summary
            )
            
        except Exception as e:
            error_msg = f"Error creating selections summary: {str(e)}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )


# Example usage if run directly
if __name__ == "__main__":
    import sys
    from DXF.file_loader import DxfLoader
    from DXF.drilling_extractor import DrillingExtractor
    
    extractor = ToolRequirementExtractor()
    drill_extractor = DrillingExtractor()
    loader = DxfLoader()
    
    success, message, details = loader.load_dxf()
    
    if success:
        print(message)
        
        # Get document from details
        doc = details.get('document')
        
        # Extract drilling information first
        drill_success, drill_message, drilling_details = drill_extractor.extract_all_drilling_info(doc)
        
        if drill_success:
            # Extract tool requirements based on drilling info
            tool_success, tool_message, tool_details = extractor.extract_tool_requirements(doc, drilling_details)
            
            print(f"\nTool requirements extraction: {'Succeeded' if tool_success else 'Failed'}")
            print(f"Message: {tool_message}")
            
            if tool_success and 'readable_summary' in tool_details:
                print("\n" + tool_details['readable_summary'])
        else:
            print(f"Error extracting drilling info: {drill_message}")
            if 'details' in drilling_details:
                print(f"Details: {drilling_details.get('details')}")
    else:
        print(f"Error: {message}")
        if 'details' in details:
            print(f"Details: {details.get('details')}")