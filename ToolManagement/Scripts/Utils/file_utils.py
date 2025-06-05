"""
File handling utilities for the CNC milling project.

This module provides safe file operations with locking mechanisms
to prevent concurrent access issues across the application.

Classes:
    FileUtils: Main class for safe file operations
"""

import csv
import os
import platform
import shutil
import sys
import time
from pathlib import Path
from typing import Any

# Import project utilities
try:
    from Utils.error_utils import ErrorHandler, ErrorSeverity, FileError
    from Utils.file_lock_utils import FileLock
    from Utils.path_utils import PathUtils
except ImportError:
    # Add parent directory to path for standalone testing
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from error_utils import ErrorHandler, ErrorSeverity, FileError
    from file_lock_utils import FileLock
    from path_utils import PathUtils


class FileUtils:
    """
    Provides utilities for safe file operations with locking.

    This class implements methods for reading, writing, and managing
    files safely with proper error handling and locking.
    """

    @staticmethod
    def read_text(
        file_path: str | Path,
        encoding: str = "utf-8",
        use_lock: bool = True,
        lock_timeout: float = 30.0,
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Read text from a file safely with optional locking.

        Args:
            file_path: Path to the file to read
            encoding: File encoding (default: utf-8)
            use_lock: Whether to use file locking (default: True)
            lock_timeout: Timeout for lock acquisition in seconds (default: 30)

        Returns:
            Tuple: (success, content, details) where:
                success: True if read was successful, False otherwise
                content: File content if successful, error message otherwise
                details: Dictionary with operation details or error information
        """
        file_path = Path(file_path)

        try:
            # Check if file exists
            if not file_path.exists():
                return ErrorHandler.from_exception(
                    FileError(
                        message=f"File not found: {file_path.name}",
                        file_path=str(file_path),
                        severity=ErrorSeverity.ERROR,
                    )
                )

            if use_lock:
                lock = FileLock(file_path, timeout=lock_timeout)
                if not lock.acquire():
                    return ErrorHandler.from_exception(
                        FileError(
                            message=f"Could not acquire lock for {file_path.name}",
                            file_path=str(file_path),
                            severity=ErrorSeverity.ERROR,
                            details={"timeout": lock_timeout},
                        )
                    )

            # Read file content
            with open(file_path, encoding=encoding) as f:
                content = f.read()

            # Release lock if used
            if use_lock:
                lock.release()

            return ErrorHandler.create_success_response(
                message=f"Successfully read {file_path.name}",
                data={"content": content, "size": len(content)},
            )

        except Exception as e:
            # Ensure lock is released if used
            if use_lock and "lock" in locals() and lock.acquired:
                lock.release()

            return ErrorHandler.from_exception(
                FileError(
                    message=f"Failed to read {file_path.name}",
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error": str(e)},
                )
            )

    @staticmethod
    def write_text(
        file_path: str | Path,
        content: str,
        encoding: str = "utf-8",
        use_lock: bool = True,
        lock_timeout: float = 30.0,
        create_backup: bool = False,
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Write text to a file safely with optional locking and backup.

        Args:
            file_path: Path to the file to write
            content: Text content to write
            encoding: File encoding (default: utf-8)
            use_lock: Whether to use file locking (default: True)
            lock_timeout: Timeout for lock acquisition in seconds (default: 30)
            create_backup: Whether to create a backup before writing (default: False)

        Returns:
            Tuple: (success, message, details) where:
                success: True if write was successful, False otherwise
                message: Success or error message
                details: Dictionary with operation details or error information
        """
        file_path = Path(file_path)
        backup_path = None

        try:
            # Create parent directories if they don't exist
            PathUtils.ensure_dir(file_path.parent)

            if use_lock:
                lock = FileLock(file_path, timeout=lock_timeout)
                if not lock.acquire():
                    return ErrorHandler.from_exception(
                        FileError(
                            message=f"Could not acquire lock for {file_path.name}",
                            file_path=str(file_path),
                            severity=ErrorSeverity.ERROR,
                            details={"timeout": lock_timeout},
                        )
                    )

            # Create backup if requested and file exists
            if create_backup and file_path.exists():
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.with_name(f"{file_path.stem}_{timestamp}{file_path.suffix}")
                shutil.copy2(file_path, backup_path)

            # Write content using a temporary file to ensure atomicity
            temp_file = file_path.with_name(f"{file_path.stem}_temp{file_path.suffix}")
            with open(temp_file, "w", encoding=encoding) as f:
                f.write(content)

            # Replace the original file with the temporary file
            if platform.system() == "Windows" and file_path.exists():
                # Windows requires removing the file first
                file_path.unlink()

            temp_file.rename(file_path)

            # Release lock if used
            if use_lock:
                lock.release()

            result_details = {"size": len(content)}
            if backup_path:
                result_details["backup_path"] = str(backup_path)

            return ErrorHandler.create_success_response(
                message=f"Successfully wrote {file_path.name}", data=result_details
            )

        except Exception as e:
            # Ensure lock is released if used
            if use_lock and "lock" in locals() and lock.acquired:
                lock.release()

            return ErrorHandler.from_exception(
                FileError(
                    message=f"Failed to write {file_path.name}",
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error": str(e)},
                )
            )

    @staticmethod
    def read_binary(
        file_path: str | Path, use_lock: bool = True, lock_timeout: float = 30.0
    ) -> tuple[bool, bytes, dict[str, Any]]:
        """
        Read binary data from a file safely with optional locking.

        Args:
            file_path: Path to the file to read
            use_lock: Whether to use file locking (default: True)
            lock_timeout: Timeout for lock acquisition in seconds (default: 30)

        Returns:
            Tuple: (success, content, details) where:
                success: True if read was successful, False otherwise
                content: Binary data if successful, empty bytes otherwise
                details: Dictionary with operation details or error information
        """
        file_path = Path(file_path)

        try:
            # Check if file exists
            if not file_path.exists():
                error_result = ErrorHandler.from_exception(
                    FileError(
                        message=f"File not found: {file_path.name}",
                        file_path=str(file_path),
                        severity=ErrorSeverity.ERROR,
                    )
                )
                return error_result[0], b"", error_result[2]

            if use_lock:
                lock = FileLock(file_path, timeout=lock_timeout)
                if not lock.acquire():
                    error_result = ErrorHandler.from_exception(
                        FileError(
                            message=f"Could not acquire lock for {file_path.name}",
                            file_path=str(file_path),
                            severity=ErrorSeverity.ERROR,
                            details={"timeout": lock_timeout},
                        )
                    )
                    return error_result[0], b"", error_result[2]

            # Read file content
            with open(file_path, "rb") as f:
                content = f.read()

            # Release lock if used
            if use_lock:
                lock.release()

            success_response = ErrorHandler.create_success_response(
                message=f"Successfully read {file_path.name}", data={"size": len(content)}
            )
            return success_response[0], content, success_response[2]

        except Exception as e:
            # Ensure lock is released if used
            if use_lock and "lock" in locals() and lock.acquired:
                lock.release()

            error_result = ErrorHandler.from_exception(
                FileError(
                    message=f"Failed to read {file_path.name}",
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error": str(e)},
                )
            )
            return error_result[0], b"", error_result[2]

    @staticmethod
    def write_binary(
        file_path: str | Path,
        data: bytes,
        use_lock: bool = True,
        lock_timeout: float = 30.0,
        create_backup: bool = False,
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Write binary data to a file safely with optional locking and backup.

        Args:
            file_path: Path to the file to write
            data: Binary data to write
            use_lock: Whether to use file locking (default: True)
            lock_timeout: Timeout for lock acquisition in seconds (default: 30)
            create_backup: Whether to create a backup before writing (default: False)

        Returns:
            Tuple: (success, message, details) where:
                success: True if write was successful, False otherwise
                message: Success or error message
                details: Dictionary with operation details or error information
        """
        file_path = Path(file_path)
        backup_path = None

        try:
            # Create parent directories if they don't exist
            PathUtils.ensure_dir(file_path.parent)

            if use_lock:
                lock = FileLock(file_path, timeout=lock_timeout)
                if not lock.acquire():
                    return ErrorHandler.from_exception(
                        FileError(
                            message=f"Could not acquire lock for {file_path.name}",
                            file_path=str(file_path),
                            severity=ErrorSeverity.ERROR,
                            details={"timeout": lock_timeout},
                        )
                    )

            # Create backup if requested and file exists
            if create_backup and file_path.exists():
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.with_name(f"{file_path.stem}_{timestamp}{file_path.suffix}")
                shutil.copy2(file_path, backup_path)

            # Write content using a temporary file to ensure atomicity
            temp_file = file_path.with_name(f"{file_path.stem}_temp{file_path.suffix}")
            with open(temp_file, "wb") as f:
                f.write(data)

            # Replace the original file with the temporary file
            if platform.system() == "Windows" and file_path.exists():
                # Windows requires removing the file first
                file_path.unlink()

            temp_file.rename(file_path)

            # Release lock if used
            if use_lock:
                lock.release()

            result_details = {"size": len(data)}
            if backup_path:
                result_details["backup_path"] = str(backup_path)

            return ErrorHandler.create_success_response(
                message=f"Successfully wrote {file_path.name}", data=result_details
            )

        except Exception as e:
            # Ensure lock is released if used
            if use_lock and "lock" in locals() and lock.acquired:
                lock.release()

            return ErrorHandler.from_exception(
                FileError(
                    message=f"Failed to write {file_path.name}",
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error": str(e)},
                )
            )

    @staticmethod
    def read_csv(
        file_path: str | Path, use_lock: bool = True, lock_timeout: float = 30.0, **csv_options
    ) -> tuple[bool, list[dict[str, Any]], dict[str, Any]]:
        """
        Read a CSV file safely with optional locking.

        Args:
            file_path: Path to the CSV file to read
            use_lock: Whether to use file locking (default: True)
            lock_timeout: Timeout for lock acquisition in seconds (default: 30)
            **csv_options: Additional options to pass to csv.DictReader

        Returns:
            Tuple: (success, rows, details) where:
                success: True if read was successful, False otherwise
                rows: List of row dictionaries if successful, empty list otherwise
                details: Dictionary with operation details or error information
        """
        file_path = Path(file_path)

        try:
            # Check if file exists
            if not file_path.exists():
                return ErrorHandler.from_exception(
                    FileError(
                        message=f"CSV file not found: {file_path.name}",
                        file_path=str(file_path),
                        severity=ErrorSeverity.ERROR,
                    )
                )

            if use_lock:
                lock = FileLock(file_path, timeout=lock_timeout)
                if not lock.acquire():
                    return ErrorHandler.from_exception(
                        FileError(
                            message=f"Could not acquire lock for {file_path.name}",
                            file_path=str(file_path),
                            severity=ErrorSeverity.ERROR,
                            details={"timeout": lock_timeout},
                        )
                    )

            # Read CSV content
            rows = []
            with open(file_path, newline="") as f:
                reader = csv.DictReader(f, **csv_options)
                rows = list(reader)

            # Release lock if used
            if use_lock:
                lock.release()

            return ErrorHandler.create_success_response(
                message=f"Successfully read {len(rows)} rows from {file_path.name}",
                data={"rows": rows, "count": len(rows)},
            )

        except Exception as e:
            # Ensure lock is released if used
            if use_lock and "lock" in locals() and lock.acquired:
                lock.release()

            return ErrorHandler.from_exception(
                FileError(
                    message=f"Failed to read CSV {file_path.name}",
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error": str(e)},
                )
            )

    @staticmethod
    def write_csv(
        file_path: str | Path,
        rows: list[dict[str, Any]],
        use_lock: bool = True,
        lock_timeout: float = 30.0,
        create_backup: bool = False,
        fieldnames: list[str] | None = None,
        **csv_options,
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Write rows to a CSV file safely with optional locking and backup.

        Args:
            file_path: Path to the CSV file to write
            rows: List of dictionaries, each representing a row
            use_lock: Whether to use file locking (default: True)
            lock_timeout: Timeout for lock acquisition in seconds (default: 30)
            create_backup: Whether to create a backup before writing (default: False)
            fieldnames: List of field names for the CSV header (default: None)
            **csv_options: Additional options to pass to csv.DictWriter

        Returns:
            Tuple: (success, message, details) where:
                success: True if write was successful, False otherwise
                message: Success or error message
                details: Dictionary with operation details or error information
        """
        file_path = Path(file_path)
        backup_path = None

        try:
            # Determine fieldnames if not provided
            if fieldnames is None and rows:
                fieldnames = list(rows[0].keys())

            # Create parent directories if they don't exist
            PathUtils.ensure_dir(file_path.parent)

            if use_lock:
                lock = FileLock(file_path, timeout=lock_timeout)
                if not lock.acquire():
                    return ErrorHandler.from_exception(
                        FileError(
                            message=f"Could not acquire lock for {file_path.name}",
                            file_path=str(file_path),
                            severity=ErrorSeverity.ERROR,
                            details={"timeout": lock_timeout},
                        )
                    )

            # Create backup if requested and file exists
            if create_backup and file_path.exists():
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.with_name(f"{file_path.stem}_{timestamp}{file_path.suffix}")
                shutil.copy2(file_path, backup_path)

            # Write content using a temporary file to ensure atomicity
            temp_file = file_path.with_name(f"{file_path.stem}_temp{file_path.suffix}")
            with open(temp_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, **csv_options)
                writer.writeheader()
                writer.writerows(rows)

            # Replace the original file with the temporary file
            if platform.system() == "Windows" and file_path.exists():
                # Windows requires removing the file first
                file_path.unlink()

            temp_file.rename(file_path)

            # Release lock if used
            if use_lock:
                lock.release()

            result_details = {"count": len(rows)}
            if backup_path:
                result_details["backup_path"] = str(backup_path)

            return ErrorHandler.create_success_response(
                message=f"Successfully wrote {len(rows)} rows to {file_path.name}",
                data=result_details,
            )

        except Exception as e:
            # Ensure lock is released if used
            if use_lock and "lock" in locals() and lock.acquired:
                lock.release()

            return ErrorHandler.from_exception(
                FileError(
                    message=f"Failed to write CSV {file_path.name}",
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error": str(e)},
                )
            )

    @staticmethod
    def ensure_backup_dir(
        base_dir: str | Path, max_backups: int = 20
    ) -> tuple[bool, Path, dict[str, Any]]:
        """
        Ensure a backup directory exists and manage the number of backups.

        Args:
            base_dir: Base directory where backups should be stored
            max_backups: Maximum number of backup files to keep (default: 20)

        Returns:
            Tuple: (success, backup_dir, details) where:
                success: True if operation was successful, False otherwise
                backup_dir: Path to the backup directory
                details: Dictionary with operation details or error information
        """
        try:
            base_dir = Path(base_dir)
            backup_dir = base_dir / "backups"

            # Create backup directory if it doesn't exist
            PathUtils.ensure_dir(backup_dir)

            # Manage existing backups if max_backups is specified
            if max_backups > 0:
                # Get all backup files sorted by modification time (oldest first)
                backup_files = sorted(backup_dir.glob("*"), key=lambda f: f.stat().st_mtime)

                # Remove oldest backups if there are too many
                while len(backup_files) > max_backups:
                    oldest = backup_files.pop(0)
                    if oldest.is_file():
                        oldest.unlink()
                    elif oldest.is_dir():
                        shutil.rmtree(oldest)

            return ErrorHandler.create_success_response(
                message="Backup directory ready",
                data={"backup_dir": str(backup_dir), "managed": max_backups > 0},
            )

        except Exception as e:
            return ErrorHandler.from_exception(
                FileError(
                    message="Failed to manage backup directory",
                    file_path=str(base_dir),
                    severity=ErrorSeverity.ERROR,
                    details={"error": str(e)},
                )
            )
