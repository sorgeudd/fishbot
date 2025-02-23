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
   - Double click on `start_bot.bat`, OR
   - Run `python fishing_bot.py` in terminal
2. Configure the detection area and key bindings in the GUI
3. Start learning mode:
   - Click "Start Learning"
   - Perform the fishing actions you want the bot to learn
   - Click "Stop Learning" when done
4. Click "Start Bot" to begin automated fishing
5. Click "Stop" to pause the bot

## Configuration

- Detection Area: The screen region to monitor for fish bites (format: x,y,width,height)
- Cast Key: The key to press for casting the fishing line (default: 'f')
- Reel Key: The key to press for reeling in fish (default: 'r')

## Game Window Detection

1. Enter the game window title (or leave blank for auto-detection)
2. Click "Detect Window" to find and focus the game window
3. The bot will automatically track the selected window

## Map Management

- Load local map files (JSON or CSV format)
- Download maps from URLs for navigation and resource locations
- Maps are used for pathfinding and resource detection

## Learning Mode

The learning mode allows the bot to learn from your actions:

1. Click "Start Learning" button
2. Perform your normal fishing routine:
   - Cast your line
   - Wait for fish
   - Reel in when you get a bite
3. Click "Stop Learning" when you're satisfied
4. The bot will analyze and learn from your actions
5. Start the bot to use the learned patterns

## Features

- AI-powered pattern recognition
- Automatic window detection
- Map-based navigation
- Custom learning mode
- Emergency stop (F6)
- Detailed logging
- Configurable key bindings

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

3. If learning mode isn't working:
   - Ensure the game window is detected first
   - Try running the bot as Administrator
   - Check if the game window is properly focused

4. If window detection fails:
   - Try running as Administrator
   - Make sure the game window is not minimized
   - Enter the exact window title if auto-detection fails

## Support

For issues and feature requests, please contact the developer.