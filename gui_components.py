import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import logging
from bot_core import FishingBot
from config_manager import ConfigManager
import urllib.parse
import threading
import sys
import traceback

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
            self.master.resizable(True, True)  # Make window resizable
            self.master.minsize(400, 600)  # Set minimum size
            self.master.geometry("400x800")  # Set default size
            self.logger.debug("Main window configured")

            # Create main container frame
            main_frame = ttk.Frame(self.master)
            main_frame.pack(fill="both", expand=True)

            # Status section at top
            status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
            status_frame.pack(fill="x", padx=5, pady=2)
            self.status_label = ttk.Label(status_frame, text="Idle")
            self.status_label.pack(padx=5, pady=2)

            # Controls section
            controls_frame = ttk.LabelFrame(main_frame, text="Controls", padding="5")
            controls_frame.pack(fill="x", padx=5, pady=2)

            # Emergency Stop
            self.emergency_stop_btn = ttk.Button(controls_frame, text="EMERGENCY STOP (F6)", 
                                          command=self._emergency_stop, style="Emergency.TButton")
            self.emergency_stop_btn.pack(fill="x", padx=5, pady=2)

            # Window Detection Frame
            window_frame = ttk.LabelFrame(main_frame, text="Game Window", padding="5")
            window_frame.pack(fill="x", padx=5, pady=2)

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
            learning_frame = ttk.LabelFrame(main_frame, text="Learning Mode", padding="5")
            learning_frame.pack(fill="x", padx=5, pady=2)

            # Learning Status
            self.learning_status = ttk.Label(learning_frame, text="Learning: Inactive")
            self.learning_status.pack(padx=5, pady=2)

            # Learning Controls Frame
            learning_controls = ttk.Frame(learning_frame)
            learning_controls.pack(fill="x", padx=5, pady=2)

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
            self.import_video_btn.pack(fill="x", padx=5, pady=2)

            # Map Management Frame
            map_frame = ttk.LabelFrame(main_frame, text="Map Management", padding="5")
            map_frame.pack(fill="x", padx=5, pady=2)

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

            # Macro Management Frame
            macro_frame = ttk.LabelFrame(main_frame, text="Macro Management", padding="5")
            macro_frame.pack(fill="x", padx=5, pady=2)

            # Macro Name Entry
            macro_name_frame = ttk.Frame(macro_frame)
            macro_name_frame.pack(fill="x", padx=5, pady=2)
            ttk.Label(macro_name_frame, text="Macro Name:").pack(side="left", padx=5)
            self.macro_name_entry = ttk.Entry(macro_name_frame)
            self.macro_name_entry.pack(side="left", fill="x", expand=True, padx=5)

            # Macro Controls Frame
            macro_controls = ttk.Frame(macro_frame)
            macro_controls.pack(fill="x", padx=5, pady=2)

            # Record/Stop Macro Button
            self.record_macro_btn = ttk.Button(macro_controls, text="Record Macro", 
                                       command=self._toggle_macro_recording)
            self.record_macro_btn.pack(side="left", fill="x", expand=True, padx=2)

            # Play Macro Button
            self.play_macro_btn = ttk.Button(macro_controls, text="Play Macro",
                                    command=self._play_macro)
            self.play_macro_btn.pack(side="right", fill="x", expand=True, padx=2)

            # Sound Trigger Frame
            sound_frame = ttk.LabelFrame(main_frame, text="Sound Triggers", padding="5")
            sound_frame.pack(fill="x", padx=5, pady=2)

            # Trigger Name Entry
            trigger_name_frame = ttk.Frame(sound_frame)
            trigger_name_frame.pack(fill="x", padx=5, pady=2)
            ttk.Label(trigger_name_frame, text="Trigger Name:").pack(side="left", padx=5)
            self.trigger_name_entry = ttk.Entry(trigger_name_frame)
            self.trigger_name_entry.pack(side="left", fill="x", expand=True, padx=5)

            # Record Sound Button
            self.record_sound_btn = ttk.Button(sound_frame, text="Record Sound",
                                      command=self._record_sound)
            self.record_sound_btn.pack(fill="x", padx=5, pady=2)

            # Action Binding Frame
            action_frame = ttk.Frame(sound_frame)
            action_frame.pack(fill="x", padx=5, pady=2)
            ttk.Label(action_frame, text="Bind Action:").pack(side="left", padx=5)

            # Action Type Combobox
            self.action_type = ttk.Combobox(action_frame, 
                                          values=["Key Press", "Mouse Click", "Macro"])
            self.action_type.pack(side="left", padx=5)
            self.action_type.set("Key Press")

            # Key/Button Entry
            self.action_key_entry = ttk.Entry(action_frame, width=10)
            self.action_key_entry.pack(side="left", padx=5)

            # Save Trigger Button
            self.save_trigger_btn = ttk.Button(sound_frame, text="Save Trigger",
                                      command=self._save_sound_trigger)
            self.save_trigger_btn.pack(fill="x", padx=5, pady=2)


            # Bot Control Frame
            bot_frame = ttk.LabelFrame(main_frame, text="Bot Control", padding="5")
            bot_frame.pack(fill="x", padx=5, pady=2)

            # Start Bot Button
            self.start_bot_btn = ttk.Button(bot_frame, text="Start Bot", 
                                     command=self._start_bot)
            self.start_bot_btn.pack(fill="x", padx=5, pady=2)

            # Log Display (at bottom, fixed height)
            log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
            log_frame.pack(fill="both", expand=True, padx=5, pady=2)

            # Create log display with fixed height (30% of window)
            self.log_display = scrolledtext.ScrolledText(log_frame, height=10)
            self.log_display.pack(fill="both", expand=True, padx=5, pady=2)

            # Configure row/column weights
            main_frame.grid_rowconfigure(1, weight=1)
            main_frame.grid_columnconfigure(0, weight=1)

            # Update logging to use GUI
            self._setup_gui_logging()

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
                self.logger.info("Attempting to start learning mode...")
                if self.test_mode:
                    self.logger.debug("Running in test mode")
                success = self.bot.start_learning()
                if success:
                    self.logger.info("Successfully started learning mode")
                    self.learning_btn.config(text="Stop Learning")
                    self.learning_status.config(text="Learning: Active")
                    self.status_label.config(text="Learning Mode")
                    self.start_bot_btn.config(state="disabled")
                    self.logger.debug("GUI updated for learning mode start")
                else:
                    self.logger.error("Failed to start learning mode")
                    messagebox.showerror("Error", "Failed to start learning mode")
            else:
                self.logger.info("Attempting to stop learning mode...")
                success = self.bot.stop_learning()
                if success:
                    self.logger.info("Successfully stopped learning mode")
                    self.learning_btn.config(text="Start Learning")
                    self.learning_status.config(text="Learning: Inactive")
                    self.status_label.config(text="Idle")
                    self.start_bot_btn.config(state="normal")
                    self.logger.debug("GUI updated for learning mode stop")
                else:
                    self.logger.error("Failed to stop learning mode")
                    messagebox.showerror("Error", "Failed to stop learning mode")
        except Exception as e:
            self.logger.error(f"Error toggling learning mode: {str(e)}")
            self.logger.error(f"Stack trace: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Error toggling learning mode: {str(e)}")

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
        """Record sound for trigger"""
        try:
            trigger_name = self.trigger_name_entry.get().strip()
            if not trigger_name:
                messagebox.showerror("Error", "Please enter a trigger name")
                return

            # Toggle recording
            if self.record_sound_btn.cget("text") == "Record Sound":
                self.record_sound_btn.config(text="Stop Recording")
                self.status_label.config(text="Recording Sound...")
                self.bot.start_sound_monitoring()
            else:
                self.record_sound_btn.config(text="Record Sound")
                self.status_label.config(text="Sound Recorded")
                self.bot.stop_sound_monitoring()

        except Exception as e:
            self.logger.error(f"Error recording sound: {str(e)}")
            messagebox.showerror("Error", f"Failed to record sound: {str(e)}")

    def _save_sound_trigger(self):
        """Save sound trigger with action binding"""
        try:
            trigger_name = self.trigger_name_entry.get().strip()
            if not trigger_name:
                messagebox.showerror("Error", "Please enter a trigger name")
                return

            action_type = self.action_type.get()
            action_key = self.action_key_entry.get().strip()
            if not action_key:
                messagebox.showerror("Error", "Please enter a key or button")
                return

            # Create action function based on type
            if action_type == "Key Press":
                action = lambda: self.bot.press_key(action_key)
            elif action_type == "Mouse Click":
                action = lambda: self.bot.click(button=action_key)
            else:  # Macro
                action = lambda: self.bot.play_macro(action_key)

            # Save trigger
            if self.bot.add_sound_trigger(trigger_name, action):
                self.status_label.config(text="Trigger Saved")
                self.trigger_name_entry.delete(0, tk.END)
                self.action_key_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", "Failed to save trigger")

        except Exception as e:
            self.logger.error(f"Error saving sound trigger: {str(e)}")
            messagebox.showerror("Error", f"Failed to save trigger: {str(e)}")

    def _toggle_macro_recording(self):
        """Toggle macro recording on/off"""
        try:
            if not self.bot.recording_macro:
                macro_name = self.macro_name_entry.get().strip()
                if not macro_name:
                    messagebox.showerror("Error", "Please enter a macro name")
                    return

                if self.bot.start_macro_recording(macro_name):
                    self.record_macro_btn.config(text="Stop Recording")
                    self.play_macro_btn.config(state="disabled")
                    self.status_label.config(text=f"Recording Macro: {macro_name}")
            else:
                if self.bot.stop_macro_recording():
                    self.record_macro_btn.config(text="Record Macro")
                    self.play_macro_btn.config(state="normal")
                    self.status_label.config(text="Macro Recorded")
                    self.macro_name_entry.delete(0, tk.END)

        except Exception as e:
            self.logger.error(f"Error toggling macro recording: {str(e)}")
            messagebox.showerror("Error", f"Failed to toggle macro recording: {str(e)}")

    def _play_macro(self):
        """Play selected macro"""
        try:
            macro_name = self.macro_name_entry.get().strip()
            if not macro_name:
                messagebox.showerror("Error", "Please enter a macro name")
                return

            if macro_name not in self.bot.macros:
                messagebox.showerror("Error", f"Macro '{macro_name}' not found")
                return

            self.status_label.config(text=f"Playing Macro: {macro_name}")
            success = self.bot.play_macro(macro_name)

            if success:
                self.status_label.config(text="Macro Completed")
            else:
                self.status_label.config(text="Macro Failed")
                messagebox.showerror("Error", "Failed to play macro")

        except Exception as e:
            self.logger.error(f"Error playing macro: {str(e)}")
            messagebox.showerror("Error", f"Failed to play macro: {str(e)}")

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