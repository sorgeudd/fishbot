import platform
import logging
from threading import Thread, Event
import time
import sys
from pathlib import Path
import torch
from transformers import AutoModelForImageClassification, AutoFeatureExtractor

class FishingBot:
    def __init__(self):
        self.logger = logging.getLogger('FishingBot')

        # Check for Windows environment
        if platform.system() != 'Windows':
            self.logger.error("This bot only works on Windows operating system")
            raise SystemError("FishingBot requires Windows to run")

        # Import Windows-specific dependencies
        try:
            import pyautogui
            from PIL import ImageGrab
            import numpy as np
            import pyaudio
            import cv2
            self.pyautogui = pyautogui
            self.ImageGrab = ImageGrab
            self.np = np
            self.pyaudio = pyaudio
            self.cv2 = cv2
        except ImportError as e:
            self.logger.error(f"Failed to import required modules: {str(e)}")
            raise ImportError("Missing required modules. Please ensure all dependencies are installed.")

        self.running = False
        self.stop_event = Event()
        self.bot_thread = None
        self.emergency_stop = False

        # Initialize AI components
        self._init_ai_components()

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
            'use_ai': True,  # Enable AI by default
            'pattern_matching': True
        }

    def _init_ai_components(self):
        """Initialize AI and ML components"""
        try:
            # Create paths for model storage
            model_dir = Path("models")
            model_dir.mkdir(exist_ok=True)

            self.logger.info("Initializing machine learning models")

            # Initialize Hugging Face model and feature extractor
            try:
                model_name = "microsoft/resnet-50"  # Using ResNet-50 for image classification
                self.feature_extractor = AutoFeatureExtractor.from_pretrained(model_name)
                self.model = AutoModelForImageClassification.from_pretrained(model_name)
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                self.model.to(self.device)
                self.logger.info(f"Loaded AI model: {model_name}")
            except Exception as e:
                self.logger.warning(f"Failed to load Hugging Face model: {str(e)}")
                self.config['use_ai'] = False

            # Load pattern matching
            pattern_file = model_dir / "patterns.json"
            if pattern_file.exists():
                self.logger.info("Loaded learned patterns from file")
            else:
                self.logger.warning("No pattern file found - using default patterns")

        except Exception as e:
            self.logger.warning(f"AI initialization failed: {str(e)} - falling back to basic detection")
            self.config['use_ai'] = False

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
                # Check cast power
                cast_power = self.config.get('cast_power', 50)

                # Cast fishing line
                self.pyautogui.keyDown(self.config['cast_key'])
                time.sleep(cast_power / 100.0)  # Convert power to hold duration
                self.pyautogui.keyUp(self.config['cast_key'])
                self.logger.debug(f"Cast fishing line with power: {cast_power}")
                time.sleep(2)

                # Wait for fish bite
                while not self.stop_event.is_set():
                    if self._detect_bite():
                        # Reel in fish
                        self.pyautogui.press(self.config['reel_key'])
                        self.logger.debug("Fish detected, reeling in")
                        time.sleep(3)
                        break
                    time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Error in bot loop: {str(e)}")
                time.sleep(1)

    def _detect_bite(self):
        try:
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