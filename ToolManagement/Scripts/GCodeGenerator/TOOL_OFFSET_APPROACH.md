# Tool Offset Approach for Horizontal Drilling

## Overview

This document describes the MVP approach for handling tool offsets in the horizontal drilling system.

## Key Decisions

### 1. Tool Change Handles Offsets

The m6start macro is responsible for:
- Moving to safe tool change height (TOOL_CHANGE_HEIGHT = 50 in machine coordinates)
- Applying tool offsets via G52 for X, Y, and Z positioning

### 2. Offset Calculation in m6start

For each horizontal drill tool, offsets are calculated and applied:

```vbscript
' Example: Tool 22 (Y+ direction)
toolLength = 150      ' Physical tool length
tooltipZOffset = 5    ' Distance from holder to tooltip  
holderYOffset = 75    ' Holder offset in drilling direction

' Calculate and apply offsets
xOff = toolSpaceX * 3
yOff = (toolSpaceY * -2) - holderYOffset - toolLength

' Apply all offsets including Z
Code("G52 X" & xOff & "Y" & yOff & "Z" & tooltipZOffset)
```

### 3. G-code Drilling Sequence

The G-code generator uses simple, consistent sequences:

```gcode
G53 G00 Z50     ; Safe height (machine coordinates)
G00 X100 Y200   ; Position at drill start location X,Y (work coords + offsets)
G00 Z9          ; Lower to drilling depth
G91             ; Switch to incremental mode
G01 Y15 F100    ; Drill forward (drilling depth + safety margin)
G01 Y-15 F300   ; Retract back to start position
G90             ; Return to absolute mode
G53 G00 Z50     ; Return to safe height (machine coordinates)
```

## How Coordinates Work

1. **G53 moves**: Always in machine coordinates, ignoring all offsets
2. **Regular moves**: Use active work coordinate system (G54-G59) plus G52 offsets
3. **G52 offsets**: Applied by m6start, affect all non-G53 moves
4. **Incremental drilling**: G91/G90 for simple in/out movement

## Benefits of This Approach

1. **Separation of Concerns**
   - m6start handles tool-specific offsets
   - G-code focuses on drilling movements
   - No complex calculations in G-code

2. **Safety**
   - Consistent safe height using machine coordinates
   - Tool change always at known safe position
   - Simple, predictable movements

3. **Simplicity**
   - No M151 macro needed for MVP
   - Straightforward incremental drilling
   - Easy to understand and debug

## MVP Implementation Status

### Hardcoded Values (To Be Measured)
- `TOOL_CHANGE_HEIGHT = 50` (in m6start macro)
- Tool-specific offsets in each Case statement
- Example drilling depth Z9
- All marked with TODO comments

### Testing Notes
- Verify G52 offset behavior with actual machine
- Confirm safe heights clear all fixtures
- Test incremental drilling distances
- Validate retract speeds

This MVP approach prioritizes working code over optimization, following the KISS principle while maintaining safety and clarity.