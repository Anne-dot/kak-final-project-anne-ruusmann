# Utils Package

This package provides core utility modules used throughout the CNC milling project.

## Purpose

The Utils package is responsible for:
- Providing reusable functionality across all other packages
- Standardizing common operations (file handling, error management, logging)
- Ensuring cross-platform compatibility
- Maintaining consistent patterns throughout the codebase

## Modules

### `config.py`
- Centralized configuration constants and settings
- Platform-aware path handling
- Tool and G-code configuration parameters

### `error_utils.py`
- Standardized error handling and custom exceptions
- Error categorization and severity levels
- Integration with logging system

### `file_loader.py`
- Abstract base class for all file loading operations
- Common file validation and selection logic
- Platform-aware file dialogs

### `file_lock_utils.py`
- File locking mechanisms for concurrent access control
- Prevents simultaneous file modifications

### `file_utils.py`
- General file operations (read, write, backup)
- CSV file handling
- Path management

### `logging_utils.py`
- Centralized logging configuration
- Log file rotation and management
- Severity-based logging

### `path_utils.py`
- Cross-platform path handling
- Standard directory structure access
- Path validation and normalization

### `ui_utils.py`
- Platform-agnostic UI components
- File selection dialogs with fallbacks
- Terminal interaction utilities
- Message dialogs for user communication

## Implementation Approach

The Utils package follows these core principles:

### DRY (Don't Repeat Yourself)
- Centralized common functionality used across all packages
- Reusable components for file operations, error handling, and UI
- Single implementation of cross-platform compatibility logic

### Single Source of Truth
- All configuration constants in `config.py`
- Standardized error types and handling in `error_utils.py`
- Consistent return format `(success, message, data)` throughout
- Unified logging configuration in `logging_utils.py`

### Modularity
- Each utility module has a single, focused responsibility
- Clear interfaces between modules
- Minimal dependencies between utility modules
- Easy to test individual components

### ADHD-Friendly Code Organization
- Small, focused functions with clear purpose
- Consistent naming conventions across all utilities
- Visual separation between logical sections
- Comprehensive docstrings and type hints

### Cross-Platform Design
- Platform detection and appropriate fallbacks
- GUI fallbacks to CLI when needed
- Path handling that works on both Windows and Linux
- No hard-coded platform-specific assumptions

## Usage

All utility modules are designed to be imported and used throughout the project:

```python
from Utils.error_utils import FileError, ErrorHandler
from Utils.logging_utils import setup_logger
from Utils.file_utils import read_csv_file
from Utils.ui_utils import UIUtils
from Utils.config import AppConfig
```

## Standard Patterns

### Error Handling
```python
try:
    result = risky_operation()
    return ErrorHandler.create_success_response(
        "Operation completed",
        {"result": result}
    )
except Exception as e:
    return ErrorHandler.from_exception(e)
```

### File Operations
```python
# Using BaseFileLoader for consistent file handling
class MyFileLoader(BaseFileLoader):
    def __init__(self):
        super().__init__(
            allowed_extensions=['.txt'],
            description="Text"
        )
```

### Logging
```python
logger = setup_logger(__name__)
logger.info("Operation started")
logger.error("Operation failed", exc_info=True)
```

## Planned Improvements

### Architecture Refactoring
- **TODO**: Refactor `BaseFileLoader` to use `ui_utils.py` functions
  - Currently `BaseFileLoader` duplicates UI code that already exists in `ui_utils.py`
  - This will eliminate code duplication
  - Proper dependency hierarchy: FileLoaders → BaseFileLoader → ui_utils
  - Better separation of concerns between file operations and UI components

### Additional Utilities
- **TODO**: Add progress tracking utilities for long-running operations
- **TODO**: Add configuration file loading (YAML/JSON) support
- **TODO**: Add more comprehensive file validation utilities

## Boundaries

This package:
- Only provides utility functions, not business logic
- Does not depend on any other project packages
- Focuses on reusability and consistency
- Maintains backward compatibility for all public interfaces