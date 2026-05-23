@echo off
setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "TEMPLATE_HELPER=%SCRIPT_DIR%tools\rename_template.py"
set "DOCTOR_HELPER=%SCRIPT_DIR%tools\doctor.py"
set "FIX_HELPER=%SCRIPT_DIR%tools\fix.py"
set "HOOKS_HELPER=%SCRIPT_DIR%tools\install_git_hooks.py"

if "%~1"=="--doctor" goto doctor
if "%~1"=="--fix" goto fix
if "%~1"=="--install-hooks" goto hooks
goto rename

:doctor
shift
set "TARGET_HELPER=%DOCTOR_HELPER%"
goto run

:fix
shift
set "TARGET_HELPER=%FIX_HELPER%"
goto run

:hooks
shift
set "TARGET_HELPER=%HOOKS_HELPER%"
goto run

:rename
set "TARGET_HELPER=%TEMPLATE_HELPER%"

:run
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 "%TARGET_HELPER%" %*
    exit /b !ERRORLEVEL!
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python "%TARGET_HELPER%" %*
    exit /b !ERRORLEVEL!
)

>&2 echo error: Python 3 interpreter not found. Install Python and retry.
exit /b 1
