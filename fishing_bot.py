import tkinter as tk
from tkinter import ttk
from gui_components import MainWindow
from logger import setup_logger
import platform
import sys

def main():
    # Setup logging
    logger = setup_logger()
    logger.info("Starting Fishing Bot")

    # Check if running in test mode
    test_mode = platform.system() != 'Windows'
    if test_mode:
        logger.warning("Running in test mode (non-Windows platform)")

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
        app = MainWindow(root, test_mode=test_mode)
        root.mainloop()
    except Exception as e:
        logger.error(f"Application crashed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()