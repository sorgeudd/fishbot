import pyautogui
import time
import logging
from PIL import ImageGrab
import numpy as np
from threading import Thread, Event

class FishingBot:
    def __init__(self):
        self.logger = logging.getLogger('FishingBot')
        self.running = False
        self.stop_event = Event()
        self.bot_thread = None
        
        # Default configuration
        self.config = {
            'detection_area': (0, 0, 100, 100),
            'detection_threshold': 0.8,
            'cast_key': 'f',
            'reel_key': 'r',
            'color_threshold': (200, 200, 200)
        }

    def start(self):
        if not self.running:
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

    def _bot_loop(self):
        while not self.stop_event.is_set():
            try:
                # Cast fishing line
                pyautogui.press(self.config['cast_key'])
                self.logger.debug("Cast fishing line")
                time.sleep(2)

                # Wait for fish bite
                while not self.stop_event.is_set():
                    if self._detect_bite():
                        # Reel in fish
                        pyautogui.press(self.config['reel_key'])
                        self.logger.debug("Fish detected, reeling in")
                        time.sleep(3)
                        break
                    time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Error in bot loop: {str(e)}")
                time.sleep(1)

    def _detect_bite(self):
        try:
            # Capture screen in detection area
            screen = ImageGrab.grab(bbox=self.config['detection_area'])
            screen_np = np.array(screen)
            
            # Simple color threshold detection
            mask = np.all(screen_np >= self.config['color_threshold'], axis=-1)
            return np.any(mask)
            
        except Exception as e:
            self.logger.error(f"Error in bite detection: {str(e)}")
            return False

    def update_config(self, new_config):
        self.config.update(new_config)
        self.logger.info("Configuration updated")
