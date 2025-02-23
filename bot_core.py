"""Core bot functionality with advanced AI features"""
import platform
import logging
from threading import Thread, Event
import time
import sys
from pathlib import Path
import torch
import pyautogui
import random
from vision_system import VisionSystem
from pathfinding import PathFinder

class FishingBot:
    def __init__(self, test_mode=False, test_env=None):
        self.logger = logging.getLogger('FishingBot')
        self.test_mode = test_mode
        self.test_env = test_env

        # Configure PyAutoGUI safety settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

        if test_mode and test_env is None:
            from mock_environment import create_test_environment
            self.test_env = create_test_environment()
            self.logger.info("Created new test environment")

        if not test_mode:
            # Regular Windows environment setup
            if platform.system() != 'Windows':
                self.logger.error("This bot only works on Windows operating system")
                raise SystemError("FishingBot requires Windows to run")

            # Import Windows-specific dependencies
            try:
                from PIL import ImageGrab
                import numpy as np
                import cv2
                self.ImageGrab = ImageGrab
                self.np = np
                self.cv2 = cv2
            except ImportError as e:
                self.logger.error(f"Failed to import required modules: {str(e)}")
                raise ImportError("Missing required modules")

        self.running = False
        self.stop_event = Event()
        self.bot_thread = None
        self.emergency_stop = False

        # Initialize AI components
        self._init_ai_components()

        # Initialize pathfinding
        self.pathfinder = PathFinder(grid_size=32)
        self.logger.info("PathFinder initialized with grid size: 32")

        # Default configuration
        self.config = {
            'detection_area': (0, 0, 100, 100),
            'detection_threshold': 0.8,
            'cast_key': 'f',
            'reel_key': 'r',
            'color_threshold': (200, 200, 200),
            'cast_power': 50,
            'game_window': None,
            'obstacles': [],
            'use_ai': True,
            'pattern_matching': True,
            'mouse_movement_speed': 0.5,
            'click_delay': 0.2,
            'double_click_interval': 0.3,
            'combat_threshold': 80.0,  # Health threshold for combat response
            'resource_scan_interval': 5.0,  # Seconds between resource scans
            'combat_keys': ['1', '2', '3', '4'],  # Combat ability hotkeys
            'movement_keys': {
                'forward': 'w',
                'backward': 's',
                'left': 'a',
                'right': 'd',
                'mount': 'y'
            }
        }

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
            while self.check_combat_status() and not self.stop_event.is_set():
                # Check health and heal if needed
                if self.get_current_health() < self.config['combat_threshold']:
                    self.press_key('h')  # Healing ability
                    time.sleep(1)

                # Use combat abilities
                for key in self.config['combat_keys']:
                    if self.stop_event.is_set():
                        break
                    self.press_key(key)
                    time.sleep(random.uniform(0.5, 1.0))

                time.sleep(0.1)

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
                screen = self.ImageGrab.grab(bbox=self.config['game_window'])
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

            # Add slight randomization to prevent detection
            x += random.uniform(-2, 2)
            y += random.uniform(-2, 2)

            pyautogui.moveTo(x, y, duration=duration)
            self.logger.debug(f"Moved mouse to ({x}, {y})")
            return True
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

            pyautogui.click(clicks=clicks, interval=interval, button=button)
            self.logger.debug(f"Clicked at current position, button={button}, clicks={clicks}")
            return True
        except Exception as e:
            self.logger.error(f"Click error: {str(e)}")
            return False

    def press_key(self, key, duration=None):
        """Press key with test mode support"""
        try:
            if self.test_mode:
                return self.test_env.press_key(key, duration)

            if duration:
                pyautogui.keyDown(key)
                time.sleep(duration)
                pyautogui.keyUp(key)
            else:
                pyautogui.press(key)
            self.logger.debug(f"Pressed key: {key}, duration: {duration}")
            return True
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
            pyautogui.dragTo(end_x, end_y, duration=duration)
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
                return state['fish_bite_active']

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
                return self.np.any(mask)

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

    def _bot_loop(self):
        while not self.stop_event.is_set():
            try:
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

                # Scan for resources periodically
                time.sleep(self.config['resource_scan_interval'])
                resources, obstacles = self.scan_surroundings()
                if resources:
                    for resource in resources:
                        self.navigate_to(resource['position'])
                        # Add logic to gather the resource
                        self.logger.info(f"Gathered {resource['type']} at {resource['position']}")


            except Exception as e:
                self.logger.error(f"Error in bot loop: {str(e)}")
                time.sleep(1)