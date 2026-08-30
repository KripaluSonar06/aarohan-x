"""
Learning Agent: updates action selection preferences using outcomes.
Uses epsilon-greedy or LinUCB. For demo, we maintain simple counters.
"""
from typing import Dict, Any
import random
from config.logger import logger

class LearningAgent:
    def __init__(self):
        self.action_rewards = {}  # action -> list of (context_key, reward)
        self.epsilon = 0.1

    def get_action_preference(self, context: Dict[str, Any], allowed_actions: list) -> str:
        """Return action with highest estimated reward, with exploration."""
        if random.random() < self.epsilon:
            return random.choice(allowed_actions)
        # Simple greedy: choose action with highest average reward
        best_action = None
        best_avg = -float('inf')
        for action in allowed_actions:
            rewards = [r for c, r in self.action_rewards.get(action, []) if c == self._context_key(context)]
            avg = sum(rewards) / len(rewards) if rewards else 0.0
            if avg > best_avg:
                best_avg = avg
                best_action = action
        return best_action or allowed_actions[0]

    def update(self, context: Dict[str, Any], action: str, reward: float):
        key = self._context_key(context)
        self.action_rewards.setdefault(action, []).append((key, reward))
        logger.info(f"Learning update: action={action}, reward={reward}")

    def _context_key(self, context: Dict[str, Any]) -> str:
        # Create a simple key based on amount bucket and class
        amount = context.get("amount_paise", 0) // 10000  # bucket by ₹100
        event_class = context.get("diagnosed_class", "unknown")
        return f"{event_class}_{amount}"

# Singleton
learning_agent = LearningAgent()