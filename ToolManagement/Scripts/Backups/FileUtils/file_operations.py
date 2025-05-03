"""
File operations utilities for the FileLock system.

This module provides utility functions for common file operations
used by the FileLock class, with proper error handling.
"""

import os
import time
import random
from typing import Dict, Any, Optional, Tuple

# Import from Utils package
from Utils.logging_utils import setup_logger, log_exception
from Utils.error_utils import (
    ErrorHandler, BaseError, FileError, ErrorSeverity, ErrorCategory
)

# Set up logger
logger = setup_logger(__name__)


def create_lock_file(lock_file_path: str, content_dict: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Create a lock file with the given content.
    
    Args:
        lock_file_path: Path where lock file should be created
        content_dict: Dictionary of values to write to the lock file
        
    Returns:
        Tuple: (success, message, details) where:
            - success is a boolean indicating if the lock file was created successfully
            - message contains success details or error message
            - details contains operation information or error details
    """
    try:
        logger.info(f"Creating lock file at {lock_file_path}")
        
        # Create parent directory if it doesn't exist
        parent_dir = os.path.dirname(lock_file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir)
            logger.info(f"Created parent directory: {parent_dir}")
        
        # Write lock file content
        with open(lock_file_path, 'w') as f:
            for key, value in content_dict.items():
                f.write(f"{key}: {value}\n")
        
        logger.info(f"Successfully created lock file with {len(content_dict)} entries")
        return ErrorHandler.create_success_response(
            message=f"Successfully created lock file: {lock_file_path}",
            data={
                "lock_file_path": lock_file_path,
                "content_keys": list(content_dict.keys())
            }
        )
    except PermissionError:
        error_msg = f"Permission denied creating lock file: {lock_file_path}"
        logger.error(error_msg)
        return ErrorHandler.from_exception(
            FileError(
                message=error_msg,
                file_path=lock_file_path,
                severity=ErrorSeverity.ERROR,
                details={"error": "permission_denied"}
            )
        )
    except Exception as e:
        error_msg = f"Error creating lock file {lock_file_path}: {str(e)}"
        log_exception(logger, error_msg)
        return ErrorHandler.from_exception(
            FileError(
                message=error_msg,
                file_path=lock_file_path,
                severity=ErrorSeverity.ERROR,
                details={"error_type": type(e).__name__}
            )
        )


def remove_file_safely(file_path: str, max_retries: int = 3, retry_delay: float = 0.5) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Remove a file with retry logic for handling temporary access issues.
    
    Args:
        file_path: Path to the file to remove
        max_retries: Maximum number of removal attempts
        retry_delay: Base delay between retries in seconds
        
    Returns:
        Tuple: (success, message, details) where:
            - success is a boolean indicating if the file was removed successfully
            - message contains success details or error message
            - details contains removal information or error details
    """
    logger.info(f"Removing file safely: {file_path}")
    
    if not os.path.exists(file_path):
        logger.info(f"File does not exist, nothing to remove: {file_path}")
        return ErrorHandler.create_success_response(
            message="File does not exist, nothing to remove",
            data={"file_path": file_path}
        )
        
    last_error = None
    for attempt in range(max_retries):
        try:
            os.remove(file_path)
            logger.info(f"Successfully removed file: {file_path}")
            return ErrorHandler.create_success_response(
                message="File removed successfully",
                data={
                    "file_path": file_path,
                    "attempts_required": attempt + 1
                }
            )
        except PermissionError as e:
            last_error = e
            if attempt == max_retries - 1:
                # Last attempt failed
                error_msg = f"Permission denied removing file {file_path} after {max_retries} attempts"
                logger.error(error_msg)
                return ErrorHandler.from_exception(
                    FileError(
                        message=error_msg,
                        file_path=file_path,
                        severity=ErrorSeverity.ERROR,
                        details={"error": "permission_denied", "attempts": max_retries}
                    )
                )
            
            # Add jitter to retry delay to prevent synchronization issues
            actual_delay = retry_delay * (1 + attempt) * (1 + random.random())
            logger.info(f"Retrying file removal in {actual_delay:.2f} seconds (attempt {attempt+1}/{max_retries})")
            time.sleep(actual_delay)
        except Exception as e:
            last_error = e
            if attempt == max_retries - 1:
                # Last attempt failed
                error_msg = f"Failed to remove file {file_path} after {max_retries} attempts: {str(e)}"
                log_exception(logger, error_msg)
                return ErrorHandler.from_exception(
                    FileError(
                        message=error_msg,
                        file_path=file_path,
                        severity=ErrorSeverity.ERROR,
                        details={"error_type": type(e).__name__, "attempts": max_retries}
                    )
                )
            
            # Add jitter to retry delay to prevent synchronization issues
            actual_delay = retry_delay * (1 + attempt) * (1 + random.random())
            logger.info(f"Retrying file removal in {actual_delay:.2f} seconds (attempt {attempt+1}/{max_retries})")
            time.sleep(actual_delay)
            
    # This should never happen (we should return from the loop), but just in case
    error_msg = f"Unexpected error removing file {file_path}"
    logger.error(error_msg)
    return ErrorHandler.from_exception(
        FileError(
            message=error_msg,
            file_path=file_path,
            severity=ErrorSeverity.ERROR,
            details={"error": str(last_error) if last_error else "unknown"}
        )
    )


def backup_file(file_path: str, backup_dir: Optional[str] = None, max_backups: int = 10) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Create a timestamped backup of a file.
    
    Args:
        file_path: Path to the file to backup
        backup_dir: Directory to store backups (default: same as original)
        max_backups: Maximum number of backups to keep
        
    Returns:
        Tuple: (success, message, details) where:
            - success is a boolean indicating if backup was created successfully
            - message contains success details or error message
            - details contains backup information or error details
    """
    try:
        logger.info(f"Creating backup of file: {file_path}")
        
        if not os.path.exists(file_path):
            logger.warning(f"Cannot backup non-existent file: {file_path}")
            return ErrorHandler.from_exception(
                FileError(
                    message=f"Cannot backup non-existent file: {file_path}",
                    file_path=file_path,
                    severity=ErrorSeverity.WARNING,
                    details={"error": "file_not_found"}
                )
            )
            
        # Get file name and extension
        base_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        name, ext = os.path.splitext(file_name)
        
        # Use provided backup directory or default to same directory
        if not backup_dir:
            backup_dir = base_dir
            
        # Create backup directory if it doesn't exist
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            logger.info(f"Created backup directory: {backup_dir}")
            
        # Create timestamped backup file name
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"{name}_{timestamp}{ext}"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Copy file to backup location
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        
        # Prune old backups if needed
        pruned_count = 0
        if max_backups > 0:
            success, message, prune_details = prune_old_backups(backup_dir, name, ext, max_backups)
            if success:
                pruned_count = prune_details.get("removed_count", 0)
            else:
                logger.warning(f"Warning during backup pruning: {message}")
            
        return ErrorHandler.create_success_response(
            message=f"Successfully created backup: {backup_name}",
            data={
                "backup_path": backup_path,
                "backup_name": backup_name,
                "original_file": file_path,
                "backup_dir": backup_dir,
                "pruned_backups": pruned_count
            }
        )
    except PermissionError as e:
        error_msg = f"Permission denied creating backup of {file_path}"
        logger.error(error_msg)
        return ErrorHandler.from_exception(
            FileError(
                message=error_msg,
                file_path=file_path,
                severity=ErrorSeverity.ERROR,
                details={"error": "permission_denied"}
            )
        )
    except Exception as e:
        error_msg = f"Error creating backup of {file_path}: {str(e)}"
        log_exception(logger, error_msg)
        return ErrorHandler.from_exception(
            FileError(
                message=error_msg,
                file_path=file_path,
                severity=ErrorSeverity.ERROR,
                details={"error_type": type(e).__name__}
            )
        )


def prune_old_backups(backup_dir: str, base_name: str, extension: str, max_backups: int) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Remove old backup files when there are more than max_backups.
    
    Args:
        backup_dir: Directory containing backups
        base_name: Base name of the file (without timestamp)
        extension: File extension
        max_backups: Maximum number of backups to keep
        
    Returns:
        Tuple: (success, message, details) where:
            - success is a boolean indicating if pruning was successful
            - message contains success details or error message
            - details contains pruning information or error details
    """
    try:
        logger.info(f"Pruning old backups in {backup_dir} for {base_name}{extension}, keeping {max_backups}")
        
        # Get all backup files matching pattern
        backup_files = []
        for file in os.listdir(backup_dir):
            if file.startswith(base_name + "_") and file.endswith(extension):
                file_path = os.path.join(backup_dir, file)
                backup_files.append((file_path, os.path.getmtime(file_path)))
        
        # Sort by modification time (oldest first)
        backup_files.sort(key=lambda x: x[1])
        
        # Remove older backups if we have more than max_backups
        removed_count = 0
        failed_removals = []
        
        if len(backup_files) > max_backups:
            files_to_remove = backup_files[:-max_backups]  # Keep newest max_backups
            for file_path, _ in files_to_remove:
                success, message, details = remove_file_safely(file_path)
                if success:
                    removed_count += 1
                    logger.info(f"Removed old backup: {os.path.basename(file_path)}")
                else:
                    logger.warning(f"Failed to remove old backup: {os.path.basename(file_path)}")
                    failed_removals.append({
                        "file": os.path.basename(file_path),
                        "error": message
                    })
            
            if failed_removals:
                warning_msg = f"Partially pruned backups: removed {removed_count} of {len(files_to_remove)}"
                logger.warning(warning_msg)
                return ErrorHandler.create_success_response(
                    message=warning_msg,
                    data={
                        "removed_count": removed_count,
                        "total_backups": len(backup_files),
                        "max_backups": max_backups,
                        "failed_removals": failed_removals
                    }
                )
            
            return ErrorHandler.create_success_response(
                message=f"Successfully pruned {removed_count} old backups",
                data={
                    "removed_count": removed_count,
                    "total_backups": len(backup_files),
                    "max_backups": max_backups
                }
            )
        else:
            logger.info(f"No pruning needed, only {len(backup_files)} backups exist (max is {max_backups})")
            return ErrorHandler.create_success_response(
                message="No pruning needed, backup count is within limit",
                data={
                    "removed_count": 0,
                    "total_backups": len(backup_files),
                    "max_backups": max_backups
                }
            )
            
    except PermissionError as e:
        error_msg = f"Permission denied accessing backup directory: {backup_dir}"
        logger.error(error_msg)
        return ErrorHandler.from_exception(
            FileError(
                message=error_msg,
                file_path=backup_dir,
                severity=ErrorSeverity.ERROR,
                details={"error": "permission_denied"}
            )
        )
    except Exception as e:
        error_msg = f"Error pruning old backups: {str(e)}"
        log_exception(logger, error_msg)
        return ErrorHandler.from_exception(
            FileError(
                message=error_msg,
                file_path=backup_dir,
                severity=ErrorSeverity.ERROR,
                details={
                    "error_type": type(e).__name__,
                    "base_name": base_name,
                    "extension": extension
                }
            )
        )
