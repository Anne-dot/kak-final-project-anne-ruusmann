"""
Base file loader module providing consistent file operations.

This module defines the BaseFileLoader class that standardizes file loading,
validation, and handling across the application. It provides reusable functionality
for DXF, GCode, and other specialized file loaders.

Classes:
    BaseFileLoader: Abstract base class for file loading operations
"""

import os
import platform
import tkinter as tk
from abc import ABC, abstractmethod
from pathlib import Path
from tkinter import filedialog
from typing import Any

from .error_utils import ErrorHandler, ErrorSeverity, FileError

# Import from Utils package
from .logging_utils import setup_logger
from .path_utils import PathUtils


class BaseFileLoader(ABC):
    """
    Abstract base class for file loading operations.

    This class provides common file handling functionality including:
    - File validation (exists, readable, correct extension)
    - User interface for file selection
    - Standard error handling
    - File metadata extraction
    - Platform-aware operations

    Subclasses must implement the specific file loading and validation logic.
    """

    def __init__(self, allowed_extensions: list[str] = None, description: str = "File"):
        """
        Initialize the base file loader.

        Args:
            allowed_extensions: List of allowed file extensions (e.g., ['.dxf', '.dwg'])
            description: Description of the file type for UI and error messages
        """
        # Set up logger for this class - use the subclass's name
        self.logger = setup_logger(self.__class__.__module__)

        # Store allowed extensions and file type description
        self.allowed_extensions = allowed_extensions or []
        self.description = description

        # Initialize state
        self.file_path = None
        self.error_message = ""

        self.logger.info(
            f"{self.__class__.__name__} initialized with allowed extensions: {self.allowed_extensions}"
        )

    def validate_file(self, file_path: str | Path) -> tuple[bool, str, dict[str, Any]]:
        """
        Validates that a file exists, is readable, and has the correct extension.

        Args:
            file_path: Path to the file to validate

        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if validation was successful
                - message contains success or error message
                - details contains information about the validation
        """
        # Convert to Path object for consistent handling
        file_path = Path(file_path) if not isinstance(file_path, Path) else file_path
        self.logger.info(f"Validating {self.description} file: {file_path}")

        # Check if file exists
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return ErrorHandler.from_exception(
                FileError(
                    message=f"File not found: {file_path}",
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                )
            )

        # Check if file is accessible
        if not os.access(file_path, os.R_OK):
            self.logger.error(f"File not accessible (permission denied): {file_path}")
            return ErrorHandler.from_exception(
                FileError(
                    message=f"File not accessible (permission denied): {file_path}",
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error": "Permission denied"},
                )
            )

        # Check if file has the correct extension
        if self.allowed_extensions and not any(
            file_path.name.lower().endswith(ext.lower()) for ext in self.allowed_extensions
        ):
            self.logger.error(f"File does not have a valid extension: {file_path}")
            return ErrorHandler.from_exception(
                FileError(
                    message=f"File does not have a valid extension: {file_path.name}",
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={
                        "extension": file_path.suffix,
                        "allowed_extensions": self.allowed_extensions,
                    },
                )
            )

        # Additional validation can be added in subclasses
        # Basic validation succeeded
        return ErrorHandler.create_success_response(
            message=f"{self.description} file is valid", data={"file_path": str(file_path)}
        )

    def select_file(
        self, test_data_dir: str = None, title: str = None, filetypes: list[tuple[str, str]] = None
    ) -> str | None:
        """
        Prompts the user to select a file using an appropriate UI for the platform.

        Args:
            test_data_dir: Optional path to test data directory for non-Windows platforms
            title: Dialog title (defaults to "Select [Description] File")
            filetypes: List of (description, pattern) tuples for file dialog

        Returns:
            str: Selected file path, or None if selection was canceled
        """
        # Set defaults
        title = title or f"Select {self.description} File"

        # Generate filetypes from allowed extensions if not provided
        if filetypes is None and self.allowed_extensions:
            filetypes = [
                (f"{self.description} files", "*" + ext) for ext in self.allowed_extensions
            ]
            filetypes.append(("All files", "*.*"))

        # Windows: Use tkinter file dialog
        if platform.system() == "Windows":
            self.logger.info(f"Using Windows file dialog for {self.description} selection")
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            file_path = filedialog.askopenfilename(
                title=title,
                filetypes=filetypes or [(f"{self.description} files", "*.*"), ("All files", "*.*")],
            )

            if file_path:
                self.logger.info(f"Selected file: {file_path}")
            else:
                self.logger.info("File selection canceled")

            return file_path if file_path else None

        # Linux/Other: Show file list in terminal
        self.logger.info(f"Using terminal interface for {self.description} selection")

        # Get the path to the test data directory
        if test_data_dir is None:
            # Try to find an appropriate test data directory
            test_data_parent = PathUtils.get_test_data_dir()
            if self.allowed_extensions:
                # Look for a subdirectory that might match the file type
                ext = self.allowed_extensions[0].lower().lstrip(".")
                possible_dirs = [
                    test_data_parent / ext.upper(),
                    test_data_parent / ext.capitalize(),
                    test_data_parent / ext,
                ]

                for dir_path in possible_dirs:
                    if dir_path.exists():
                        test_data_dir = str(dir_path)
                        break

                if test_data_dir is None:
                    test_data_dir = str(test_data_parent)
            else:
                test_data_dir = str(test_data_parent)

        # Check if directory exists
        if not os.path.exists(test_data_dir):
            error_msg = f"Test data directory not found: {test_data_dir}"
            self.logger.error(error_msg)
            print(error_msg)
            return None

        # List files with matching extensions
        if self.allowed_extensions:
            matching_files = []
            for ext in self.allowed_extensions:
                matching_files.extend(
                    [f for f in os.listdir(test_data_dir) if f.lower().endswith(ext.lower())]
                )
        else:
            # List all files
            matching_files = os.listdir(test_data_dir)

        if not matching_files:
            error_msg = f"No {self.description} files found in {test_data_dir}"
            self.logger.error(error_msg)
            print(error_msg)
            return None

        # Display file list
        print(f"\nAvailable {self.description} files:")
        for i, file_name in enumerate(matching_files):
            print(f"{i + 1}. {file_name}")

        # Get user selection
        while True:
            try:
                selection = input("\nEnter file number (or 'q' to quit): ")

                if selection.lower() == "q":
                    self.logger.info("File selection canceled by user")
                    return None

                index = int(selection) - 1
                if 0 <= index < len(matching_files):
                    selected_file = os.path.join(test_data_dir, matching_files[index])
                    self.logger.info(f"Selected file: {selected_file}")
                    return selected_file
                print(f"Invalid selection. Please enter 1-{len(matching_files)}.")
            except ValueError:
                print("Please enter a valid number.")

    @abstractmethod
    def load_file(self, file_path: str | Path | None = None) -> tuple[bool, str, dict[str, Any]]:
        """
        Loads and validates a file.

        This abstract method must be implemented by subclasses to handle specific
        file loading logic (e.g., parsing DXF, reading G-code).

        Args:
            file_path: Optional path to file. If not provided, will prompt for selection.

        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if loading was successful
                - message contains success details or error message
                - details contains file content or error information
        """
        pass

    @abstractmethod
    def get_file_info(self, file_content: Any = None) -> tuple[bool, str, dict[str, Any]]:
        """
        Returns basic information about the loaded file.

        This abstract method must be implemented by subclasses to extract
        metadata for the specific file type.

        Args:
            file_content: Optional file content. If None, uses previously loaded file.

        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if info extraction was successful
                - message contains success or error message
                - details contains the file information
        """
        pass
