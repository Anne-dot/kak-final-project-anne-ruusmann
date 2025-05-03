"""
Package name: GCode
Purpose: G-code generation for CNC horizontal drilling operations.

This package contains modules for generating safe and efficient G-code
from drilling point data, applying safety constraints, and integrating
with the machine tool data system.

Modules:
- code_generator.py: Core G-code generation functionality
- safety_checker.py: Implements safety constraints
- tool_validator.py: Validates tool compatibility
- path_planner.py: Plans safe and efficient tool paths
- drilling_operations.py: Specialized horizontal drilling code generation
- preprocessor.py: G-code preprocessing and enhancement
- formatter.py: G-code formatting and organization
- gcode_normalizer.py: G-code standardization and normalization

References:
- MRFP-80: DXF to G-code Generation Epic
- Preprocessor Safety Check Requirements (knowledge base)
- DRO to G-Code Variables Mapping (knowledge base)
"""

# Import key items to make them available at package level
from .code_generator import GcodeGenerator
from .gcode_normalizer import GCodeNormalizer
from .safety_checker import SafetyChecker
from .file_loader import GCodeLoader

# Define publicly available items
__all__ = [
    'GcodeGenerator',
    'GCodeNormalizer',
    'SafetyChecker',
    'GCodeLoader'
]

# Note: Additional classes and functions will be added to exports
# as they are implemented in their respective modules