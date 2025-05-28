M6START.M1S REFACTORING RECOMMENDATIONS
=======================================

This document outlines recommendations for refactoring m6Start.m1s to follow DRY principles,
improve modularity, and enhance ADHD-friendly organization within Mach3 VBScript limitations.

CURRENT STRUCTURE IMPROVEMENTS IMPLEMENTED
==========================================
✓ Added clear visual section headers with ASCII art dividers
✓ Organized code into logical sections:
  - Variable Declarations
  - Configuration Constants
  - Initialization & Signal Reset
  - Tool Retrieval & Storage
  - Position Variable Initialization
  - Tool Position Calculation
  - Tool Movement Execution
  - Signal Activation
  - Tool State Update
  - Tool Data Synchronization

RECOMMENDED CONSTANTS TO ADD
============================
1. DRO Numbers (currently hardcoded):
   - DRO_TOOL_PASSING = 1899  ' DRO for inter-macro tool number passing
   - DRO_TOOL_CHANGE_SUCCESS = 824  ' DRO to check if tool change successful

2. Timing Constants (milliseconds):
   - DELAY_SIGNAL_RESET = 1000
   - DELAY_AFTER_POSITION = 500
   - DELAY_MOVEMENT_CHECK = 100
   - DELAY_AFTER_EXPAND = 200

3. Tool Range Constants:
   - M1_TOOL_START = 1
   - M1_TOOL_END = 10
   - M2_TOOL_START = 11
   - M2_TOOL_END = 20
   - M3_TOOL_NUMBER = 21

DRY PRINCIPLE VIOLATIONS TO ADDRESS
===================================
1. Tool Position Pattern Recognition
   - Tools 22-36 follow clear mathematical patterns
   - Currently each tool has explicit case statement
   - Solution: Calculate positions using pattern formulas

2. Bit Signal Activation Pattern
   - Repeated If statements for each bit
   - Solution: Loop through bits using bit manipulation

3. Magazine Selection Logic
   - Scattered across multiple case statements
   - Solution: Centralize magazine determination logic

MODULARIZATION STRATEGIES (Within VBScript Limitations)
=======================================================
Since Mach3 doesn't support functions/subroutines, use #expand directives:

1. Create Helper Macro Files:
   - ToolPositionCalculator.m1s
     * Input: Tool number from DRO
     * Output: xOff, yOff values in DROs
     * Logic: Pattern-based position calculation
   
   - SignalManager.m1s
     * Handles all signal activation/deactivation
     * Uses bit manipulation for muxOut signals
     * Centralizes magazine signal logic
   
   - ToolValidator.m1s
     * Validates tool numbers
     * Sets error flags in DROs
     * Provides consistent error messaging

2. Data Exchange via DROs:
   - Use designated DRO ranges for inter-macro communication
   - Example: DROs 1890-1899 for temporary calculation values

ADHD-FRIENDLY IMPROVEMENTS
==========================
1. Visual Clarity:
   - Add blank lines between logical blocks
   - Use consistent indentation (tabs)
   - Add inline comments for complex calculations
   - Group related constants together

2. Cognitive Load Reduction:
   - Break Select Case into smaller logical groups:
     * Tool 0 (no tool)
     * Tools 1-20 (Magazine 1 & 2)
     * Tool 21 (Magazine 3)
     * Tools 22-36 (Pattern-based tools)
     * Special cases (37, 42, 48)
     * Error handling

3. Pattern Documentation:
   - Add ASCII art diagrams showing tool layouts
   - Document the mathematical patterns clearly
   - Example:
     ' Tool Layout Pattern (22-36):
     ' Base Pattern: X = toolSpaceX * multiplier
     '               Y = toolSpaceY * offset
     ' Tool 22: X=3*32, Y=-2*32, mux=1
     ' Tool 23: X=2*32, Y=-3*32, mux=2
     ' ...

CRITICAL TOOL NUMBERING ISSUE
=============================
**IMPORTANT**: The current case numbering does not properly handle horizontal drilling tools.

Horizontal Tool Requirements:
- Each horizontal tool position has 2 drills mounted in opposite directions
- These paired drills need consecutive tool numbers for logical operation
- Current implementation doesn't separate or pair these tools correctly
- This separation was previously implemented but lost due to code loss

Example of Correct Pairing:
- Tool 22: Horizontal drill facing direction 1
- Tool 23: Horizontal drill facing direction 3 (opposite of tool 22)
- Tool 24: Next horizontal position, direction 1
- Tool 25: Same position as 24, direction 3

This pairing is critical for:
- Efficient tool changes between opposite drilling operations
- Clear operator understanding of tool relationships
- Proper G-code generation for horizontal drilling sequences

IMPLEMENTATION PRIORITIES
=========================
1. High Priority:
   - Fix horizontal tool numbering to group paired drills
   - Add missing constants for DROs and delays
   - Document tool position patterns
   - Improve error messages

2. Medium Priority:
   - Create SignalManager.m1s for signal handling
   - Implement pattern-based position calculation
   - Add validation for tool ranges

3. Low Priority:
   - Create visual tool layout documentation
   - Optimize timing delays
   - Add debug mode with extra logging

EXAMPLE REFACTORED STRUCTURE
============================
' === TOOL POSITION CALCULATION ===
' Pattern-based tools (22-36)
If tool >= 22 And tool <= 36 Then
    ' Calculate position based on pattern
    ' Tools follow a specific layout pattern
    Select Case tool
        Case 22 To 27  ' First column pattern
            xOff = toolSpaceX * 2
            yOff = toolSpaceY * (tool - 25)
            muxOut = tool - 21
        Case 28 To 36  ' Second column pattern
            xOff = toolSpaceX * -(tool - 27)
            yOff = toolSpaceY * IIf(tool = 28 Or tool = 37, -1, 0)
            muxOut = tool - 21
    End Select
End If

TESTING CONSIDERATIONS
======================
1. Create test macros for each refactored component
2. Test boundary conditions (tool 0, 1, 10, 11, 20, 21, etc.)
3. Verify signal activation/deactivation sequences
4. Test error handling for invalid tool numbers
5. Ensure timing is adequate for physical tool changes

NOTES ON VBSCRIPT LIMITATIONS
=============================
- No user-defined functions or subroutines
- No classes or objects
- Limited string manipulation
- Must use #expand for code reuse
- Communication between macros via DROs or files
- Error handling limited to On Error Resume Next