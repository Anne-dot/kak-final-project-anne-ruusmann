"""
DXF Package for parsing and processing DXF files.

This package handles the parsing, extraction, and coordinate translation of DXF files
for further processing by the CNC toolchain.
"""

# Import main classes for easier access
from .parser import DXFParser
from .extractor import DXFExtractor, DrillPointExtractor, WorkpieceExtractor
from .visual_coordinate_translator import VisualCoordinateTranslator

# Define package version
__version__ = "0.1.0"