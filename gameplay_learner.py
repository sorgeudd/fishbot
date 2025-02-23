"""AI system for learning and replicating player gameplay patterns"""
import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import json
from pathlib import Path

@dataclass
class GameplayAction:
    """Represents a single player action"""
    action_type: str  # 'move', 'gather', 'combat', 'mount', 'cast', 'reel', 'timeout'
    timestamp: float
    position: Tuple[int, int]
    target_position: Optional[Tuple[int, int]] = None
    resource_type: Optional[str] = None
    combat_ability: Optional[str] = None
    success_rate: float = 1.0
    success: bool = True
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert action to dictionary for serialization"""
        return {
            'action_type': self.action_type,
            'timestamp': self.timestamp,
            'position': self.position,
            'target_position': self.target_position,
            'resource_type': self.resource_type,
            'combat_ability': self.combat_ability,
            'success_rate': self.success_rate,
            'success': self.success,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'GameplayAction':
        """Create action from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

class GameplayPattern:
    """Base class for all gameplay patterns"""
    def __init__(self):
        self.count = 0
        self.success_rate = 0.0
        self.total_time = 0.0

    def update(self, success_rate: float, time_taken: float = 0.0):
        self.count += 1
        self.total_time += time_taken
        self.success_rate = (self.success_rate * (self.count - 1) + success_rate) / self.count

