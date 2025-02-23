import tkinter as tk
from tkinter import ttk, scrolledtext  # Added scrolledtext import
import logging
from bot_core import FishingBot
from config_manager import ConfigManager

class MainWindow:
    def __init__(self, master):
        self.master = master
        self.bot = FishingBot()
        self.config_manager = ConfigManager()

        # Configure main window
        self.master.title("Fishing Bot")
        self.master.resizable(False, False)

        self._create_gui()
        self._setup_logging()
        self._register_emergency_stop()

    def _create_gui(self):
        # Status section
        status_frame = ttk.LabelFrame(self.master, text="Status")
        status_frame.pack(fill="x", padx=5, pady=5)
        self.status_label = ttk.Label(status_frame, text="Idle")
        self.status_label.pack(padx=5, pady=5)

        # Controls section
        controls_frame = ttk.LabelFrame(self.master, text="Controls")
        controls_frame.pack(fill="x", padx=5, pady=5)

        # Emergency Stop
        self.emergency_stop_btn = ttk.Button(controls_frame, text="EMERGENCY STOP (F6)", 
                                           command=self._emergency_stop, style="Emergency.TButton")
        self.emergency_stop_btn.pack(fill="x", padx=5, pady=5)

        # Start Bot
        self.start_bot_btn = ttk.Button(controls_frame, text="Start Bot", command=self._start_bot)
        self.start_bot_btn.pack(padx=5, pady=5)

        # Record Fish Bite Sound
        self.record_sound_btn = ttk.Button(controls_frame, text="Record Fish Bite Sound", 
                                         command=self._record_sound)
        self.record_sound_btn.pack(padx=5, pady=5)

        # Settings
        self.settings_btn = ttk.Button(controls_frame, text="Settings", command=self._open_settings)
        self.settings_btn.pack(padx=5, pady=5)

        # Configuration section
        config_frame = ttk.LabelFrame(self.master, text="Configuration")
        config_frame.pack(fill="x", padx=5, pady=5)

        # Cast Power
        ttk.Label(config_frame, text="Cast Power:").pack(padx=5, pady=2)
        self.cast_power = ttk.Scale(config_frame, from_=0, to=100, orient="horizontal")
        self.cast_power.pack(fill="x", padx=5, pady=2)

        # Region controls
        region_frame = ttk.Frame(config_frame)
        region_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(region_frame, text="Set Minigame Region:").pack(pady=2)
        region_controls = ttk.Frame(region_frame)
        region_controls.pack(fill="x")

        self.set_region_btn = ttk.Button(region_controls, text="Set Region", 
                                       command=self._set_region)
        self.set_region_btn.pack(side="left", padx=2)
        self.region_status = ttk.Label(region_controls, text="Not Set")
        self.region_status.pack(side="left", padx=5)

        # Game Window Region
        window_frame = ttk.Frame(config_frame)
        window_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(window_frame, text="Game Window Region:").pack(pady=2)
        window_controls = ttk.Frame(window_frame)
        window_controls.pack(fill="x")

        self.select_window_btn = ttk.Button(window_controls, text="Select Game Window", 
                                          command=self._select_game_window)
        self.select_window_btn.pack(side="left", padx=2)
        self.window_status = ttk.Label(window_controls, text="Not Set")
        self.window_status.pack(side="left", padx=5)

        # Movement Controls
        movement_frame = ttk.LabelFrame(self.master, text="Movement Controls")
        movement_frame.pack(fill="x", padx=5, pady=5)

        self.add_obstacle_btn = ttk.Button(movement_frame, text="Add Obstacle", 
                                         command=self._add_obstacle)
        self.add_obstacle_btn.pack(padx=5, pady=2)

        self.clear_obstacles_btn = ttk.Button(movement_frame, text="Clear Obstacles", 
                                            command=self._clear_obstacles)
        self.clear_obstacles_btn.pack(padx=5, pady=2)

        self.movement_status = ttk.Label(movement_frame, text="Movement: Ready")
        self.movement_status.pack(padx=5, pady=2)

        #Log Display (adapted from original)
        log_frame = ttk.LabelFrame(self.master, text="Log", padding="5")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5) #modified to fill and expand
        self.log_display = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_display.pack(fill="both", expand=True) #modified to fill and expand

        # Create custom log handler (adapted from original)
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget

            def emit(self, record):
                msg = self.format(record) + '\n'
                self.text_widget.insert(tk.END, msg)
                self.text_widget.see(tk.END)

        # Add handler to logger (adapted from original)
        log_handler = TextHandler(self.log_display)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_handler.setFormatter(formatter)
        self.logger.addHandler(log_handler) # Added to use the logger from _setup_logging


    def _setup_logging(self):
        # Create logger
        self.logger = logging.getLogger('GUI')
        self.logger.setLevel(logging.INFO) # Set log level

    def _register_emergency_stop(self):
        self.master.bind('<F6>', lambda e: self._emergency_stop())
        self.logger.info("Emergency stop hotkey (F6) registered")

    def _emergency_stop(self):
        self.bot.stop()
        self.status_label.config(text="Emergency Stop Activated")
        self.logger.warning("Emergency stop activated")

    def _start_bot(self):
        try:
            self.bot.start()
            self.status_label.config(text="Bot Running")
            self.start_bot_btn.config(text="Stop Bot", command=self._stop_bot) #Changed command
            self.logger.info("Bot started")
        except Exception as e:
            self.logger.error(f"Failed to start bot: {str(e)}")
            self.status_label.config(text="Error Starting Bot")

    def _stop_bot(self):
        self.bot.stop()
        self.status_label.config(text="Bot Stopped")
        self.start_bot_btn.config(text="Start Bot", command=self._start_bot) #Changed command
        self.logger.info("Bot stopped")

    def _record_sound(self):
        # To be implemented
        self.logger.info("Recording fish bite sound...")
        pass

    def _open_settings(self):
        # To be implemented
        self.logger.info("Opening settings...")
        pass

    def _set_region(self):
        # To be implemented
        self.logger.info("Setting minigame region...")
        pass

    def _select_game_window(self):
        # To be implemented
        self.logger.info("Selecting game window...")
        pass

    def _add_obstacle(self):
        # To be implemented
        self.logger.info("Adding obstacle...")
        pass

    def _clear_obstacles(self):
        # To be implemented
        self.logger.info("Clearing obstacles...")
        pass