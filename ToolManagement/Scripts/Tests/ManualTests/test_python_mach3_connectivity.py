"""
Python-Mach3 Connectivity Test

This script tests the basic connectivity between Python and Mach3 by:
1. Creating a logs directory
2. Writing to a log file
3. Creating a status file for Mach3 to detect
4. Displaying system information

This is a minimal connectivity test and doesn't test specific functionality.
"""

import datetime
import os
import platform
import sys

# Print header
print("Python-Mach3 Connectivity Test")
print("------------------------------")
print(f"Python version: {sys.version}")
print(f"Operating system: {platform.system()} {platform.release()}")
print(f"Test executed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("")

# Create log directory if it doesn't exist
log_dir = r"C:\Mach3\ToolManagement\Logs"
print(f"Creating/checking log directory: {log_dir}")
os.makedirs(log_dir, exist_ok=True)

# Log execution
log_file = os.path.join(log_dir, "python_test_log.txt")
print(f"Writing to log file: {log_file}")
with open(log_file, "a") as f:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f.write(f"{timestamp} - Python-Mach3 connectivity test ran successfully\n")

# Create status file for Mach3 to detect
status_file = os.path.join(log_dir, "execution_status.txt")
print(f"Creating status file: {status_file}")
with open(status_file, "w") as f:
    f.write("SUCCESS")

print("\nRESULTS:")
print("✓ Log directory created/confirmed")
print("✓ Log entry written successfully")
print("✓ Status file created successfully")
print("✓ Python execution completed normally")
print("\nSUCCESS: Basic connectivity test completed")

# Keep console open on Windows if run directly
if platform.system() == "Windows" and not sys.stdin.isatty():
    print("\nPress Enter to exit...")
    input()

sys.exit(0)  # Exit with success code
