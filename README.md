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
3. Click "Start" to begin fishing
4. Click "Stop" to pause the bot

## Configuration

- Detection Area: The screen region to monitor for fish bites (format: x,y,width,height)
- Cast Key: The key to press for casting the fishing line (default: 'f')
- Reel Key: The key to press for reeling in fish (default: 'r')

## Testing

### Windows Development Environment (Recommended)

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the tests:
   ```bash
   python -m unittest test_bot.py -v
   ```

Note: Tests must be run on Windows as they require display server access for GUI interaction.

### Test Coverage

The test suite includes:
- Mouse movement accuracy
- Keyboard input timing
- Fish bite detection
- Full fishing cycle automation
- Game window detection
- Error handling

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