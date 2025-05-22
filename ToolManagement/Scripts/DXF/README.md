# DXF Package

This package handles the parsing, extraction, and coordinate translation of DXF files.

## Purpose

The DXF package is responsible for:
- Parsing DXF files into structured representations
- Extracting relevant entities (drill points, workpiece boundaries)
- Translating coordinates to match physical machining requirements for horizontal drilling

## Components & Implementation

### Key Modules & Classes

#### 1️⃣ `parser.py`
- Handles loading and parsing DXF files using the ezdxf library
- Provides validation and error handling for different DXF versions
- Returns structured document objects for further processing

#### 2️⃣ `extractor.py`
Contains three main classes:

- **DrillPointExtractor**
  - Extracts drilling operations from various entity types
  - Specializes in identifying circles, points, and inserts that represent drill points
  - Extracts parameters like diameter and depth from layer names using regex patterns
  - Validates drilling parameters and provides detailed error reporting

- **WorkpieceExtractor**
  - Identifies workpiece boundaries from polylines on specific layers
  - Extracts dimensions and coordinates from boundary entities
  - Extracts thickness information from layer naming conventions

- **DXFExtractor**
  - Coordinates the extraction process using the specialized extractors
  - Combines results into a unified data structure
  - Provides comprehensive validation and error handling

#### 3️⃣ `visual_coordinate_translator.py`
- **VisualCoordinateTranslator** class
  - Transforms DXF coordinates to physical machine coordinates
  - Specialized handling for both X-direction and Y-direction horizontal drilling
  - Applies workpiece dimension-aware transformations
  - Preserves original coordinates alongside translated ones for debugging

### Data Structures

Instead of formal class hierarchies, the implementation uses dictionary-based data structures:

1. **Drill Point**
   ```python
   {
     "position": (x, y, z),           # Coordinates in DXF space
     "diameter": float,               # Drill bit diameter in mm
     "depth": float,                  # Drilling depth in mm
     "direction": (dx, dy, dz),       # Direction vector
     "layer": str,                    # Source layer name
     "entity_type": str               # Type of source entity
   }
   ```

2. **Workpiece**
   ```python
   {
     "corner_points": [(x, y, z), ...],  # Corner coordinates
     "width": float,                      # Width in mm
     "height": float,                     # Height in mm
     "thickness": float,                  # Thickness in mm
     "layer": str,                        # Source layer name
     "entity_type": str                   # Type of source entity
   }
   ```

3. **Translated Drill Point**
   ```python
   {
     "position": (x, y, z),           # Transformed coordinates for machine
     "original_position": (x, y, z),  # Original DXF coordinates
     "diameter": float,               # Drill bit diameter
     "depth": float,                  # Drilling depth
     "direction": (dx, dy, dz),       # Direction vector
     "layer": str                     # Source layer
   }
   ```

### Data Flow

1. **Input**: DXF file path
   ```
   "/path/to/drawing.dxf"
   ```

2. **Parse** via DXF parser
   ```
   Document object with raw DXF entities
   ```

3. **Extract** via specialized extractors
   ```
   - Workpiece boundary and dimensions
   - List of drill points with parameters
   ```

4. **Translate** via VisualCoordinateTranslator
   ```
   Drill points with machine-appropriate coordinates
   ```

5. **Output**: Structured data ready for ProcessingEngine
   ```python
   {
     "drill_points": [
       {
         "position": (120.5, 85.3, 22.5),        # Machine coordinates
         "original_position": (542.0, -9.5, 0.0), # Original DXF coordinates
         "diameter": 8.0,
         "depth": 15.0,
         "direction": (1.0, 0.0, 0.0)            # X+ direction
       },
       # more points...
     ],
     "workpiece": {
       "width": 600.0,
       "height": 400.0,
       "thickness": 18.0,
       "corner_points": [(0,0,0), (600,0,0), (600,400,0), (0,400,0)]
     }
   }
   ```

### Pipeline Execution

```
DXFParser.parse(file_path)
  ↓
DXFExtractor.process(document)
  ├─ WorkpieceExtractor.extract(document)
  └─ DrillPointExtractor.extract(document)
  ↓
VisualCoordinateTranslator.translate_coordinates(drill_points, workpiece)
  ↓
Return processed data structure to ProcessingEngine
```

## Implementation Approach

The DXF package follows these core principles:

### DRY (Don't Repeat Yourself)
- Leverages the Utils package for common functionality
- Uses specialized extractors for different entity types
- Centralizes parameter extraction logic

### Single Source of Truth
- Utilizes ErrorHandler from Utils for consistent error responses
- Standardized return format (success, message, data) throughout
- Uses validator functions to ensure data integrity

### Modularity
- Clear separation of concerns between modules
- Well-defined interfaces between components
- Each module has a single, focused responsibility

### ADHD-Friendly Code Organization
- Small, focused methods with clear visual separation
- Consistent naming conventions and patterns
- Proper type annotations for better IDE support
- Extensive logging for debugging

### OOP and Functional Principles
- Encapsulation of extraction logic in specialized classes
- Pure functions for coordinate transformations
- Immutable data handling (copying rather than modifying)

### Utils Package Integration
- Uses Utils.error_utils for standardized error handling
- Leverages Utils.logging_utils for consistent logging
- Follows established patterns in the codebase

## Boundaries

This package only handles DXF parsing and coordinate translation. It does not:
- Perform machine-specific path planning (handled by ProcessingEngine)
- Generate G-code (handled by GCodeGenerator package)
- Perform safety validation (handled by safety modules)