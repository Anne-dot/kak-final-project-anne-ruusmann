# Mach3 VBScript Test Runner README

## Overview
This test suite validates VBScript functionality in Mach3 R3.043.22. The test runner (TestRunnerExpanded.m1s) executes 53 tests covering basic VBScript features, file operations, and Mach3-specific functions.

## Running Tests

### Start from Beginning
```vbscript
Const START_TEST = 1
```

### Resume from Specific Test
To resume from where you left off, change the START_TEST constant:
```vbscript
Const START_TEST = 31  ' Resume from test 31
```

## Test Results Summary

### Tests Expected to PASS (Working Features)
- **Tests 1-14**: Core VBScript functionality
  - 1-4: Variables, constants, variant types
  - 5-10: Control structures (If/Then, Select Case, loops)
  - 11-14: String functions (Len, Left, Right, Mid, InStr)
- **Tests 16-17**: Arrays (static and dynamic)
- **Test 19**: Error handling (On Error Resume Next)
- **Tests 23-36**: Objects and file operations
  - 23-24: CreateObject, Set keyword
  - 25-32: FileSystemObject operations
  - 33: Math functions
  - 34-35: Type checking/conversion
  - 36: Timer function
- **Tests 39-50**: Mach3-specific functions
  - 39: #expand directive
  - 40-41: DRO operations
  - 42-43: Code() and IsMoving()
  - 44: Sleep after Message (educational)
  - 45-50: Tool management functions
- **Tests 51-53**: Additional tool/DRO tests

### Tests Expected to FAIL (Non-Working Features)
- **Test 15**: Replace() function - Not supported
- **Test 18**: Split() function - Not supported
- **Test 37**: SetTimer/GetTimer - Unreliable (91-93% failure rate)

### Tests SKIPPED (Would Break Test Runner)
- **Test 20**: User-defined Function - Syntax error
- **Test 21**: User-defined Sub - Syntax error
- **Test 22**: Exit Sub - Terminates entire macro
- **Test 38**: MsgBox - Creates blocking dialog

## Test Results from 2025-01-25

### Passed Tests (29/30 executed)
- Tests 1-14: All basic VBScript features ✓
- Tests 16-17: Arrays ✓
- Test 19: Error handling ✓
- Tests 23-29: File operations ✓

### Failed Tests (2)
- Test 15: Replace() - Failed as expected ✓
- Test 18: Split() - Failed as expected ✓

### Skipped Tests (3)
- Test 20: Function keyword
- Test 21: Sub keyword
- Test 22: Exit Sub

### Not Yet Run (23)
- Tests 30-53 (stopped during test 30)

## Known Issues
1. Test runner may cause VBScript editor to become unresponsive during long runs
2. Total runtime approximately 2-3 minutes for all tests
3. Some tests may show different results on different Mach3 installations

## Manual Testing Required
The following tests should be run individually outside the test runner:
- test_20_user_function.m1s - Demonstrates Function syntax error
- test_21_user_sub.m1s - Demonstrates Sub syntax error  
- test_22_exit_sub.m1s - Shows Exit Sub behavior
- test_38_msgbox.m1s - Interactive dialog test

## Configuration
- `TEST_DELAY`: 1000ms between tests (reduced from 5000ms)
- `MESSAGE_DELAY`: 100ms after messages
- `ERROR_DELAY`: 150ms after errors

## File Locations
All test files are located in:
- InitialTests/ folder (tests 1-50)
- Root folder (tests 51-53)