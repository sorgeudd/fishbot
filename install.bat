@echo off
echo ===============================
echo    Setting up Fishing Bot...
echo ===============================

REM Check if Python is installed
python --version > nul 2>&1
if errorlevel 1 (
    echo Python is not installed!
    echo Please install Python 3.8 or later from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo.
echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing required packages...
echo This might take a minute...

echo Installing numpy...
pip install numpy
if errorlevel 1 goto error

echo Installing OpenCV...
pip install opencv-python
if errorlevel 1 goto error

echo Installing Pillow...
pip install pillow
if errorlevel 1 goto error

echo Installing PyAudio...
pip install pyaudio
if errorlevel 1 goto error

echo Installing PyAutoGUI...
pip install pyautogui
if errorlevel 1 goto error

echo Installing Torch...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto error

echo Installing Transformers...
pip install transformers
if errorlevel 1 goto error

echo.
echo ===================================
echo    Installation Complete!
echo ===================================
echo.
echo To start the Fishing Bot:
echo 1. Double click on 'start_bot.bat'
echo    OR
echo 2. Run 'python fishing_bot.py' in terminal
echo.
echo Note: Make sure to run as Administrator
echo for proper keyboard control functionality
echo.
pause

exit /b 0

:error
echo.
echo Error during installation!
echo Please check your internet connection and try again
echo If the problem persists, try running as Administrator
pause
exit /b 1