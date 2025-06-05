#!/usr/bin/env python3
"""
Manual test script for backup_manager.py

This script provides a simple interface to test the backup_manager.py
functionality through manual verification steps following the modular,
DRY, single source of truth OOP approach.
"""

import argparse
import os
import shutil
import sys
import tempfile
import time

# Ensure we can import from the parent directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from Backups.backup_manager import BackupManager

from Utils.logging_utils import setup_logger

# Configure logging for tests
logger = setup_logger("backup_manager_tests")


class BackupManagerTester:
    """
    Test harness for BackupManager functionality.
    Provides methods to verify backup creation, rotation, restoration and file locking.
    """

    def __init__(self):
        """Initialize the test environment with temporary directories and files"""
        self.test_dir = tempfile.mkdtemp(prefix="backup_test_")
        self.backup_dir = os.path.join(self.test_dir, "backups")
        self.test_file = os.path.join(self.test_dir, "test_file.csv")
        os.makedirs(self.backup_dir, exist_ok=True)
        logger.info(f"Created test environment in: {self.test_dir}")
        print(f"Creating test environment in: {self.test_dir}")

    def create_test_file(self, content="test,data\n1,value1"):
        """Create a test file with sample content"""
        os.makedirs(os.path.dirname(self.test_file), exist_ok=True)
        with open(self.test_file, "w") as f:
            f.write(content)
        logger.info(f"Created test file at: {self.test_file}")
        print(f"Created test file at: {self.test_file}")

    def cleanup_test_files(self):
        """Remove all test files and directories"""
        try:
            shutil.rmtree(self.test_dir)
            logger.info(f"Cleaned up test directory: {self.test_dir}")
            print(f"Cleaned up test directory: {self.test_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up: {e}")
            print(f"Error cleaning up: {e}")

    def test_backup_creation(self):
        """Test creating backups"""
        print("\n=== Testing Backup Creation ===")
        logger.info("Starting backup creation test")

        # Create test file
        self.create_test_file()

        # Create backup manager
        backup_mgr = BackupManager(self.backup_dir)

        # Create backup
        success, message, details = backup_mgr.create_backup(self.test_file)

        if success:
            backup_path = details.get("backup_path", "unknown")
            print(f"SUCCESS: {message}")
            print(f"  Backup created at: {backup_path}")
            logger.info(f"Backup creation succeeded: {message}")
        else:
            print(f"ERROR: {message}")
            logger.error(f"Backup creation failed: {message}")

        # List backups
        list_success, list_message, list_details = backup_mgr.list_backups()
        backups = list_details.get("backups", []) if list_success else []

        print(f"\nFound {len(backups)} backup(s):")
        for i, backup in enumerate(backups, 1):
            print(f"  {i}. {backup['filename']}")

        return success, message, details

    def test_backup_rotation(self):
        """Test backup rotation (creating multiple backups)"""
        print("\n=== Testing Backup Rotation ===")
        logger.info("Starting backup rotation test")

        # Create test file
        self.create_test_file()

        # Create backup manager with small max_backups
        backup_mgr = BackupManager(self.backup_dir, max_backups=3)

        # Create multiple backups
        for i in range(5):
            # Modify file content to make it unique
            with open(self.test_file, "w") as f:
                f.write(f"test,data\n{i},value{i}")

            # Create backup
            success, message, details = backup_mgr.create_backup(self.test_file)
            print(f"Created backup {i + 1}: {message}")

            # Small delay to ensure different timestamps
            time.sleep(1)

        # List backups (should be only 3)
        list_success, list_message, list_details = backup_mgr.list_backups()
        backups = list_details.get("backups", []) if list_success else []

        print(f"\nFound {len(backups)} backup(s) after rotation:")
        for i, backup in enumerate(backups, 1):
            print(f"  {i}. {backup['filename']}")

        rotation_success = len(backups) == 3
        if rotation_success:
            print("SUCCESS: Rotation worked correctly (kept 3 newest backups)")
            logger.info("Backup rotation test passed")
        else:
            print(f"ERROR: Rotation did not work correctly (found {len(backups)} backups)")
            logger.error(f"Backup rotation test failed: found {len(backups)} backups, expected 3")

        return rotation_success, "Rotation test completed", {"backup_count": len(backups)}

    def test_restore(self):
        """Test restoring from backup"""
        print("\n=== Testing Restore ===")
        logger.info("Starting restore test")

        # Create test file with initial content
        initial_content = "initial,content\n1,value1"
        self.create_test_file(initial_content)

        # Create backup manager
        backup_mgr = BackupManager(self.backup_dir)

        # Create backup
        success, message, details = backup_mgr.create_backup(self.test_file)
        backup_path = details.get("backup_path") if success else None

        if not backup_path:
            logger.error("Restore test failed: Could not create initial backup")
            print("ERROR: Could not create initial backup for restore test")
            return False, "Could not create initial backup", {}

        print(f"Created backup: {os.path.basename(backup_path)}")

        # Modify original file
        modified_content = "modified,content\n2,value2"
        with open(self.test_file, "w") as f:
            f.write(modified_content)
        print("Modified original file")

        # Restore from backup
        restore_path = self.test_file + ".restored"
        restore_success, restore_message, restore_details = backup_mgr.restore_from_backup(
            backup_path, restore_path
        )

        if restore_success:
            print(f"SUCCESS: {restore_message}")

            # Verify content
            try:
                with open(restore_path) as f:
                    restored_content = f.read()

                content_match = restored_content == initial_content
                if content_match:
                    print("Restored content matches original")
                    logger.info("Restore test passed: content matches")
                else:
                    print("Restored content does not match original")
                    logger.error("Restore test partial failure: content mismatch")
                    restore_success = False
            except Exception as e:
                print(f"ERROR verifying restored content: {e}")
                logger.error(f"Restore test failed: error verifying content: {e}")
                restore_success = False
        else:
            print(f"ERROR: {restore_message}")
            logger.error(f"Restore test failed: {restore_message}")

        return restore_success, restore_message, restore_details

    def test_file_locking(self):
        """Test file locking during backup operations"""
        print("\n=== Testing File Locking ===")
        logger.info("Starting file locking test")

        # Create test file
        self.create_test_file()

        # Create backup manager
        backup_mgr = BackupManager(self.backup_dir)

        # Create first backup
        success1, message1, details1 = backup_mgr.create_backup(self.test_file)
        print(f"First backup: {message1}")

        # Simulate concurrent access by creating a second backup manager
        backup_mgr2 = BackupManager(self.backup_dir)

        # Try to create a second backup immediately (should work because locks are released)
        success2, message2, details2 = backup_mgr2.create_backup(self.test_file)
        print(f"Second backup: {message2}")

        locking_success = success1 and success2
        if locking_success:
            print("SUCCESS: File locking worked correctly")
            logger.info("File locking test passed")
        else:
            print("ERROR: File locking test failed")
            logger.error(
                f"File locking test failed: First backup: {success1}, Second backup: {success2}"
            )

        return (
            locking_success,
            "File locking test completed",
            {
                "first_backup": {"success": success1, "message": message1},
                "second_backup": {"success": success2, "message": message2},
            },
        )

    def run_all_tests(self):
        """Run all tests in sequence"""
        try:
            logger.info("Running all backup manager tests")

            # Run tests
            backup_success, backup_message, backup_details = self.test_backup_creation()
            rotation_success, rotation_message, rotation_details = self.test_backup_rotation()
            restore_success, restore_message, restore_details = self.test_restore()
            locking_success, locking_message, locking_details = self.test_file_locking()

            # Summary
            print("\n=== Test Summary ===")
            print(f"Backup Creation: {'PASS' if backup_success else 'FAIL'}")
            print(f"Backup Rotation: {'PASS' if rotation_success else 'FAIL'}")
            print(f"Restore: {'PASS' if restore_success else 'FAIL'}")
            print(f"File Locking: {'PASS' if locking_success else 'FAIL'}")

            all_passed = backup_success and rotation_success and restore_success and locking_success

            overall_status = "ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED"
            print(f"\nOverall: {overall_status}")
            logger.info(f"Test suite completed: {overall_status}")

            return (
                all_passed,
                overall_status,
                {
                    "backup_creation": backup_success,
                    "backup_rotation": rotation_success,
                    "restore": restore_success,
                    "file_locking": locking_success,
                },
            )

        finally:
            # Ask if test files should be cleaned up
            cleanup = input("\nClean up test files? (y/n): ").lower() == "y"
            if cleanup:
                self.cleanup_test_files()
            else:
                print(f"Test files kept at: {self.test_dir}")


def main():
    """Main function to parse arguments and run tests"""
    parser = argparse.ArgumentParser(description="Test backup_manager.py functionality")
    parser.add_argument(
        "--test",
        choices=["backup", "rotation", "restore", "locking", "all"],
        default="all",
        help="Test to run",
    )

    args = parser.parse_args()

    # Create tester instance
    tester = BackupManagerTester()

    # Run specified test
    if args.test == "backup":
        tester.test_backup_creation()
    elif args.test == "rotation":
        tester.test_backup_rotation()
    elif args.test == "restore":
        tester.test_restore()
    elif args.test == "locking":
        tester.test_file_locking()
    else:
        tester.run_all_tests()


if __name__ == "__main__":
    main()
