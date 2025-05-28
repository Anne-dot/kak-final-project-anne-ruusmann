# CSV Editor GUI

A simple Tkinter-based CSV editor for tool data management in Mach3.

## Overview

This is an MVP (Minimum Viable Product) CSV editor that provides a graphical interface for editing the tool-data.csv file. It automatically creates a backup when opened and allows basic editing operations.

## Features

- **Automatic Backup**: Creates a timestamped backup using existing BackupManager when the editor opens
- **Simple Table View**: Edit CSV data in a spreadsheet-like interface
- **Add/Delete Rows**: Basic row management
- **Direct Save**: Overwrites the original file (backup already created)

## Requirements

- Python 3.x
- tkinter (usually comes with Python)
- Existing project modules from parent directories

## Usage

```bash
cd ToolManagement/Scripts/CSVEditor
python csv_editor_gui.py
```

## Workflow

1. Launch the editor
2. Automatic backup is created (using BackupManager)
3. tool-data.csv is loaded automatically
4. Edit data in the table
5. Click "Save" to overwrite the original file
6. Close the editor

## File Structure

```
CSVEditor/
├── __init__.py
├── csv_editor_gui.py    # Main GUI application
└── README.md           # This file
```

## Design Principles

- **Simple is Better**: No validation, no complex features
- **MVP Focus**: Only essential functionality
- **Use Existing Code**: Leverages Utils and Backup modules
- **Linear Code**: Easy to read and understand
- **No Over-Engineering**: Direct approach to solving the problem

## Code Structure Following Project Standards

### Module Dependencies

This module follows the same import patterns as other project modules:

```python
# Standard library imports
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add parent directory to path (same pattern as other modules)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Project imports
from Utils.file_utils import SafeFileHandler
from Utils.path_utils import PathManager  
from Utils.logging_utils import setup_logger
from Utils.error_utils import FileOperationError, ErrorHandler
from Backups.backup_manager import BackupManager
```

### Error Handling Pattern

Following the project's standardized return format:

```python
def load_csv(self) -> Tuple[bool, str, Dict]:
    """
    Load CSV file following project patterns.
    
    Returns:
        Tuple[bool, str, Dict]: (success, message, details)
    """
    try:
        # Implementation
        return True, "CSV loaded successfully", {"rows": len(data)}
    except FileOperationError as e:
        self.logger.error(f"Failed to load CSV: {str(e)}")
        return False, str(e), {}
```

### File Operations

All file operations follow the project's established patterns:

- File reading through `SafeFileHandler` from Utils
- Path resolution through `PathManager.get_tool_data_path()`
- No direct `open()` calls in the main code
- Proper error propagation using project's error classes

### Logging

Uses the project's centralized logging system:

```python
class CSVEditor:
    def __init__(self):
        # Set up logging using project standards
        self.logger = setup_logger(__name__)
        self.logger.info("CSV Editor initialized")
```

### GUI Error Display

Error messages are shown to users while also being logged:

```python
def show_error(self, message: str):
    """Show error to user and log it."""
    self.logger.error(message)
    messagebox.showerror("Error", message)
```

## MVP Limitations

- No data validation (user responsibility)
- No undo/redo functionality
- No sorting or filtering  
- No concurrent access handling (file_lock_utils not used in MVP)
- Single file only (tool-data.csv)
- Desktop use only (minimum 1200px width)

## Integration with Existing Systems

- Uses same CSV file as VBScript macros (`LoadToolData.m1s`)
- Compatible with existing backup rotation system
- Logs integrate with project's centralized logging
- Follows same error handling patterns as other Python modules

## Notes

This tool is designed for occasional manual editing of tool data. For automated or frequent updates, use the existing VBScript macros or Python scripts in the project.