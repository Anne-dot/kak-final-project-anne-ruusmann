"""
ProcessingEngine package for CNC drilling operations.

This package handles the transformation, analysis, and optimization
of extracted DXF data to prepare it for G-code generation.
"""

# Import key components to make them available at package level
from .workpiece_rotator import WorkpieceRotator
from .machine_positioner import MachinePositioner
from .drill_point_grouper import DrillPointGrouper