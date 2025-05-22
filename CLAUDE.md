# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Run unit tests: `python3 ToolManagement/Scripts/Tests/run_tests.py`
- Run single test: `python3 -m unittest ToolManagement/Scripts/Tests/UnitTests/test_file_name.py`
- Run manual test: `python3 ToolManagement/Scripts/Tests/ManualTests/test_file_name.py`
- Install dependencies: `pip3 install -r ToolManagement/Scripts/requirements.txt`

## Project Documentation

### Jira Tasks and Confluence Documentation
- Jira tasks are stored in `atlassian-docs/jira_tasks/` folder
- Confluence documentation is stored in `atlassian-docs/confluence_all/` folder
- Epic MRFP-80 "DXF to G-code Generation" contains the main development tasks
- Use these files to understand current task status and requirements
- Tasks are organized by epics with individual task files containing detailed requirements

## Code Style Guidelines

### Python
- Follow PEP 8 conventions with 100 char line limit
- Python 3.13.2 target version
- Use snake_case for functions, variables; PascalCase for classes
- Document with Google-style docstrings for modules, classes, methods
- Use type hints for function parameters and return values
- Imports order: standard library, third-party, project modules
- Return values standardized as: Tuple[bool, str, Dict] (success, message, details)
- Error handling with custom exceptions from BaseError hierarchy
- Wrap potentially problematic code in try-except blocks with specific exceptions
- Logging through Utils.logging_utils with severity levels (INFO, WARNING, ERROR, CRITICAL)
- Handle cross-platform path operations via Utils.path_utils
- Maintain modular structure based on functionality: DXF, GCode, Utils
- One responsibility per Python file following project directory structure

### Core Development Principles

#### DRY (Don't Repeat Yourself)
- Eliminate duplication by extracting common functionality into utility methods
- Use inheritance and composition to reuse code across similar components
- Implement abstract base classes for shared interfaces
- Create reusable helper functions for common operations

#### Single Source of Truth
- Store configuration values in one location (Utils.config)
- Define constants, enums, and mappings in dedicated modules
- Create centralized registries for related components
- Use factories to standardize object creation
- Implement the repository pattern for data access

#### Modularity
- Design independent modules with well-defined interfaces
- Minimize dependencies between modules
- Use dependency injection to decouple components
- Expose only necessary functionality through public interfaces
- Package related functionality together

#### ADHD-Friendly Code Organization
- Break complex methods into smaller, focused functions (max 30-50 lines)
- Create clear visual separation between logical sections
- Use consistent formatting with whitespace to improve readability
- Add explicit comments for non-obvious logic
- Include diagrams for complex workflows
- Organize code in a predictable, consistent pattern

#### OOP Best Practices
- Follow SOLID principles (especially Single Responsibility and Interface Segregation)
- Prefer composition over inheritance where appropriate
- Design for testability with dependency injection
- Use factory methods for complex object creation
- Implement interfaces consistently across related classes
- Encapsulate implementation details behind clean interfaces

### Mach3 VBScript (.m1s files)
- No user-defined functions or subroutines (not supported in Mach3)
- Use #expand directive for code inclusion
- Variables: camelCase (e.g., csvLine, fieldPos)
- Constants: ALL_UPPERCASE_WITH_UNDERSCORES
- Message format: "CATEGORY: Message content" (e.g., "ERROR: File not found")
- Always use Sleep() after Message() calls to ensure proper display
- Always use GetMainFolder() for file paths
- Follow standardized message prefixes (ERROR, WARNING, INFO, DEBUG, SYSTEM, USER, SUCCESS)
- Implement timeouts for operations that might hang
- Always validate user input with proper error handling
- Use On Error Resume Next with Err.Number checks for error handling