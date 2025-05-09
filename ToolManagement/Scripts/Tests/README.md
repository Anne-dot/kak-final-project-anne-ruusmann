# Testing Framework

This directory contains tests for the CNC Milling Project. The tests are organized into unit tests and manual tests.

## Directory Structure

```
Tests/
├── UnitTests/        # Automated unit tests
│   ├── DXF/          # Tests for DXF modules
│   ├── GCode/        # Tests for GCode modules
│   └── Utils/        # Tests for utility modules
├── ManualTests/      # Tests that require manual verification
├── TestData/         # Test data files
│   ├── DXF/          # DXF test files
│   └── GCode/        # GCode test files
└── run_tests.py      # Test runner script
```

## Running Tests

### Running All Tests

To run all tests, use the `run_tests.py` script:

```bash
# From the Tests directory
python3 run_tests.py
```

The test runner will:
1. Set up the correct Python path for imports
2. Discover and run all tests in the UnitTests directory
3. Generate a report in the Logs directory

### Running Individual Tests

Individual test modules can be run directly:

```bash
# From the Scripts directory
python3 Tests/UnitTests/DXF/test_dxf_parser.py
```

For diagnostic purposes, you can also check if a module can be imported correctly:

```bash
python3 Tests/UnitTests/DXF/test_dxf_parser.py --check-import
```

## Test Implementation Guidelines

### Path Handling

Each test file should handle import paths correctly to ensure it can be run both directly and through the test runner. Use this boilerplate code at the top of your test files:

```python
# Get the current file's directory
current_dir = Path(__file__).parent.absolute()

# Get the Scripts directory (parent of Tests directory)
scripts_dir = current_dir.parent.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Add ToolManagement directory to path for absolute imports
project_dir = scripts_dir.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))
```

### Test Organization

- Each test class should focus on testing a specific module
- Use descriptive test names that clearly indicate what is being tested
- Include both positive and negative test cases
- Use appropriate assertions

### Output Format

For manual tests, consider implementing a clear output format:

```python
def create_test_summary(result):
    """Create a detailed test summary with structured output."""
    # Define status based on test results
    status = "[PASS]" if result.wasSuccessful() else "[FAIL]"
    
    # Define test results with clear, structured format
    test_details = {
        "Feature 1": f"{status} Description",
        "Feature 2": {
            "Subfeature A": f"{status} Description",
            "Subfeature B": f"{status} Description"
        }
    }
    
    # Format and return output
    # ...
```

## Adding New Tests

When adding new tests:

1. Create a new test file in the appropriate directory
2. Use proper path handling as described above
3. Follow the naming convention `test_*.py`
4. Implement both direct execution and test runner discovery

## Test Data

Add test data files to the TestData directory in the appropriate subdirectory. Reference test data using relative paths from the test file location:

```python
test_data_dir = Path(__file__).parent.parent.parent / "TestData" / "DXF"
```