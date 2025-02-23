import tkinter as tk
from tkinter import ttk
from gui_components import MainWindow
from logger import setup_logger
import platform
import sys

def check_windows_environment():
    """Verify Windows environment and required dependencies"""
    if platform.system() != 'Windows':
        return False, "This application requires Windows to run"

    try:
        import win32gui
        import pyautogui
        import cv2
        import numpy as np
        from PIL import ImageGrab
        return True, "All dependencies available"
    except ImportError as e:
        return False, f"Missing required dependency: {str(e)}"

def main():
    # Setup logging
    logger = setup_logger()
    logger.info("Starting Fishing Bot")

    # Check environment
    is_windows, message = check_windows_environment()
    if not is_windows:
        logger.error(message)
        print(f"Error: {message}")
        print("Please run this application on a Windows system")
        sys.exit(1)

    # Create main window
    root = tk.Tk()
    root.title("Fishing Bot")

    # Set a fixed window size
    root.geometry("300x600")

    # Create a custom style for the emergency stop button
    style = ttk.Style()
    style.configure("Emergency.TButton", foreground="red", font=('bold'))

    # Initialize main application window
    try:
        app = MainWindow(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Application crashed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()