class GameplayLearner:
    def __init__(self):
        self.logger = logging.getLogger('GameplayLearner')
        self.recorded_actions: List[GameplayAction] = []
        self.movement_patterns = {}
        self.resource_preferences = {}
        self.combat_patterns = {}
        self.learning_start_time = None
        self.is_learning = False

        # Initialize AI components
        self._init_ai_models()

    def _init_ai_models(self):
        """Initialize machine learning models"""
        self.logger.info("Initializing machine learning models")

        try:
            import torch
            import numpy as np

            # Initialize neural networks for pattern recognition
            self.timing_predictor = torch.nn.Sequential(
                torch.nn.Linear(10, 32),
                torch.nn.ReLU(),
                torch.nn.Linear(32, 1)
            )

            self.success_predictor = torch.nn.Sequential(
                torch.nn.Linear(15, 32),
                torch.nn.ReLU(),
                torch.nn.Linear(32, 1),
                torch.nn.Sigmoid()
            )

            # Load existing patterns if available
            pattern_file = Path("models/learned_patterns.json")
            if pattern_file.exists():
                with open(pattern_file, 'r') as f:
                    patterns = json.load(f)
                    self.movement_patterns = patterns.get('movement', {})
                    self.resource_preferences = patterns.get('resources', {})
                    self.combat_patterns = patterns.get('combat', {})
                    for key, pattern in self.movement_patterns.items():
                        self.movement_patterns[key] = GameplayPattern()
                        self.movement_patterns[key].__dict__.update(pattern)
                    for key, pattern in self.resource_preferences.items():
                        self.resource_preferences[key] = GameplayPattern()
                        self.resource_preferences[key].__dict__.update(pattern)
                    for key, pattern in self.combat_patterns.items():
                        self.combat_patterns[key] = GameplayPattern()
                        self.combat_patterns[key].__dict__.update(pattern)
                self.logger.info("Loaded learned patterns from file")

        except ImportError:
            self.logger.warning("AI models not available - running in basic mode")
            self.timing_predictor = None
            self.success_predictor = None

    def start_learning(self):
        """Start recording player actions"""
        self.learning_start_time = time.time()
        self.is_learning = True
        self.recorded_actions.clear()
        self.logger.info("Started learning mode")

    def stop_learning(self):
        """Stop recording and analyze patterns"""
        if not self.is_learning:
            return

        self.is_learning = False
        if self.learning_start_time:
            duration = time.time() - self.learning_start_time
            self.logger.info(f"Stopped learning mode after {duration:.1f} seconds")

        # Analyze recorded actions
        self._analyze_patterns()

        # Save learned patterns
        self._save_patterns()

    def record_action(self, action_type: str, position: Tuple[int, int], **kwargs):
        """Record a player action during learning mode"""
        if not self.is_learning:
            return

        try:
            action = GameplayAction(
                action_type=action_type,
                timestamp=time.time(),
                position=position,
                **{k: v for k, v in kwargs.items() if k in GameplayAction.__dataclass_fields__}
            )
            self.recorded_actions.append(action)
            self.logger.debug(f"Recorded action: {action_type} at {position}")
        except Exception as e:
            self.logger.error(f"Error recording action: {str(e)}")

    def _analyze_patterns(self):
        """Analyze recorded actions to learn patterns"""
        if not self.recorded_actions:
            return

        # Analyze movement patterns
        moves = [a for a in self.recorded_actions if a.action_type == 'move']
        if moves:
            self._analyze_movement(moves)

        # Analyze resource gathering
        gathers = [a for a in self.recorded_actions if a.action_type == 'gather']
        if gathers:
            self._analyze_gathering(gathers)

        # Analyze combat
        combat = [a for a in self.recorded_actions if a.action_type == 'combat']
        if combat:
            self._analyze_combat(combat)

        # Retrain models with new data
        if self.timing_predictor and self.success_predictor:
            self._train_timing_model()
            self._train_success_model()

    def _analyze_movement(self, moves: List[GameplayAction]):
        """Learn movement patterns"""
        for m1, m2 in zip(moves[:-1], moves[1:]):
            key = (m1.position, m2.position)
            if key not in self.movement_patterns:
                self.movement_patterns[key] = GameplayPattern()

            pattern = self.movement_patterns[key]
            time_taken = m2.timestamp - m1.timestamp
            pattern.update(m2.success_rate, time_taken)

    def _analyze_gathering(self, gathers: List[GameplayAction]):
        """Learn resource gathering patterns"""
        for action in gathers:
            if action.resource_type not in self.resource_preferences:
                self.resource_preferences[action.resource_type] = GameplayPattern()

            pref = self.resource_preferences[action.resource_type]
            pref.update(action.success_rate)

    def _analyze_combat(self, combat: List[GameplayAction]):
        """Learn combat patterns"""
        for action in combat:
            if action.combat_ability not in self.combat_patterns:
                self.combat_patterns[action.combat_ability] = GameplayPattern()

            pattern = self.combat_patterns[action.combat_ability]
            pattern.update(action.success_rate)

    def _train_timing_model(self):
        """Train neural network for action timing prediction"""
        try:
            import torch
            # Prepare training data from patterns
            X = []  # Features
            y = []  # Target timing values

            for pattern in self.movement_patterns.values():
                if pattern.count > 0:
                    avg_time = pattern.total_time / pattern.count
                    features = self._extract_timing_features(pattern)
                    X.append(features)
                    y.append(avg_time)

            if X and y:
                X = torch.tensor(X, dtype=torch.float32)
                y = torch.tensor(y, dtype=torch.float32).reshape(-1, 1)

                # Train model
                optimizer = torch.optim.Adam(self.timing_predictor.parameters())
                criterion = torch.nn.MSELoss()

                for _ in range(100):  # Training epochs
                    optimizer.zero_grad()
                    pred = self.timing_predictor(X)
                    loss = criterion(pred, y)
                    loss.backward()
                    optimizer.step()

                self.logger.info("Trained timing prediction model")

        except Exception as e:
            self.logger.error(f"Error training timing model: {str(e)}")

    def _train_success_model(self):
        """Train neural network for success prediction"""
        try:
            import torch
            # Prepare training data
            X = []  # Features
            y = []  # Success rates

            # Combine patterns from different action types
            all_patterns = {
                **self.movement_patterns,
                **self.resource_preferences,
                **self.combat_patterns
            }

            for pattern in all_patterns.values():
                if hasattr(pattern, 'success_rate'):
                    features = self._extract_success_features(pattern)
                    X.append(features)
                    y.append(pattern.success_rate)

            if X and y:
                X = torch.tensor(X, dtype=torch.float32)
                y = torch.tensor(y, dtype=torch.float32).reshape(-1, 1)

                # Train model
                optimizer = torch.optim.Adam(self.success_predictor.parameters())
                criterion = torch.nn.BCELoss()

                for _ in range(100):  # Training epochs
                    optimizer.zero_grad()
                    pred = self.success_predictor(X)
                    loss = criterion(pred, y)
                    loss.backward()
                    optimizer.step()

                self.logger.info("Trained success prediction model")

        except Exception as e:
            self.logger.error(f"Error training success model: {str(e)}")

    def _extract_timing_features(self, pattern) -> List[float]:
        """Extract features for timing prediction"""
        if isinstance(pattern, GameplayPattern):
            return [
                pattern.count,
                pattern.total_time / max(1, pattern.count),
                pattern.success_rate,
                # Add more relevant features
            ] + [0] * 7  # Pad to 10 features
        return [0] * 10  # Return zeroed features for unsupported pattern types

    def _extract_success_features(self, pattern) -> List[float]:
        """Extract features for success prediction"""
        if isinstance(pattern, GameplayPattern):
            return [
                pattern.count,
                pattern.success_rate,
                # Add more relevant features
            ] + [0] * 13  # Pad to 15 features
        elif isinstance(pattern, dict):
            return [
                pattern.get('count', 0),
                pattern.get('success_rate', 0),
                # Add more relevant features
            ] + [0] * 13  # Pad to 15 features
        return [0] * 15  # Return zeroed features for unsupported pattern types

    def _save_patterns(self):
        """Save learned patterns to file"""
        try:
            patterns = {
                'movement': {k: v.to_dict() for k, v in self.movement_patterns.items()},
                'resources': {k: v.to_dict() for k, v in self.resource_preferences.items()},
                'combat': {k: v.to_dict() for k, v in self.combat_patterns.items()}
            }

            pattern_file = Path("models/learned_patterns.json")
            pattern_file.parent.mkdir(exist_ok=True)

            with open(pattern_file, 'w') as f:
                json.dump(patterns, f, indent=2)

            self.logger.info("Saved learned patterns to file")

        except Exception as e:
            self.logger.error(f"Error saving patterns: {str(e)}")

    def predict_next_action(self, current_state: Dict) -> Optional[Dict]:
        """Predict optimal next action based on learned patterns"""
        try:
            # If AI models aren't available, use basic pattern matching
            if not self.timing_predictor or not self.success_predictor:
                return self._basic_pattern_matching(current_state)

            import torch

            # Extract current state features
            features = self._extract_state_features(current_state)

            # Get timing prediction
            timing_input = torch.tensor(features[:10], dtype=torch.float32)
            predicted_timing = self.timing_predictor(timing_input).item()

            # Get success prediction
            success_input = torch.tensor(features[:15], dtype=torch.float32)
            success_prob = self.success_predictor(success_input).item()

            # Find best matching pattern
            best_action = None
            best_score = -1

            for action_type in ['move', 'gather', 'combat']:
                patterns = self._get_patterns_for_type(action_type)
                for pattern in patterns:
                    score = self._score_pattern(pattern, current_state, success_prob)
                    if score > best_score:
                        best_score = score
                        best_action = {
                            'type': action_type,
                            'pattern': pattern,
                            'timing': predicted_timing,
                            'success_probability': success_prob
                        }

            return best_action

        except Exception as e:
            self.logger.error(f"Error predicting next action: {str(e)}")
            return self._basic_pattern_matching(current_state)

    def _basic_pattern_matching(self, current_state: Dict) -> Dict:
        """Basic pattern matching without AI models"""
        try:
            # Simple rule-based decision making
            if current_state.get('in_combat', False):
                return {
                    'type': 'combat',
                    'pattern': {'success_rate': 0.8},
                    'timing': 1.0,
                    'success_probability': 0.8
                }

            if current_state.get('detected_resources', []):
                return {
                    'type': 'gather',
                    'pattern': {'success_rate': 0.9},
                    'timing': 2.0,
                    'success_probability': 0.9
                }

            return {
                'type': 'move',
                'pattern': {'success_rate': 1.0},
                'timing': 0.5,
                'success_probability': 1.0
            }

        except Exception as e:
            self.logger.error(f"Error in basic pattern matching: {str(e)}")
            return {
                'type': 'move',
                'pattern': {'success_rate': 1.0},
                'timing': 1.0,
                'success_probability': 1.0
            }

    def _extract_state_features(self, state: Dict) -> List[float]:
        """Extract features from current game state"""
        return [
            state.get('health', 100) / 100,
            float(state.get('in_combat', False)),
            float(state.get('is_mounted', False)),
            len(state.get('detected_resources', [])),
            len(state.get('detected_obstacles', [])),
            # Add more state features
        ] + [0] * 10  # Pad to required size

    def _get_patterns_for_type(self, action_type: str) -> List[Dict]:
        """Get relevant patterns for action type"""
        if action_type == 'move':
            return [{'type': 'move', **vars(p)} for p in self.movement_patterns.values()]
        elif action_type == 'gather':
            return [{'type': 'gather', **p} for p in self.resource_preferences.values()]
        elif action_type == 'combat':
            return [{'type': 'combat', **vars(p)} for p in self.combat_patterns.values()]
        return []

    def _score_pattern(self, pattern: Dict, current_state: Dict, success_prob: float) -> float:
        """Score how well a pattern matches current state"""
        base_score = pattern.get('success_rate', 0) * success_prob

        # Add bonuses based on state
        if current_state.get('in_combat', False) and pattern['type'] == 'combat':
            base_score *= 1.5
        elif len(current_state.get('detected_resources', [])) > 0 and pattern['type'] == 'gather':
            base_score *= 1.3

        return base_score