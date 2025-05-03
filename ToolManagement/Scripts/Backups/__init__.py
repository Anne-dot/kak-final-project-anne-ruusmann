"""
Backups package for tool data backup management.

This package provides functionality for creating, managing, and
restoring backups of tool data files, ensuring data safety during
system operations.

Classes and Functions:
    - BackupManager: Main class for backup operations
    - BackupRotation: Rotation management for backup files
"""

from .backup_manager import BackupManager, BackupRotation

__all__ = ['BackupManager', 'BackupRotation']