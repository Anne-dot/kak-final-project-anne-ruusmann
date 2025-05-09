"""
Package name: DXF
Purpose: DXF file processing for CNC horizontal drilling.

This package contains modules for reading and processing DXF files,
extracting drilling points, and preparing data for G-code generation.

Modules:
- file_loader.py: Loading and validating DXF files
- workpiece_extractor.py: Extracting workpiece geometry
- drilling_extractor.py: Finding drilling points and parameters
- drilling_analyzer.py: Analyzing drilling point patterns
- entity_processor.py: Processing different entity types
- geometry.py: Geometric calculations
- coordinate_transformer.py: Coordinate transformations
- tool_path_generator.py: Generate optimized tool paths

Conventions:
- Z-coordinate values in DXF entities determine the drilling edge:
  - Z values near 0: FRONT edge (drilling direction Y+)
  - Z values near -555: BACK edge (drilling direction Y-)

References:
- MRFP-80: DXF to G-code Generation Epic
- Python Code Structure and Organization (knowledge base)
"""

# Import key items to make them available at package level
from .file_loader import DxfLoader
from .workpiece_extractor import WorkpieceExtractor
from .drilling_extractor import DrillingExtractor
from .drilling_analyzer import DrillPointAnalyzer, DrillPointClassifier
from .coordinate_transformer import CoordinateTransformer
from .tool_path_generator import ToolPathGenerator

# Define publicly available items
__all__ = [
    'DxfLoader',
    'WorkpieceExtractor',
    'DrillingExtractor',
    'DrillPointAnalyzer',
    'DrillPointClassifier',
    'CoordinateTransformer',
    'ToolPathGenerator'
]