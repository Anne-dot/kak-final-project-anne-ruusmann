"""
Cross-platform test for GCodeProcessor modules.

This test validates G-code normalization and safety preprocessing
functionality across Linux and Windows platforms using standardized
Utils modules and ADHD-friendly organization.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add Scripts directory to path using proper path resolution
current_file = Path(__file__).resolve()
scripts_dir = current_file.parent.parent.parent.parent
sys.path.insert(0, str(scripts_dir))

# Import Utils modules for DRY principles
from Utils.path_utils import PathUtils
from Utils.logging_utils import setup_logger
from Utils.error_utils import ErrorHandler
from Utils.config import AppConfig

# Import modules under test
from GCodeProcessor import GCodeNormalizer, GCodePreprocessor


class GCodeTestRunner:
    """
    Cross-platform test runner for G-code processing modules.
    
    Follows ADHD-friendly organization with clear separation of concerns:
    - Test data discovery
    - Module testing
    - Results reporting
    """
    
    def __init__(self):
        """Initialize test runner with logging and paths."""
        self.logger = setup_logger(__name__)
        self.test_results = []
        
    def discover_test_files(self) -> List[Path]:
        """
        Discover G-code test files using same pattern as existing tests.
        
        Returns:
            List[Path]: Paths to available test files
        """
        # Use same pattern as existing DXF tests
        test_data_dir = Path(__file__).parent.parent.parent / "TestData" / "Gcode"
        
        if not test_data_dir.exists():
            self.logger.warning(f"G-code test data directory not found: {test_data_dir}")
            return []
        
        # Find original (non-processed) G-code files
        test_files = []
        for file_path in test_data_dir.glob("*.txt"):
            if not any(suffix in file_path.name for suffix in ["_normalized", "_safe", "_test"]):
                test_files.append(file_path)
        
        return sorted(test_files)
    
    def test_normalizer(self, input_file: Path) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Test G-code normalizer on input file.
        
        Args:
            input_file: Path to G-code file to test
            
        Returns:
            Tuple: (success, message, details)
        """
        normalizer = GCodeNormalizer()
        
        # Generate output path
        output_file = input_file.with_stem(f"{input_file.stem}_test_normalized")
        
        try:
            success, message, details = normalizer.normalize_file(
                str(input_file), str(output_file)
            )
            
            if success:
                self.logger.info(f"Normalizer test passed: {input_file.name}")
            else:
                self.logger.error(f"Normalizer test failed: {message}")
                
            return success, message, details
            
        except Exception as e:
            error_msg = f"Normalizer test exception: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, {}
    
    def test_preprocessor(self, input_file: Path) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Test G-code safety preprocessor on input file.
        
        Args:
            input_file: Path to G-code file to test
            
        Returns:
            Tuple: (success, message, details)
        """
        preprocessor = GCodePreprocessor()
        
        # Generate output path
        output_file = input_file.with_stem(f"{input_file.stem}_test_safe")
        
        try:
            success, message, details = preprocessor.preprocess_file(
                str(input_file), str(output_file)
            )
            
            if success:
                self.logger.info(f"Preprocessor test passed: {input_file.name}")
            else:
                self.logger.error(f"Preprocessor test failed: {message}")
                
            return success, message, details
            
        except Exception as e:
            error_msg = f"Preprocessor test exception: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, {}
    
    def run_all_tests(self) -> None:
        """Run all tests and report results."""
        print(f"G-code Processor Test Runner")
        print(f"Platform: {AppConfig.get_platform()}")
        print("=" * 50)
        
        # Discover test files
        test_files = self.discover_test_files()
        if not test_files:
            print("No test files found.")
            return
        
        print(f"Found {len(test_files)} test files:")
        for test_file in test_files:
            print(f"  - {test_file.name}")
        print()
        
        # Test each file
        for test_file in test_files:
            self._test_single_file(test_file)
        
        # Report summary
        self._report_summary()
    
    def _test_single_file(self, test_file: Path) -> None:
        """Test both modules on a single file."""
        print(f"Testing: {test_file.name}")
        
        # Test normalizer
        norm_success, norm_msg, norm_details = self.test_normalizer(test_file)
        self.test_results.append({
            "file": test_file.name,
            "module": "Normalizer",
            "success": norm_success,
            "message": norm_msg,
            "details": norm_details
        })
        
        # Test preprocessor
        prep_success, prep_msg, prep_details = self.test_preprocessor(test_file)
        self.test_results.append({
            "file": test_file.name,
            "module": "Preprocessor", 
            "success": prep_success,
            "message": prep_msg,
            "details": prep_details
        })
        
        # Print results for this file
        norm_status = "✓" if norm_success else "✗"
        prep_status = "✓" if prep_success else "✗"
        print(f"  Normalizer:   {norm_status}")
        print(f"  Preprocessor: {prep_status}")
        print()
    
    def _report_summary(self) -> None:
        """Report test summary."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print("=" * 50)
        print("Test Summary:")
        print(f"  Total tests:  {total_tests}")
        print(f"  Passed:       {passed_tests}")
        print(f"  Failed:       {failed_tests}")
        
        if failed_tests > 0:
            print("\nFailed tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['file']} ({result['module']}): {result['message']}")


def main():
    """Main test function."""
    try:
        runner = GCodeTestRunner()
        runner.run_all_tests()
    except Exception as e:
        print(f"Test runner error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()