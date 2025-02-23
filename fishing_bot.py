import tkinter as tk
from gui_components import MainWindow
from logger import setup_logger

def main():
    # Setup logging
    logger = setup_logger()
    logger.info("Starting Fishing Bot")
    
    # Create main window
    root = tk.Tk()
    root.title("Fishing Bot")
    root.geometry("800x600")
    
    # Initialize main application window
    app = MainWindow(root)
    
    # Start the application
    try:
        root.mainloop()
    except Exception as e:
        logger.error(f"Application crashed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
