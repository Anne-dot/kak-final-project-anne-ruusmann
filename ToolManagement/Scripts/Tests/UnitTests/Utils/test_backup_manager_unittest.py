#!/usr/bin/env python3
"""
Unit tests for backup_manager.py

This module contains unit tests for the backup_manager.py script.
It tests the BackupRotation and BackupManager classes.
"""

import sys
import os
import unittest
import tempfile
from unittest.mock import patch, MagicMock
import shutil
import time
import logging

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Backups'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Mock the setup_logger function to avoid logging issues
with patch('Utils.logging_utils.setup_logger', return_value=logging.getLogger('backup_manager')):
    from backup_manager import BackupManager, BackupRotation

class TestBackupRotation(unittest.TestCase):
    """Test the BackupRotation class"""
    
    def setUp(self):
        """Set up the test environment"""
        # Create a temp directory for testing
        self.test_dir = tempfile.mkdtemp(prefix="backup_test_")
        self.backup_dir = os.path.join(self.test_dir, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Create some test backup files
        self.test_files = []
        for i in range(5):
            filename = f"test_{i}.csv"
            filepath = os.path.join(self.backup_dir, filename)
            with open(filepath, 'w') as f:
                f.write(f"test data {i}")
            self.test_files.append(filepath)
            # Sleep to ensure different creation times
            time.sleep(0.1)
    
    def tearDown(self):
        """Clean up the test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_list_backups(self):
        """Test listing backups"""
        rotation = BackupRotation(self.backup_dir)
        success, message, details = rotation.list_backups()
        
        # Check success status
        self.assertTrue(success)
        
        # Get backups from details
        backups = details.get("backups", [])
        
        # Check if we found all files
        self.assertEqual(len(backups), 5)
        
        # Check if files are sorted by timestamp (newest first)
        timestamps = [b['timestamp'] for b in backups]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))
    
    def test_prune(self):
        """Test pruning old backups"""
        # Create rotation with max_backups=3
        rotation = BackupRotation(self.backup_dir, max_backups=3)
        
        # Prune backups
        success, message, details = rotation.prune()
        
        # Check success status
        self.assertTrue(success)
        
        # Check if correct number of files were removed
        self.assertEqual(details.get("removed_count", 0), 2)
        
        # Check if only 3 files remain
        success, message, list_details = rotation.list_backups()
        backups = list_details.get("backups", [])
        self.assertEqual(len(backups), 3)
        
        # Check if newest files were kept
        filenames = [os.path.basename(b['path']) for b in backups]
        self.assertIn("test_4.csv", filenames)
        self.assertIn("test_3.csv", filenames)
        self.assertIn("test_2.csv", filenames)


class TestBackupManager(unittest.TestCase):
    """Test the BackupManager class"""
    
    def setUp(self):
        """Set up the test environment"""
        # Create a temp directory for testing
        self.test_dir = tempfile.mkdtemp(prefix="backup_test_")
        self.backup_dir = os.path.join(self.test_dir, "backups")
        self.test_file = os.path.join(self.test_dir, "test_file.csv")
        
        # Create test file
        with open(self.test_file, 'w') as f:
            f.write("test,data\n1,value1")
        
        # Create backup manager
        self.backup_mgr = BackupManager(self.backup_dir)
    
    def tearDown(self):
        """Clean up the test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_create_backup(self):
        """Test creating a backup"""
        success, message, details = self.backup_mgr.create_backup(self.test_file)
        
        # Check result
        self.assertTrue(success)
        self.assertTrue('backup_path' in details)
        self.assertTrue(os.path.exists(details['backup_path']))
        
        # Check backup content
        with open(details['backup_path'], 'r') as f:
            content = f.read()
        with open(self.test_file, 'r') as f:
            original = f.read()
        
        self.assertEqual(content, original)
    
    def test_create_backup_missing_file(self):
        """Test creating a backup of a non-existent file"""
        missing_file = os.path.join(self.test_dir, "does_not_exist.csv")
        success, message, details = self.backup_mgr.create_backup(missing_file)
        
        # Check result
        self.assertFalse(success)
        self.assertIn("does not exist", message)
    
    def test_restore_from_backup(self):
        """Test restoring from a backup"""
        # Create backup
        success, message, backup_details = self.backup_mgr.create_backup(self.test_file)
        backup_path = backup_details['backup_path']
        
        # Change original file
        with open(self.test_file, 'w') as f:
            f.write("modified,data\n2,value2")
        
        # Create target path
        target_path = os.path.join(self.test_dir, "restored_file.csv")
        
        # Restore from backup
        success, message, details = self.backup_mgr.restore_from_backup(backup_path, target_path)
        
        # Check result
        self.assertTrue(success)
        self.assertTrue(os.path.exists(target_path))
        
        # Check restored content
        with open(target_path, 'r') as f:
            restored = f.read()
        with open(self.test_file, 'r') as f:
            modified = f.read()
        
        self.assertNotEqual(restored, modified)
        self.assertEqual(restored, "test,data\n1,value1")
    
    def test_restore_missing_backup(self):
        """Test restoring from a non-existent backup"""
        missing_backup = os.path.join(self.backup_dir, "does_not_exist.csv")
        target_path = os.path.join(self.test_dir, "restored_file.csv")
        
        success, message, details = self.backup_mgr.restore_from_backup(missing_backup, target_path)
        
        # Check result
        self.assertFalse(success)
        self.assertIn("does not exist", message)
    
    def test_restore_safety_backup(self):
        """Test that safety backup is created when restoring"""
        # Create backup
        success, message, backup_details = self.backup_mgr.create_backup(self.test_file)
        backup_path = backup_details['backup_path']
        
        # Restore to same location (should create safety backup)
        success, message, details = self.backup_mgr.restore_from_backup(backup_path, self.test_file)
        
        # Check result
        self.assertTrue(success)
        self.assertTrue('safety_backup' in details)
        self.assertTrue(os.path.exists(details['safety_backup']))


if __name__ == '__main__':
    unittest.main()
