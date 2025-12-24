@echo off
echo ==========================================
echo Lending Tracker - Starting...
echo ==========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

REM Run the application
echo.
echo ==========================================
echo Starting Flask application...
echo Default PIN: 1234
echo Access at: http://localhost:5000
echo ==========================================
echo.

python app.py

pause
