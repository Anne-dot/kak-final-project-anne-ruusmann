CONFIGURATION FILES STRUCTURE
==========================

This folder contains configuration constants organized by category.
Each file should be focused on a specific aspect of the system.

Suggested Configuration Files:
-----------------------------

1. ToolDataDroConfig.m1s
   - DRO number assignments for tool data storage
   - Tool parameter offsets in DRO blocks
   - System status DROs

2. ToolValidationConfig.m1s
   - Min/max values for tool parameters
   - Valid tool types and directions
   - Reserved tool numbers

3. MachineLimitsConfig.m1s
   - Axis travel limits
   - Speed and feed rate limits
   - Safe movement heights and positions

4. TimeoutConfig.m1s
   - Operation timeout values
   - User interaction timeouts
   - Movement and spindle timeouts

5. PathsConfig.m1s
   - File paths and locations
   - CSV filenames and formats
   - Backup directories

6. SystemConfig.m1s
   - Debug settings
   - System-wide flags
   - General constants

USAGE INSTRUCTIONS:
-----------------
1. Only #expand the specific config files needed by each macro
2. Avoid duplicating constants across files (follow DRY principle)
3. Keep configuration values separate from implementation logic
4. Document each constant with clear comments