# Mach3 VBScript Functionality Testing

## Overview
This folder contains comprehensive VBScript tests for validating Mach3 R3.043.22 functionality. Tests validate both working features and confirm non-working functions fail as expected.

## Test Organization

### InitialTests/ShouldPass/ (44 tests)
Tests that should execute successfully:

**Basic VBScript Features (Tests 1-10)**
- `test_01_dim_variable.m1s` - Variable declaration with Dim
- `test_02_multiple_dim.m1s` - Multiple variable declarations
- `test_03_constants.m1s` - Const keyword functionality
- `test_04_variant_type.m1s` - Variant type behavior
- `test_05_if_then.m1s` - If-Then conditional statements
- `test_06_select_case.m1s` - Select Case statements
- `test_07_for_next.m1s` - For-Next loops
- `test_08_while_wend.m1s` - While-Wend loops
- `test_09_do_loop.m1s` - Do-Loop statements
- `test_10_exit_for.m1s` - Exit For statement

**String Functions (Tests 11-14)**
- `test_11_string_len.m1s` - Len() function
- `test_12_string_left_right.m1s` - Left() and Right() functions
- `test_13_string_mid.m1s` - Mid() function
- `test_14_string_instr.m1s` - InStr() function

**Arrays & Error Handling (Tests 16-17, 19)**
- `test_16_array_static.m1s` - Static array declaration
- `test_17_array_redim.m1s` - ReDim and ReDim Preserve
- `test_19_error_handling.m1s` - On Error Resume Next
- `test_on_error_resume_next.m1s` - Detailed error handling validation

**File Operations (Tests 23-32)**
- `test_23_create_object.m1s` - CreateObject("Scripting.FileSystemObject")
- `test_24_set_keyword.m1s` - Set keyword for objects
- `test_25_file_exists.m1s` - FileExists() method
- `test_26_create_text_file.m1s` - CreateTextFile() method
- `test_27_getmainfolder.m1s` - GetMainFolder() function
- `test_28_open_text_file.m1s` - OpenTextFile() method
- `test_29_read_all.m1s` - ReadAll() method
- `test_30_atendofstream.m1s` - AtEndOfStream property
- `test_31_append_file.m1s` - Appending to files
- `test_32_folder_exists.m1s` - FolderExists() method

**Math & Type Functions (Tests 33-36)**
- `test_33_math_functions.m1s` - Mathematical functions (Sin, Cos, Sqrt, etc.)
- `test_34_type_checking.m1s` - Type checking (IsNumeric, IsArray, etc.)
- `test_35_type_conversion.m1s` - Type conversion (CInt, CDbl, CStr, etc.)
- `test_36_timer_function.m1s` - Timer() function

**Mach3-Specific Functions (Tests 39-44 + others)**
- `test_39_expand_directive.m1s` - #expand preprocessor directive
- `test_40_getoemdro.m1s` - GetOEMDRO() for reading DROs
- `test_41_setuserdro.m1s` - SetUserDRO() for user DROs
- `test_42_code_function.m1s` - Code() for G-code execution
- `test_43_ismoving.m1s` - IsMoving() status check
- `test_44_sleep_after_message.m1s` - Sleep() requirement demonstration
- `test_code_gcode.m1s` - G-code execution tests
- `test_getcurrenttool.m1s` - GetCurrentTool() function
- `test_gettoolparam.m1s` - GetToolParam() function
- `test_setcurrenttool.m1s` - SetCurrentTool() function
- `test_settoolparam.m1s` - SetToolParam() function
- `test_message_display.m1s` - Message() display testing

### InitialTests/ShouldFail/ (7 tests)
Tests expected to fail or cause issues:

**Non-Working Functions**
- `test_15_string_replace.m1s` - Replace() function not supported
- `test_18_split_function.m1s` - Split() function not supported

**Syntax Errors (Cannot be run in test runner)**
- `test_20_user_function.m1s` - Function keyword causes parse error
- `test_21_user_sub.m1s` - Sub keyword causes parse error

**Problematic Behavior**
- `test_22_exit_sub.m1s` - Exit Sub terminates entire macro
- `test_37_settimer_gettimer.m1s` - SetTimer/GetTimer 91-93% unreliable
- `test_38_msgbox.m1s` - MsgBox creates blocking dialog boxes

### Root Level Tests (3 tests)
Additional functional tests:
- `check_dro.m1s` - DRO read/write functionality
- `test_settoolparam.m1s` - Tool parameter operations
- `test_update_mach2_native_tool_table.m1s` - Native tool table updates

### CorruptsScreen/
⚠️ **WARNING**: Contains tests that corrupt Mach3 screen - DO NOT RUN

### Deprecated/
Contains deprecated automated test runners that caused:
- VBScript editor to become unresponsive
- #expand preprocessing issues
- Mach3 crashes

## Running Tests

**Individual Test Execution (Recommended)**
1. Open Mach3
2. Navigate to Operator → VB Script Editor
3. File → Open → Select test file
4. Run → Run (or press F5)
5. View → Last Error (for errors)
6. Operator → Show History (for test output)

**Test Output Format**
```vbscript
Message("TEST XX: Feature name")
Sleep(100)
Message("  Expected: <what should happen>")
Sleep(100)
Message("  Actual: <what actually happened>")
Sleep(100)
Message("  Result: PASSED/FAILED - <explanation>")
Sleep(100)
```

## Key Findings

### Working Features ✅
- Basic VBScript syntax (variables, loops, conditions)
- String manipulation (Len, Left, Right, Mid, InStr)
- File system operations via FileSystemObject
- Math functions and type conversions
- Mach3-specific functions (DROs, tools, G-code)
- Error handling with On Error Resume Next

### Non-Working Features ❌
- Replace() and Split() string functions
- User-defined Function and Sub procedures
- On Error GoTo labels (except GoTo 0)
- SetTimer/GetTimer (highly unreliable)

### Critical Guidelines
1. **Always use Sleep(100) after Message()** - Required for display
2. **No On Error GoTo** - Not supported except possibly GoTo 0
3. **No user Functions/Subs** - Cause syntax errors
4. **Variable naming** - Use descriptive names with test number suffix
5. **Error handling** - Use On Error Resume Next, check Err.Number

## Test Development

When creating new tests:
1. Use the established format with Expected/Actual/Result
2. Include proper error handling where applicable
3. Add Sleep() after every Message()
4. Test one specific feature per file
5. Name files descriptively: test_XX_feature_name.m1s
6. Place in appropriate folder (ShouldPass or ShouldFail)

## Version Information
- Mach3 Version: R3.043.22
- VBScript Engine: Microsoft VBScript
- Test Suite Version: 2025-01-25
- Total Tests: 54 (44 passing, 7 failing, 3 root level)