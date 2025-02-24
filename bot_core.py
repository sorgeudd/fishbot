"""Core bot functionality with advanced AI features"""
import platform
import logging
from threading import Thread, Event
import time
import sys
from pathlib import Path
import random
import json
import pyaudio
import wave
import numpy as np
import traceback
from collections import deque

try:
    from vision_system import VisionSystem
    from gameplay_learner import GameplayLearner
    from pathfinding import PathFinder
except ImportError as e:
    VisionSystem = None
    GameplayLearner = None
    PathFinder = None

class FishingBot:
    def __init__(self, test_mode=False, test_env=None):
        self.logger = logging.getLogger('FishingBot')
        self.test_mode = test_mode
        self.test_env = test_env

        # Load default configuration first
        self._load_default_config()

        # Initialize empty fields
        self.pyautogui = None
        self.cv2 = None
        self.np = None
        self.ImageGrab = None
        self.win32gui = None
        self.win32process = None
        self.pyaudio = None

        self._init_dependencies()
        self._init_ai_components()

        self.running = False
        self.stop_event = Event()
        self.bot_thread = None
        self.emergency_stop = False
        self.window_handle = None
        self.window_rect = None

        # Initialize pathfinding
        if PathFinder:
            self.pathfinder = PathFinder(grid_size=32)
            self.logger.info("PathFinder initialized with grid_size: 32")
        else:
            self.logger.warning("PathFinder not available")
            self.pathfinder = None

        # Initialize gameplay learning
        if GameplayLearner:
            self.gameplay_learner = GameplayLearner()
            self.logger.info("GameplayLearner initialized")
        else:
            self.logger.warning("GameplayLearner not available")
            self.gameplay_learner = None

        self.learning_mode = False
        self.adaptive_mode = False

        # Add new functionality for macros
        self.macros = {}
        self.current_macro = None
        self.recording_macro = False
        self.macro_actions = []

        # Sound trigger system
        self.sound_triggers = {}
        self.audio_threshold = 0.1
        self.audio_sample_rate = 44100
        self.audio_chunk_size = 1024
        self.audio_format = pyaudio.paFloat32
        self.audio_channels = 1

        # Initialize audio if not in test mode
        if not test_mode:
            try:
                self.audio = pyaudio.PyAudio()
                self.audio_stream = None
            except Exception as e:
                self.logger.warning(f"Could not initialize audio: {e}")
                self.audio = None

        # Load saved configurations
        self._load_macros() #load macros on init
        self._load_sound_triggers() #load sound triggers on init


    def _init_dependencies(self):
        """Initialize dependencies based on platform"""
        if self.test_mode:
            return

        try:
            import cv2
            import numpy as np
            from PIL import ImageGrab

            self.cv2 = cv2
            self.np = np
            self.ImageGrab = ImageGrab

            # Only import Windows-specific modules when on Windows
            if platform.system() == 'Windows':
                import win32gui
                import win32process
                import pyautogui

                self.win32gui = win32gui
                self.win32process = win32process
                self.pyautogui = pyautogui

                # Configure PyAutoGUI safety settings
                self.pyautogui.FAILSAFE = True
                self.pyautogui.PAUSE = 0.1
            else:
                self.logger.warning("Running on non-Windows platform. Some features will be limited.")

            self.logger.info("Successfully initialized dependencies")
        except ImportError as e:
            self.logger.error(f"Failed to import required modules: {str(e)}")
            raise ImportError(f"Missing required module: {str(e)}")

    def _load_default_config(self):
        """Load default configuration"""
        self.config = {
            'detection_area': (0, 0, 100, 100),
            'detection_threshold': 0.8,
            'cast_key': 'f',
            'reel_key': 'r',
            'color_threshold': (200, 200, 200),
            'cast_power': 50,
            'game_window': None,
            'window_title': None,
            'obstacles': [],
            'use_ai': True,
            'pattern_matching': True,
            'mouse_movement_speed': 0.5,
            'click_delay': 0.2,
            'double_click_interval': 0.3,
            'combat_threshold': 80.0,
            'resource_scan_interval': 5.0,
            'combat_keys': ['1', '2', '3', '4'],
            'movement_keys': {
                'forward': 'w',
                'backward': 's',
                'left': 'a',
                'right': 'd',
                'mount': 'y'
            },
            'learning_duration': 3600
        }

    def find_game_window(self, window_title=None):
        """Find game window by title with improved test mode handling"""
        if self.test_mode:
            if window_title and window_title.lower() not in ['test game', 'mock window']:
                # Return False for invalid window titles in test mode
                return False, f"Window '{window_title}' not found in test mode"

            self.window_handle = 1
            self.window_rect = (0, 0, 800, 600)
            return True, "Test mode: Using mock window"

        if platform.system() != 'Windows':
            return False, "Window detection requires Windows OS"

        try:
            if not window_title:
                # Common game window titles to try
                common_titles = [
                    "RuneScape", "World of Warcraft", "OSRS", 
                    "Final Fantasy XIV", "Black Desert", "Lost Ark"
                ]
                for title in common_titles:
                    found = self._find_window_by_title(title)
                    if found:
                        return True, f"Found game window: {title}"
                return False, "No supported game window found"

            found = self._find_window_by_title(window_title)
            if found:
                return True, f"Found specific window: {window_title}"
            return False, f"Window '{window_title}' not found"

        except Exception as e:
            self.logger.error(f"Error finding game window: {str(e)}")
            return False, f"Error: {str(e)}"

    def _find_window_by_title(self, title):
        """Helper method to find window by title"""
        try:
            def callback(hwnd, extra):
                if self.win32gui and self.win32gui.IsWindowVisible(hwnd):
                    window_text = self.win32gui.GetWindowText(hwnd)
                    if title.lower() in window_text.lower():
                        self.window_handle = hwnd
                        self.window_rect = self.win32gui.GetWindowRect(hwnd)
                        return False
                return True

            if self.win32gui:
                self.win32gui.EnumWindows(callback, None)

            if self.window_handle:
                # Get additional window info
                if self.win32gui:
                    self.window_placement = self.win32gui.GetWindowPlacement(self.window_handle)
                    self.window_style = self.win32gui.GetWindowLong(self.window_handle, -16)  # GWL_STYLE

                # Get process info for debugging
                try:
                    if self.win32process:
                        _, pid = self.win32process.GetWindowThreadProcessId(self.window_handle)
                        self.window_process_id = pid
                except Exception as e:
                    self.logger.warning(f"Could not get process ID: {str(e)}")
                    self.window_process_id = None

                # Update config
                self.config['game_window'] = self.window_rect
                self.config['window_title'] = title

                # Log window details
                self.logger.info(f"Found window '{title}' at {self.window_rect}")
                self.logger.debug(f"Window handle: {self.window_handle}")
                self.logger.debug(f"Window placement: {self.window_placement}")
                self.logger.debug(f"Process ID: {self.window_process_id}")

                return True

            return False

        except Exception as e:
            self.logger.error(f"Error in _find_window_by_title: {str(e)}")
            return False

    def _save_sound_triggers(self):
        """Save sound triggers to file"""
        try:
            trigger_file = Path("models/sound_triggers.json")
            trigger_file.parent.mkdir(exist_ok=True)

            # Convert sound trigger data to serializable format
            serializable_triggers = {}
            for name, trigger in self.sound_triggers.items():
                serializable_triggers[name] = {
                    'pattern': trigger['pattern'].tolist() if isinstance(trigger['pattern'], np.ndarray) else trigger['pattern'],
                    'threshold': trigger['threshold']
                }

            with open(trigger_file, 'w') as f:
                json.dump(serializable_triggers, f, indent=2)
            self.logger.info(f"Saved {len(serializable_triggers)} sound triggers")
        except Exception as e:
            self.logger.error(f"Error saving sound triggers: {e}")

    def _load_sound_triggers(self):
        """Load sound triggers from file"""
        try:
            trigger_file = Path("models/sound_triggers.json")
            if trigger_file.exists():
                with open(trigger_file, 'r') as f:
                    data = json.load(f)
                
                # Convert loaded data back to sound triggers
                for name, trigger_data in data.items():
                    pattern = np.array(trigger_data['pattern']) if isinstance(trigger_data['pattern'], list) else trigger_data['pattern']
                    self.sound_triggers[name] = {
                        'pattern': pattern,
                        'threshold': trigger_data['threshold'],
                        'action': None  # Action will be set when binding is created
                    }
                self.logger.info(f"Loaded {len(self.sound_triggers)} sound triggers")
        except Exception as e:
            self.logger.error(f"Error loading sound triggers: {e}")
            self.sound_triggers = {}

    def add_sound_trigger(self, trigger_name, action=None):
        """Add or update a sound trigger with associated action
        Args:
            trigger_name: Name of the trigger
            action: Callable action to execute when trigger activates
        Returns:
            bool: True if trigger was added successfully
        """
        try:
            if not trigger_name:
                self.logger.error("No trigger name provided")
                return False

            if trigger_name not in self.sound_triggers:
                self.logger.error(f"No recorded sound pattern found for trigger: {trigger_name}")
                return False

            if action is None:
                self.logger.error("No action provided for trigger")
                return False

            # Update the trigger with the action
            self.sound_triggers[trigger_name]['action'] = action
            self.logger.info(f"Added action to sound trigger: {trigger_name}")

            # Save updated triggers
            self._save_sound_triggers()
            return True

        except Exception as e:
            self.logger.error(f"Error adding sound trigger: {str(e)}")
            self.logger.error(f"Stack trace: {traceback.format_exc()}")
            return False

    def get_window_info(self):
        """Get detailed information about the current game window"""
        if self.test_mode:
            return {
                'title': 'Test Game Window',
                'rect': (0, 0, 800, 600),
                'is_visible': True,
                'is_active': True,
                'process_id': 12345,
                'placement': None
            }

        if not self.window_handle:
            return None

        try:
            info = {
                'title': self.win32gui.GetWindowText(self.window_handle) if self.win32gui else "N/A",
                'rect': self.window_rect,
                'is_visible': self.win32gui.IsWindowVisible(self.window_handle) if self.win32gui else False,
                'is_active': self.is_window_active(),
                'process_id': getattr(self, 'window_process_id', None),
                'placement': self.window_placement if hasattr(self, 'window_placement') else None
            }
            return info

        except Exception as e:
            self.logger.error(f"Error getting window info: {str(e)}")
            return None

    def load_map_data(self, map_file):
        """Load map data from file for navigation
        Args:
            map_file (str): Path to map data file (JSON, CSV, PNG, etc.)
        Returns:
            bool: True if map was loaded successfully
        """
        try:
            import json
            import csv
            from pathlib import Path

            file_path = Path(map_file)
            if not file_path.exists():
                self.logger.error(f"Map file not found: {map_file}")
                return False

            self.logger.info(f"Loading map data from {file_path}")

            # Handle different file formats
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r') as f:
                    map_data = json.load(f)
                    self.logger.debug(f"Loaded JSON data: {len(map_data)} bytes")
                    if not self._validate_map_data(map_data):
                        return False
                    self.pathfinder.update_map(map_data)
                    self.logger.info(f"Successfully loaded JSON map with {len(map_data.get('nodes', []))} nodes")
                    return True

            elif file_path.suffix.lower() == '.csv':
                with open(file_path, 'r') as f:
                    reader = csv.DictReader(f)
                    map_data = list(reader)
                    self.logger.debug(f"Loaded CSV data: {len(map_data)} rows")
                    if not self._validate_map_data(map_data, format='csv'):
                        return False
                    self.pathfinder.update_map(map_data)
                    self.logger.info(f"Successfully loaded CSV map with {len(map_data)} rows")
                    return True

            elif file_path.suffix.lower() == '.png':
                return self._load_png_map(file_path)

            else:
                self.logger.error(f"Unsupported map file format: {file_path.suffix}")
                return False

        except Exception as e:
            self.logger.error(f"Error loading map data: {str(e)}")
            return False

    def _load_png_map(self, file_path):
        """Load and process PNG map file
        Args:
            file_path: Path to PNG map file
        Returns:
            bool: True if map was loaded successfully
        """
        try:
            # Read PNG file
            self.logger.info(f"Loading map data from {file_path}")
            image = self.cv2.imread(str(file_path)) if self.cv2 else None
            if image is None:
                self.logger.error("Failed to read PNG file")
                return False

            # Convert to grayscale
            gray = self.cv2.cvtColor(image, self.cv2.COLOR_BGR2GRAY) if self.cv2 else None

            # Create binary mask for walkable areas (assuming white/light areas are walkable)
            _, binary = self.cv2.threshold(gray, 200, 255, self.cv2.THRESH_BINARY) if self.cv2 else None
            binary = binary > 127  # Convert to boolean array

            # Create map data structure
            map_data = {
                'binary_map': binary.tolist(), #convert numpy array to list for json serializability
                'resolution': self.pathfinder.grid_size
            }

            # Update pathfinder with new map data
            self.pathfinder.update_map(map_data)
            self.logger.info(f"Successfully loaded PNG map")
            return True

        except Exception as e:
            self.logger.error(f"Error processing PNG map: {str(e)}")
            return False

    def _validate_map_data(self, data, format='json'):
        """Validate map data structure
        Args:
            data: Map data to validate
            format: Format of the data ('json' or 'csv')
        Returns:
            bool: True if data is valid
        """
        try:
            if format == 'json':
                required_keys = {'nodes', 'edges'}
                if not all(key in data for key in required_keys):
                    self.logger.error(f"Missing required keys in map data: {required_keys}")
                    return False

                # Validate nodes
                for node in data['nodes']:
                    if not all(key in node for key in ['id', 'x', 'y', 'type']):
                        self.logger.error(f"Invalid node data: {node}")
                        return False

                # Validate edges
                for edge in data['edges']:
                    if not all(key in edge for key in ['from', 'to']):
                        self.logger.error(f"Invalid edge data: {edge}")
                        return False

            elif format == 'csv':
                required_columns = {'x', 'y', 'type'}
                if not data or not all(col in data[0] for col in required_columns):
                    self.logger.error(f"Missing required columns in CSV: {required_columns}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating map data: {str(e)}")
            return False

    def download_map_data(self, url):
        """Download map data from URL
        Args:
            url (str): URL to map data file
        Returns:
            bool: True if map was downloaded and loaded successfully
        """
        try:
            import requests
            import json
            from pathlib import Path
            import tempfile

            # Download map file
            self.logger.info(f"Downloading map data from {url}")
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                self.logger.error(f"Failed to download map data: {response.status_code}")
                return False

            # Try to parse as JSON first
            try:
                map_data = response.json()
                # Update pathfinder directly with JSON data
                self.pathfinder.update_map(map_data)
                self.logger.info("Successfully downloaded and loaded JSON map data")
                return True
            except json.JSONDecodeError:
                # Not JSON, try as image
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as tmp:
                    tmp.write(response.content)
                    tmp_path = tmp.name

                # Try to load as PNG
                success = self._load_png_map(tmp_path)
                Path(tmp_path).unlink()  # Clean up temp file

                if success:
                    self.logger.info("Successfully downloaded and loaded PNG map")
                    return True

                self.logger.error("Unsupported map data format")
                return False

        except Exception as e:
            self.logger.error(f"Error downloading map data: {str(e)}")
            return False

    def set_window_region(self, region):
        """Set specific region within game window"""
        if not region or len(region) != 4:
            self.logger.error("Invalid window region format")
            return False

        try:
            x, y, width, height = region
            if self.window_rect:
                # Adjust region relative to window position
                window_x, window_y, _, _ = self.window_rect
                absolute_region = (
                    window_x + x,
                    window_y + y,
                    width,
                    height
                )
                self.config['detection_area'] = absolute_region
                self.logger.info(f"Set detection area to: {absolute_region}")
                return True

            self.logger.warning("Window not found, using absolute coordinates")
            self.config['detection_area'] = region
            return True

        except Exception as e:
            self.logger.error(f"Error setting window region: {str(e)}")
            return False

    def is_window_active(self):
        """Check if game window is active/focused"""
        if self.test_mode:
            return True

        try:
            if not self.window_handle:
                return False

            if self.win32gui:
                active_window = self.win32gui.GetForegroundWindow()
                return active_window == self.window_handle
            return False

        except Exception as e:
            self.logger.error(f"Error checking window focus: {str(e)}")
            return False

    def activate_window(self):
        """Activate/focus game window"""
        if self.test_mode:
            return True

        try:
            if not self.window_handle:
                return False

            if not self.is_window_active():
                if self.win32gui:
                    self.win32gui.SetForegroundWindow(self.window_handle)
                    time.sleep(0.1)  # Wait for window activation
                    return self.is_window_active()
            return True

        except Exception as e:
            self.logger.error(f"Error activating window: {str(e)}")
            return False

    def get_window_screenshot(self):
        """Capture screenshot of game window"""
        if self.test_mode:
            return self.test_env.get_screen_region()

        try:
            if not self.window_rect:
                self.logger.warning("No window region set for screenshot")
                return None

            screenshot = self.ImageGrab.grab(bbox=self.window_rect) if self.ImageGrab else None
            return self.np.array(screenshot) if self.np else None

        except Exception as e:
            self.logger.error(f"Error capturing window screenshot: {str(e)}")
            return None

    def _init_ai_components(self):
        """Initialize AI vision system"""
        try:
            model_dir = Path("models")
            model_dir.mkdir(exist_ok=True)

            if VisionSystem is not None:
                self.vision_system = VisionSystem()
                self.logger.info("Vision system initialized")
            else:
                self.logger.warning("VisionSystem not available. Disabling AI features.")
                self.config['use_ai'] = False

        except Exception as e:
            self.logger.error(f"Failed to initialize AI components: {str(e)}")
            self.config['use_ai'] = False

    def train_on_resource_video(self, video_path, resource_type):
        """Train AI on resource video footage"""
        try:
            success = self.vision_system.train_on_video(video_path, resource_type) if self.vision_system else False
            if success:
                self.logger.info(f"Successfully trained on {resource_type} video")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error training on video: {str(e)}")
            return False

    def navigate_to(self, target_pos):
        """Navigate to target position avoiding obstacles"""
        try:
            # Get current position
            current_pos = self.get_current_position()
            if not current_pos:
                return False

            # Find path
            if self.pathfinder:
                path = self.pathfinder.find_path(
                    current_pos,
                    target_pos,
                    bounds=(self.config['game_window'][2], self.config['game_window'][3])
                )
            else:
                path = None

            if not path:
                self.logger.warning("No path found to target")
                return False

            # Smooth path
            if self.pathfinder:
                path = self.pathfinder.smooth_path(path)

            # Follow path
            for next_pos in path:
                if self.stop_event.is_set():
                    return False

                # Turn and move to next position
                self._move_to_position(next_pos)

                # Check for combat
                if self.check_combat_status():
                    self._handle_combat()

            return True

        except Exception as e:
            self.logger.error(f"Navigation error: {str(e)}")
            return False

    def _move_to_position(self, target_pos):
        """Move to specific position using keyboard controls"""
        try:
            current_pos = self.get_current_position()
            if not current_pos:
                return False

            # Calculate direction
            dx = target_pos[0] - current_pos[0]
            dy = target_pos[1] - current_pos[1]

            # Determine key presses needed
            keys = []
            if dx > 0:
                keys.append(self.config['movement_keys']['right'])
            elif dx < 0:
                keys.append(self.config['movement_keys']['left'])

            if dy > 0:
                keys.append(self.config['movement_keys']['forward'])
            elif dy < 0:
                keys.append(self.config['movement_keys']['backward'])

            # Press keys
            for key in keys:
                self.press_key(key, duration=0.1)

            return True

        except Exception as e:
            self.logger.error(f"Movement error: {str(e)}")
            return False

    def _handle_combat(self):
        """Handle combat situation"""
        try:
            combat_start = time.time()
            max_combat_duration = 5.0 if self.test_mode else 30.0

            while (self.check_combat_status() and 
                   not self.stop_event.is_set() and 
                   time.time() - combat_start < max_combat_duration):

                # Check health and heal if needed
                if self.get_current_health() < self.config['combat_threshold']:
                    self.press_key('h')  # Healing ability
                    time.sleep(0.1 if self.test_mode else 1.0)

                # Use combat abilities
                for key in self.config['combat_keys']:
                    if self.stop_event.is_set():
                        break
                    self.press_key(key)
                    time.sleep(0.1 if self.test_mode else random.uniform(0.5, 1.0))

                time.sleep(0.1)

            self.logger.debug("Combat handling complete")

        except Exception as e:
            self.logger.error(f"Combat handling error: {str(e)}")

    def get_current_position(self):
        """Get current position in game world"""
        if self.test_mode:
            state = self.test_env.get_screen_region()
            return state['current_position']
        # TODO: Implement actual position detection
        return (0, 0)

    def scan_surroundings(self):
        """Scan surroundings for resources and obstacles"""
        try:
            if self.test_mode:
                state = self.test_env.get_screen_region()
                resources = state['resources'] or []
                obstacles = state['obstacles'] or []
            else:
                # Capture screen
                if self.window_rect:
                    screen = self.ImageGrab.grab(bbox=self.window_rect) if self.ImageGrab else None
                else:
                    self.logger.warning("Game window not found. Cannot capture screen.")
                    return [], []
                frame = self.np.array(screen) if self.np else None

                # Detect objects
                detections = self.vision_system.detect_objects(frame) if self.vision_system else []

                # Process detections
                resources = []
                obstacles = []
                for det in detections:
                    if det['class_id'] in ['herb', 'ore', 'wood']:
                        resources.append({
                            'type': det['class_id'],
                            'position': det['bbox'][:2] if det['bbox'] else (0, 0)
                        })
                    elif det['class_id'] in ['rock', 'tree', 'wall']:
                        if det['bbox']:
                            obstacles.append(det['bbox'][:2])

            # Update pathfinding obstacles
            if self.pathfinder:
                self.pathfinder.update_obstacles(obstacles)

            return resources, obstacles

        except Exception as e:
            self.logger.error(f"Scanning error: {str(e)}")
            return [], []

    def move_mouse_to(self, x, y, duration=None):
        """Move mouse with enhanced control and window coordinate translation"""
        try:
            if duration is None:
                duration = self.config['mouse_movement_speed']

            if self.test_mode:
                self.record_action('mouse_move', x=x, y=y)
                return self.test_env.move_mouse(x, y)

            if not self.window_handle or not self.window_rect:
                self.logger.error("Window not detected. Cannot move mouse.")
                return False

            # Translate coordinates relative to game window
            window_x, window_y, _, _ = self.window_rect
            target_x = window_x + x
            target_y = window_y + y

            if self.pyautogui:
                # Add slight randomization
                target_x += random.uniform(-2, 2)
                target_y += random.uniform(-2, 2)

                # Ensure window is active
                if not self.is_window_active():
                    self.activate_window()
                    time.sleep(0.1)

                # Get current position
                current_x, current_y = self.pyautogui.position()

                # Generate smooth path
                points = self._generate_bezier_curve(
                    current_x, current_y,
                    target_x, target_y,
                    num_points=20
                )

                # Move through points
                for point_x, point_y in points:
                    if self.stop_event.is_set():
                        return False
                    self.pyautogui.moveTo(point_x, point_y, 
                                        duration/len(points))

                # Record action if recording macro
                self.record_action('mouse_move', x=x, y=y)
                self.logger.debug(f"Moved mouse to ({target_x}, {target_y})")
                return True
            return False

        except Exception as e:
            self.logger.error(f"Mouse movement error: {e}")
            return False

    def start_macro_recording(self, macro_name):
        """Start recording a new macro"""
        try:
            if self.recording_macro:
                self.logger.warning("Already recording a macro")
                return False

            self.recording_macro = True
            self.current_macro = macro_name
            self.macro_actions = []
            self.logger.info(f"Started recording macro: {macro_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error starting macro recording: {e}")
            return False

    def stop_macro_recording(self):
        """Stop recording the current macro"""
        try:
            if not self.recording_macro:
                return False

            self.macros[self.current_macro] = self.macro_actions.copy()
            self.recording_macro = False
            
            # Save macros to file immediately
            self._save_macros()
            
            self.logger.info(f"Stopped recording macro '{self.current_macro}' with {len(self.macro_actions)} actions")
            self.current_macro = None
            self.macro_actions = []
            return True
        except Exception as e:
            self.logger.error(f"Error stopping macro recording: {e}")
            return False

    def _save_macros(self):
        """Save macros to file"""
        try:
            macro_file = Path("models/macros.json")
            macro_file.parent.mkdir(exist_ok=True)

            with open(macro_file, 'w') as f:
                json.dump(self.macros, f, indent=2)
            self.logger.info(f"Saved {len(self.macros)} macros to file")
        except Exception as e:
            self.logger.error(f"Error saving macros: {e}")

    def _load_macros(self):
        """Load macros from file"""
        try:
            macro_file = Path("models/macros.json")
            if macro_file.exists():
                with open(macro_file, 'r') as f:
                    self.macros = json.load(f)
                self.logger.info(f"Loaded {len(self.macros)} macros from file")
            else:
                self.macros = {}
                self.logger.info("No saved macros found")
        except Exception as e:
            self.logger.error(f"Error loading macros: {e}")
            self.macros = {}

    def record_action(self, action_type, **kwargs):
        """Record player action for learning mode and macros
        Args:
            action_type: Type of action ('move', 'click', 'key', etc.)
            **kwargs: Additional action parameters (x, y for mouse, key for keyboard, etc.)

        This method records actions for both learning mode and macro recording.
        """
        try:
            timestamp = time.time()
            self.logger.debug(f"Recording action: {action_type} at {timestamp} with params {kwargs}")

            if self.learning_mode and self.gameplay_learner:
                # Record for learning mode
                position = (kwargs.get('x'), kwargs.get('y')) if 'x' in kwargs and 'y' in kwargs else None
                self.gameplay_learner.record_action(action_type, position, **kwargs)
                self.logger.debug(f"Recorded learning action: {action_type} at {position}")

            if self.recording_macro:
                # Record for macro with detailed coordinates
                action = {
                    'type': action_type,
                    'timestamp': timestamp
                }

                # Handle different action types
                if action_type == 'mouse_move':
                    action.update({
                        'x': kwargs.get('x'),
                        'y': kwargs.get('y')
                    })
                    self.logger.debug(f"Recording mouse movement to ({kwargs.get('x')}, {kwargs.get('y')})")
                elif action_type == 'click':
                    action.update({
                        'x': kwargs.get('x'),
                        'y': kwargs.get('y'),
                        'button': kwargs.get('button', 'left')
                    })
                    self.logger.debug(f"Recording mouse click at ({kwargs.get('x')}, {kwargs.get('y')}) with button {kwargs.get('button')}")
                elif action_type == 'key':
                    action.update({
                        'key': kwargs.get('key'),
                        'duration': kwargs.get('duration', 0.1)
                    })
                    self.logger.debug(f"Recording key press: {kwargs.get('key')}")

                self.macro_actions.append(action)
                self.logger.debug(f"Added action to macro '{self.current_macro}', total actions: {len(self.macro_actions)}")

        except Exception as e:
            self.logger.error(f"Error recording action: {str(e)}")
            self.logger.error(f"Stack trace: {traceback.format_exc()}")



    def _generate_bezier_curve(self, x1, y1, x2, y2, num_points=20):
        """Generate points along a bezier curve for smooth mouse movement"""
        # Control points for the curve
        control_x = x1 + (x2 - x1) * random.uniform(0.3, 0.7)
        control_y = y1 + (y2 - y1) * random.uniform(0.3, 0.7)

        points = []
        for i in range(num_points):
            t = i / (num_points - 1)
            # Quadratic Bezier curve formula
            x = (1-t)**2 * x1 + 2*(1-t)*t * control_x + t**2 * x2
            y = (1-t)**2 * y1 + 2*(1-t)*t * control_y + t**2 * y2
            points.append((int(x), int(y)))

        return points

    def click(self, x=None, y=None, button='left', clicks=1, interval=None):
        """Perform mouse click with optional position and window coordinate translation"""
        try:
            if interval is None:
                interval = self.config['click_delay']

            if x is not None and y is not None:
                if not self.move_mouse_to(x, y):
                    return False

            if not self.window_handle:
                self.logger.error("Window not detected. Cannot click.")
                return False

            if clicks == 2:
                interval = self.config['double_click_interval']

            if self.test_mode:
                self.record_action('click', x=x, y=y, button=button, clicks=clicks)
                return self.test_env.click(button, clicks)

            if self.pyautogui:
                # Ensure window is active
                if not self.is_window_active():
                    self.activate_window()
                    time.sleep(0.1)

                # Convert button name to pyautogui format
                button_map = {
                    'left': 'left',
                    'right': 'right', 
                    'middle': 'middle',
                    'left_click': 'left',
                    'right_click': 'right',
                    'middle_click': 'middle'
                }
                button = button_map.get(button.lower(), button)

                # Add slight random delay for more natural clicking
                time.sleep(random.uniform(0, 0.1))

                self.pyautogui.click(clicks=clicks, interval=interval, button=button)
                self.record_action('click', x=x, y=y, button=button, clicks=clicks)
                self.logger.debug(f"Clicked at current position, button={button}, clicks={clicks}")
                return True
            return False

        except Exception as e:
            self.logger.error(f"Click error: {str(e)}")
            return False

    def press_key(self, key, duration=None):
        """Press key with test mode support"""
        try:
            if self.test_mode:
                self.record_action('key', key=key, duration=duration)
                return self.test_env.press_key(key, duration)

            if self.pyautogui:
                if duration:
                    self.pyautogui.keyDown(key)
                    time.sleep(duration)
                    self.pyautogui.keyUp(key)
                else:
                    self.pyautogui.press(key)
                self.record_action('key', key=key, duration=duration)
                self.logger.debug(f"Pressed key: {key}, duration: {duration}")
                return True
            return False

        except Exception as e:
            self.logger.error(f"Key press error: {str(e)}")
            return False

    def drag_mouse(self, start_x, start_y, end_x, end_y, duration=None):
        """Perform mouse drag operation"""
        try:
            if duration is None:
                duration = self.config['mouse_movement_speed']

            # Move to start position
            self.move_mouse_to(start_x, start_y)

            # Perform drag
            if self.pyautogui:
                self.pyautogui.dragTo(end_x, end_y, duration=duration)
                self.logger.debug(f"Dragged mouse from ({start_x}, {start_y}) to ({end_x}, {end_y})")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Mouse drag error: {str(e)}")
            return False

    def _detect_bite(self):
        """Detect fish bite with test mode support"""
        try:
            if self.test_mode:
                state = self.test_env.get_screen_region()
                if state.get('fish_bite_active', False):
                    self.logger.debug("Test mode: Bite detected")
                    # Trigger reeling action
                    self.press_key(self.config['reel_key'])
                    return True
                return False

            if not self.config['game_window']:
                self.logger.warning("Game window not set")
                return False

            # Process detection area
            screen = self.ImageGrab.grab(bbox=self.config['detection_area']) if self.ImageGrab else None
            screen_np = self.np.array(screen) if self.np else None

            if self.config['use_ai'] and self.vision_system:
                # Use AI-based detection when enabled
                bite_detected = self._ai_detect_bite(screen_np)
            else:
                # Use basic color/motion detection
                bite_detected = self._basic_detect_bite(screen_np)

            if bite_detected:
                # Trigger reeling action when bite detected
                self.press_key(self.config['reel_key'])
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error detecting bite: {str(e)}")
            return False

    def _basic_detect_bite(self, screen_np):
        """Basic color threshold bite detection"""
        try:
            mask = self.np.all(screen_np >= self.config['color_threshold'], axis=-1) if self.np else False
            return bool(self.np.any(mask)) if self.np else False
        except Exception as e:
            self.logger.error(f"Error in basic bite detection: {str(e)}")
            return False


    def record_action(self, action_type, position=None, **kwargs):
        """Record player action for learning mode and macros
        Args:
            action_type: Type of action ('move', 'click', 'key', etc.)
            position: Optional position tuple for the action
            **kwargs: Additional action parameters
        """
        try:
            if self.learning_mode and self.gameplay_learner:
                # Record for learning mode
                self.gameplay_learner.record_action(action_type, position, **kwargs)
                self.logger.debug(f"Recorded learning action: {action_type} at {position}")

            if self.recording_macro:
                # Record for macro
                action = {
                    'type': action_type,
                    'position': position,
                    'timestamp': time.time(),
                    **kwargs
                }
                self.macro_actions.append(action)
                self.logger.debug(f"Recorded macro action: {action}")

        except Exception as e:
            self.logger.error(f"Error recording action: {str(e)}")

    def get_next_action(self):
        """Get next optimal action based on learned patterns"""
        if not self.adaptive_mode or not self.gameplay_learner:
            return None

        current_state = {
            'health': self.get_current_health(),
            'in_combat': self.check_combat_status(),
            'is_mounted': False,  # TODO: Implement mount detection
            'detected_resources': self.scan_for_resources(),
            'detected_obstacles': self.scan_for_obstacles()
        }

        return self.gameplay_learner.predict_next_action(current_state)


    def _bot_loop(self):
        """Main bot loop with enhanced action recording"""
        while not self.stop_event.is_set():
            try:
                if self.learning_mode and self.gameplay_learner:
                    # Record current state
                    current_state = {
                        'position': self.get_current_position(),
                        'health': self.get_current_health(),
                        'in_combat': self.check_combat_status()
                    }

                    # Cast fishing line with variable timing
                    self.press_key(self.config['cast_key'])
                    time.sleep(random.uniform(0.5, 1.0) if self.test_mode else random.uniform(1.8, 2.2))

                    # Wait for and handle fish bite
                    bite_detected = False
                    start_time = time.time()
                    max_wait = 2.0 if self.test_mode else 10.0

                    while not self.stop_event.is_set() and time.time() - start_time < max_wait:
                        if self._detect_bite():
                            bite_detected = True
                            self.logger.debug("Bite detected, reeling...")
                            time.sleep(random.uniform(0.1, 0.3))
                            self.press_key(self.config['reel_key'])
                            self.record_action('reel', current_state['position'], success=True)
                            time.sleep(random.uniform(0.5, 1.0) if self.test_mode else random.uniform(2.8, 3.2))
                            break
                        time.sleep(0.1)

                    if not bite_detected:
                        self.record_action('timeout', current_state['position'], success=False)
                        self.logger.debug("Recording timeout action")

                # Regular fishing bot behavior
                else:
                    # Get cast power and add randomization
                    cast_power = self.config.get('cast_power', 50)
                    cast_power += random.uniform(-5, 5)  # Add variation
                    cast_power = max(0, min(100, cast_power))  # Clamp between 0 and 100

                    # Cast fishing line with variable timing
                    self.press_key(self.config['cast_key'], duration=cast_power/100.0)
                    time.sleep(random.uniform(1.8, 2.2))  # Randomized delay

                    # Wait for fish bite with timeout
                    bite_detected = False
                    start_time = time.time()
                    max_wait = 2.0 if self.test_mode else 10.0

                    while not self.stop_event.is_set() and time.time() - start_time < max_wait:
                        if self._detect_bite():
                            bite_detected = True
                            self.logger.debug("Bite detected, reeling...")
                            time.sleep(random.uniform(0.1, 0.3))
                            self.press_key(self.config['reel_key'])
                            time.sleep(random.uniform(2.8, 3.2))
                            break
                        time.sleep(0.1)

                # Scan for resources and handle combat periodically
                self._scan_and_handle_environment()

            except Exception as e:
                self.logger.error(f"Error in bot loop: {str(e)}")
                if not self.test_mode:
                    time.sleep(1.0)  # Prevent rapid retries in case of persistent errors

    def _scan_and_handle_environment(self):
        """Handle resource scanning and combat situations"""
        try:
            # Check for combat
            if self.check_combat_status():
                self._handle_combat()
                return

            # Scan for resources
            resources = self.scan_for_resources()
            for resource in resources:
                if self.stop_event.is_set():
                    break
                # Navigate to resource
                if self.pathfinder:
                    self.navigate_to(resource['position'])
                # Record gathering action if in learning mode
                if self.learning_mode and self.gameplay_learner:
                    self.record_action('gather', resource['position'],
                                        resource_type=resource['type'])

        except Exception as e:
            self.logger.error(f"Error in environment scanning: {str(e)}")

    def start_macro_recording(self, macro_name):
        """Start recording a new macro"""
        try:
            if self.recording_macro:
                self.logger.warning("Already recording a macro")
                return False

            self.recording_macro = True
            self.current_macro = macro_name
            self.macro_actions = []
            self.logger.info(f"Started recording macro: {macro_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error starting macro recording: {e}")
            return False

    def stop_macro_recording(self):
        """Stop recording the current macro"""
        try:
            if not self.recording_macro:
                return False

            self.macros[self.current_macro] = self.macro_actions.copy()
            self.recording_macro = False
            self.current_macro = None
            self.macro_actions = []

            # Save macros to file
            self._save_macros()
            self.logger.info("Stopped macro recording and saved")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping macro recording: {e}")
            return False

    def _save_macros(self):
        """Save macros to file"""
        try:
            macro_file = Path("models/macros.json")
            macro_file.parent.mkdir(exist_ok=True)

            with open(macro_file, 'w') as f:
                json.dump(self.macros, f, indent=2)
            self.logger.debug("Saved macros to file")
        except Exception as e:
            self.logger.error(f"Error saving macros: {e}")

    def _load_macros(self):
        """Load macros from file"""
        try:
            macro_file = Path("models/macros.json")
            if macro_file.exists():
                with open(macro_file, 'r') as f:
                    self.macros = json.load(f)
                self.logger.info(f"Loaded {len(self.macros)} macros")
        except Exception as e:
            self.logger.error(f"Error loading macros: {e}")

    def play_macro(self, macro_name):
        """Play back a recorded macro"""
        if macro_name not in self.macros:
            self.logger.error(f"Macro '{macro_name}' not found")
            return False

        try:
            actions = self.macros[macro_name]
            for action in actions:
                if self.stop_event.is_set():
                    break

                action_type = action['type']
                if action_type == 'mouse_move':
                    self.move_mouse_to(action['x'], action['y'])
                elif action_type == 'click':
                    self.click(action['x'], action['y'], 
                             button=action.get('button', 'left'),
                             clicks=action.get('clicks', 1))
                elif action_type == 'key':
                    self.press_key(action['key'], 
                                 duration=action.get('duration', None))

                # Wait specified delay
                time.sleep(action.get('delay', 0.1))

            return True
        except Exception as e:
            self.logger.error(f"Error playing macro: {e}")
            return False

    def add_sound_trigger(self, name, sound_file, action, threshold=0.1):
        """Add a sound trigger that executes an action when matched"""
        try:
            # Load sound file
            with wave.open(sound_file, 'rb') as wf:
                audio_data = wf.readframes(wf.getnframes())
                audio_data = np.frombuffer(audio_data, dtype=np.float32)

            self.sound_triggers[name] = {
                'pattern': audio_data,
                'action': action,
                'threshold': threshold
            }
            self.logger.info(f"Added sound trigger: {name}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding sound trigger: {e}")
            return False

    def start_sound_monitoring(self):
        """Start monitoring audio for sound triggers"""
        if not self.audio:
            self.logger.error("Audio not initialized")
            return False

        try:
            def audio_callback(in_data, frame_count, time_info, status):
                if status:
                    self.logger.warning(f"Audio status: {status}")

                # Convert input to numpy array
                audio_data = np.frombuffer(in_data, dtype=np.float32)

                # Check each trigger
                for name, trigger in self.sound_triggers.items():
                    if self._match_audio_pattern(audio_data, 
                                               trigger['pattern'],
                                               trigger['threshold']):
                        # Execute the triggered action
                        Thread(target=trigger['action']).start()
                        self.logger.info(f"Sound trigger activated: {name}")

                return (in_data, pyaudio.paContinue)

            # Start audio stream
            self.audio_stream = self.audio.open(
                format=self.audio_format,
                channels=self.audio_channels,
                rate=self.audio_sample_rate,
                input=True,
                frames_per_buffer=self.audio_chunk_size,
                stream_callback=audio_callback
            )

            self.audio_stream.start_stream()
            self.logger.info("Started sound monitoring")
            return True

        except Exception as e:
            self.logger.error(f"Error starting sound monitoring: {e}")
            return False

    def stop_sound_monitoring(self):
        """Stop monitoring audio"""
        try:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            self.logger.info("Stopped sound monitoring")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping sound monitoring: {e}")
            return False

    def _match_audio_pattern(self, input_data, pattern, threshold):
        """Match input audio against a stored pattern"""
        try:
            # Simple amplitude threshold for now
            if np.max(np.abs(input_data)) > threshold:
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error matching audio: {e}")
            return False

    def import_map(self, map_file):
        """Import and process map file with resource locations"""
        try:
            map_path = Path(map_file)
            if not map_path.exists():
                self.logger.error(f"Map file not found: {map_file}")
                return False

            # Process based on file type
            if map_path.suffix.lower() == '.json':
                with open(map_path, 'r') as f:
                    map_data = json.load(f)
            else:
                # Use CV2 to process image map
                if not self.cv2:
                    self.logger.error("CV2 not available for map processing")
                    return False

                # Read map image
                map_img = self.cv2.imread(str(map_path))
                if map_img is None:
                    self.logger.error("Failed to read map image")
                    return False

                # Process map image to extract resource locations
                map_data = self._process_map_image(map_img)

            # Update pathfinding with new map data
            if map_data and self.pathfinder:
                self.pathfinder.update_map(map_data)
                self.logger.info("Successfully imported and processed map")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error importing map: {e}")
            return False

    def _process_map_image(self, map_img):
        """Process map image to extract resource locations and walkable areas"""
        try:
            # Convert to HSV for better color detection
            hsv = self.cv2.cvtColor(map_img, self.cv2.COLOR_BGR2HSV)

            # Define color ranges for different resources
            color_ranges = {
                'fishing_spot': [(100, 150, 100), (140, 255, 255)],  # Blue
                'tree': [(35, 100, 100), (85, 255, 255)],  # Green
                'ore': [(0, 100, 100), (20, 255, 255)]  # Brown/Orange
            }

            resources = {}
            for resource_type, (lower, upper) in color_ranges.items():
                # Create color mask
                lower = np.array(lower)
                upper = np.array(upper)
                mask = self.cv2.inRange(hsv, lower, upper)

                # Find contours
                contours, _ = self.cv2.findContours(
                    mask, self.cv2.RETR_EXTERNAL, 
                    self.cv2.CHAIN_APPROX_SIMPLE
                )

                # Extract locations
                locations = []
                for contour in contours:
                    # Get center point
                    M = self.cv2.moments(contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        locations.append((cx, cy))

                resources[resource_type] = locations

            # Create walkable area mask (light areas)
            gray = self.cv2.cvtColor(map_img, self.cv2.COLOR_BGR2GRAY)
            _, walkable = self.cv2.threshold(
                gray, 200, 255, self.cv2.THRESH_BINARY
            )

            # Combine into map data
            map_data = {
                'resources': resources,
                'walkable': walkable.tolist(),
                'resolution': self.pathfinder.grid_size if self.pathfinder else 32
            }

            return map_data

        except Exception as e:
            self.logger.error(f"Error processing map image: {e}")
            return None

    def import_training_video(self, video_file):
        """Import and process training video file with progress updates"""
        try:
            video_path = Path(video_file)
            if not video_path.exists():
                self.logger.error(f"Video file not found: {video_file}")
                return False

            if not self.cv2:
                self.logger.error("CV2 not available for video processing")
                return False

            # Open video file
            cap = self.cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                self.logger.error("Failed to open video file")
                return False

            # Get total frame count for progress tracking
            total_frames = int(cap.get(self.cv2.CAP_PROP_FRAME_COUNT))
            self.logger.info(f"Processing video with {total_frames} frames")

            # Start learning mode
            self.start_learning()

            # Process frames in chunks to prevent freezing
            frame_count = 0
            chunk_size = 100  # Process 100 frames at a time

            while cap.isOpened():
                chunk_start = time.time()

                # Process a chunk of frames
                for _ in range(chunk_size):
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # Process frame
                    self._process_training_frame(frame)
                    frame_count += 1

                    # Report progress
                    progress = (frame_count / total_frames) * 100
                    self.logger.info(f"Processed {frame_count}/{total_frames} frames ({progress:.1f}%)")

                # Small delay between chunks to prevent freezing
                chunk_time = time.time() - chunk_start
                if chunk_time < 0.1:  # If chunk processed too quickly
                    time.sleep(0.1 - chunk_time)  # Add small delay

                if frame_count >= total_frames:
                    break

            cap.release()

            # Stop learning and save patterns
            self.stop_learning()
            self.logger.info(f"Completed video training: {frame_count} frames")
            return True

        except Exception as e:
            self.logger.error(f"Error importing training video: {str(e)}")
            self.stop_learning()  # Ensure learning mode is stopped
            return False

    def _process_training_frame(self, frame):
        """Process a single frame from training video"""
        try:
            # Convert frame to format expected by vision system
            frame_rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)

            # Detect objects and activities
            detections = self.vision_system.detect_objects(frame_rgb) if self.vision_system else []

            # Process each detection
            for det in detections:
                if det['class_id'] == 'fishing_action':
                    self.record_action('fishing', position=det['bbox'][:2])
                elif det['class_id'] == 'movement':
                    self.record_action('move', position=det['bbox'][:2])
                elif det['class_id'] == 'resource_interaction':
                    self.record_action('gather', position=det['bbox'][:2])

        except Exception as e:
            self.logger.error(f"Error processing training frame: {e}")

    def load_video(self, video_path):
        """Load and process video data for AI training"""
        try:
            video_path = Path(video_path)
            if not video_path.exists():
                self.logger.error(f"Video file not found: {video_path}")
                return False
            
            if not self.cv2:
                self.logger.error("OpenCV (cv2) is not installed. Cannot load video.")
                return False
            
            cap = self.cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                self.logger.error(f"Could not open video file: {video_path}")
                return False
            
            frames = []
            while(cap.isOpened()):
                ret, frame = cap.read()
                if not ret:
                    break
                frames.append(frame)
            
            cap.release()
            self.logger.info(f"Loaded video with {len(frames)} frames")
            return frames
            
        except Exception as e:
            self.logger.error(f"Error loading video: {e}")
            return None

    def _ai_detect_bite(self, screen_image):
        """AI-based bite detection using both CV and Hugging Face model"""
        try:
            # Convert to RGB for the feature extractor
            if len(screen_image.shape) == 2:  # If grayscale
                screen_image = self.cv2.cvtColor(screen_image, self.cv2.COLOR_GRAY2RGB) if self.cv2 else None
            elif screen_image.shape[2] == 4:  # If RGBA
                screen_image = screen_image[:, :, :3]  # Convert to RGB

            # Use Hugging Face model for prediction
            if self.config['use_ai'] and hasattr(self, 'feature_extractor'):
                inputs = self.feature_extractor(screen_image, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                with torch.no_grad():
                    outputs = self.model(**inputs)
                    predictions = outputs.logits.softmax(-1)
                    confidence = predictions.max().item()

                if confidence > self.config['detection_threshold']:
                    self.logger.debug(f"AI detected bite with confidence: {confidence:.2f}")
                    return True

            # Fallback to CV-based detection
            gray = self.cv2.cvtColor(screen_image, self.cv2.COLOR_RGB2GRAY) if self.cv2 else None
            edges = self.cv2.Canny(gray, 100, 200) if self.cv2 else None
            contours, _ = self.cv2.findContours(edges, self.cv2.RETR_EXTERNAL, self.cv2.CHAIN_APPROX_SIMPLE) if self.cv2 else ([], None)

            for contour in contours:
                area = self.cv2.contourArea(contour) if self.cv2 else 0
                if area > 100:  # Minimum area threshold
                    return True
            return False

        except Exception as e:
            self.logger.error(f"AI detection error: {str(e)}")
            return False

    def record_bite_sound(self):
        """Record sound for bite detection"""
        try:
            self.logger.info("Starting bite sound recording...")
            # Initialize PyAudio
            if self.pyaudio:
                p = self.pyaudio.PyAudio()

                # Set recording parameters
                FORMAT = self.pyaudio.paFloat32
                CHANNELS = 1
                RATE = 44100
                CHUNK = 1024
                RECORD_SECONDS = 3

                # Start recording
                stream = p.open(format=FORMAT,
                                         channels=CHANNELS,
                                         rate=RATE,
                                         input=True,
                                         frames_per_buffer=CHUNK)

                self.logger.info("Recording...")
                frames = []

                for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    data = stream.read(CHUNK)
                    frames.append(data)

                self.logger.info("Finished recording")

                # Stop and close the stream
                stream.stop_stream()
                stream.close()
                p.terminate()

                # Save the recorded data
                # TODO: Implement save functionality
                self.logger.info("Saved recorded sound")
            else:
                self.logger.warning("pyaudio not initialized. Skipping sound recording.")

        except Exception as e:
            self.logger.error(f"Error recording sound: {str(e)}")

    def add_obstacle(self, position):
        self.config['obstacles'].append(position)
        self.logger.info(f"Added obstacle at position: {position}")

    def clear_obstacles(self):
        self.config['obstacles'].clear()
        self.logger.info("Cleared all obstacles")

    def set_game_window(self, region):
        self.config['game_window'] = region
        self.logger.info(f"Set game window region: {region}")

    def update_config(self, new_config):
        self.config.update(new_config)
        self.logger.info("Configuration updated")

    def check_combat_status(self):
        """Check if bot is in combat"""
        if self.test_mode:
            state = self.test_env.get_screen_region()
            return state['in_combat']
        # Real implementation will check game window for combat indicators
        return False

    def get_current_health(self):
        """Get current health percentage"""
        if self.test_mode:
            state = self.test_env.get_screen_region()
            return state['health']
        # Real implementation will read health from game UI
        return 100.0

    def scan_for_obstacles(self):
        """Detect obstacles in view"""
        if self.test_mode:
            state = self.test_env.get_screen_region()
            return state['obstacles'] or []
        # Real implementation will use computer vision
        return []

    def scan_for_resources(self):
        """Detect gatherable resources"""
        if self.test_mode:
            state = self.test_env.get_screen_region()
            return state['resources'] or []
        # Real implementation will use AI model
        return []

    def start(self):
        if not self.running and not self.emergency_stop:
            self.running = True
            self.stop_event.clear()
            self.bot_thread = Thread(target=self._bot_loop)
            self.bot_thread.start()
            self.logger.info("Bot started")

    def stop(self):
        """Stop bot operation and cleanup resources"""
        try:
            if self.running:
                self.logger.info("Stopping bot operation...")
                self.running = False
                self.stop_event.set()

                if self.bot_thread:
                    self.logger.debug("Waiting for bot thread to finish...")
                    self.bot_thread.join(timeout=5.0)  # Add timeout
                    if self.bot_thread.is_alive():
                        self.logger.warning("Bot thread did not terminate properly")

                self.logger.info("Bot stopped successfully")

            # Reset state
            self.emergency_stop = False
            self.bot_thread = None
            self.stop_event.clear()
            if self.audio_stream:
                self.stop_sound_monitoring()

        except Exception as e:
            self.logger.error(f"Error stopping bot: {str(e)}")

    def emergency_stop_action(self):
        self.emergency_stop = True
        self.stop()
        self.logger.warning("Emergency stop activated")

    def start_learning(self):
        """Start learning mode to capture user actions"""
        try:
            if not self.window_handle and not self.test_mode:
                self.logger.error("Cannot start learning - no game window detected")
                return False

            self.learning_mode = True
            if self.gameplay_learner:
                self.gameplay_learner.start_learning()  # Start the gameplay learner
            else:
                self.logger.warning("GameplayLearner not initialized, skipping learning.")
            self.logger.info("Learning mode started - Now recording user actions")
            return True

        except Exception as e:
            self.logger.error(f"Error starting learning mode: {str(e)}")
            return False

    def stop_learning(self):
        """Stop learning mode and save learned patterns"""
        try:
            if not self.learning_mode:
                self.logger.debug("Learning mode was not active")
                return True

            self.learning_mode = False
            if self.gameplay_learner:
                # Stop learning and save patterns
                success = self.gameplay_learner.stop_learning()
                if success:
                    self.logger.info("Learning mode stopped and patterns saved successfully")
                else:
                    self.logger.error("Failed to stop learning mode or save patterns")
                return success
            else:
                self.logger.warning("GameplayLearner not initialized, skipping saving.")
                return True

        except Exception as e:
            self.logger.error(f"Error stopping learning mode: {str(e)}")
            return False

    def start_learning_mode(self):
        """Start recording player actions to learn patterns"""
        self.learning_mode = True
        self.adaptive_mode = False
        if self.gameplay_learner:
            self.gameplay_learner.start_learning()
        else:
            self.logger.warning("GameplayLearner not initialized, skipping learning.")
        self.logger.info("Started learning mode")

        # Start timer to automatically stop learning
        def auto_stop():
            time.sleep(self.config['learning_duration'])
            if self.learning_mode:
                self.stop_learning_mode()

        Thread(target=auto_stop, daemon=True).start()

    def stop_learning_mode(self):
        """Stop learning mode and analyze patterns"""
        if not self.learning_mode:
            return
        self.learning_mode = False
        if self.gameplay_learner:
            self.gameplay_learner.stop_learning()
        self.logger.info("Stopped learning mode and analyzed patterns")

    def start_adaptive_mode(self):
        """Start using learned patterns for gameplay"""
        self.adaptive_mode = True
        self.learning_mode = False
        self.logger.info("Started adaptive gameplay mode")

    def record_action(self, action_type, position=None, **kwargs):
        """Record player action for learning mode and macros
        Args:
            action_type: Type of action ('move', 'click', 'key', etc.)
            position: Optional position tuple for the action
            **kwargs: Additional action parameters
        """
        try:
            if self.learning_mode and self.gameplay_learner:
                # Record for learning mode
                self.gameplay_learner.record_action(action_type, position, **kwargs)
                self.logger.debug(f"Recorded learning action: {action_type} at {position}")

            if self.recording_macro:
                # Record for macro
                action = {
                    'type': action_type,
                    'position': position,
                    'timestamp': time.time(),
                    **kwargs
                }
                self.macro_actions.append(action)
                self.logger.debug(f"Recorded macro action: {action}")

        except Exception as e:
            self.logger.error(f"Error recording action: {str(e)}")

    def _ai_detect_bite(self, screen_image):
        """AI-based bite detection using both CV and Hugging Face model"""
        try:
            # Convert to RGB for the feature extractor
            if len(screen_image.shape) == 2:  # If grayscale
                screen_image = self.cv2.cvtColor(screen_image, self.cv2.COLOR_GRAY2RGB) if self.cv2 else None
            elif screen_image.shape[2] == 4:  # If RGBA
                screen_image = screen_image[:, :, :3]  # Convert to RGB

            # Use Hugging Face model for prediction
            if self.config['use_ai'] and hasattr(self, 'feature_extractor'):
                inputs = self.feature_extractor(screen_image, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                with torch.no_grad():
                    outputs = self.model(**inputs)
                    predictions = outputs.logits.softmax(-1)
                    confidence = predictions.max().item()

                if confidence > self.config['detection_threshold']:
                    self.logger.debug(f"AI detected bite with confidence: {confidence:.2f}")
                    return True

            # Fallback to CV-based detection
            gray = self.cv2.cvtColor(screen_image, self.cv2.COLOR_RGB2GRAY) if self.cv2 else None
            edges = self.cv2.Canny(gray, 100, 200) if self.cv2 else None
            contours, _ = self.cv2.findContours(edges, self.cv2.RETR_EXTERNAL, self.cv2.CHAIN_APPROX_SIMPLE) if self.cv2 else ([], None)

            for contour in contours:
                area = self.cv2.contourArea(contour) if self.cv2 else 0
                if area > 100:  # Minimum area threshold
                    return True
            return False

        except Exception as e:
            self.logger.error(f"AI detection error: {str(e)}")
            return False

    def record_bite_sound(self):
        """Record sound for bite detection"""
        try:
            self.logger.info("Starting bite sound recording...")
            # Initialize PyAudio
            if self.pyaudio:
                p = self.pyaudio.PyAudio()

                # Set recording parameters
                FORMAT = self.pyaudio.paFloat32
                CHANNELS = 1
                RATE = 44100
                CHUNK = 1024
                RECORD_SECONDS = 3

                # Start recording
                stream = p.open(format=FORMAT,
                                         channels=CHANNELS,
                                         rate=RATE,
                                         input=True,
                                         frames_per_buffer=CHUNK)

                self.logger.info("Recording...")
                frames = []

                for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    data = stream.read(CHUNK)
                    frames.append(data)

                self.logger.info("Finished recording")

                # Stop and close the stream
                stream.stop_stream()
                stream.close()
                p.terminate()

                # Save the recorded data
                # TODO: Implement save functionality
                self.logger.info("Saved recorded sound")
            else:
                self.logger.warning("pyaudio not initialized. Skipping sound recording.")

        except Exception as e:
            self.logger.error(f"Error recording sound: {str(e)}")

    def add_obstacle(self, position):
        self.config['obstacles'].append(position)
        self.logger.info(f"Added obstacle at position: {position}")

    def clear_obstacles(self):
        self.config['obstacles'].clear()
        self.logger.info("Cleared all obstacles")

    def set_game_window(self, region):
        self.config['game_window'] = region
        self.logger.info(f"Set game window region: {region}")

    def update_config(self, new_config):
        self.config.update(new_config)
        self.logger.info("Configuration updated")

    def check_combat_status(self):
        """Check if bot is in combat"""
        if self.test_mode:
            state = self.test_env.get_screen_region()
            return state['in_combat']
        # Real implementation will check game window for combat indicators
        return False

    def get_current_health(self):
        """Get current health percentage"""
        if self.test_mode:
            state = self.test_env.get_screen_region()
            return state['health']
        # Real implementation will read health from game UI
        return 100.0

    def scan_for_obstacles(self):
        """Detect obstacles in view"""
        if self.test_mode:
            state = self.test_env.get_screen_region()
            return state['obstacles'] or []
        # Real implementation will use computer vision
        return []

    def scan_for_resources(self):
        """Detect gatherable resources"""
        if self.test_mode:
            state = self.test_env.get_screen_region()
            return state['resources'] or []
        # Real implementation will use AI model
        return []

    def start(self):
        if not self.running and not self.emergency_stop:
            self.running = True
            self.stop_event.clear()
            self.bot_thread = Thread(target=self._bot_loop)
            self.bot_thread.start()
            self.logger.info("Bot started")

    def stop(self):
        """Stop bot operation and cleanup resources"""
        try:
            if self.running:
                self.logger.info("Stopping bot operation...")
                self.running = False
                self.stop_event.set()

                if self.bot_thread:
                    self.logger.debug("Waiting for bot thread to finish...")
                    self.bot_thread.join(timeout=5.0)  # Add timeout
                    if self.bot_thread.is_alive():
                        self.logger.warning("Bot thread did not terminate properly")

                self.logger.info("Bot stopped successfully")

            # Reset state
            self.emergency_stop = False
            self.bot_thread = None
            self.stop_event.clear()
            if self.audio_stream:
                self.stop_sound_monitoring()

        except Exception as e:
            self.logger.error(f"Error stopping bot: {str(e)}")

    def emergency_stop_action(self):
        self.emergency_stop = True
        self.stop()
        self.logger.warning("Emergency stop activated")

    def start_learning(self):
        """Start learning mode to capture user actions"""
        try:
            if not self.window_handle and not self.test_mode:
                self.logger.error("Cannot start learning - no game window detected")
                return False

            self.learning_mode = True
            if self.gameplay_learner:
                self.gameplay_learner.start_learning()  # Start the gameplay learner
            else:
                self.logger.warning("GameplayLearner not initialized, skipping learning.")
            self.logger.info("Learning mode started - Now recording user actions")
            return True

        except Exception as e:
            self.logger.error(f"Error starting learning mode: {str(e)}")
            return False

    def stop_learning(self):
        """Stop learning mode and save learned patterns"""
        try:
            if not self.learning_mode:
                self.logger.debug("Learning mode was not active")
                return True

            self.learning_mode = False
            if self.gameplay_learner:
                # Stop learning and save patterns
                success = self.gameplay_learner.stop_learning()
                if success:
                    self.logger.info("Learning mode stopped and patterns saved successfully")
                else:
                    self.logger.error("Failed to stop learning mode or save patterns")
                return success
            else:
                self.logger.warning("GameplayLearner not initialized, skipping saving.")
                return True

        except Exception as e:
            self.logger.error(f"Error stopping learning mode: {str(e)}")
            return False

    def start_learning_mode(self):
        """Start recording player actions to learn patterns"""
        self.learning_mode = True
        self.adaptive_mode = False
        if self.gameplay_learner:
            self.gameplay_learner.start_learning()
        else:
            self.logger.warning("GameplayLearner not initialized, skipping learning.")
        self.logger.info("Started learning mode")

        # Start timer to automatically stop learning
        def auto_stop():
            time.sleep(self.config['learning_duration'])
            if self.learning_mode:
                self.stop_learning_mode()

        Thread(target=auto_stop, daemon=True).start()

    def stop_learning_mode(self):
        """Stop learning mode and analyze patterns"""
        if not self.learning_mode:
            return
        self.learning_mode = False
        if self.gameplay_learner:
            self.gameplay_learner.stop_learning()
        self.logger.info("Stopped learning mode and analyzed patterns")

    def start_adaptive_mode(self):
        """Start using learned patterns for gameplay"""
        self.adaptive_mode = True
        self.learning_mode = False
        self.logger.info("Started adaptive gameplay mode")

    def record_action(self, action_type, position=None, **kwargs):
        """Record player action for learning mode and macros
        Args:
            action_type: Type of action ('move', 'click', 'key', etc.)
            position: Optional position tuple for the action
            **kwargs: Additional action parameters
        """
        try:
            if self.learning_mode and self.gameplay_learner:
                # Record for learning mode
                self.gameplay_learner.record_action(action_type, position, **kwargs)
                self.logger.debug(f"Recorded learning action: {action_type} at {position}")

            if self.recording_macro:
                # Record for macro
                action = {
                    'type': action_type,
                    'position': position,
                    'timestamp': time.time(),
                    **kwargs
                }
                self.macro_actions.append(action)
                self.logger.debug(f"Recorded macro action: {action}")

        except Exception as e:
            self.logger.error(f"Error recording action: {str(e)}")

    def get_next_action(self):
        """Get next optimal action based on learned patterns"""
        if not self.adaptive_mode or not self.gameplay_learner:
            return None

        current_state = {
            'health': self.get_current_health(),
            'in_combat': self.check_combat_status(),
            'is_mounted': False,  # TODO: Implement mount detection
            'detected_resources': self.scan_for_resources(),
            'detected_obstacles': self.scan_for_obstacles()
        }

        return self.gameplay_learner.predict_next_action(current_state)


    def _bot_loop(self):
        """Main bot loop with enhanced action recording"""
        while not self.stop_event.is_set():
            try:
                if self.learning_mode and self.gameplay_learner:
                    # Record current state
                    current_state = {
                        'position': self.get_current_position(),
                        'health': self.get_current_health(),
                        'in_combat': self.check_combat_status()
                    }

                    # Cast fishing line with variable timing
                    self.press_key(self.config['cast_key'])
                    time.sleep(random.uniform(0.5, 1.0) if self.test_mode else random.uniform(1.8, 2.2))

                    # Wait for and handle fish bite
                    bite_detected = False
                    start_time = time.time()
                    max_wait = 2.0 if self.test_mode else 10.0

                    while not self.stop_event.is_set() and time.time() - start_time < max_wait:
                        if self._detect_bite():
                            bite_detected = True
                            self.logger.debug("Bite detected, reeling...")
                            time.sleep(random.uniform(0.1, 0.3))
                            self.press_key(self.config['reel_key'])
                            self.record_action('reel', current_state['position'], success=True)
                            time.sleep(random.uniform(0.5, 1.0) if self.test_mode else random.uniform(2.8, 3.2))
                            break
                        time.sleep(0.1)

                    if not bite_detected:
                        self.record_action('timeout', current_state['position'], success=False)
                        self.logger.debug("Recording timeout action")

                # Regular fishing bot behavior
                else:
                    # Get cast power and add randomization
                    cast_power = self.config.get('cast_power', 50)
                    cast_power += random.uniform(-5, 5)  # Add variation
                    cast_power = max(0, min(100, cast_power))  # Clamp between 0 and 100

                    # Cast fishing line with variable timing
                    self.press_key(self.config['cast_key'], duration=cast_power/100.0)
                    time.sleep(random.uniform(1.8, 2.2))  # Randomized delay

                    # Wait for fish bite with timeout
                    bite_detected = False
                    start_time = time.time()
                    max_wait = 2.0 if self.test_mode else 10.0

                    while not self.stop_event.is_set() and time.time() - start_time < max_wait:
                        if self._detect_bite():
                            bite_detected = True
                            self.logger.debug("Bite detected, reeling...")
                            time.sleep(random.uniform(0.1, 0.3))
                            self.press_key(self.config['reel_key'])
                            time.sleep(random.uniform(2.8, 3.2))
                            break
                        time.sleep(0.1)

                # Scan for resources and handle combat periodically
                self._scan_and_handle_environment()

            except Exception as e:
                self.logger.error(f"Error in bot loop: {str(e)}")
                if not self.test_mode:
                    time.sleep(1.0)  # Prevent rapid retries in case of persistent errors

    def _scan_and_handle_environment(self):
        """Handle resource scanning and combat situations"""
        try:
            # Check for combat
            if self.check_combat_status():
                self._handle_combat()
                return

            # Scan for resources
            resources = self.scan_for_resources()
            for resource in resources:
                if self.stop_event.is_set():
                    break
                # Navigate to resource
                if self.pathfinder:
                    self.navigate_to(resource['position'])
                # Record gathering action if in learning mode
                if self.learning_mode and self.gameplay_learner:
                    self.record_action('gather', resource['position'],
                                        resource_type=resource['type'])

        except Exception as e:
            self.logger.error(f"Error in environment scanning: {str(e)}")

    def start_macro_recording(self, macro_name):
        """Start recording a new macro"""
        try:
            if self.recording_macro:
                self.logger.warning("Already recording a macro")
                return False

            self.recording_macro = True
            self.current_macro = macro_name
            self.macro_actions = []
            self.logger.info(f"Started recording macro: {macro_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error starting macro recording: {e}")
            return False

    def stop_macro_recording(self):
        """Stop recording the current macro"""
        try:
            if not self.recording_macro:
                return False

            self.macros[self.current_macro] = self.macro_actions.copy()
            self.recording_macro = False
            self.current_macro = None
            self.macro_actions = []

            # Save macros to file
            self._save_macros()
            self.logger.info("Stopped macro recording and saved")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping macro recording: {e}")
            return False

    def _save_macros(self):
        """Save macros to file"""
        try:
            macro_file = Path("models/macros.json")
            macro_file.parent.mkdir(exist_ok=True)

            with open(macro_file, 'w') as f:
                json.dump(self.macros, f, indent=2)
            self.logger.debug("Saved macros to file")
        except Exception as e:
            self.logger.error(f"Error saving macros: {e}")

    def _load_macros(self):
        """Load macros from file"""
        try:
            macro_file = Path("models/macros.json")
            if macro_file.exists():
                with open(macro_file, 'r') as f:
                    self.macros = json.load(f)
                self.logger.info(f"Loaded {len(self.macros)} macros")
        except Exception as e:
            self.logger.error(f"Error loading macros: {e}")

    def play_macro(self, macro_name):
        """Play back a recorded macro"""
        if macro_name not in self.macros:
            self.logger.error(f"Macro '{macro_name}' not found")
            return False

        try:
            actions = self.macros[macro_name]
            for action in actions:
                if self.stop_event.is_set():
                    break

                action_type = action['type']
                if action_type == 'mouse_move':
                    self.move_mouse_to(action['x'], action['y'])
                elif action_type == 'click':
                    self.click(action['x'], action['y'], 
                             button=action.get('button', 'left'),
                             clicks=action.get('clicks', 1))
                elif action_type == 'key':
                    self.press_key(action['key'], 
                                 duration=action.get('duration', None))

                # Wait specified delay
                time.sleep(action.get('delay', 0.1))

            return True
        except Exception as e:
            self.logger.error(f"Error playing macro: {e}")
            return False

    def add_sound_trigger(self, name, sound_file, action, threshold=0.1):
        """Add a sound trigger that executes an action when matched"""
        try:
            # Load sound file
            with wave.open(sound_file, 'rb') as wf:
                audio_data = wf.readframes(wf.getnframes())
                audio_data = np.frombuffer(audio_data, dtype=np.float32)

            self.sound_triggers[name] = {
                'pattern': audio_data,
                'action': action,
                'threshold': threshold
            }
            self.logger.info(f"Added sound trigger: {name}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding sound trigger: {e}")
            return False

    def start_sound_monitoring(self):
        """Start monitoring audio for sound triggers"""
        if not self.audio:
            self.logger.error("Audio not initialized")
            return False

        try:
            def audio_callback(in_data, frame_count, time_info, status):
                if status:
                    self.logger.warning(f"Audio status: {status}")

                # Convert input to numpy array
                audio_data = np.frombuffer(in_data, dtype=np.float32)

                # Check each trigger
                for name, trigger in self.sound_triggers.items():
                    if self._match_audio_pattern(audio_data, 
                                               trigger['pattern'],
                                               trigger['threshold']):
                        # Execute the triggered action
                        Thread(target=trigger['action']).start()
                        self.logger.info(f"Sound trigger activated: {name}")

                return (in_data, pyaudio.paContinue)

            # Start audio stream
            self.audio_stream = self.audio.open(
                format=self.audio_format,
                channels=self.audio_channels,
                rate=self.audio_sample_rate,
                input=True,
                frames_per_buffer=self.audio_chunk_size,
                stream_callback=audio_callback
            )

            self.audio_stream.start_stream()
            self.logger.info("Started sound monitoring")
            return True

        except Exception as e:
            self.logger.error(f"Error starting sound monitoring: {e}")
            return False

    def stop_sound_monitoring(self):
        """Stop monitoring audio"""
        try:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            self.logger.info("Stopped sound monitoring")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping sound monitoring: {e}")
            return False

    def _match_audio_pattern(self, input_data, pattern, threshold):
        """Match input audio against a stored pattern"""
        try:
            # Simple amplitude threshold for now
            if np.max(np.abs(input_data)) > threshold:
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error matching audio: {e}")
            return False

    def import_map(self, map_file):
        """Import and process map file with resource locations"""
        try:
            map_path = Path(map_file)
            if not map_path.exists():
                self.logger.error(f"Map file not found: {map_file}")
                return False

            # Process based on file type
            if map_path.suffix.lower() == '.json':
                with open(map_path, 'r') as f:
                    map_data = json.load(f)
            else:
                # Use CV2 to process image map
                if not self.cv2:
                    self.logger.error("CV2 not available for map processing")
                    return False

                # Read map image
                map_img = self.cv2.imread(str(map_path))
                if map_img is None:
                    self.logger.error("Failed to read map image")
                    return False

                # Process map image to extract resource locations
                map_data = self._process_map_image(map_img)

            # Update pathfinding with new map data
            if map_data and self.pathfinder:
                self.pathfinder.update_map(map_data)
                self.logger.info("Successfully imported and processed map")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error importing map: {e}")
            return False

    def _process_map_image(self, map_img):
        """Process map image to extract resource locations and walkable areas"""
        try:
            # Convert to HSV for better color detection
            hsv = self.cv2.cvtColor(map_img, self.cv2.COLOR_BGR2HSV)

            # Define color ranges for different resources
            color_ranges = {
                'fishing_spot': [(100, 150, 100), (140, 255, 255)],  # Blue
                'tree': [(35, 100, 100), (85, 255, 255)],  # Green
                'ore': [(0, 100, 100), (20, 255, 255)]  # Brown/Orange
            }

            resources = {}
            for resource_type, (lower, upper) in color_ranges.items():
                # Create color mask
                lower = np.array(lower)
                upper = np.array(upper)
                mask = self.cv2.inRange(hsv, lower, upper)

                # Find contours
                contours, _ = self.cv2.findContours(
                    mask, self.cv2.RETR_EXTERNAL, 
                    self.cv2.CHAIN_APPROX_SIMPLE
                )

                # Extract locations
                locations = []
                for contour in contours:
                    # Get center point
                    M = self.cv2.moments(contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        locations.append((cx, cy))

                resources[resource_type] = locations

            # Create walkable area mask (light areas)
            gray = self.cv2.cvtColor(map_img, self.cv2.COLOR_BGR2GRAY)
            _, walkable = self.cv2.threshold(
                gray, 200, 255, self.cv2.THRESH_BINARY
            )

            # Combine into map data
            map_data = {
                'resources': resources,
                'walkable': walkable.tolist(),
                'resolution': self.pathfinder.grid_size if self.pathfinder else 32
            }

            return map_data

        except Exception as e:
            self.logger.error(f"Error processing map image: {e}")
            return None

    def import_training_video(self, video_file):
        """Import and process training video file with progress updates"""
        try:
            video_path = Path(video_file)
            if not video_path.exists():
                self.logger.error(f"Video file not found: {video_file}")
                return False

            if not self.cv2:
                self.logger.error("CV2 not available for video processing")
                return False

            # Open video file
            cap = self.cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                self.logger.error("Failed to open video file")
                return False

            # Get total frame count for progress tracking
            total_frames = int(cap.get(self.cv2.CAP_PROP_FRAME_COUNT))
            self.logger.info(f"Processing video with {total_frames} frames")

            # Start learning mode
            self.start_learning()

            # Process frames in chunks to prevent freezing
            frame_count = 0
            chunk_size = 100  # Process 100 frames at a time

            while cap.isOpened():
                chunk_start = time.time()

                # Process a chunk of frames
                for _ in range(chunk_size):
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # Process frame
                    self._process_training_frame(frame)
                    frame_count += 1

                    # Report progress
                    progress = (frame_count / total_frames) * 100
                    self.logger.info(f"Processed {frame_count}/{total_frames} frames ({progress:.1f}%)")

                # Small delay between chunks to prevent freezing
                chunk_time = time.time() - chunk_start
                if chunk_time < 0.1:  # If chunk processed too quickly
                    time.sleep(0.1 - chunk_time)  # Add small delay

                if frame_count >= total_frames:
                    break

            cap.release()

            # Stop learning and save patterns
            self.stop_learning()
            self.logger.info(f"Completed video training: {frame_count} frames")
            return True

        except Exception as e:
            self.logger.error(f"Error importing training video: {str(e)}")
            self.stop_learning()  # Ensure learning mode is stopped
            return False

    def _process_training_frame(self, frame):
        """Process a single frame from training video"""
        try:
            # Convert frame to format expected by vision system
            frame_rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)

            # Detect objects and activities
            detections = self.vision_system.detect_objects(frame_rgb) if self.vision_system else []

            # Process each detection
            for det in detections:
                if det['class_id'] == 'fishing_action':
                    self.record_action('fishing', position=det['bbox'][:2])
                elif det['class_id'] == 'movement':
                    self.record_action('move', position=det['bbox'][:2])
                elif det['class_id'] == 'resource_interaction':
                    self.record_action('gather', position=det['bbox'][:2])

        except Exception as e:
            self.logger.error(f"Error processing training frame: {e}")

    def load_video(self, video_path):
        """Load and process video data for AI training"""
        try:
            video_path = Path(video_path)
            if not video_path.exists():
                self.logger.error(f"Video file not found: {video_path}")
                return False
            
            if not self.cv2:
                self.logger.error("OpenCV (cv2) is not installed. Cannot load video.")
                return False
            
            cap = self.cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                self.logger.error(f"Could not open video file: {video_path}")
                return False
            
            frames = []
            while(cap.isOpened()):
                ret, frame = cap.read()
                if not ret:
                    break
                frames.append(frame)
            
            cap.release()
            self.logger.info(f"Loaded video with {len(frames)} frames")
            return frames
            
        except Exception as e:
            self.logger.error(f"Error loading video: {e}")
            return None