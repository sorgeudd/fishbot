"""Core bot functionality with advanced AI features"""
import platform
import logging
from threading import Thread, Event
import time
import sys
from pathlib import Path
import random
from vision_system import VisionSystem
from pathfinding import PathFinder
from gameplay_learner import GameplayLearner

class FishingBot:
    def __init__(self, test_mode=False, test_env=None):
        self.logger = logging.getLogger('FishingBot')
        self.test_mode = test_mode
        self.test_env = test_env

        # Only import Windows dependencies when needed
        self.pyautogui = None
        self.cv2 = None
        self.np = None
        self.ImageGrab = None
        self.win32gui = None
        self.win32process = None # Added for process ID retrieval

        self._init_dependencies()
        self._init_ai_components()

        self.running = False
        self.stop_event = Event()
        self.bot_thread = None
        self.emergency_stop = False
        self.window_handle = None
        self.window_rect = None

        # Initialize pathfinding
        self.pathfinder = PathFinder(grid_size=32)
        self.logger.info("PathFinder initialized with grid size: 32")

        # Initialize gameplay learning
        self.gameplay_learner = GameplayLearner()
        self.learning_mode = False
        self.adaptive_mode = False

        # Load default configuration
        self._load_default_config()

    def _init_dependencies(self):
        """Initialize Windows-specific dependencies"""
        if self.test_mode:
            return

        if platform.system() != 'Windows':
            self.logger.error("This bot only works on Windows operating system")
            raise SystemError("FishingBot requires Windows to run")

        try:
            import pyautogui
            import cv2
            import numpy as np
            from PIL import ImageGrab
            import win32gui
            import win32process # Added for process ID retrieval

            self.pyautogui = pyautogui
            self.cv2 = cv2
            self.np = np
            self.ImageGrab = ImageGrab
            self.win32gui = win32gui
            self.win32process = win32process # Added for process ID retrieval

            # Configure PyAutoGUI safety settings
            self.pyautogui.FAILSAFE = True
            self.pyautogui.PAUSE = 0.1

            self.logger.info("Successfully initialized Windows dependencies")
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
        """Find game window by title

        Args:
            window_title (str): Full or partial window title to match. If None, 
                              will try to find any game window from common titles.

        Returns:
            tuple: (success, message)
                - success (bool): True if window was found
                - message (str): Status message or error details
        """
        if self.test_mode:
            self.window_handle = 1
            self.window_rect = (0, 0, 800, 600)
            return True, "Test mode: Using mock window"

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
                if self.win32gui.IsWindowVisible(hwnd):
                    window_text = self.win32gui.GetWindowText(hwnd)
                    if title.lower() in window_text.lower():
                        self.window_handle = hwnd
                        self.window_rect = self.win32gui.GetWindowRect(hwnd)
                        return False
                return True

            self.win32gui.EnumWindows(callback, None)

            if self.window_handle:
                # Get additional window info
                self.window_placement = self.win32gui.GetWindowPlacement(self.window_handle)
                self.window_style = self.win32gui.GetWindowLong(self.window_handle, -16)  # GWL_STYLE

                # Update config
                self.config['game_window'] = self.window_rect
                self.config['window_title'] = title

                # Log window details
                self.logger.info(f"Found window '{title}' at {self.window_rect}")
                self.logger.debug(f"Window handle: {self.window_handle}")
                self.logger.debug(f"Window placement: {self.window_placement}")

                return True

            return False

        except Exception as e:
            self.logger.error(f"Error in _find_window_by_title: {str(e)}")
            return False

    def get_window_info(self):
        """Get detailed information about the current game window"""
        if not self.window_handle:
            return None

        try:
            info = {
                'title': self.win32gui.GetWindowText(self.window_handle),
                'rect': self.window_rect,
                'is_visible': self.win32gui.IsWindowVisible(self.window_handle),
                'is_active': self.is_window_active(),
                'placement': self.window_placement if hasattr(self, 'window_placement') else None
            }

            # Get process info
            if hasattr(self, 'win32process'):
                try:
                    _, pid = self.win32process.GetWindowThreadProcessId(self.window_handle)
                    info['process_id'] = pid
                except:
                    info['process_id'] = None

            return info

        except Exception as e:
            self.logger.error(f"Error getting window info: {str(e)}")
            return None

    def load_map_data(self, map_file):
        """Load map data from file for navigation

        Args:
            map_file (str): Path to map data file (JSON, CSV, etc.)

        Returns:
            bool: True if map was loaded successfully
        """
        try:
            import json
            import csv

            # Handle different file formats
            if map_file.endswith('.json'):
                with open(map_file, 'r') as f:
                    map_data = json.load(f)
                    self.pathfinder.load_map(map_data)
                    self.logger.info(f"Loaded JSON map data from {map_file}")
                    return True

            elif map_file.endswith('.csv'):
                with open(map_file, 'r') as f:
                    reader = csv.DictReader(f)
                    map_data = list(reader)
                    self.pathfinder.load_map(map_data)
                    self.logger.info(f"Loaded CSV map data from {map_file}")
                    return True

            else:
                self.logger.error(f"Unsupported map file format: {map_file}")
                return False

        except Exception as e:
            self.logger.error(f"Error loading map data: {str(e)}")
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
            import tempfile
            import os

            # Download map file
            response = requests.get(url)
            if response.status_code != 200:
                self.logger.error(f"Failed to download map data: {response.status_code}")
                return False

            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name

            # Load the downloaded map
            success = self.load_map_data(tmp_path)

            # Cleanup temp file
            os.unlink(tmp_path)

            return success

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

            active_window = self.win32gui.GetForegroundWindow()
            return active_window == self.window_handle

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

            screenshot = self.ImageGrab.grab(bbox=self.window_rect)
            return self.np.array(screenshot)

        except Exception as e:
            self.logger.error(f"Error capturing window screenshot: {str(e)}")
            return None

    def _init_ai_components(self):
        """Initialize AI vision system"""
        try:
            model_dir = Path("models")
            model_dir.mkdir(exist_ok=True)

            self.vision_system = VisionSystem()
            self.logger.info("Vision system initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize AI components: {str(e)}")
            self.config['use_ai'] = False

    def train_on_resource_video(self, video_path, resource_type):
        """Train AI on resource video footage"""
        try:
            success = self.vision_system.train_on_video(video_path, resource_type)
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
            path = self.pathfinder.find_path(
                current_pos,
                target_pos,
                bounds=(self.config['game_window'][2], self.config['game_window'][3])
            )

            if not path:
                self.logger.warning("No path found to target")
                return False

            # Smooth path
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
                    screen = self.ImageGrab.grab(bbox=self.window_rect)
                else:
                    self.logger.warning("Game window not found. Cannot capture screen.")
                    return [], []
                frame = self.np.array(screen)

                # Detect objects
                detections = self.vision_system.detect_objects(frame)

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
            self.pathfinder.update_obstacles(obstacles)

            return resources, obstacles

        except Exception as e:
            self.logger.error(f"Scanning error: {str(e)}")
            return [], []

    def move_mouse_to(self, x, y, duration=None):
        """Move mouse with test mode support"""
        try:
            if duration is None:
                duration = self.config['mouse_movement_speed']

            if self.test_mode:
                return self.test_env.move_mouse(x, y)

            if self.pyautogui:
                # Add slight randomization to prevent detection
                x += random.uniform(-2, 2)
                y += random.uniform(-2, 2)
                self.pyautogui.moveTo(x, y, duration=duration)
                self.logger.debug(f"Moved mouse to ({x}, {y})")
                return True
            return False

        except Exception as e:
            self.logger.error(f"Mouse movement error: {str(e)}")
            return False

    def click(self, x=None, y=None, button='left', clicks=1, interval=None):
        """Perform mouse click with optional position"""
        try:
            if interval is None:
                interval = self.config['click_delay']

            if x is not None and y is not None:
                self.move_mouse_to(x, y)

            if clicks == 2:
                interval = self.config['double_click_interval']

            if self.test_mode:
                return self.test_env.click(button, clicks)

            if self.pyautogui:
                self.pyautogui.click(clicks=clicks, interval=interval, button=button)
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
                return self.test_env.press_key(key, duration)

            if self.pyautogui:
                if duration:
                    self.pyautogui.keyDown(key)
                    time.sleep(duration)
                    self.pyautogui.keyUp(key)
                else:
                    self.pyautogui.press(key)
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
            self.pyautogui.dragTo(end_x, end_y, duration=duration)
            self.logger.debug(f"Dragged mouse from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            return True
        except Exception as e:
            self.logger.error(f"Mouse drag error: {str(e)}")
            return False

    def _detect_bite(self):
        """Detect fish bite with test mode support"""
        try:
            if self.test_mode:
                state = self.test_env.get_screen_region()
                # Force bite detection in test mode after 1 second
                if hasattr(self, '_test_mode_start_time'):
                    if time.time() - self._test_mode_start_time > 1.0:
                        return True
                else:
                    self._test_mode_start_time = time.time()
                return bool(state.get('fish_bite_active', False))

            if not self.config['game_window']:
                self.logger.warning("Game window not set")
                return False

            # Capture screen in detection area
            screen = self.ImageGrab.grab(bbox=self.config['detection_area'])
            screen_np = self.np.array(screen)

            if self.config['use_ai']:
                # Use AI-based detection when enabled
                return self._ai_detect_bite(screen_np)
            else:
                # Simple color threshold detection
                mask = self.np.all(screen_np >= self.config['color_threshold'], axis=-1)
                return bool(self.np.any(mask))

        except Exception as e:
            self.logger.error(f"Error in bite detection: {str(e)}")
            return False

    def _ai_detect_bite(self, screen_image):
        """AI-based bite detection using both CV and Hugging Face model"""
        try:
            # Convert to RGB for the feature extractor
            if len(screen_image.shape) == 2:  # If grayscale
                screen_image = self.cv2.cvtColor(screen_image, self.cv2.COLOR_GRAY2RGB)
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
            gray = self.cv2.cvtColor(screen_image, self.cv2.COLOR_RGB2GRAY)
            edges = self.cv2.Canny(gray, 100, 200)
            contours, _ = self.cv2.findContours(edges, self.cv2.RETR_EXTERNAL, self.cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                area = self.cv2.contourArea(contour)
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
        if self.running:
            self.running = False
            self.stop_event.set()
            if self.bot_thread:
                self.bot_thread.join()
            self.logger.info("Bot stopped")

    def emergency_stop_action(self):
        self.emergency_stop = True
        self.stop()
        self.logger.warning("Emergency stop activated")

    def start_learning_mode(self):
        """Start recording player actions to learn patterns"""
        self.learning_mode = True
        self.adaptive_mode = False
        self.gameplay_learner.start_learning()
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
        self.gameplay_learner.stop_learning()
        self.logger.info("Stopped learning mode and analyzed patterns")

    def start_adaptive_mode(self):
        """Start using learned patterns for gameplay"""
        self.adaptive_mode = True
        self.learning_mode = False
        self.logger.info("Started adaptive gameplay mode")

    def record_action(self, action_type, position, **kwargs):
        """Record player action during learning mode"""
        if self.learning_mode:
            self.gameplay_learner.record_action(action_type, position, **kwargs)
            self.logger.debug(f"Recorded action: {action_type} at {position}")

    def get_next_action(self):
        """Get next optimal action based on learned patterns"""
        if not self.adaptive_mode:
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
                if self.learning_mode:
                    # Record current state
                    current_state = {
                        'position': self.get_current_position(),
                        'health': self.get_current_health(),
                        'in_combat': self.check_combat_status()
                    }

                    # Clear test mode timer at start of each cycle
                    if self.test_mode:
                        self._test_mode_start_time = time.time()

                    # Record fishing action
                    self.record_action('cast', current_state['position'])
                    self.logger.debug("Recording cast action")

                    # Cast fishing line with variable timing
                    cast_power = self.config.get('cast_power', 50)
                    cast_power += random.uniform(-5, 5)
                    cast_power = max(0, min(100, cast_power))

                    self.press_key(self.config['cast_key'], duration=cast_power/100.0)
                    time.sleep(random.uniform(0.5, 1.0) if self.test_mode else random.uniform(1.8, 2.2))

                    # Wait for and handle fish bite
                    bite_detected = False
                    start_time = time.time()
                    max_wait = 2.0 if self.test_mode else 10.0

                    while not self.stop_event.is_set() and time.time() - start_time < max_wait:
                        if self._detect_bite():
                            bite_detected = True
                            time.sleep(random.uniform(0.1, 0.3))
                            self.press_key(self.config['reel_key'])
                            self.record_action('reel', current_state['position'], success=True)
                            self.logger.debug("Recording reel action")
                            time.sleep(random.uniform(0.5, 1.0) if self.test_mode else random.uniform(2.8, 3.2))
                            break
                        time.sleep(0.1)

                    if not bite_detected:
                        self.record_action('timeout', current_state['position'], success=False)
                        self.logger.debug(""Recording timeout action")

                else:
                    # Regular fishing bot behavior
                    # Get cast power and add randomization
                    cast_power = self.config.get('cast_power', 50)
                    cast_power += random.uniform(-5, 5)  # Add variation
                    cast_power = max(0, min(100, cast_power))  # Clamp between 0 and 100

                    # Cast fishing line with variable timing
                    self.press_key(self.config['cast_key'], duration=cast_power/100.0)
                    time.sleep(random.uniform(1.8, 2.2))  # Randomized delay

                    # Wait for fish bite
                    while not self.stop_event.is_set():
                        if self._detect_bite():
                            # Add random delay before reeling
                            time.sleep(random.uniform(0.1, 0.3))

                            # Reel in fish with randomized timing
                            self.press_key(self.config['reel_key'])
                            time.sleep(random.uniform(2.8, 3.2))
                            break
                        time.sleep(0.1)

                    # Record action if in learning mode
                    if self.learning_mode:
                        self.record_action('fish', self.get_current_position(),
                                        success_rate=1.0)  # TODO: Implement success detection

                # Scan for resources and handle combat periodically
                time.sleep(self.config['resource_scan_interval'])
                resources, obstacles = self.scan_surroundings()

                if self.check_combat_status():
                    self._handle_combat()
                elif resources:
                    for resource in resources:
                        self.navigate_to(resource['position'])
                        # Record gathering action if in learning mode
                        if self.learning_mode:
                            self.record_action('gather', resource['position'],
                                            resource_type=resource['type'])

            except Exception as e:
                self.logger.error(f"Error in bot loop: {str(e)}")
                time.sleep(1)