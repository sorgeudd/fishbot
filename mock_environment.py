"""Mock environment for headless testing of fishing bot functionality"""
import logging
from dataclasses import dataclass
from threading import Thread, Event
import time
import random
import numpy as np

@dataclass
class GameState:
    """Represents the current state of the game"""
    health: float = 100.0
    is_mounted: bool = False
    is_in_combat: bool = False
    current_position: tuple = (0, 0)
    detected_resources: list = None
    detected_obstacles: list = None
    fish_bite_active: bool = False
    window_active: bool = True
    screen_content: np.ndarray = None
    combat_start_time: float = None
    last_action_time: float = None  # Track timing of last action

    def __post_init__(self):
        if self.screen_content is None:
            # Create a mock screen content (black screen)
            self.screen_content = np.zeros((600, 800, 3), dtype=np.uint8)
        self.last_action_time = time.time()

class MockEnvironment:
    def __init__(self):
        self.logger = logging.getLogger('MockEnvironment')
        self.state = GameState()
        self.input_events = []
        self.fish_bite_event = Event()
        self.running = False
        self.min_action_interval = 0.5  # Minimum time between actions

        # Initialize mock screen
        self.window_size = (800, 600)
        self.state.screen_content = np.zeros((*self.window_size, 3), dtype=np.uint8)

    def start_simulation(self):
        """Start background simulation"""
        self.running = True
        self.simulation_thread = Thread(target=self._run_simulation)
        self.simulation_thread.daemon = True  # Allow clean shutdown
        self.simulation_thread.start()
        self.logger.info("Mock environment simulation started")

    def stop_simulation(self):
        """Stop background simulation"""
        self.running = False
        if hasattr(self, 'simulation_thread'):
            self.simulation_thread.join(timeout=1.0)  # Wait with timeout
        self.logger.info("Mock environment simulation stopped")

    def _run_simulation(self):
        """Simulate game events"""
        bite_cooldown = 0
        while self.running:
            current_time = time.time()

            # Only generate events if enough time has passed since last action
            if current_time - self.state.last_action_time >= self.min_action_interval:
                # Simulate random fish bites with cooldown
                if bite_cooldown <= 0 and random.random() < 0.3:  # 30% chance per cycle
                    self.state.fish_bite_active = True
                    self.fish_bite_event.set()
                    time.sleep(0.5)
                    self.state.fish_bite_active = False
                    self.fish_bite_event.clear()
                    bite_cooldown = 2.0  # 2 second cooldown
                else:
                    bite_cooldown = max(0, bite_cooldown - 0.1)

                # Handle combat timeout
                if self.state.is_in_combat and self.state.combat_start_time:
                    if current_time - self.state.combat_start_time > 5.0:
                        self.state.is_in_combat = False
                        self.state.combat_start_time = None
                        self.logger.debug("Combat timeout reached, ending combat")

                # Simulate random combat events
                if random.random() < 0.1 and not self.state.is_in_combat:
                    self.state.is_in_combat = True
                    self.state.combat_start_time = current_time
                    self.state.health -= random.uniform(5, 15)
                    self.logger.debug("Started combat simulation")

                # Update mock screen with random content
                self._update_mock_screen()
                self.state.last_action_time = current_time

            time.sleep(0.1)  # Reduce CPU usage

    def _update_mock_screen(self):
        """Update mock screen content"""
        # Create some random visual elements
        screen = np.zeros((*self.window_size, 3), dtype=np.uint8)

        # Add random elements (e.g., resources, obstacles)
        if random.random() < 0.3:  # 30% chance to add elements
            x = random.randint(0, self.window_size[0]-50)
            y = random.randint(0, self.window_size[1]-50)
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            screen[y:y+50, x:x+50] = color

        self.state.screen_content = screen

    def record_input(self, input_type, **kwargs):
        """Record input events for verification"""
        current_time = time.time()
        if current_time - self.state.last_action_time >= self.min_action_interval:
            event = {'type': input_type, 'timestamp': current_time, **kwargs}
            self.input_events.append(event)
            self.logger.debug(f"Recorded input event: {event}")
            self.state.last_action_time = current_time
            return True
        return False

    def move_mouse(self, x, y):
        """Record mouse movement"""
        return self.record_input('mouse_move', x=x, y=y)

    def click(self, button='left', clicks=1):
        """Record mouse click"""
        return self.record_input('mouse_click', button=button, clicks=clicks)

    def press_key(self, key, duration=None):
        """Record key press"""
        return self.record_input('key_press', key=key, duration=duration)

    def get_screen_region(self):
        """Get current game state data"""
        return {
            'health': self.state.health,
            'current_position': self.state.current_position,
            'in_combat': self.state.is_in_combat,
            'resources': self.state.detected_resources or [],
            'obstacles': self.state.detected_obstacles or [],
            'fish_bite_active': self.state.fish_bite_active,
            'screen_content': self.state.screen_content
        }

    def set_game_state(self, **kwargs):
        """Update game state for testing"""
        current_time = time.time()
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
                if key == 'is_in_combat' and value:
                    self.state.combat_start_time = current_time
                elif key == 'fish_bite_active' and value:
                    self.fish_bite_event.set()
                else:
                    self.fish_bite_event.clear()
        self.logger.info(f"Updated game state: {kwargs}")
        self.state.last_action_time = current_time

def create_test_environment():
    """Create and return a mock environment instance"""
    env = MockEnvironment()
    return env