"""Mock environment for headless testing of fishing bot functionality"""
import logging
from dataclasses import dataclass
from threading import Thread, Event
import time
import random

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

class MockEnvironment:
    def __init__(self):
        self.logger = logging.getLogger('MockEnvironment')
        self.state = GameState()
        self.input_events = []
        self.fish_bite_event = Event()
        self.running = False

    def start_simulation(self):
        """Start background simulation"""
        self.running = True
        self.simulation_thread = Thread(target=self._run_simulation)
        self.simulation_thread.start()
        self.logger.info("Mock environment simulation started")

    def stop_simulation(self):
        """Stop background simulation"""
        self.running = False
        if hasattr(self, 'simulation_thread'):
            self.simulation_thread.join()
        self.logger.info("Mock environment simulation stopped")

    def _run_simulation(self):
        """Simulate game events"""
        while self.running:
            # Simulate random fish bites
            if random.random() < 0.2:  # 20% chance per cycle
                self.state.fish_bite_active = True
                self.fish_bite_event.set()
                time.sleep(0.5)
                self.state.fish_bite_active = False
                self.fish_bite_event.clear()

            # Simulate random combat events
            if random.random() < 0.1:  # 10% chance per cycle
                self.state.is_in_combat = True
                self.state.health -= random.uniform(5, 15)

            time.sleep(1)

    def record_input(self, input_type, **kwargs):
        """Record input events for verification"""
        event = {'type': input_type, 'timestamp': time.time(), **kwargs}
        self.input_events.append(event)
        self.logger.debug(f"Recorded input event: {event}")
        return True

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
            'fish_bite_active': self.state.fish_bite_active
        }

    def set_game_state(self, **kwargs):
        """Update game state for testing"""
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        self.logger.info(f"Updated game state: {kwargs}")

def create_test_environment():
    """Create and return a mock environment instance"""
    env = MockEnvironment()
    return env