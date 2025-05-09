# DXF Package

This package handles the parsing, extraction, and coordinate translation of DXF files.

## Purpose

The DXF package is responsible for:
- Parsing DXF files into structured representations
- Extracting relevant entities (drill points, workpiece boundaries, etc.)
- Translating coordinates to match what's visually seen in production drawings

## MVP Components & Pipeline

### Key Modules & Classes

#### 1️⃣ `parser.py`
- **DXFParser** class (extends BaseFileLoader)
  - **parse(file_path)** → Takes file path, returns Document
  - Validates DXF files
  - Handles exceptions with Utils.error_utils

#### 2️⃣ `entities.py`
- **DXFEntity** (abstract base class)
  - **validate()** → Checks entity validity
  - **to_dict()** → Serializes to dictionary

- **DrillPoint** (extends DXFEntity)
  - **position**: (x, y, z) coordinates
  - **diameter**: Drill bit diameter
  - **depth**: Drilling depth
  - **extrusion_vector**: Drilling direction
  - **layer**: Source layer name

- **Workpiece** (extends DXFEntity)
  - **width**, **height**, **thickness**: Dimensions
  - **corner_points**: List of corner coordinates
  - **dimensions**: Property returning (width, height, thickness)

#### 3️⃣ `extractor.py`
- **DXFExtractor** class
  - **extract_drill_points(document)** → Finds drill entities
  - **extract_workpiece(document)** → Identifies workpiece boundaries
  - Uses pattern matching to extract properties from layers

#### 4️⃣ `visual_coordinate_translator.py`
- **VisualCoordinateTranslator** class
  - **translate_coordinates(points, workpiece)** → Converts to visual space
  - Ensures coordinates match what's seen in the drawing

### Data Flow

1. **Input**: DXF file path
   ```
   "/path/to/drawing.dxf"
   ```

2. **Parse** via `DXFParser.parse()`
   ```
   Document object with raw DXF entities
   ```

3. **Extract** via `DXFExtractor.extract_drill_points()`
   ```
   List of DrillPoint objects with properties
   ```

4. **Translate** via `VisualCoordinateTranslator.translate_coordinates()`
   ```
   DrillPoint objects with visually correct coordinates
   ```

5. **Output**: Structured data ready for ProcessingEngine
   ```
   {
     "drill_points": [
       {
         "position": (120.5, 85.3, 0.0),
         "diameter": 8.0,
         "depth": 15.0,
         "extrusion_vector": (0, 0, 1)
       },
       // more points...
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
process_dxf_file(file_path)
  ↓
DXFParser.parse(file_path)
  ↓
DXFExtractor.extract_drill_points(document)
  ↓
DXFExtractor.extract_workpiece(document) [optional]
  ↓
VisualCoordinateTranslator.translate_coordinates(points, workpiece)
  ↓
Return processed data structure
```

## Implementation Approach

The DXF package follows these core principles:

### DRY (Don't Repeat Yourself)
- Leverages the Utils package for common functionality
- Uses abstract base classes for shared entity behavior
- Centralizes configuration and constants

### Single Source of Truth
- Utilizes ErrorHandler from Utils for consistent error responses
- Relies on centralized configuration in Utils.config
- Provides unified entity representations

### Modularity
- Clear separation of concerns between modules
- Well-defined interfaces between components
- Each module has a single, focused responsibility

### ADHD-Friendly Code Organization
- Small, focused methods with clear visual separation
- Consistent naming conventions and patterns
- Proper type annotations for better IDE support

### OOP Best Practices
- Clean class hierarchy with proper inheritance
- Strong encapsulation of implementation details
- Composition over inheritance where appropriate

### Utils Package Integration
- Uses Utils.error_utils for standardized error handling
- Leverages Utils.logging_utils for consistent logging
- Extends BaseFileLoader for DXF file operations
- Follows established patterns in the codebase

## Boundaries

This package only handles DXF parsing and initial data extraction. It does not:
- Perform machine-specific transformations (handled by ProcessingEngine)
- Generate G-code (handled by GCode package)