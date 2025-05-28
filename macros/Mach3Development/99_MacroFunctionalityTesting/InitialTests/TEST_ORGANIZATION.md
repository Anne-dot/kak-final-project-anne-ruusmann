# Test Organization

## Folder Structure
- **ShouldPass/** - Tests that should execute successfully
- **ShouldFail/** - Tests that should fail or have special behavior

## Tests in ShouldPass/ (44 tests)
1. test_01_dim_variable.m1s - Variable declaration
2. test_02_multiple_dim.m1s - Multiple variable declaration
3. test_03_constants.m1s - Const declaration
4. test_04_variant_type.m1s - Variant type behavior
5. test_05_if_then.m1s - If-Then statements
6. test_06_select_case.m1s - Select Case statements
7. test_07_for_next.m1s - For-Next loops
8. test_08_while_wend.m1s - While-Wend loops
9. test_09_do_loop.m1s - Do-Loop statements
10. test_10_exit_for.m1s - Exit For statement
11. test_11_string_len.m1s - Len() function
12. test_12_string_left_right.m1s - Left() and Right() functions
13. test_13_string_mid.m1s - Mid() function
14. test_14_string_instr.m1s - InStr() function
15. test_16_array_static.m1s - Static arrays
16. test_17_array_redim.m1s - ReDim arrays
17. test_19_error_handling.m1s - On Error Resume Next
18. test_23_create_object.m1s - CreateObject()
19. test_24_set_keyword.m1s - Set keyword
20. test_25_file_exists.m1s - FileExists()
21. test_26_create_text_file.m1s - CreateTextFile()
22. test_27_getmainfolder.m1s - GetMainFolder()
23. test_28_open_text_file.m1s - OpenTextFile()
24. test_29_read_all.m1s - ReadAll()
25. test_30_atendofstream.m1s - AtEndOfStream
26. test_31_append_file.m1s - Append to file
27. test_32_folder_exists.m1s - FolderExists()
28. test_33_math_functions.m1s - Math functions
29. test_34_type_checking.m1s - Type checking functions
30. test_35_type_conversion.m1s - Type conversion
31. test_36_timer_function.m1s - Timer function
32. test_39_expand_directive.m1s - #expand directive
33. test_40_getoemdro.m1s - GetOEMDRO()
34. test_41_setuserdro.m1s - SetUserDRO()
35. test_42_code_function.m1s - Code() function
36. test_43_ismoving.m1s - IsMoving()
37. test_44_sleep_after_message.m1s - Sleep after Message (educational)
38. test_code_gcode.m1s - G-code execution
39. test_getcurrenttool.m1s - GetCurrentTool()
40. test_gettoolparam.m1s - GetToolParam()
41. test_message_display.m1s - Message display testing
42. test_on_error_resume_next.m1s - Error handling validation
43. test_setcurrenttool.m1s - SetCurrentTool()
44. test_settoolparam.m1s - SetToolParam()

## Tests in ShouldFail/ (7 tests)
1. test_15_string_replace.m1s - Replace() function (not supported)
2. test_18_split_function.m1s - Split() function (not supported)
3. test_20_user_function.m1s - User-defined Function (syntax error)
4. test_21_user_sub.m1s - User-defined Sub (syntax error)
5. test_22_exit_sub.m1s - Exit Sub (terminates entire macro)
6. test_37_settimer_gettimer.m1s - SetTimer/GetTimer (91-93% unreliable)
7. test_38_msgbox.m1s - MsgBox (creates blocking dialogs)

## Total Tests: 51
- Should Pass: 44
- Should Fail: 7

Note: Tests 15, 18, 20-22, 37-38 are in ShouldFail because they either:
- Use functions not supported in Mach3 (Replace, Split)
- Cause syntax errors (Function, Sub)
- Have problematic behavior (Exit Sub, MsgBox)
- Are unreliable (SetTimer/GetTimer)