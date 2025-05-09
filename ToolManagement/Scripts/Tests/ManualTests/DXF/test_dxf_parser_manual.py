"""
Manual test for the DXF parser module.

This script provides a more comprehensive manual test for the DXFParser
class beyond the basic test built into the parser module.
"""

import os
import sys
from pathlib import Path

# Add parent directories to path for imports
script_dir = Path(__file__).parent.parent.parent.parent
if str(script_dir) not in sys.path:
    sys.path.append(str(script_dir))

# Import utilities and the parser
from DXF.parser import DXFParser
from Utils.logging_utils import setup_logger

# Set up logger
logger = setup_logger(__name__)

def test_parser_with_all_test_files():
    """Test the parser with all available test DXF files."""
    print("DXF Parser Manual Test")
    print("=====================")
    
    # Get path to test DXF files
    test_data_dir = Path(__file__).parent.parent.parent / "TestData" / "DXF"
    
    if not test_data_dir.exists():
        print(f"Error: Test data directory not found: {test_data_dir}")
        return
    
    # Find all DXF files in the test directory
    dxf_files = list(test_data_dir.glob("*.dxf"))
    
    if not dxf_files:
        print(f"No DXF test files found in {test_data_dir}")
        return
    
    print(f"Found {len(dxf_files)} test files")
    
    # Test each file
    for idx, file_path in enumerate(dxf_files, 1):
        print(f"\n{idx}/{len(dxf_files)} Testing: {file_path.name}")
        
        # Create a new parser instance for each file
        parser = DXFParser()
        
        # Test loading and parsing
        print("- Loading file...")
        load_success, load_message, load_result = parser.load_file(file_path)
        
        if not load_success:
            print(f"  ERROR: {load_message}")
            continue
        
        print(f"  Success: {load_message}")
        print(f"  Entity count: {load_result['entity_count']}")
        
        # Test get_file_info
        print("- Getting file info...")
        info_success, info_message, info_data = parser.get_file_info()
        
        if not info_success:
            print(f"  ERROR: {info_message}")
            continue
        
        print(f"  {info_message}")
        
        # Display entity types
        print("- Entity types:")
        for entity_type, count in info_data["entity_types"].items():
            print(f"  {entity_type}: {count}")
        
        # Display layers
        print("- Layers:")
        for layer in info_data["layers"]:
            print(f"  {layer}")
    
    print("\nAll tests completed!")


if __name__ == "__main__":
    test_parser_with_all_test_files()