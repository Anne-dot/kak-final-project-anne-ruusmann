#!/usr/bin/env python3
"""
Tool Data Backup System for Mach3 CNC Retrofit Project.

This module manages the creation, rotation, and restoration of tool data backups.
It implements a lightweight OOP approach with separate classes for backup management,
rotation, and command-line interface functionality.

Usage:
    python backup_manager.py --create path/to/file.csv
    python backup_manager.py --restore path/to/backup.csv path/to/target.csv
    python backup_manager.py --list
"""

import argparse
import datetime
import os
import shutil
import sys

# Import from Utils package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Utils.config import AppConfig
from Utils.error_utils import (
    BaseError,
    ErrorCategory,
    ErrorHandler,
    ErrorSeverity,
    FileError,
)
from Utils.file_lock_utils import FileLock
from Utils.logging_utils import log_exception, setup_logger

# Configure logging
log_dir = AppConfig.paths.get_logs_dir()
os.makedirs(log_dir, exist_ok=True)

# Use default logging configuration
logger = setup_logger(__name__)


class BackupRotation:
    """
    Manages backup file rotation and pruning.

    This class is responsible for listing backups and removing
    old backups beyond the maximum limit.
    """

    def __init__(self, backup_dir, max_backups=None):
        """
        Initialize the backup rotation manager.

        Args:
            backup_dir: Directory where backups are stored
            max_backups: Maximum number of backups to keep (default: from AppConfig)
        """
        self.logger = setup_logger(f"{__name__}.BackupRotation")
        self.backup_dir = backup_dir

        # Use config value if not specified
        if max_backups is None:
            max_backups = AppConfig.limits.DEFAULT_MAX_BACKUPS
        self.max_backups = max_backups

        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        self.logger.info(
            f"BackupRotation initialized with directory: {backup_dir}, max_backups: {max_backups}"
        )

    def list_backups(self):
        """
        List all backup files with creation times.

        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if operation succeeded
                - message contains success details or error message
                - details contains the backup list or error information
        """
        try:
            self.logger.info(f"Listing backups in {self.backup_dir}")
            backups = []

            # Verify directory exists
            if not os.path.exists(self.backup_dir):
                self.logger.error(f"Backup directory does not exist: {self.backup_dir}")
                return ErrorHandler.from_exception(
                    FileError(
                        message=f"Backup directory does not exist: {self.backup_dir}",
                        file_path=self.backup_dir,
                        severity=ErrorSeverity.ERROR,
                    )
                )

            # Get all CSV files in backup directory
            for file in os.listdir(self.backup_dir):
                if file.endswith(".csv"):
                    file_path = os.path.join(self.backup_dir, file)
                    creation_time = os.path.getctime(file_path)

                    backups.append(
                        {
                            "path": file_path,
                            "timestamp": creation_time,
                            "datetime": datetime.datetime.fromtimestamp(creation_time),
                            "filename": file,
                        }
                    )

            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x["timestamp"], reverse=True)
            self.logger.info(f"Found {len(backups)} backup files")

            return ErrorHandler.create_success_response(
                message=f"Found {len(backups)} backup files", data={"backups": backups}
            )

        except PermissionError:
            error_msg = f"Permission denied accessing backup directory: {self.backup_dir}"
            self.logger.error(error_msg)
            return ErrorHandler.from_exception(
                FileError(
                    message=error_msg,
                    file_path=self.backup_dir,
                    severity=ErrorSeverity.ERROR,
                    details={"error": "permission_denied"},
                )
            )
        except Exception as e:
            error_msg = f"Error listing backups: {e!s}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    category=ErrorCategory.FILE,
                    severity=ErrorSeverity.ERROR,
                    details={"error_type": type(e).__name__},
                )
            )

    def prune(self):
        """
        Remove old backups beyond the maximum limit.

        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if pruning was successful
                - message contains success details or error message
                - details contains pruning statistics or error information
        """
        try:
            self.logger.info(f"Pruning backups to maintain maximum of {self.max_backups}")

            # Get the current list of backups
            success, message, details = self.list_backups()
            if not success:
                self.logger.error(f"Failed to list backups for pruning: {message}")
                return ErrorHandler.from_exception(
                    BaseError(
                        message=f"Failed to list backups for pruning: {message}",
                        category=ErrorCategory.FILE,
                        severity=ErrorSeverity.ERROR,
                        details=details,
                    )
                )

            backups = details.get("backups", [])

            # If we have more backups than the limit, remove the oldest ones
            if len(backups) > self.max_backups:
                backups_to_remove = backups[self.max_backups :]
                removed_count = 0
                failed_removals = []

                for backup in backups_to_remove:
                    try:
                        os.remove(backup["path"])
                        self.logger.info(f"Removed old backup: {backup['filename']}")
                        removed_count += 1
                    except PermissionError:
                        error_msg = f"Permission denied removing backup: {backup['path']}"
                        self.logger.error(error_msg)
                        failed_removals.append(
                            {"path": backup["path"], "error": "permission_denied"}
                        )
                    except Exception as e:
                        error_msg = f"Error removing backup {backup['path']}: {e!s}"
                        self.logger.error(error_msg)
                        failed_removals.append({"path": backup["path"], "error": str(e)})

                if failed_removals:
                    return ErrorHandler.create_success_response(
                        message=f"Partially pruned backups: removed {removed_count} of {len(backups_to_remove)} old backups",
                        data={
                            "removed_count": removed_count,
                            "attempted_count": len(backups_to_remove),
                            "failed_removals": failed_removals,
                        },
                    )

                return ErrorHandler.create_success_response(
                    message=f"Successfully pruned {removed_count} old backups",
                    data={"removed_count": removed_count},
                )

            self.logger.info(
                f"No pruning needed, current backup count ({len(backups)}) is within limit"
            )
            return ErrorHandler.create_success_response(
                message="No pruning needed, backup count is within limit",
                data={"removed_count": 0, "current_count": len(backups)},
            )

        except Exception as e:
            error_msg = f"Error pruning backups: {e!s}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    category=ErrorCategory.FILE,
                    severity=ErrorSeverity.ERROR,
                    details={"error_type": type(e).__name__},
                )
            )


