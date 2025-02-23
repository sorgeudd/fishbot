import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import logging
from bot_core import FishingBot
from config_manager import ConfigManager
import urllib.parse
import threading

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

        # Window Detection Frame
        window_frame = ttk.LabelFrame(self.master, text="Game Window")
        window_frame.pack(fill="x", padx=5, pady=5)

        # Window Title Entry
        title_frame = ttk.Frame(window_frame)
        title_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(title_frame, text="Window Title:").pack(side="left", padx=5)
        self.window_title_entry = ttk.Entry(title_frame)
        self.window_title_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Detect Window Button
        detect_frame = ttk.Frame(window_frame)
        detect_frame.pack(fill="x", padx=5, pady=2)
        self.detect_window_btn = ttk.Button(detect_frame, text="Detect Window", 
                                        command=self._detect_window)
        self.detect_window_btn.pack(side="left", padx=5)
        self.window_status_label = ttk.Label(detect_frame, text="No window detected")
        self.window_status_label.pack(side="left", padx=5)

        # Learning Mode Frame
        learning_frame = ttk.LabelFrame(self.master, text="Learning Mode")
        learning_frame.pack(fill="x", padx=5, pady=5)

        # Learning Status
        self.learning_status = ttk.Label(learning_frame, text="Learning: Inactive")
        self.learning_status.pack(padx=5, pady=2)

        # Start/Stop Learning Button
        self.learning_btn = ttk.Button(learning_frame, text="Start Learning", 
                                   command=self._toggle_learning)
        self.learning_btn.pack(fill="x", padx=5, pady=2)

        # Map Management Frame
        map_frame = ttk.LabelFrame(self.master, text="Map Management")
        map_frame.pack(fill="x", padx=5, pady=5)

        # Load Map File
        load_map_btn = ttk.Button(map_frame, text="Load Map File", 
                               command=self._load_map_file)
        load_map_btn.pack(fill="x", padx=5, pady=2)

        # Download Map URL
        url_frame = ttk.Frame(map_frame)
        url_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(url_frame, text="Map URL:").pack(side="left", padx=5)
        self.map_url_entry = ttk.Entry(url_frame)
        self.map_url_entry.pack(side="left", fill="x", expand=True, padx=5)
        download_map_btn = ttk.Button(url_frame, text="Download", 
                                   command=self._download_map)
        download_map_btn.pack(side="right", padx=5)

        # Bot Control Frame
        bot_frame = ttk.LabelFrame(self.master, text="Bot Control")
        bot_frame.pack(fill="x", padx=5, pady=5)

        # Start Bot Button (moved to Bot Control frame)
        self.start_bot_btn = ttk.Button(bot_frame, text="Start Bot", 
                                     command=self._start_bot)
        self.start_bot_btn.pack(fill="x", padx=5, pady=5)

        # Log Display
        log_frame = ttk.LabelFrame(self.master, text="Log", padding="5")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_display = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_display.pack(fill="both", expand=True)

    def _setup_logging(self):
        self.logger = logging.getLogger('GUI')
        self.logger.setLevel(logging.INFO)

        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget

            def emit(self, record):
                msg = self.format(record) + '\n'
                self.text_widget.insert(tk.END, msg)
                self.text_widget.see(tk.END)

        log_handler = TextHandler(self.log_display)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_handler.setFormatter(formatter)
        self.logger.addHandler(log_handler)

    def _toggle_learning(self):
        """Toggle learning mode on/off"""
        if not self.bot.learning_mode:
            # Start learning mode
            self.bot.start_learning_mode()
            self.learning_btn.config(text="Stop Learning")
            self.learning_status.config(text="Learning: Active")
            self.status_label.config(text="Learning Mode")
            self.logger.info("Started learning mode")
            # Disable bot start button during learning
            self.start_bot_btn.config(state="disabled")
        else:
            # Stop learning mode
            self.bot.stop_learning_mode()
            self.learning_btn.config(text="Start Learning")
            self.learning_status.config(text="Learning: Inactive")
            self.status_label.config(text="Idle")
            self.logger.info("Stopped learning mode")
            # Re-enable bot start button
            self.start_bot_btn.config(state="normal")

    def _register_emergency_stop(self):
        self.master.bind('<F6>', lambda e: self._emergency_stop())
        self.logger.info("Emergency stop hotkey (F6) registered")

    def _emergency_stop(self):
        self.bot.stop()
        if self.bot.learning_mode:
            self.bot.stop_learning_mode()
            self.learning_btn.config(text="Start Learning")
            self.learning_status.config(text="Learning: Inactive")
        self.status_label.config(text="Emergency Stop Activated")
        self.start_bot_btn.config(text="Start Bot", command=self._start_bot, state="normal")
        self.logger.warning("Emergency stop activated")

    def _detect_window(self):
        title = self.window_title_entry.get()
        success, message = self.bot.find_game_window(title if title else None)

        if success:
            self.window_status_label.config(text="Window detected")
            window_info = self.bot.get_window_info()
            if window_info:
                details = f"Found: {window_info['title']} ({window_info['rect']})"
                self.logger.info(details)
        else:
            self.window_status_label.config(text="Detection failed")
            self.logger.error(f"Window detection failed: {message}")

    def _load_map_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Map Files", "*.json;*.csv"), ("All Files", "*.*")]
        )
        if file_path:
            if self.bot.load_map_data(file_path):
                self.logger.info(f"Successfully loaded map from {file_path}")
            else:
                messagebox.showerror("Error", "Failed to load map file")

    def _download_map(self):
        url = self.map_url_entry.get()
        if not url:
            messagebox.showwarning("Warning", "Please enter a map URL")
            return

        try:
            # Validate URL
            parsed = urllib.parse.urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError("Invalid URL format")

            def download():
                if self.bot.download_map_data(url):
                    self.logger.info("Successfully downloaded and loaded map")
                else:
                    self.logger.error("Failed to download map")

            # Run download in background
            thread = threading.Thread(target=download)
            thread.daemon = True
            thread.start()

        except Exception as e:
            self.logger.error(f"Error downloading map: {str(e)}")
            messagebox.showerror("Error", f"Failed to download map: {str(e)}")

    def _start_bot(self):
        try:
            self.bot.start()
            self.status_label.config(text="Bot Running")
            self.start_bot_btn.config(text="Stop Bot", command=self._stop_bot)
            self.learning_btn.config(state="disabled")  # Disable learning while bot is running
            self.logger.info("Bot started")
        except Exception as e:
            self.logger.error(f"Failed to start bot: {str(e)}")
            self.status_label.config(text="Error Starting Bot")

    def _stop_bot(self):
        self.bot.stop()
        self.status_label.config(text="Bot Stopped")
        self.start_bot_btn.config(text="Start Bot", command=self._start_bot)
        self.learning_btn.config(state="normal")  # Re-enable learning button
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