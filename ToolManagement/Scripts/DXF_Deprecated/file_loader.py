"""
Module for loading and validating DXF files.

This module handles the initial loading of DXF files, validation of file
format, and provides the basic file object that other modules will use
for data extraction. It isolates file I/O operations from data processing.

References:
    - MRFP-80: DXF to G-code Generation Epic
"""

import os
import sys
import platform
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, Union, List

# Import from Utils package
from Utils.logging_utils import setup_logger, log_exception
from Utils.error_utils import ErrorHandler, FileError, ErrorSeverity, ErrorCategory
from Utils.file_loader import BaseFileLoader

try:
    import ezdxf
    from ezdxf.document import Drawing
except ImportError:
    print("Error: ezdxf library not found. Please install with: pip install ezdxf")
    sys.exit(1)


class DxfLoader(BaseFileLoader):
    """Class for loading and validating DXF files."""
    
    def __init__(self):
        """Initialize the DXF loader."""
        # Initialize base class with DXF-specific settings
        super().__init__(
            allowed_extensions=['.dxf'],
            description="DXF"
        )
        
        self.dxf_doc = None
        self.logger.info("DxfLoader initialized")
        
    def load_file(self, file_path=None):
        """
        Loads and validates a DXF file.
        
        Args:
            file_path: Optional path to DXF file. If not provided, will prompt for selection.
            
        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if loading was successful
                - message contains success details or error message
                - details contains the document or error information
        """
        return self.load_dxf(file_path)
    
    def load_dxf(self, file_path=None):
        """
        Loads and validates a DXF file.
        
        Args:
            file_path: Optional path to DXF file. If not provided, will prompt for selection.
            
        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if loading was successful
                - message contains success details or error message
                - details contains the document or error information
        """
        # If no path provided, prompt for file selection
        if file_path is None:
            self.logger.info("No file path provided, prompting for selection")
            file_path = self.select_file()
            
            # Check if user canceled file selection
            if not file_path:
                self.logger.warning("File selection canceled by user")
                return ErrorHandler.from_exception(
                    FileError(
                        message="File selection canceled by user",
                        severity=ErrorSeverity.WARNING
                    )
                )
        
        # Convert to Path object for consistent handling
        file_path = Path(file_path) if not isinstance(file_path, Path) else file_path
        self.file_path = file_path
        self.logger.info(f"Attempting to load DXF file: {file_path}")
        
        try:
            # Validate the file using the base class method
            success, message, details = self.validate_file(file_path)
            if not success:
                return success, message, details
            
            # Load the DXF file
            self.dxf_doc = ezdxf.readfile(file_path)
            
            # Check if modelspace contains at least one entity
            modelspace = self.dxf_doc.modelspace()
            entity_count = len(list(modelspace))
            
            if entity_count == 0:
                self.logger.error("DXF file contains no entities in modelspace")
                return ErrorHandler.from_exception(
                    FileError(
                        message="DXF file contains no entities in modelspace",
                        file_path=str(file_path),
                        severity=ErrorSeverity.ERROR,
                        details={"entity_count": 0}
                    )
                )
            
            success_msg = f"Successfully loaded DXF file: {file_path.name}"
            self.logger.info(success_msg)
            
            # Return success with document and details
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    "document": self.dxf_doc,
                    "entity_count": entity_count,
                    "file_path": str(file_path)
                }
            )
            
        except ezdxf.DXFError as e:
            error_msg = f"Error loading DXF file: {str(e)}"
            self.error_message = error_msg
            log_exception(self.logger, error_msg)
            
            return ErrorHandler.from_exception(
                FileError(
                    message=error_msg,
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error_type": "DXFError", "error": str(e)}
                )
            )
        except Exception as e:
            error_msg = f"Unexpected error loading DXF file: {str(e)}"
            self.error_message = error_msg
            log_exception(self.logger, error_msg)
            
            return ErrorHandler.from_exception(
                FileError(
                    message=error_msg,
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )

    def is_valid_dxf(self, file_path):
        """
        Validates that a file is a readable, valid DXF.
        
        Required elements:
        - Valid DXF format parsable by ezdxf
        - Contains at least one entity
        
        Note: Specific entity requirements (workpiece boundaries, 
        drilling points) are validated in their respective modules.
        
        Args:
            file_path: Path to DXF file
            
        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if validation was successful
                - message contains success or error message
                - details contains information about the validation
        """
        # Convert to Path object for consistent handling
        file_path = Path(file_path) if not isinstance(file_path, Path) else file_path
        self.logger.info(f"Validating DXF file: {file_path}")
        
        # Start with the base validation
        success, message, details = self.validate_file(file_path)
        if not success:
            return success, message, details
            
        try:
            # Try to parse with ezdxf to check format
            doc = ezdxf.readfile(file_path)
            
            # Check if modelspace contains at least one entity
            modelspace = doc.modelspace()
            entity_count = len(list(modelspace))
            
            if entity_count == 0:
                self.logger.error("DXF file contains no entities in modelspace")
                return ErrorHandler.from_exception(
                    FileError(
                        message="DXF file contains no entities in modelspace",
                        file_path=str(file_path),
                        severity=ErrorSeverity.ERROR,
                        details={"entity_count": 0}
                    )
                )
            
            valid_msg = f"DXF file is valid with {entity_count} entities"
            self.logger.info(valid_msg)
            
            return ErrorHandler.create_success_response(
                message=valid_msg,
                data={
                    "file_path": str(file_path),
                    "entity_count": entity_count,
                    "is_valid": True
                }
            )
            
        except ezdxf.DXFError as e:
            error_msg = f"Invalid DXF file format: {str(e)}"
            log_exception(self.logger, error_msg)
            
            return ErrorHandler.from_exception(
                FileError(
                    message=error_msg,
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error_type": "DXFError", "error": str(e)}
                )
            )
        except Exception as e:
            error_msg = f"Error validating DXF file: {str(e)}"
            log_exception(self.logger, error_msg)
            
            return ErrorHandler.from_exception(
                FileError(
                    message=error_msg,
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )
    
    def get_file_info(self, file_content=None):
        """
        Returns basic information about the loaded file.
        
        This implementation calls get_dxf_info which does the actual work.
        
        Args:
            file_content: Optional ezdxf document object. If None, uses previously loaded document.
            
        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if info extraction was successful
                - message contains success or error message
                - details contains the file information
        """
        return self.get_dxf_info(file_content)
    
    def get_dxf_info(self, dxf_doc=None):
        """
        Returns basic information about the DXF file.
        
        Args:
            dxf_doc: Optional ezdxf document object. If None, uses previously loaded document.
            
        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if info extraction was successful
                - message contains success or error message
                - details contains the DXF information
        """
        doc = dxf_doc if dxf_doc is not None else self.dxf_doc
        
        if doc is None:
            self.logger.warning("Attempted to get DXF info with no document loaded")
            return ErrorHandler.from_exception(
                FileError(
                    message="No DXF document loaded",
                    severity=ErrorSeverity.WARNING,
                    details={"reason": "no_document"}
                )
            )
            
        try:
            self.logger.info("Extracting DXF file information")
            
            # Get modelspace for entity analysis
            modelspace = doc.modelspace()
            
            # Count entities by type
            entity_counts = {}
            for entity in modelspace:
                entity_type = entity.dxftype()
                if entity_type not in entity_counts:
                    entity_counts[entity_type] = 0
                entity_counts[entity_type] += 1
            
            # Get layer information
            layers = {layer.dxf.name: {
                'color': layer.dxf.color,
                'linetype': layer.dxf.linetype,
                'is_on': layer.is_on
            } for layer in doc.layers}
            
            # Get filename as string if we have a Path object
            filename = self.file_path.name if isinstance(self.file_path, Path) else \
                      os.path.basename(self.file_path) if self.file_path else "Unknown"
            
            # Compile information
            info = {
                'filename': filename,
                'dxf_version': doc.dxfversion,
                'encoding': doc.encoding,
                'entity_counts': entity_counts,
                'total_entities': sum(entity_counts.values()),
                'layers': layers,
                'header_variables': len(doc.header)
            }
            
            total_entities = info['total_entities']
            self.logger.info(f"Extracted information from DXF file with {total_entities} total entities")
            
            return ErrorHandler.create_success_response(
                message=f"Successfully extracted DXF information with {total_entities} entities",
                data=info
            )
            
        except Exception as e:
            error_msg = f"Error extracting DXF information: {str(e)}"
            log_exception(self.logger, error_msg)
            
            return ErrorHandler.from_exception(
                FileError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )
    


# Example usage if run directly
if __name__ == "__main__":
    loader = DxfLoader()
    success, message, details = loader.load_dxf()
    
    if success:
        print(f"Success: {message}")
        doc = details.get("document")
        
        # Get file information
        info_success, info_message, info_details = loader.get_dxf_info(doc)
        
        if info_success:
            info = info_details
            print("\nDXF Information:")
            print(f"File: {info['filename']}")
            print(f"Version: {info['dxf_version']}")
            print(f"Total entities: {info['total_entities']}")
            print("\nEntity counts:")
            for entity_type, count in info['entity_counts'].items():
                print(f"  - {entity_type}: {count}")
            print("\nLayers:")
            for layer_name in info['layers']:
                print(f"  - {layer_name}")
        else:
            print(f"Error getting DXF info: {info_message}")
    else:
        print(f"Error: {message}")
        if "details" in details:
            print(f"Details: {details['details']}")
