"""
GCodeProcessor package for processing and enhancing existing G-code.

This package contains modules for normalizing G-code format and adding
safety checks to movement commands.

Modules:
- gcode_normalizer: Standardizes G-code format and removes redundant coordinates
- preprocessor: Adds safety checks and variable assignments to G-code movements
"""

from .gcode_normalizer import GCodeNormalizer
from .preprocessor import GCodePreprocessor

__all__ = ["GCodeNormalizer", "GCodePreprocessor"]
