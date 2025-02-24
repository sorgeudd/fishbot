import ctypes
import time
import math
import random
from ctypes import Structure, c_long, c_ulong, sizeof, POINTER, pointer
import logging

# Windows API Constants
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040

# Define necessary structures for Windows API
class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]

class MOUSEINPUT(Structure):
    _fields_ = [
        ("dx", c_long),
        ("dy", c_long),
        ("mouseData", c_ulong),
        ("dwFlags", c_ulong),
        ("time", c_ulong),
        ("dwExtraInfo", POINTER(c_ulong))
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]

class INPUT(Structure):
    _fields_ = [
        ("type", c_ulong),
        ("union", INPUT_UNION)
    ]

class DirectInput:
    def __init__(self):
        self.logger = logging.getLogger('DirectInput')
        self.user32 = ctypes.windll.user32
        self.screen_width = self.user32.GetSystemMetrics(0)
        self.screen_height = self.user32.GetSystemMetrics(1)
        self.logger.info(f"Initialized DirectInput with screen size: {self.screen_width}x{self.screen_height}")

    def _normalize_coordinates(self, x, y):
        """Convert screen coordinates to normalized coordinates (0-65535 range)"""
        norm_x = int((x * 65535) / self.screen_width)
        norm_y = int((y * 65535) / self.screen_height)
        return norm_x, norm_y

    def move_mouse(self, x, y, smooth=True):
        """Move mouse using SendInput with optional smooth movement"""
        try:
            if smooth:
                current = POINT()
                self.user32.GetCursorPos(pointer(current))
                self.logger.debug(f"Current position: ({current.x}, {current.y})")
                
                # Calculate path points
                steps = 20
                dx = (x - current.x) / steps
                dy = (y - current.y) / steps
                
                for i in range(steps):
                    if i == steps - 1:
                        # Last step - move to exact target
                        next_x, next_y = x, y
                    else:
                        # Add slight randomization to path
                        next_x = int(current.x + dx * (i + 1) + random.uniform(-2, 2))
                        next_y = int(current.y + dy * (i + 1) + random.uniform(-2, 2))
                    
                    self._send_mouse_input(next_x, next_y)
                    time.sleep(0.001)  # Small delay between movements
            else:
                # Direct movement
                self._send_mouse_input(x, y)
                
            # Verify final position
            final = POINT()
            self.user32.GetCursorPos(pointer(final))
            self.logger.debug(f"Final position: ({final.x}, {final.y})")
            
            return True
        except Exception as e:
            self.logger.error(f"Error moving mouse: {str(e)}")
            return False

    def _send_mouse_input(self, x, y):
        """Send a single mouse movement input"""
        try:
            # Convert to normalized coordinates
            norm_x, norm_y = self._normalize_coordinates(x, y)
            
            # Prepare input structure
            mouse_input = MOUSEINPUT()
            mouse_input.dx = norm_x
            mouse_input.dy = norm_y
            mouse_input.mouseData = 0
            mouse_input.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
            mouse_input.time = 0
            mouse_input.dwExtraInfo = pointer(c_ulong(0))

            input_struct = INPUT()
            input_struct.type = 0  # INPUT_MOUSE
            input_struct.union.mi = mouse_input

            # Send input
            result = self.user32.SendInput(1, pointer(input_struct), sizeof(INPUT))
            if result != 1:
                self.logger.error("SendInput failed")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"Error sending mouse input: {str(e)}")
            return False

    def click(self, button='left'):
        """Perform mouse click using SendInput"""
        try:
            current = POINT()
            self.user32.GetCursorPos(pointer(current))
            
            # Select appropriate button flags
            if button == 'left':
                down_flag = MOUSEEVENTF_LEFTDOWN
                up_flag = MOUSEEVENTF_LEFTUP
            elif button == 'right':
                down_flag = MOUSEEVENTF_RIGHTDOWN
                up_flag = MOUSEEVENTF_RIGHTUP
            elif button == 'middle':
                down_flag = MOUSEEVENTF_MIDDLEDOWN
                up_flag = MOUSEEVENTF_MIDDLEUP
            else:
                self.logger.error(f"Invalid button type: {button}")
                return False

            # Send button down
            mouse_input = MOUSEINPUT()
            mouse_input.dx = 0
            mouse_input.dy = 0
            mouse_input.mouseData = 0
            mouse_input.dwFlags = down_flag
            mouse_input.time = 0
            mouse_input.dwExtraInfo = pointer(c_ulong(0))

            input_struct = INPUT()
            input_struct.type = 0  # INPUT_MOUSE
            input_struct.union.mi = mouse_input

            self.user32.SendInput(1, pointer(input_struct), sizeof(INPUT))
            time.sleep(0.05)  # Short delay between down and up

            # Send button up
            mouse_input.dwFlags = up_flag
            input_struct.union.mi = mouse_input
            self.user32.SendInput(1, pointer(input_struct), sizeof(INPUT))

            return True
        except Exception as e:
            self.logger.error(f"Error performing click: {str(e)}")
            return False
