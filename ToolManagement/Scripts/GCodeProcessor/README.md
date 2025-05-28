# GCodeProcessor Package

This package processes existing G-code files for safety and standardization.

> **Note**: This document is up for further review and analysis to determine the final MVP scope.

## Purpose

The GCodeProcessor is responsible for:
- Processing G-code from various sources (Vectric, manual) to a standard format
- Adding safety checks and commands to ensure safe machine operation
- Validating G-code against machine constraints and limitations
- Formatting G-code for specific machine controllers

## Processing Pipeline

1. **Loading**: Load G-code from file
2. **Processing**: Convert to standard format and structure
3. **Safety Enhancement**: Add safety variables and M150 calls
4. **Validation**: Ensure code meets machine constraints
5. **Formatting**: Apply machine-specific formatting

## Core Modules (MVP)

### `processor.py`
- Standardize G-code structure and commands
- Normalize coordinate formats
- Ensure consistent decimal precision
- Standardize feed rates and speeds

### `safety_enhancer.py`
- Add safety variables (#600-#603)
- Add M150 safety macro calls
- Track movement types (G00/G01)
- Track axis movements (X,Y,Z)

### `validator.py`
- Validate against machine constraints
- Check speeds and feeds
- Verify within machine work envelope
- Ensure proper command sequences

### `formatter.py`
- Format for specific controller requirements
- Add machine-specific headers/footers
- Apply consistent line numbering
- Format comments appropriately

## Planned Improvements

### File Loading Architecture
- **TODO**: Implement `GCodeFileLoader` class inheriting from `BaseFileLoader`
  - Consistent file handling across the project
  - Automatic validation and error handling
  - Platform-aware file selection
  - Standardized logging
  - This will allow GCodeProcessor to focus solely on G-code processing logic

## Data Flow

Input:
```
Raw G-code from Vectric or manual source
G00X10Y20
G01Z-5F100
...
```

Output:
```
Processed, safe G-code ready for machine
(Header with safety initialization)
G00 X10 Y20 Z5 (Rapid to position with safe Z)
#600 = 1 (G1 mode)
#601 = 0 (X no movement)
#602 = 0 (Y no movement)
#603 = 1 (Z movement)
M150 (Safety check)
G01 Z-5 F100 (Controlled feed into material)
...
(Safety checks and footer)
```

## Boundaries

This package:
- Only processes existing G-code files
- Does not generate G-code from scratch (handled by GCodeGenerator)
- Focuses on safety and standardization, not creation