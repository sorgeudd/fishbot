"""Test module for fishing bot functionality"""
import unittest
from mock_environment import create_test_environment
from bot_core import FishingBot
import logging
import time

class TestFishingBot(unittest.TestCase):
    def setUp(self):
        """Setup test environment"""
        logging.basicConfig(level=logging.DEBUG)
        self.mock_env = create_test_environment()
        self.mock_env.start_simulation()
        self.bot = FishingBot(test_mode=True, test_env=self.mock_env)

    def tearDown(self):
        """Cleanup test environment"""
        if hasattr(self, 'bot'):
            if self.bot.running:
                self.bot.stop()
            if self.bot.learning_mode:
                self.bot.stop_learning_mode()
        self.mock_env.stop_simulation()

    def test_learning_mode(self):
        """Test gameplay learning functionality"""
        # Start learning mode
        self.bot.start_learning_mode()
        self.assertTrue(self.bot.learning_mode)
        self.assertFalse(self.bot.adaptive_mode)

        # Simulate actions
        self.bot.record_action('move', (100, 200))
        self.bot.record_action('cast', (100, 200))
        self.bot.click()
        self.bot.press_key('f')

        # Wait for actions to be recorded
        time.sleep(0.5)

        # Stop learning mode
        self.bot.stop_learning_mode()
        self.assertFalse(self.bot.learning_mode)

        # Verify patterns were learned
        recorded_actions = self.bot.gameplay_learner.recorded_actions
        self.assertGreater(len(recorded_actions), 0)

        # Verify specific actions were recorded
        action_types = [a.action_type for a in recorded_actions]
        self.assertIn('move', action_types)
        self.assertIn('cast', action_types)

    def test_full_gameplay_cycle(self):
        """Test complete gameplay cycle with learning"""
        # Start learning mode
        self.bot.start_learning_mode()

        # Start bot
        self.bot.start()
        time.sleep(1)  # Allow initialization

        # Record initial events count
        initial_events = len(self.mock_env.input_events)

        # Simulate fish bite to trigger reeling
        self.mock_env.set_game_state(fish_bite_active=True)
        time.sleep(0.5)  # Wait for bite detection

        # Verify bite detection triggered reel action
        events_after_bite = [e for e in self.mock_env.input_events[initial_events:] 
                            if e['type'] == 'key_press' and e['key'] == 'r']
        self.assertGreater(len(events_after_bite), 0, "No reeling occurred after bite")

        # Clear bite state
        self.mock_env.set_game_state(fish_bite_active=False)
        time.sleep(0.5)

        # Stop learning and verify actions were recorded
        self.bot.stop()
        self.bot.stop_learning_mode()
        recorded_actions = self.bot.gameplay_learner.recorded_actions
        self.assertGreater(len(recorded_actions), 0, "No actions recorded in learning mode")

        # Switch to adaptive mode
        self.bot.start_adaptive_mode()
        self.assertTrue(self.bot.adaptive_mode)
        self.assertFalse(self.bot.learning_mode)

        # Let it run in adaptive mode
        self.bot.start()
        events_before_adaptive = len(self.mock_env.input_events)

        # Simulate conditions that should trigger adaptive actions
        self.mock_env.set_game_state(fish_bite_active=True)
        time.sleep(1.0)  # Wait for adaptive response
        self.mock_env.set_game_state(fish_bite_active=False)
        time.sleep(1.0)  # Allow completion of action

        # Verify adaptive actions occurred
        adaptive_events = self.mock_env.input_events[events_before_adaptive:]
        self.assertGreater(len(adaptive_events), 0, "No adaptive actions occurred")

        # Cleanup
        self.bot.stop()

    def test_fish_detection(self):
        """Test fish bite detection"""
        # Simulate fish bite
        self.mock_env.set_game_state(fish_bite_active=True)
        self.assertTrue(self.bot._detect_bite())

        # Clear fish bite
        self.mock_env.set_game_state(fish_bite_active=False)
        self.assertFalse(self.bot._detect_bite())

    def test_combat_response(self):
        """Test combat detection and response"""
        # Simulate combat with health at 80%
        self.mock_env.set_game_state(is_in_combat=True, health=80.0)
        self.assertTrue(self.bot.check_combat_status())
        self.assertEqual(self.bot.get_current_health(), 80.0)

        # Test combat handling with shorter duration for tests
        start_time = time.time()
        self.bot._handle_combat()
        duration = time.time() - start_time

        # Verify combat didn't take too long
        self.assertLess(duration, 6.0, "Combat handling took too long")

        # Verify combat actions were taken
        combat_events = [e for e in self.mock_env.input_events if e['type'] == 'key_press']
        self.assertGreater(len(combat_events), 0, "No combat abilities used")

    def test_obstacle_detection(self):
        """Test obstacle detection and avoidance"""
        obstacles = [(10, 10), (20, 20)]
        self.mock_env.set_game_state(detected_obstacles=obstacles)
        detected = self.bot.scan_for_obstacles()
        self.assertEqual(len(detected), 2)
        self.assertIn((10, 10), detected)

    def test_resource_detection(self):
        """Test resource detection"""
        resources = [{'type': 'herb', 'position': (50, 50)}]
        self.mock_env.set_game_state(detected_resources=resources)
        detected = self.bot.scan_for_resources()
        self.assertEqual(len(detected), 1)
        self.assertEqual(detected[0]['type'], 'herb')

    def test_input_control(self):
        """Test basic input controls"""
        # Test mouse movement
        result = self.bot.move_mouse_to(100, 200)
        self.assertTrue(result)
        last_event = self.mock_env.input_events[-1]
        self.assertEqual(last_event['type'], 'mouse_move')
        self.assertEqual(last_event['x'], 100)

        # Test key press
        result = self.bot.press_key('f')
        self.assertTrue(result)
        last_event = self.mock_env.input_events[-1]
        self.assertEqual(last_event['type'], 'key_press')
        self.assertEqual(last_event['key'], 'f')

    def test_window_management(self):
        """Test window detection and management"""
        # Test window finding
        success = self.bot.find_game_window("Test Game")
        self.assertTrue(success)
        self.assertIsNotNone(self.bot.window_handle)
        self.assertIsNotNone(self.bot.window_rect)

        # Test setting window region
        region = (0, 0, 800, 600)
        success = self.bot.set_window_region(region)
        self.assertTrue(success)
        self.assertEqual(self.bot.config['detection_area'], region)

        # Test window activation
        self.assertTrue(self.bot.is_window_active())
        self.assertTrue(self.bot.activate_window())

        # Test screenshot capture
        screenshot = self.bot.get_window_screenshot()
        self.assertIsNotNone(screenshot)

    def test_initialization(self):
        """Test bot initialization"""
        self.assertIsNotNone(self.bot)
        self.assertTrue(self.bot.test_mode)
        self.assertFalse(self.bot.running)

    def test_adaptive_mode(self):
        """Test adaptive gameplay based on learned patterns"""
        # First learn some patterns
        self.bot.start_learning_mode()
        self.bot.move_mouse_to(100, 200)
        self.bot.press_key('f')
        time.sleep(0.5)
        self.bot.stop_learning_mode()

        # Start adaptive mode
        self.bot.start_adaptive_mode()
        self.assertTrue(self.bot.adaptive_mode)
        self.assertFalse(self.bot.learning_mode)

        # Get next action recommendation
        next_action = self.bot.get_next_action()
        if next_action:
            self.assertIn('type', next_action)
            self.assertIn('timing', next_action)


if __name__ == '__main__':
    unittest.main()