class BackupManager:
    """
    Manages backup operations for tool data files.

    This class creates and restores backups, using the BackupRotation
    class to handle backup file rotation.
    """

    def __init__(self, backup_dir=None, max_backups=None, lock_timeout=None):
        """
        Initialize the backup manager.

        Args:
            backup_dir: Directory where backups are stored (default: from AppConfig)
            max_backups: Maximum number of backups to keep (default: from AppConfig)
            lock_timeout: Timeout for file locks in seconds (default: from AppConfig)
        """
        self.logger = setup_logger(f"{__name__}.BackupManager")

        # Set default backup directory if not provided
        if backup_dir is None:
            backup_dir = str(AppConfig.paths.get_backups_dir() / "ToolData")

        # Set default timeouts and limits from config
        if max_backups is None:
            max_backups = AppConfig.limits.DEFAULT_MAX_BACKUPS

        if lock_timeout is None:
            lock_timeout = AppConfig.timeouts.BACKUP_LOCK_TIMEOUT

        self.backup_dir = backup_dir
        self.lock_timeout = lock_timeout

        # Initialize rotation manager
        self.rotation = BackupRotation(backup_dir, max_backups)

        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        self.logger.info(
            f"BackupManager initialized with directory: {backup_dir}, max_backups: {max_backups}, lock_timeout: {lock_timeout}"
        )

    def create_backup(self, file_path):
        """
        Create a timestamped backup of the specified file.

        Args:
            file_path: Path to the file to backup

        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if backup was successful
                - message contains success details or error message
                - details contains backup information or error details
        """
        try:
            self.logger.info(f"Creating backup of file: {file_path}")

            # Verify the source file exists
            if not os.path.exists(file_path):
                self.logger.error(f"Source file does not exist: {file_path}")
                return ErrorHandler.from_exception(
                    FileError(
                        message=f"Source file does not exist: {file_path}",
                        file_path=file_path,
                        severity=ErrorSeverity.ERROR,
                    )
                )

            # Get file name and generate backup file name with timestamp
            file_name = os.path.basename(file_path)
            name, ext = os.path.splitext(file_name)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file_name = f"{name}_{timestamp}{ext}"
            backup_path = os.path.join(self.backup_dir, backup_file_name)

            # Acquire file lock on the source file
            file_lock = FileLock(file_path, self.lock_timeout)

            # Explicitly check if file is locked first
            file_locked, lock_info = file_lock.check_file_lock()
            if file_locked:
                self.logger.warning(f"Cannot create backup: {file_path} is locked: {lock_info}")
                return ErrorHandler.from_exception(
                    FileError(
                        message=f"Could not backup file: {file_path} is currently in use by another application",
                        file_path=file_path,
                        severity=ErrorSeverity.WARNING,
                        details={"lock_info": lock_info},
                    )
                )

            # Then try to acquire the lock
            if not file_lock.acquire():
                self.logger.error(f"Could not acquire lock on {file_path}")
                return ErrorHandler.from_exception(
                    FileError(
                        message=f"Could not acquire lock on {file_path}. File may be in use.",
                        file_path=file_path,
                        severity=ErrorSeverity.ERROR,
                        details={"error": "lock_acquisition_failed"},
                    )
                )

            try:
                # Create backup
                shutil.copy2(file_path, backup_path)
                self.logger.info(f"Created backup: {backup_file_name}")

                # Prune old backups
                success, message, prune_details = self.rotation.prune()
                if success:
                    removed_count = prune_details.get("removed_count", 0)
                    if removed_count > 0:
                        self.logger.info(f"Removed {removed_count} old backup(s)")
                else:
                    self.logger.warning(f"Pruning failed: {message}")

                return ErrorHandler.create_success_response(
                    message=f"Backup created: {backup_file_name}",
                    data={
                        "backup_path": backup_path,
                        "backup_file_name": backup_file_name,
                        "original_file": file_path,
                        "timestamp": timestamp,
                        "pruning_result": {
                            "success": success,
                            "message": message,
                            "details": prune_details,
                        },
                    },
                )

            finally:
                # Always release the lock
                file_lock.release()
                self.logger.debug(f"Released lock on {file_path}")

        except PermissionError:
            error_msg = f"Permission denied accessing file: {file_path}"
            self.logger.error(error_msg)
            return ErrorHandler.from_exception(
                FileError(
                    message=error_msg,
                    file_path=file_path,
                    severity=ErrorSeverity.ERROR,
                    details={"error": "permission_denied"},
                )
            )
        except Exception as e:
            error_msg = f"Error creating backup: {e!s}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    category=ErrorCategory.FILE,
                    severity=ErrorSeverity.ERROR,
                    details={"error_type": type(e).__name__},
                )
            )

    def restore_from_backup(self, backup_path, target_path):
        """
        Restore a file from a backup.

        Args:
            backup_path: Path to the backup file
            target_path: Path where the file should be restored

        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if restore was successful
                - message contains success details or error message
                - details contains restore information or error details
        """
        try:
            self.logger.info(f"Restoring from backup {backup_path} to {target_path}")

            # Verify the backup file exists
            if not os.path.exists(backup_path):
                self.logger.error(f"Backup file does not exist: {backup_path}")
                return ErrorHandler.from_exception(
                    FileError(
                        message=f"Backup file does not exist: {backup_path}",
                        file_path=backup_path,
                        severity=ErrorSeverity.ERROR,
                    )
                )

            # Create safety backup of current file if it exists
            safety_backup = None
            if os.path.exists(target_path):
                # Create a safety backup with a special name
                target_name = os.path.basename(target_path)
                name, ext = os.path.splitext(target_name)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                safety_name = f"{name}_prerestore_{timestamp}{ext}"
                safety_backup = os.path.join(self.backup_dir, safety_name)

                # Acquire lock on target file
                file_lock = FileLock(target_path, self.lock_timeout)
                if not file_lock.acquire():
                    self.logger.error(f"Could not acquire lock on {target_path}")
                    return ErrorHandler.from_exception(
                        FileError(
                            message=f"Could not acquire lock on {target_path}. File may be in use.",
                            file_path=target_path,
                            severity=ErrorSeverity.ERROR,
                            details={"error": "lock_acquisition_failed"},
                        )
                    )

                try:
                    # Create safety backup
                    shutil.copy2(target_path, safety_backup)
                    self.logger.info(f"Created safety backup before restore: {safety_name}")

                    # Copy backup to target
                    shutil.copy2(backup_path, target_path)
                    self.logger.info(f"Restored from backup: {os.path.basename(backup_path)}")

                    return ErrorHandler.create_success_response(
                        message=f"Restored from backup: {os.path.basename(backup_path)}",
                        data={
                            "backup_path": backup_path,
                            "target_path": target_path,
                            "backup_filename": os.path.basename(backup_path),
                            "safety_backup": safety_backup,
                            "safety_backup_name": safety_name,
                        },
                    )

                finally:
                    # Always release the lock
                    file_lock.release()
                    self.logger.debug(f"Released lock on {target_path}")
            else:
                # Target doesn't exist, just copy the backup
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(backup_path, target_path)
                self.logger.info(
                    f"Restored from backup (target did not exist): {os.path.basename(backup_path)}"
                )

                return ErrorHandler.create_success_response(
                    message=f"Restored from backup: {os.path.basename(backup_path)}",
                    data={
                        "backup_path": backup_path,
                        "target_path": target_path,
                        "backup_filename": os.path.basename(backup_path),
                        "target_created": True,
                    },
                )

        except PermissionError:
            error_msg = "Permission denied accessing file during restore"
            self.logger.error(error_msg)
            return ErrorHandler.from_exception(
                FileError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    details={
                        "error": "permission_denied",
                        "backup_path": backup_path,
                        "target_path": target_path,
                    },
                )
            )
        except Exception as e:
            error_msg = f"Error restoring backup: {e!s}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    category=ErrorCategory.FILE,
                    severity=ErrorSeverity.ERROR,
                    details={
                        "error_type": type(e).__name__,
                        "backup_path": backup_path,
                        "target_path": target_path,
                    },
                )
            )

    def list_backups(self):
        """
        List all available backups.

        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if listing was successful
                - message contains success details or error message
                - details contains the backups list or error information
        """
        self.logger.info("Listing available backups")
        # The rotation class now returns the standardized response format
        return self.rotation.list_backups()


