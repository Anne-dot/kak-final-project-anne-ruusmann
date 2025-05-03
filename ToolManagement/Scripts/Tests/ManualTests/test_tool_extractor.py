import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from DXF.file_loader import DxfLoader
from DXF.drilling_extractor import DrillingExtractor
from DXF.tool_extractor import ToolRequirementExtractor

# Set up path to test data
test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")
dxf_dir = os.path.join(test_data_dir, "DXF")

# Simple DXF file selector
def select_dxf_file(auto_select=True):
    """Display a simple selection menu for DXF files.
    
    Args:
        auto_select: If True, automatically select the first file
                    If False, prompt for user input
    """
    dxf_files = [f for f in os.listdir(dxf_dir) if f.lower().endswith('.dxf')]
    
    if not dxf_files:
        print("No DXF files found in TestData/DXF directory.")
        return None
    
    print("\nAvailable DXF files:")
    for i, file in enumerate(dxf_files):
        print(f"{i+1}. {file}")
    
    if auto_select:
        # Default to first file for automated testing
        selected_index = 0
        print(f"\nAutomatically selecting: {dxf_files[selected_index]}")
    else:
        # Interactive mode for manual testing
        while True:
            try:
                choice = input("\nSelect a file number (or press Enter for default): ")
                if choice.strip() == "":
                    # Default to first file
                    selected_index = 0
                    break
                else:
                    selected_index = int(choice) - 1
                    if 0 <= selected_index < len(dxf_files):
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(dxf_files)}")
            except ValueError:
                print("Please enter a valid number")
    
    selected_file = dxf_files[selected_index]
    return os.path.join(dxf_dir, selected_file)

# Create the required extractors
loader = DxfLoader()
drill_extractor = DrillingExtractor()
tool_extractor = ToolRequirementExtractor()

print("=== Tool Requirements Extraction Test ===")

# Let user select a DXF file
dxf_file_path = select_dxf_file()
if not dxf_file_path:
    print("No DXF file selected. Exiting.")
    sys.exit(1)

print(f"Using test DXF file: {dxf_file_path}")

# Step 1: Load the DXF file
print("\nStep 1: Loading DXF file...")
success, message, details = loader.load_dxf(dxf_file_path)
doc = details.get('document') if success else None

if not success:
    print(f"Error loading DXF: {message}")
    sys.exit(1)

print(f"SUCCESS: DXF loaded successfully: {message}")

# Step 2: Extract drilling information
print("\nStep 2: Extracting drilling information...")
drill_success, drill_message, drill_details = drill_extractor.extract_all_drilling_info(doc)

if not drill_success:
    print(f"Error extracting drilling info: {drill_message}")
    sys.exit(1)

# With new error response format, the drilling_info is the entire drill_details
drilling_info = drill_details

# Debug the structure
print(f"SUCCESS: Drilling information extracted: {drill_message}")
print(f"  Found {len(drilling_info.get('points', []))} drilling points")
print("\nDebugging drilling_info structure:")
import json
try:
    # Convert only serializable parts for display
    debug_info = {}
    for k, v in drilling_info.items():
        if k == 'points':
            debug_info[k] = f"List with {len(v)} DrillPoint objects"
        elif k == 'parameters':
            debug_info[k] = json.dumps({'vertical': len(v), 'horizontal': 0})
        else:
            debug_info[k] = str(v)
    print(json.dumps(debug_info, indent=2))
except Exception as e:
    print(f"Error debugging structure: {str(e)}")

# Step 3: Extract tool requirements
print("\nStep 3: Extracting tool requirements...")
# Fix the drilling_info structure to match what tool_extractor expects
# It expects a different format than what drilling_extractor now returns
fixed_drilling_info = {
    'parameters': {
        'vertical': drilling_info.get('parameters', []),
        'horizontal': []
    }
}
tool_success, tool_message, requirements = tool_extractor.extract_tool_requirements(doc, fixed_drilling_info)

if not tool_success:
    print(f"Error extracting tool requirements: {tool_message}")
    sys.exit(1)

print(f"SUCCESS: Tool requirements extracted: {tool_message}")

# Step 4: Display extracted information
print("\nStep 4: Examining extracted tool requirements...")

# Display diameter information
if 'all_diameters' in requirements:
    diameters = sorted(list(requirements['all_diameters']))
    print(f"\nRequired drill diameters: {len(diameters)} unique sizes")
    for diameter in diameters:
        print(f"  - {diameter:.1f}mm")

# Display vertical drill information
if 'vertical_drills' in requirements and requirements['vertical_drills']:
    print(f"\nVertical drilling operations: {len(requirements['vertical_drills'])}")
    # Group by diameter and count
    diameter_counts = {}
    for req in requirements['vertical_drills']:
        diameter = round(req['diameter'], 1)
        if diameter not in diameter_counts:
            diameter_counts[diameter] = 0
        diameter_counts[diameter] += 1
    
    for diameter, count in sorted(diameter_counts.items()):
        print(f"  - {diameter:.1f}mm: {count} operations")

# Display horizontal drill information
if 'horizontal_drills' in requirements and requirements['horizontal_drills']:
    print(f"\nHorizontal drilling operations: {len(requirements['horizontal_drills'])}")
    # Group by diameter, edge and count
    edge_diameter_counts = {}
    for req in requirements['horizontal_drills']:
        diameter = round(req['diameter'], 1)
        edge = req['edge']
        key = f"{edge}_{diameter}"
        if key not in edge_diameter_counts:
            edge_diameter_counts[key] = 0
        edge_diameter_counts[key] += 1
    
    for key, count in sorted(edge_diameter_counts.items()):
        edge, diameter = key.split('_')
        print(f"  - {edge} edge, {float(diameter):.1f}mm: {count} operations")

# Step 5: Display human-readable summary
if 'readable_summary' in requirements:
    print("\nStep 5: Human-readable requirements summary:")
    print("="*50)
    print(requirements['readable_summary'])
    print("="*50)

print("\nTest completed successfully.")