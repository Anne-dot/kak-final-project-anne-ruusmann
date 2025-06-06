# ProcessingEngine Package

This package handles the transformation, analysis, and optimization of drilling data between DXF extraction and G-code generation.

## Purpose

The ProcessingEngine is responsible for:
- Transforming visual coordinates into machine-specific coordinates
- Rotating workpieces to desired orientations
- Applying machine offsets based on workpiece positioning
- Grouping related drilling operations by direction and diameter

## MVP Components & Pipeline

### Key Modules & Classes

#### 1️⃣ `workpiece_rotator.py`
- **WorkpieceRotator** class
  - Handles rotation of workpieces and drilling points
  - Stateless coordinate transformation
  - Derives orientation from point C position
  - Methods:
    - `rotate_coordinates_90(x, y)` - Rotates a single coordinate pair
    - `rotate_point_90(point)` - Rotates a drill point's position and extrusion vector
    - `transform_drilling_data(data)` - Processes complete drilling data

#### 2️⃣ `machine_positioner.py`
- **MachinePositioner** class
  - Positions workpiece with top-left corner at machine origin
  - Calculates offsets based on point C's quadrant
  - Stores original points alongside machine-positioned points
  - Methods:
    - `position_for_top_left_machine(data)` - Main positioning method
    - `_determine_offset(x_c, y_c)` - Calculates offset based on quadrant rules:
      - If x_c < 0: Apply -x_c offset in X direction
      - If y_c > 0: Apply -y_c offset in Y direction

#### 3️⃣ `drill_point_filter.py`
- **DrillPointFilter** class
  - Filters drill points based on machine capabilities
  - MVP: Removes vertical drilling operations (Z+ direction)
  - Preserves all horizontal drilling (X+, X-, Y+, Y-)
  - Methods:
    - `filter_for_horizontal_drilling(data)` - Main filtering method

#### 4️⃣ `drill_point_grouper.py`
- **DrillPointGrouper** class
  - Simple grouping by diameter and direction
  - Creates a dictionary with (diameter, direction) keys
  - Adds a group_key property to each point
  - Methods:
    - `group_drilling_points(data)` - Main grouping method

### Pipeline Architecture

The ProcessingEngine modules form a straightforward pipeline:

1. **Input**: Data from DXF package with visual coordinates
2. **Rotation** (optional): Apply rotation via `WorkpieceRotator`
3. **Positioning**: Apply machine offsets via `MachinePositioner`
4. **Filtering**: Filter for horizontal drilling via `DrillPointFilter` (MVP)
5. **Grouping**: Group drill points via `DrillPointGrouper`
6. **Output**: Processed data ready for GCodeGenerator

### Key Design Decisions

1. **Modular, Stateless Design**
   - All modules operate independently without internal state
   - Modules can be used individually or in a pipeline
   - All modules follow the same interface pattern with `(success, message, data)` return values

2. **Consistent Data Flow**
   - All data passes through each module in the same structure
   - Each module enriches the data without destroying previous information
   - Original coordinates preserved alongside transformed coordinates

3. **Strict Validation**
   - All modules perform strict validation of inputs
   - Missing required data causes immediate failure with clear messages
   - No skipping of invalid points - fails fast to prevent incorrect machining

4. **ADHD-Friendly Implementation**
   - Simple, focused methods with clear visual separation
   - Methods kept under 50 lines for readability
   - Descriptive naming indicating purpose

### Data Flow Example

Input from DXF package:
```python
{
    "workpiece": {
        "width": 600.0,           # Workpiece width (mm)
        "height": 400.0,          # Workpiece height (mm)
        "thickness": 18.0,        # Workpiece thickness (mm)
        "corner_points": [        # Corner coordinates
            (0, 0, 0),            # Origin point
            (600, 0, 0),          # Width edge
            (600, 400, 0),        # Point C (opposite corner)
            (0, 400, 0)           # Height edge
        ]
    },
    "drill_points": [
        {
            "position": (120.5, 85.3, 0.0),      # Visual coordinates
            "diameter": 8.0,                     # Drill bit diameter
            "depth": 15.0,                       # Drilling depth
            "extrusion_vector": (0.0, 0.0, 1.0), # Direction of drilling
            "layer": "DRILL"                     # Layer from DXF
        }
        # ... more points
    ]
}
```

Output to GCode package:
```python
{
    "workpiece": {
        "width": 600.0,           # Original width (mm)
        "height": 400.0,          # Original height (mm)
        "thickness": 18.0,        # Thickness (mm)
        "width_after_rotation": 400.0,   # Width after rotation (mm)
        "height_after_rotation": 600.0,  # Height after rotation (mm)
        "corner_points": [        # Original corner coordinates
            (0, 0, 0),            # Origin point
            (0, 400, 0),          # Rotated width edge
            (600, 400, 0),        # Point C (opposite corner)
            (600, 0, 0)           # Height edge
        ],
        "machine_corner_points": [ # Transformed corner coordinates
            (0, 0, 0),             # Machine origin point
            (0, 400, 0),           # Corner point
            (600, 400, 0),         # Corner point
            (600, 0, 0)            # Corner point
        ],
        "machine_offset": (0, 0)   # Applied offset
    },
    "drill_points": [
        {
            "position": (120.5, 85.3, 0.0),       # Original visual coordinates
            "original_position": (120.5, 85.3, 0.0), # Original position after rotation
            "machine_position": (120.5, 85.3, 0.0),  # Machine coordinates
            "diameter": 8.0,                      # Drill bit diameter
            "depth": 15.0,                        # Drilling depth
            "extrusion_vector": (0.0, 0.0, 1.0),  # Direction of drilling
            "layer": "DRILL",                     # Layer from DXF
            "group_key": (8.0, (0.0, 0.0, 1.0))   # Grouping identifier
        }
        # ... more points
    ],
    "grouped_points": {
        (8.0, (0.0, 0.0, 1.0)): [  # Group by (diameter, extrusion_vector)
            # Points with 8mm diameter and Z+ direction
        ],
        # ... more groups
    }
}
```

## Boundaries

This package:
- Only handles coordinate transformations, not G-code generation
- Takes data from the DXF package and prepares it for the GCode package
- Focuses on drilling operations for CNC machining
- Supports only rectangular workpieces in the MVP

## Future Enhancements (Post-MVP)

- Path optimization for efficient tool movement
- Advanced pattern recognition for drilling operations
- Safety validation for machine constraints
- Support for different machine configurations
- Support for non-rectangular workpieces