# ToolManagement System

## Purpose

The ToolManagement system is the core Python-based component of the Mach3 CNC retrofit project. It provides a modular, ADHD-friendly architecture for managing tool data, processing DXF files, and generating G-code for CNC operations.

## ADHD-Friendly Design Principles

This codebase is specifically designed to be maintainable and understandable, following these core principles:

### 1. Small, Focused Components
- Each module has ONE clear responsibility
- Functions are kept under 30-50 lines
- Clear visual separation between logical sections
- Immediate validation with descriptive error messages

### 2. Consistent Patterns
- Standardized return format: `Tuple[bool, str, Dict]` (success, message, details)
- Same import order everywhere: standard library → third-party → project modules
- Uniform error handling across all modules
- Predictable file and function naming

### 3. Visual Organization
- Clear directory structure with logical grouping
- Descriptive folder and file names
- Extensive use of docstrings and type hints
- Visual separators in code for easy scanning

### 4. No Hidden Complexity
- Explicit over implicit
- Direct approach to solving problems
- No over-engineering or premature optimization
- Clear data flow through the system

## Directory Structure

```
ToolManagement/
├── Backups/              # Automated backups of tool data
│   └── ToolData/         # Timestamped CSV backups
├── Data/                 # Primary data storage
│   └── tool-data.csv     # Main tool database (single source of truth)
├── Logs/                 # System and operation logs
├── Scripts/              # All Python code
│   ├── Backups/          # Backup management utilities
│   ├── CSVEditor/        # Simple GUI for editing tool data
│   ├── DXF/              # DXF parsing and extraction
│   ├── FileMonitor/      # File monitoring utilities
│   ├── GCode/            # DEPRECATED - see GCodeProcessor/Generator
│   ├── GCodeGenerator/   # G-code generation from processed data
│   ├── GCodeProcessor/   # G-code safety and validation
│   ├── ProcessingEngine/ # Coordinate transformation pipeline
│   ├── Tests/            # All test files and test data
│   └── Utils/            # Core utility modules (DRY principle)
└── requirements.txt      # Python dependencies
```

## Core Modules

### Utils/ - Foundation Layer
The utilities package provides core functionality used by all other modules:
- `file_utils.py` - Safe file operations with automatic backups
- `path_utils.py` - Cross-platform path handling
- `logging_utils.py` - Centralized logging system
- `error_utils.py` - Standardized error handling
- `ui_utils.py` - User interface helpers

**Key Principle**: Every module uses Utils - no direct file operations!

### DXF/ - CAD File Processing
Handles reading and extracting information from DXF files:
- `parser.py` - Low-level DXF file parsing
- `extractor.py` - Extract drilling points and workpiece boundaries
- `visual_coordinate_translator.py` - Convert from visual to machine coordinates

**Pipeline**: Parse → Extract → Translate

### ProcessingEngine/ - Coordinate Transformation
Transforms extracted data for machine use:
- `workpiece_rotator.py` - Handle workpiece rotation
- `machine_positioner.py` - Position at machine origin
- `drill_point_grouper.py` - Group operations by tool requirements

**Pipeline**: Rotate → Position → Group

### GCodeGenerator/ - Machine Code Generation
Creates G-code from processed data:
- `tool_matcher.py` - Match operations to available tools
- `machine_settings.py` - Machine-specific configurations
- Future: `generator.py` - Orchestrate G-code creation

### GCodeProcessor/ - Safety Enhancement
Ensures G-code safety and compatibility:
- `preprocessor.py` - Standardize G-code structure
- Future: `safety_enhancer.py` - Add safety checks
- Future: `validator.py` - Validate against machine limits

### CSVEditor/ - Tool Data Management
Simple GUI for editing tool data:
- MVP approach - only essential features
- Automatic backup on every change
- No complex validation (KISS principle)

## Quick Start

### Installation
```bash
pip3 install -r ToolManagement/Scripts/requirements.txt
```

### Running Tests
```bash
# Run all tests
python3 ToolManagement/Scripts/Tests/run_tests.py

# Run specific unit test
python3 -m unittest ToolManagement.Scripts.Tests.UnitTests.test_file_utils

# Run manual test
python3 ToolManagement/Scripts/Tests/ManualTests/test_dxf_processing_pipeline.py
```

### Basic Usage Example
```python
from ToolManagement.Scripts.Utils.file_utils import SafeFileHandler
from ToolManagement.Scripts.DXF.parser import DXFParser

# All file operations go through utilities
file_handler = SafeFileHandler()
success, message, data = file_handler.read_file("drawing.dxf")

if success:
    parser = DXFParser()
    parsed = parser.parse(data['content'])
```

## Code Organization Principles

### 1. DRY (Don't Repeat Yourself)
- Common functionality extracted to Utils
- Shared patterns in base classes
- Reusable helper functions

### 2. Single Source of Truth
- Configuration in one place (Utils.config)
- Tool data in one CSV file
- Constants defined once and imported

### 3. Modular Architecture
- Each module is independent
- Clear interfaces between modules
- Minimal coupling, high cohesion

### 4. Consistent Patterns
- All functions return `(success, message, details)`
- All modules follow same structure
- Error handling always the same way

## Development Guidelines

### When Adding New Features:
1. **Check if it fits existing modules** - don't create new ones unnecessarily
2. **Use utility functions** - never implement file operations directly
3. **Follow the patterns** - consistency reduces cognitive load
4. **Keep it simple** - MVP first, optimize later if needed
5. **Document as you go** - future you will thank present you

### Code Style Checklist:
- [ ] Functions under 50 lines
- [ ] Clear, descriptive names
- [ ] Type hints on all functions
- [ ] Docstrings for modules, classes, and public methods
- [ ] Visual separation between logical sections
- [ ] Consistent return format: `Tuple[bool, str, Dict]`
- [ ] Error handling with descriptive messages
- [ ] Logging for important operations

## Testing Philosophy

- **Unit tests** for individual functions
- **Manual tests** for integration and visual verification
- **Test data** in TestData/ for reproducible testing
- **Cross-platform** testing on Windows and Linux

## Related Documentation

- Main project: [../README.md](../README.md)
- Development guide: [../CLAUDE.md](../CLAUDE.md)
- Confluence docs: [../atlassian-docs/confluence_all/](../atlassian-docs/confluence_all/)
- Individual module READMEs in each Scripts/ subdirectory

## Future Enhancements

As the project grows, we maintain this structure while adding:
- New utility modules as patterns emerge
- Additional processing pipeline stages
- Enhanced safety validations
- More tool types and operations

The key is maintaining simplicity and consistency as we expand!

---

*Remember: Good code is code that your future self (or someone with ADHD) can understand at 3 AM after a long day. Keep it simple, keep it consistent, keep it working!*