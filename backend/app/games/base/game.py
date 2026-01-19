from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseGame(ABC):
    """Abstract base class for all games"""

    def __init__(self, game_config):
        self.config = game_config

    @abstractmethod
    def initialize_session(
        self, user_id: str, options: Optional[dict] = None
    ) -> dict[str, Any]:
        """
        Initialize a new game session

        Args:
            user_id: ID of the user starting the game
            options: Optional game-specific settings (difficulty, mode, etc.)

        Returns:
            Initial game state dict
        """
        pass

    @abstractmethod
    def process_action(self, game_state: dict, action: dict) -> tuple[dict, dict]:
        """
        Process a player action and return updated state and response

        Args:
            game_state: Current game state
            action: Player action (format varies by game type)
                Examples:
                - Turn-based: {'type': 'move', 'row': 1, 'col': 2}
                - Quiz: {'type': 'answer', 'answer': 'Paris'}
                - Puzzle: {'type': 'swap', 'from': 1, 'to': 5}

        Returns:
            Tuple of (new_game_state, action_result)
            action_result format: {
                'valid': bool,
                'message': str,
                'points_earned': int,
                'feedback': dict # Game-specific feedback
            }
        """
        pass

    @abstractmethod
    def check_completion(self, game_state: dict) -> tuple[bool, Optional[dict]]:
        """
        Check if the game/session is complete

        Returns:
            Tuple of (is_complete, completion_data)
            completion_data format when complete: {
                'final_score': int,
                'performance': dict,  # Game-specific performance metrics
                'stats': dict  # Stats to save
            }
        """
        pass

    def validate_action(self, game_state: dict, action: dict) -> tuple[bool, str]:
        """
        Validate if an action is legal (optional override)

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Default: all actions are valid, games can override
        return True, ""

    def get_next_challenge(self, game_state: dict) -> Optional[dict]:
        """
        Get the next challenge/question/level (for quiz, challenge games)

        Returns:
            Challenge data or None if no more challenges
        """
        # Default implementation for games that don't use challenges
        return None

    def calculate_final_score(self, game_state: dict) -> int:
        """
        Calculate the final score from game state

        Args:
            game_state: Final game state

        Returns:
            Final score as integer
        """
        # Default: return score from state
        score = game_state.get("score", 0) or 0
        return score

    def get_performance_metrics(self, game_state: dict) -> dict[str, Any]:
        """
        Extract performance metrics for display/analysis

        Returns:
            Dict of metrics like accuracy, speed, etc.
        """
        return {}

    def get_stats_to_track(self, game_static: dict) -> dict[str, Any]:
        """
        Extract stats to save to user_game_stats.custom_stats

        Returns:
            Dict of stats to aggregate over time
        """
        return {}
