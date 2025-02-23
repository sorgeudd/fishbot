import tkinter as tk
from tkinter import ttk, scrolledtext
import logging
from bot_core import FishingBot
from config_manager import ConfigManager

class MainWindow:
    def __init__(self, master):
        self.master = master
        self.bot = FishingBot()
        self.config_manager = ConfigManager()
        
        self._create_gui()
        self._setup_logging_display()

    def _create_gui(self):
        # Create main frame
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Control buttons
        self.start_button = ttk.Button(main_frame, text="Start", command=self._start_bot)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)

        self.stop_button = ttk.Button(main_frame, text="Stop", command=self._stop_bot)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)
        self.stop_button.state(['disabled'])

        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="5")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Detection area settings
        ttk.Label(config_frame, text="Detection Area:").grid(row=0, column=0, sticky=tk.W)
        self.area_entry = ttk.Entry(config_frame)
        self.area_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        self.area_entry.insert(0, ",".join(map(str, self.config_manager.get_config()['detection_area'])))

        # Key bindings
        ttk.Label(config_frame, text="Cast Key:").grid(row=1, column=0, sticky=tk.W)
        self.cast_key_entry = ttk.Entry(config_frame)
        self.cast_key_entry.grid(row=1, column=1, sticky=(tk.W, tk.E))
        self.cast_key_entry.insert(0, self.config_manager.get_config()['cast_key'])

        ttk.Label(config_frame, text="Reel Key:").grid(row=2, column=0, sticky=tk.W)
        self.reel_key_entry = ttk.Entry(config_frame)
        self.reel_key_entry.grid(row=2, column=1, sticky=(tk.W, tk.E))
        self.reel_key_entry.insert(0, self.config_manager.get_config()['reel_key'])

        # Save config button
        ttk.Button(config_frame, text="Save Configuration", 
                  command=self._save_config).grid(row=3, column=0, columnspan=2, pady=5)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))

    def _setup_logging_display(self):
        # Create log display
        log_frame = ttk.LabelFrame(self.master, text="Log", padding="5")
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)

        self.log_display = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create custom log handler
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget

            def emit(self, record):
                msg = self.format(record) + '\n'
                self.text_widget.insert(tk.END, msg)
                self.text_widget.see(tk.END)

        # Add handler to logger
        log_handler = TextHandler(self.log_display)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_handler.setFormatter(formatter)
        logging.getLogger().addHandler(log_handler)

    def _start_bot(self):
        self.bot.start()
        self.start_button.state(['disabled'])
        self.stop_button.state(['!disabled'])
        self.status_var.set("Bot running...")

    def _stop_bot(self):
        self.bot.stop()
        self.stop_button.state(['disabled'])
        self.start_button.state(['!disabled'])
        self.status_var.set("Bot stopped")

    def _save_config(self):
        try:
            # Parse detection area
            area = tuple(map(int, self.area_entry.get().split(',')))
            
            new_config = {
                'detection_area': area,
                'cast_key': self.cast_key_entry.get(),
                'reel_key': self.reel_key_entry.get()
            }
            
            self.config_manager.update_config(new_config)
            self.bot.update_config(new_config)
            self.status_var.set("Configuration saved")
            
        except Exception as e:
            self.status_var.set(f"Error saving configuration: {str(e)}")
