"""
Contextual bandit for action preference learning.
Simple epsilon-greedy implementation.
"""

import random
from typing import Dict, Any, List

class ContextualBandit:
    def __init__(self, epsilon=0.1):
        self.epsilon = epsilon
        self.action_rewards = {}  # action -> list of (context_key, reward)

    def select_action(self, context: Dict[str, Any], allowed_actions: List[str]) -> str:
        """Choose action with exploration."""
        if random.random() < self.epsilon or not allowed_actions:
            return random.choice(allowed_actions) if allowed_actions else "stop"
        # Greedy selection
        best_action = allowed_actions[0]
        best_avg = -float('inf')
        for action in allowed_actions:
            rewards = [r for c, r in self.action_rewards.get(action, []) if c == self._context_key(context)]
            avg = sum(rewards) / len(rewards) if rewards else 0.0
            if avg > best_avg:
                best_avg = avg
                best_action = action
        return best_action

    def update(self, context: Dict[str, Any], action: str, reward: float):
        key = self._context_key(context)
        self.action_rewards.setdefault(action, []).append((key, reward))

    def _context_key(self, context: Dict[str, Any]) -> str:
        # Simple bucket: class + amount bucket
        cls = context.get("diagnosed_class", "unknown")
        amount = context.get("amount_paise", 0) // 10000  # bucket by ₹100
        return f"{cls}_{amount}"