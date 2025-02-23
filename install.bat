@echo off
echo ===============================
echo    Setting up Fishing Bot...
echo ===============================

REM Check system architecture
reg Query "HKLM\Hardware\Description\System\CentralProcessor\0" | find /i "x86" > NUL && set ARCH=32BIT || set ARCH=64BIT
if %ARCH%==32BIT (
    echo Warning: 32-bit Windows detected. 64-bit is recommended for optimal performance.
    echo Some AI features might be limited on 32-bit systems.
    echo.
)

REM Check if Python is installed
python --version > nul 2>&1
if errorlevel 1 (
    echo Python is not installed!
    echo Please install Python 3.8 or later from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check Python version
python -c "import sys; ver=sys.version_info; exit(0 if ver.major==3 and ver.minor>=8 else 1)" > nul 2>&1
if errorlevel 1 (
    echo Error: Python 3.8 or later is required
    echo Current Python installation is too old
    pause
    exit /b 1
)

echo.
echo Checking and upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 goto error

echo.
echo Installing required packages...
echo This might take a few minutes...

REM Create and activate virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate
if errorlevel 1 (
    echo Error: Failed to create virtual environment
    goto error
)

echo Installing Win32GUI...
pip install pywin32
if errorlevel 1 goto error

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
if errorlevel 1 (
    echo PyAudio installation failed. 
    echo Attempting alternative installation method...
    python -m pip install pipwin
    pipwin install pyaudio
    if errorlevel 1 (
        echo PyAudio installation failed. 
        echo You might need to install Microsoft Visual C++ Build Tools
        echo Visit: https://visualstudio.microsoft.com/visual-cpp-build-tools/
        pause
        exit /b 1
    )
)

echo Installing PyAutoGUI...
pip install pyautogui
if errorlevel 1 goto error

echo Installing Torch CPU...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto error

echo Installing Transformers...
pip install transformers
if errorlevel 1 goto error

REM Check Visual C++ Redistributable
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0" >nul 2>&1
if errorlevel 1 (
    echo Warning: Microsoft Visual C++ 2015-2022 Redistributable might be missing
    echo Please download and install from:
    echo https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo.
)

REM Verify installations
echo.
echo Verifying installations...
python -c "import win32gui; import numpy; import cv2; import PIL; import pyautogui; import torch; import transformers" > nul 2>&1
if errorlevel 1 (
    echo Error: Some dependencies failed to install correctly
    echo Please check the error messages above and try again
    goto error
)

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
echo If you encounter any issues:
echo 1. Check if all dependencies are installed correctly
echo 2. Verify you have administrator privileges
echo 3. Make sure your antivirus isn't blocking the bot
echo 4. Check the documentation for troubleshooting
echo.
pause

exit /b 0

:error
echo.
echo Error during installation!
echo Please check:
echo 1. Your internet connection
echo 2. If you have administrator privileges
echo 3. If any antivirus is blocking the installation
echo 4. If Microsoft Visual C++ Build Tools are installed
echo.
echo For additional help:
echo - Check the documentation
echo - Visit our GitHub page for known issues
echo - Run the script as administrator
echo.
pause
exit /b 1