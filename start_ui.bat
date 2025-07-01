@echo off
echo 🚀 Resume Agent UI Launcher
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo    Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "resume_agent_ui.py" (
    echo ❌ resume_agent_ui.py not found
    echo    Please run this script from the resume_agent directory
    pause
    exit /b 1
)

echo ✅ Python found
echo 🌐 Starting Resume Agent UI...
echo    Open your browser to: http://localhost:5000
echo.
echo 💡 Press Ctrl+C to stop the server
echo ========================================
echo.

REM Run the UI launcher
python start_ui.py

echo.
echo 👋 Resume Agent UI stopped
pause 