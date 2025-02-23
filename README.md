# Fishing Bot

A Python-based fishing bot with GUI controls for online game automation.

## Requirements

- Windows operating system
- Python 3.8 or later
- Administrator privileges (for keyboard control)

## Quick Installation

1. Extract all files from the zip archive
2. Run `install.bat` as Administrator
3. Follow the on-screen instructions

## Manual Installation

If the automatic installation fails, you can install the required packages manually:

```bash
pip install numpy opencv-python pillow pyaudio pyautogui requests
```

## Usage

1. Run the bot:
   - Double click on `fishing_bot.py`, OR
   - Run `python fishing_bot.py` in terminal
2. Configure the detection area and key bindings in the GUI
3. Click "Start" to begin fishing
4. Click "Stop" to pause the bot

## Configuration

- Detection Area: The screen region to monitor for fish bites (format: x,y,width,height)
- Cast Key: The key to press for casting the fishing line (default: 'f')
- Reel Key: The key to press for reeling in fish (default: 'r')

## Troubleshooting

1. If the bot doesn't start:
   - Make sure you're running on Windows
   - Run as Administrator
   - Verify Python is installed and in PATH
   - Check all dependencies are installed

2. If keyboard controls don't work:
   - Run as Administrator
   - Ensure game window is active and not minimized
   - Check key bindings match your game settings

## Support

For issues and feature requests, please contact the developer.