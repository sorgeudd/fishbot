import tkinter as tk
from tkinter import ttk # Added import for ttk
from gui_components import MainWindow
from logger import setup_logger
import platform
import sys

def main():
    # Setup logging
    logger = setup_logger()
    logger.info("Starting Fishing Bot")

    # Check for Windows environment
    if platform.system() != 'Windows':
        logger.error("This application only works on Windows")
        print("Error: FishingBot requires Windows to run")
        print("Please run this application on a Windows system")
        sys.exit(1)

    # Create main window
    root = tk.Tk()
    root.title("Fishing Bot")

    # Set a fixed window size that matches the original design
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

if __name__ == "__main__":
    main()