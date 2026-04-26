@echo off
title AeroFramework - Editable Installation
setlocal

:: Change to the script's directory for safety
cd /d "%~dp0"

echo ==================================================
echo   AeroFramework: Installation in progress...
echo ==================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRORE] Python was not found in PATH.
    echo Please ensure Python is installed and added to your environment variables.
    pause
    exit /b
)

:: Execute editable installation
echo Running: pip install -e .
pip install -e .

if %errorlevel% equ 0 (
    echo.
    echo ==================================================
    echo   INSTALLATION COMPLETED SUCCESSFULLY!
    echo   You can now use 'import aeroframework'
    echo ==================================================
) else (
    echo.
    echo [ERRORE] Installation failed.
)

echo.
pause