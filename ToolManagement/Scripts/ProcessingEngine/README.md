# ProcessingEngine Package

This package handles the transformation, analysis, and optimization of drilling data between DXF extraction and G-code generation.

## Purpose

The ProcessingEngine is responsible for:
- Transforming visual coordinates into machine-specific coordinates
- Rotating workpieces to desired orientations
- Applying machine offsets based on workpiece positioning
- Grouping related drilling operations by direction and diameter

## MVP Components & Pipeline

### Key Modules & Functions

#### 1️⃣ `transformer.py`
- **rotate_clockwise_90(x, y)**
  - Simple 90° clockwise rotation: (x, y) → (y, -x)
  - Used for both point coordinates and extrusion vectors

- **rotate_point_with_extrusion(point)**
  - Rotates both position and extrusion vector
  - Preserves all other point properties

#### 2️⃣ `machine_positioner.py`
- **position_for_top_left_machine(points, point_c)**
  - Positions workpiece with top-left corner at machine origin
  - Determines offset based on point C's quadrant:
    - Q1 (x>0, y>0): offset (0, -y_c)
    - Q2 (x<0, y>0): offset (-x_c, -y_c)
    - Q3 (x<0, y<0): offset (-x_c, 0)
    - Q4 (x>0, y<0): offset (0, 0)

#### 3️⃣ `drill_point_grouper.py`
- **group_drilling_points(points)**
  - Simple grouping by diameter and direction
  - Creates a dictionary with (diameter, direction) keys
  - Adds a group_key property to each point

### Data Flow

1. **Input**: Data from DXF package
   ```
   {
     "drill_points": [...],
     "workpiece": {...}
   }
   ```

2. **Rotation** via `rotate_clockwise_90()` or multiple rotations
   ```
   # Apply 90° clockwise rotation to all points
   for point in points:
       x, y, z = point["position"]
       ex, ey, ez = point["extrusion_vector"]

       # Rotate position
       point["position"] = (y, -x, z)

       # Rotate extrusion
       point["extrusion_vector"] = (ey, -ex, ez)
   ```

3. **Machine Positioning** via `position_for_top_left_machine()`
   ```
   # Get point C (opposite corner)
   x_c, y_c = workpiece["corner_points"][2][:2]

   # Determine offset based on quadrant
   if x_c > 0 and y_c > 0:      # Q1
       offset = (0, -y_c)
   elif x_c < 0 and y_c > 0:    # Q2
       offset = (-x_c, -y_c)
   elif x_c < 0 and y_c < 0:    # Q3
       offset = (-x_c, 0)
   else:                        # Q4
       offset = (0, 0)

   # Apply offset to all points
   for point in points:
       x, y, z = point["position"]
       point["machine_position"] = (x + offset[0], y + offset[1], z)
   ```

4. **Grouping** via `group_drilling_points()`
   ```
   # Group by diameter and direction
   groups = {}

   for point in points:
       key = (point["diameter"], point["extrusion_vector"])

       if key not in groups:
           groups[key] = []

       groups[key].append(point)
       point["group_key"] = key
   ```

5. **Output**: Processed data ready for GCodeGenerator
   ```
   {
     "workpiece": {...},
     "drill_points": [...],  # With machine_position and group_key added
     "grouped_points": {...}  # Points organized by diameter and direction
   }
   ```

### OOP Implementation

While keeping the simple function logic above, the MVP will use these OOP patterns:

- **Transformer** class
  - Encapsulates rotation logic
  - Maintains stateless transformation operations
  - Provides helper methods for coordinate manipulation

- **MachinePositioner** class
  - Handles positioning logic
  - Calculates offsets based on workpiece orientation
  - Transforms all corner points consistently

- **DrillPointGrouper** class
  - Manages grouping operations
  - Creates standardized group keys
  - Maintains group metadata

- **ProcessEngine** class
  - Orchestrates the complete process
  - Validates input and output data
  - Provides a clean public API

## Data Flow Example

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
            "type": "drill_point",
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
        "machine_width": 400.0,   # Width after rotation (mm)
        "machine_height": 600.0,  # Height after rotation (mm)
        "corner_points": [        # Original corner coordinates
            (0, 0, 0),            # Origin point
            (600, 0, 0),          # Width edge
            (600, 400, 0),        # Point C
            (0, 400, 0)           # Height edge
        ],
        "machine_corner_points": [ # Transformed corner coordinates
            (0, 0, 0),             # Machine origin point
            (0, 600, 0),           # Rotated width edge
            (400, 600, 0),         # Rotated point C
            (400, 0, 0)            # Rotated height edge
        ]
    },
    "drill_points": [
        {
            "type": "drill_point",
            "position": (120.5, 85.3, 0.0),      # Original visual coordinates
            "machine_position": (85.3, 479.5, 0.0), # Machine coordinates
            "diameter": 8.0,                     # Drill bit diameter
            "depth": 15.0,                       # Drilling depth
            "extrusion_vector": (1.0, 0.0, 0.0), # Rotated direction of drilling
            "layer": "DRILL",                    # Layer from DXF
            "group_key": (8.0, (1.0, 0.0, 0.0))  # Grouping identifier
        }
        # ... more points
    ],
    "grouped_points": {
        (8.0, (1.0, 0.0, 0.0)): [  # Group by (diameter, extrusion_vector)
            # Points with 8mm diameter and X+ direction
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

## Future Enhancements (Post-MVP)

- Path optimization for efficient tool movement
- Advanced pattern recognition for drilling operations
- Safety validation for machine constraints
- Support for different machine configurations