def write_status_file(status, message=""):
    """
    Write status file for Mach3 VBScript to read.

    Args:
        status: Status string (SUCCESS, ERROR)
        message: Optional message

    Returns:
        tuple: (success, message, details) containing the result
    """
    status_logger = setup_logger("backup_status_writer")
    status_file = os.path.join(AppConfig.paths.get_logs_dir(), "backup_status.txt")

    try:
        with open(status_file, "w") as f:
            f.write(f"{status}\n")
            if message:
                f.write(message)

        status_logger.info(f"Wrote status file: {status}")
        return ErrorHandler.create_success_response(
            message="Status file written successfully",
            data={"status": status, "file_path": status_file},
        )
    except PermissionError:
        error_msg = f"Permission denied writing status file: {status_file}"
        status_logger.error(error_msg)
        return ErrorHandler.from_exception(
            FileError(
                message=error_msg,
                file_path=status_file,
                severity=ErrorSeverity.ERROR,
                details={"error": "permission_denied"},
            )
        )
    except Exception as e:
        error_msg = f"Error writing status file: {e!s}"
        log_exception(status_logger, error_msg)
        return ErrorHandler.from_exception(
            FileError(
                message=error_msg,
                file_path=status_file,
                severity=ErrorSeverity.ERROR,
                details={"error_type": type(e).__name__},
            )
        )


