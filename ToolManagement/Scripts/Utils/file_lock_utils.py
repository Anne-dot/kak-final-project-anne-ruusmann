"""
File locking utilities for preventing concurrent file access.

This module provides a standardized FileLock implementation that works consistently
across all project modules. It handles creating, managing, and checking file locks
to prevent concurrent access to files.

Classes:
    FileLock: Main class for file locking operations
"""

import json
import os
import platform
import socket
import sys
import time
from pathlib import Path

# Import project utilities
try:
    from Utils.config import AppConfig
    from Utils.error_utils import ErrorHandler, ErrorSeverity, FileError
    from Utils.logging_utils import log_exception, setup_logger
except ImportError:
    # Add parent directory to path for standalone testing
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from logging_utils import setup_logger

    # Avoid circular import for standalone testing
    class AppConfig:
        class timeouts:
            DEFAULT_LOCK_TIMEOUT = 30.0


class FileLock:
    """
    Implements a file locking mechanism to prevent concurrent access.

    This class creates and manages .lock files alongside target files
    to prevent multiple processes from accessing the same files.
    It also detects if files are currently locked by applications.
    """

    def __init__(self, file_path: str | Path, timeout: float = None):
        """
        Initialize the file lock.

        Args:
            file_path: Path to the file to lock
            timeout: Seconds after which a lock is considered stale (default: from AppConfig)
        """
        self.file_path = Path(file_path) if not isinstance(file_path, Path) else file_path
        self.lock_path = self.file_path.with_suffix(self.file_path.suffix + ".lock")

        # Use config value if not specified
        if timeout is None:
            timeout = AppConfig.timeouts.DEFAULT_LOCK_TIMEOUT
        self.timeout = timeout

        self.acquired = False

        # Configure logger
        self.logger = setup_logger(__name__)

    def check_file_lock(self) -> tuple[bool, str]:
        """
        Check if the target file is locked by another application.

        Returns:
            tuple: (is_locked, lock_info) where:
                - is_locked is a boolean indicating if file is locked
                - lock_info contains process information if available
        """
        try:
            # Windows-specific implementation
            if platform.system() == "Windows":
                try:
                    # Try to open file in exclusive mode
                    with open(self.file_path, "r+") as f:
                        return False, ""
                except OSError as e:
                    return True, f"File is locked by another process: {e!s}"
                except FileNotFoundError:
                    return False, "File does not exist"
            else:
                # Unix-like implementation (simplified)
                if not os.path.exists(self.file_path):
                    return False, "File does not exist"

                try:
                    # Try to open file in write mode
                    with open(self.file_path, "r+") as f:
                        return False, ""
                except OSError as e:
                    return True, f"File is locked by another process: {e!s}"

            return False, ""
        except Exception as e:
            self.logger.error(f"Error checking file lock: {e!s}")
            # If we can't check, assume it's not locked
            return False, f"Error checking lock: {e!s}"

    # Alias for backward compatibility
    is_file_locked = check_file_lock

    def acquire(self) -> bool:
        """
        Acquire a lock on the file.

        Returns:
            bool: True if lock acquired, False if file already locked
        """
        if self.acquired:
            return True

        try:
            # First check if file is locked by another application
            file_locked, lock_info = self.check_file_lock()
            if file_locked:
                self.logger.warning(f"Cannot acquire lock: {self.file_path} is in use: {lock_info}")
                return False

            # Check if lock file already exists
            if self.lock_path.exists():
                # Check if it's a stale lock
                if self._is_stale_lock():
                    # Remove stale lock
                    try:
                        self.lock_path.unlink()
                        self.logger.info(f"Removed stale lock: {self.lock_path}")
                    except Exception as e:
                        self.logger.error(f"Failed to remove stale lock: {self.lock_path} - {e!s}")
                        return False
                else:
                    # Lock is still valid
                    self.logger.info(f"Lock file exists and is still valid: {self.lock_path}")
                    return False

            # Create lock file with process info
            lock_info = {
                "pid": os.getpid(),
                "hostname": socket.gethostname(),
                "created": time.time(),
                "application": os.path.basename(sys.argv[0]) if len(sys.argv) > 0 else "unknown",
            }

            # Write lock info to file
            try:
                with open(self.lock_path, "w") as f:
                    json.dump(lock_info, f, indent=2)

                # Successfully created lock file
                self.acquired = True
                self.logger.info(f"Lock acquired: {self.lock_path}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to create lock file: {self.lock_path} - {e!s}")
                return False

        except Exception as e:
            self.logger.error(f"Error acquiring lock: {e!s}")
            return False

    def release(self) -> bool:
        """
        Release the lock if it exists.

        Returns:
            bool: True if released successfully, False otherwise
        """
        if not self.acquired:
            return True

        try:
            if self.lock_path.exists():
                self.lock_path.unlink()
                self.logger.info(f"Lock released: {self.lock_path}")
                self.acquired = False
                return True

            # If lock file doesn't exist, just mark as released
            self.acquired = False
            return True
        except Exception as e:
            self.logger.error(f"Error releasing lock: {e!s}")
            return False

    def _is_stale_lock(self) -> bool:
        """
        Check if the lock file is older than the timeout.

        Returns:
            bool: True if lock is stale, False otherwise
        """
        try:
            if not self.lock_path.exists():
                return False

            mtime = os.path.getmtime(self.lock_path)
            age = time.time() - mtime

            # If file is older than timeout, it's stale
            return age > self.timeout
        except Exception as e:
            self.logger.error(f"Error checking stale lock: {e!s}")
            # If we can't check the time, assume it's stale
            return True

    def __enter__(self):
        """Context manager enter."""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()

    def __del__(self):
        """Destructor to ensure lock is released."""
        self.release()


# Example usage if run directly
if __name__ == "__main__":
    import tempfile

    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(b"Test content")
        temp_path = temp.name

    try:
        print(f"Testing file lock on: {temp_path}")

        # Test lock acquisition
        lock = FileLock(temp_path)

        print("Acquiring lock...")
        if lock.acquire():
            print("Lock acquired successfully")

            # Test lock checking
            is_locked, info = lock.check_file_lock()
            print(f"Is file locked? {is_locked}, Info: {info}")

            # Test lock release
            print("Releasing lock...")
            if lock.release():
                print("Lock released successfully")
            else:
                print("Failed to release lock")
        else:
            print("Failed to acquire lock")

        # Test context manager
        print("\nTesting context manager...")
        with FileLock(temp_path) as lock:
            print("Lock acquired in context")

        print("Context exited, lock should be released")

    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
            print(f"Temporary file removed: {temp_path}")
