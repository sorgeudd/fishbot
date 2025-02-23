import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import logging
from bot_core import FishingBot
from config_manager import ConfigManager
import urllib.parse
import threading
import sys

class MainWindow:
    def __init__(self, master, test_mode=False):
        self.master = master
        self.test_mode = test_mode

        # Setup logging first
        self.logger = logging.getLogger('GUI')
        self._setup_logging()

        self.logger.info(f"Initializing GUI (Test Mode: {test_mode})")

        try:
            self.bot = FishingBot(test_mode=test_mode)
            self.config_manager = ConfigManager()

            # Configure main window
            self.master.title("Fishing Bot")
            self.master.resizable(False, False)
            self.logger.debug("Main window configured")

            self._create_styles()
            self._create_gui()
            self._register_emergency_stop()

            self.logger.info("GUI initialization complete")

        except Exception as e:
            self.logger.error(f"Failed to initialize GUI: {str(e)}")
            messagebox.showerror("Error", f"Failed to initialize: {str(e)}")
            sys.exit(1)

    def _setup_logging(self):
        """Setup logging with GUI handler"""
        try:
            # Create a temporary console handler until GUI is ready
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            self.logger.setLevel(logging.DEBUG if self.test_mode else logging.INFO)

        except Exception as e:
            print(f"Error setting up initial logging: {str(e)}")
            sys.exit(1)

    def _create_gui(self):
        """Create all GUI components with logging"""
        try:
            # Status section
            self.logger.debug("Creating status section")
            status_frame = ttk.LabelFrame(self.master, text="Status", padding="10")
            status_frame.pack(fill="x", padx=10, pady=5)
            self.status_label = ttk.Label(status_frame, text="Idle")
            self.status_label.pack(padx=5, pady=5)

            # Log Display (create this early for logging)
            self.logger.debug("Creating log display")
            log_frame = ttk.LabelFrame(self.master, text="Log", padding="10")
            log_frame.pack(fill="both", expand=True, padx=10, pady=5)
            self.log_display = scrolledtext.ScrolledText(log_frame, height=20)
            self.log_display.pack(fill="both", expand=True, padx=5, pady=5)

            # Update logging to use GUI
            self._setup_gui_logging()

            # Controls section
            self.logger.debug("Creating controls section")
            controls_frame = ttk.LabelFrame(self.master, text="Controls", padding="10")
            controls_frame.pack(fill="x", padx=10, pady=5)

            # Emergency Stop
            self.emergency_stop_btn = ttk.Button(controls_frame, text="EMERGENCY STOP (F6)", 
                                             command=self._emergency_stop, style="Emergency.TButton")
            self.emergency_stop_btn.pack(fill="x", padx=5, pady=5)

            # Window Detection Frame
            self.logger.debug("Creating window detection section")
            window_frame = ttk.LabelFrame(self.master, text="Game Window", padding="10")
            window_frame.pack(fill="x", padx=10, pady=5)

            # Window Title Entry
            title_frame = ttk.Frame(window_frame)
            title_frame.pack(fill="x", padx=5, pady=2)
            ttk.Label(title_frame, text="Window Title:").pack(side="left", padx=5)
            self.window_title_entry = ttk.Entry(title_frame)
            self.window_title_entry.pack(side="left", fill="x", expand=True, padx=5)

            # Detect Window Button
            detect_frame = ttk.Frame(window_frame)
            detect_frame.pack(fill="x", padx=5, pady=5)
            self.detect_window_btn = ttk.Button(detect_frame, text="Detect Window", 
                                            command=self._detect_window)
            self.detect_window_btn.pack(side="left", padx=5)
            self.window_status_label = ttk.Label(detect_frame, text="No window detected")
            self.window_status_label.pack(side="left", padx=5)

            # Learning Mode Frame
            self.logger.debug("Creating learning mode section")
            learning_frame = ttk.LabelFrame(self.master, text="Learning Mode", padding="10")
            learning_frame.pack(fill="x", padx=10, pady=5)

            # Learning Status
            self.learning_status = ttk.Label(learning_frame, text="Learning: Inactive")
            self.learning_status.pack(padx=5, pady=5)

            # Learning Controls Frame
            learning_controls = ttk.Frame(learning_frame)
            learning_controls.pack(fill="x", padx=5, pady=5)

            # Start/Stop Learning Button
            self.learning_btn = ttk.Button(learning_controls, text="Start Learning", 
                                       command=self._toggle_learning)
            self.learning_btn.pack(side="left", fill="x", expand=True, padx=2)

            # Reset Learning Button
            self.reset_learning_btn = ttk.Button(learning_controls, text="Reset Learning",
                                             command=self._reset_learning,
                                             style="Danger.TButton")
            self.reset_learning_btn.pack(side="right", fill="x", expand=True, padx=2)

            # Import Video Button
            self.import_video_btn = ttk.Button(learning_frame, text="Import Training Video",
                                           command=self._import_training_video)
            self.import_video_btn.pack(fill="x", padx=5, pady=5)

            # Map Management Frame
            self.logger.debug("Creating map management section")
            map_frame = ttk.LabelFrame(self.master, text="Map Management", padding="10")
            map_frame.pack(fill="x", padx=10, pady=5)

            # Load Map File
            load_map_btn = ttk.Button(map_frame, text="Load Map File", 
                                   command=self._load_map_file)
            load_map_btn.pack(fill="x", padx=5, pady=5)

            # Download Map URL
            url_frame = ttk.Frame(map_frame)
            url_frame.pack(fill="x", padx=5, pady=5)
            ttk.Label(url_frame, text="Map URL:").pack(side="left", padx=5)
            self.map_url_entry = ttk.Entry(url_frame)
            self.map_url_entry.pack(side="left", fill="x", expand=True, padx=5)
            download_map_btn = ttk.Button(url_frame, text="Download", 
                                      command=self._download_map)
            download_map_btn.pack(side="right", padx=5)

            # Bot Control Frame
            self.logger.debug("Creating bot control section")
            bot_frame = ttk.LabelFrame(self.master, text="Bot Control", padding="10")
            bot_frame.pack(fill="x", padx=10, pady=5)

            # Start Bot Button
            self.start_bot_btn = ttk.Button(bot_frame, text="Start Bot", 
                                        command=self._start_bot)
            self.start_bot_btn.pack(fill="x", padx=5, pady=5)

            self.logger.info("All GUI components created successfully")

        except Exception as e:
            self.logger.error(f"Error creating GUI components: {str(e)}")
            raise

    def _create_styles(self):
        """Create custom styles for buttons"""
        try:
            style = ttk.Style()
            style.configure("Emergency.TButton", foreground="red", font=('bold'))
            style.configure("Danger.TButton", foreground="orange", font=('bold'))
            self.logger.debug("Custom styles created")
        except Exception as e:
            self.logger.error(f"Error creating styles: {str(e)}")

    def _setup_gui_logging(self):
        """Setup GUI-based logging"""
        try:
            class TextHandler(logging.Handler):
                def __init__(self, text_widget):
                    super().__init__()
                    self.text_widget = text_widget

                def emit(self, record):
                    msg = self.format(record) + '\n'
                    self.text_widget.insert(tk.END, msg)
                    self.text_widget.see(tk.END)

            # Remove any existing handlers
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)

            # Add GUI handler
            gui_handler = TextHandler(self.log_display)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            gui_handler.setFormatter(formatter)
            self.logger.addHandler(gui_handler)
            self.logger.info("GUI logging system initialized")

        except Exception as e:
            print(f"Error setting up GUI logging: {str(e)}")
            # Keep the console handler if GUI logging fails


    def _toggle_learning(self):
        """Toggle learning mode on/off"""
        try:
            if not self.bot.learning_mode:
                self.logger.info("Starting learning mode")
                self.bot.start_learning()
                self.learning_btn.config(text="Stop Learning")
                self.learning_status.config(text="Learning: Active")
                self.status_label.config(text="Learning Mode")
                self.start_bot_btn.config(state="disabled")
            else:
                self.logger.info("Stopping learning mode")
                self.bot.stop_learning()
                self.learning_btn.config(text="Start Learning")
                self.learning_status.config(text="Learning: Inactive")
                self.status_label.config(text="Idle")
                self.start_bot_btn.config(state="normal")
        except Exception as e:
            self.logger.error(f"Error toggling learning mode: {str(e)}")

    def _register_emergency_stop(self):
        """Register emergency stop hotkey"""
        try:
            self.master.bind('<F6>', lambda e: self._emergency_stop())
            self.logger.info("Emergency stop hotkey (F6) registered")
        except Exception as e:
            self.logger.error(f"Error registering emergency stop: {str(e)}")

    def _emergency_stop(self):
        """Handle emergency stop"""
        try:
            self.logger.warning("Emergency stop activated")
            self.bot.stop()
            if self.bot.learning_mode:
                self.bot.stop_learning()
                self.learning_btn.config(text="Start Learning")
                self.learning_status.config(text="Learning: Inactive")
            self.status_label.config(text="Emergency Stop Activated")
            self.start_bot_btn.config(text="Start Bot", command=self._start_bot, state="normal")
        except Exception as e:
            self.logger.error(f"Error during emergency stop: {str(e)}")

    def _detect_window(self):
        """Detect game window"""
        try:
            title = self.window_title_entry.get()
            self.logger.info(f"Attempting to detect window with title: {title}")
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
        except Exception as e:
            self.logger.error(f"Error detecting window: {str(e)}")

    def _import_training_video(self):
        """Import video file for AI training"""
        try:
            self.logger.info("Opening file dialog for video import")
            file_path = filedialog.askopenfilename(
                title="Select Training Video",
                filetypes=[
                    ("Video Files", "*.mp4 *.avi *.mkv"),
                    ("All Files", "*.*")
                ]
            )
            if file_path:
                self.status_label.config(text="Processing Video...")
                self.logger.info(f"Processing video: {file_path}")
                success = self.bot.gameplay_learner.import_video_for_training(file_path)
                if success:
                    self.logger.info(f"Successfully processed training video: {file_path}")
                    self.status_label.config(text="Video Training Complete")
                else:
                    self.logger.error("Failed to process training video")
                    self.status_label.config(text="Video Processing Failed")
                    messagebox.showerror("Error", "Failed to process training video")
        except Exception as e:
            self.logger.error(f"Error importing training video: {str(e)}")
            messagebox.showerror("Error", f"Failed to import video: {str(e)}")

    def _reset_learning(self):
        """Reset all learned patterns"""
        try:
            if messagebox.askyesno("Confirm Reset", 
                                   "Are you sure you want to reset all learned patterns? " +
                                   "This cannot be undone."):
                self.logger.info("Resetting learning patterns")
                if self.bot.gameplay_learner.reset_learning():
                    self.logger.info("Successfully reset all learned patterns")
                    self.status_label.config(text="Learning Reset Complete")
                else:
                    self.logger.error("Failed to reset learning patterns")
                    messagebox.showerror("Error", "Failed to reset learning patterns")
        except Exception as e:
            self.logger.error(f"Error resetting learning: {str(e)}")

    def _load_map_file(self):
        """Load map file (now including PNG support)"""
        try:
            self.logger.info("Opening file dialog for map loading")
            file_path = filedialog.askopenfilename(
                filetypes=[
                    ("Map Files", "*.json;*.csv;*.png"),
                    ("JSON Files", "*.json"),
                    ("CSV Files", "*.csv"),
                    ("PNG Maps", "*.png"),
                    ("All Files", "*.*")
                ]
            )
            if file_path:
                self.logger.info(f"Loading map from: {file_path}")
                if self.bot.load_map_data(file_path):
                    self.logger.info(f"Successfully loaded map from {file_path}")
                else:
                    self.logger.error("Failed to load map file")
                    messagebox.showerror("Error", "Failed to load map file")
        except Exception as e:
            self.logger.error(f"Error loading map: {str(e)}")
            messagebox.showerror("Error", f"Failed to load map: {str(e)}")

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