def main():
    """
    Main function that processes command line arguments and executes operations.
    """
    main_logger = setup_logger("backup_manager_main")

    parser = argparse.ArgumentParser(description="Tool Data Backup Manager")

    # Add exclusive command arguments
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--create", help="Create a backup of the specified file")
    group.add_argument("--restore", help="Restore from a backup file")
    group.add_argument("--list", action="store_true", help="List available backups")

    # Add target path for restore operation
    parser.add_argument("--target", help="Target path for restore operation")

    # Add status file option for VBScript integration
    parser.add_argument(
        "--status-file", action="store_true", help="Write result to status file for VBScript"
    )

    args = parser.parse_args()

    # Create backup manager
    backup_manager = BackupManager()

    success = False
    message = "Operation not executed"
    details = {}

    if args.create:
        # Create backup
        main_logger.info(f"Creating backup of file: {args.create}")
        success, message, details = backup_manager.create_backup(args.create)
        status_str = "SUCCESS" if success else "ERROR"
        print(f"{status_str}: {message}")

    elif args.restore:
        # Verify target path is provided
        if not args.target:
            main_logger.error("Target path is required for restore operation")
            print("ERROR: Target path is required for restore operation")
            parser.print_help()
            sys.exit(1)

        # Restore from backup
        main_logger.info(f"Restoring from backup {args.restore} to {args.target}")
        success, message, details = backup_manager.restore_from_backup(args.restore, args.target)
        status_str = "SUCCESS" if success else "ERROR"
        print(f"{status_str}: {message}")

    elif args.list:
        # List backups
        main_logger.info("Listing backups")
        success, message, details = backup_manager.list_backups()

        if success:
            backups = details.get("backups", [])
            if not backups:
                print("No backups found")
            else:
                print(f"Found {len(backups)} backup(s):")
                for i, backup in enumerate(backups, 1):
                    date_str = backup["datetime"].strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{i}. {backup['filename']} - {date_str}")
        else:
            print(f"Error listing backups: {message}")

    # Write status file for VBScript if requested
    if args.status_file:
        status_str = "SUCCESS" if success else "ERROR"
        write_result = write_status_file(status_str, message)
        if not write_result[0]:  # If writing status file failed
            main_logger.error(f"Failed to write status file: {write_result[1]}")

    # Return exit code based on result
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
