# DEPRECATED TEST RUNNERS

These test runners are deprecated due to issues with #expand directive handling and Mach3 stability.

## Why Deprecated

1. **#expand Preprocessing Issues**: All #expand directives are processed at compile time, making it impossible to conditionally skip tests based on START_TEST value
2. **Mach3 Stability**: Long-running test suites caused VBScript editor to become unresponsive
3. **Exit Sub Problem**: test_22_exit_sub.m1s terminates the entire test runner when expanded
4. **MsgBox Blocking**: test_38_msgbox.m1s creates blocking dialogs requiring user interaction
5. **Syntax Error Tests**: Tests with Function/Sub keywords cause parse errors preventing execution

## Recommended Approach

Run tests individually or in small groups manually. Tests are now organized in:
- `InitialTests/ShouldPass/` - Tests expected to work
- `InitialTests/ShouldFail/` - Tests expected to fail or have issues

## Deprecated Files
- TestRunnerExpanded.m1s - Original full test runner
- TestRunnerFrom31.m1s - Attempt to resume from test 31
- TEST_RUNNER_README.md - Documentation for deprecated runners