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
        self.mock_env.stop_simulation()

    def test_initialization(self):
        """Test bot initialization"""
        self.assertIsNotNone(self.bot)
        self.assertTrue(self.bot.test_mode)
        self.assertFalse(self.bot.running)

    def test_learning_mode(self):
        """Test gameplay learning functionality"""
        # Start learning mode
        self.bot.start_learning_mode()
        self.assertTrue(self.bot.learning_mode)
        self.assertFalse(self.bot.adaptive_mode)

        # Simulate some actions
        self.bot.move_mouse_to(100, 200)
        self.bot.click()
        self.bot.press_key('f')

        # Wait for a few actions to be recorded
        time.sleep(2)

        # Stop learning mode
        self.bot.stop_learning_mode()
        self.assertFalse(self.bot.learning_mode)

        # Verify patterns were learned
        self.assertTrue(hasattr(self.bot.gameplay_learner, 'recorded_actions'))
        self.assertGreater(len(self.bot.gameplay_learner.recorded_actions), 0)

    def test_adaptive_mode(self):
        """Test adaptive gameplay based on learned patterns"""
        # First learn some patterns
        self.bot.start_learning_mode()
        self.bot.move_mouse_to(100, 200)
        self.bot.press_key('f')
        time.sleep(1)
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
        # Simulate combat
        self.mock_env.set_game_state(is_in_combat=True, health=80.0)
        self.assertTrue(self.bot.check_combat_status())

        # Test health monitoring
        self.assertEqual(self.bot.get_current_health(), 80.0)

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

    def test_full_gameplay_cycle(self):
        """Test complete gameplay cycle with learning"""
        # Start learning mode
        self.bot.start_learning_mode()

        # Start bot
        self.bot.start()
        time.sleep(1)  # Allow time for one cycle

        # Verify fishing actions occurred
        input_events = self.mock_env.input_events
        cast_events = [e for e in input_events if e['type'] == 'key_press' and e['key'] == 'f']
        reel_events = [e for e in input_events if e['type'] == 'key_press' and e['key'] == 'r']

        self.assertGreater(len(cast_events), 0, "No casting occurred")
        self.assertGreater(len(reel_events), 0, "No reeling occurred")

        # Stop learning and switch to adaptive mode
        self.bot.stop_learning_mode()
        self.bot.start_adaptive_mode()

        # Let it run in adaptive mode
        time.sleep(1)

        # Verify adaptive actions
        adaptive_events = self.mock_env.input_events[len(input_events):]
        self.assertGreater(len(adaptive_events), 0, "No adaptive actions occurred")

        self.bot.stop()

if __name__ == '__main__':
    unittest.main()