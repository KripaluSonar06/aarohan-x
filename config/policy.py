"""
Merchant-configurable policy boundaries.
These values are loaded from settings.py but can be overridden via UI (stored in DB later).
For now, we provide a PolicyManager that reads from settings.
"""
from config.settings import settings
from typing import Dict, Any

class PolicyManager:
    """Manages the current policy for the agent.
    In production, this could be loaded from a database per merchant.
    For demo, we use system defaults."""

    def __init__(self):
        self.policy = {
            "max_silent_retries": settings.SYSTEM_MAX_SILENT_RETRIES,
            "max_customer_contacts": settings.SYSTEM_MAX_CUSTOMER_CONTACTS,
            "max_ptp_promises": settings.SYSTEM_MAX_PTP_PROMISES,
            "voice_min_amount_paise": settings.VOICE_MIN_AMOUNT_PAISE,
            "high_value_review_paise": settings.HIGH_VALUE_REVIEW_PAISE,
            "quiet_hours_start": settings.QUIET_HOURS_START,
            "quiet_hours_end": settings.QUIET_HOURS_END,
            "stop_words": settings.STOP_WORDS,
        }

    def get_policy(self) -> Dict[str, Any]:
        return self.policy

    def update_policy(self, updates: Dict[str, Any]) -> None:
        """
        Update policy with merchant-provided values.
        Enforce that merchant cannot increase beyond system max.
        """
        for key, value in updates.items():
            if key in self.policy:
                if key.startswith("max_") or key == "voice_min_amount_paise":
                    # merchant can only lower max or raise min amount
                    if key == "max_silent_retries":
                        self.policy[key] = min(value, settings.SYSTEM_MAX_SILENT_RETRIES)
                    elif key == "max_customer_contacts":
                        self.policy[key] = min(value, settings.SYSTEM_MAX_CUSTOMER_CONTACTS)
                    elif key == "max_ptp_promises":
                        self.policy[key] = min(value, settings.SYSTEM_MAX_PTP_PROMISES)
                    elif key == "voice_min_amount_paise":
                        self.policy[key] = max(value, settings.VOICE_MIN_AMOUNT_PAISE)
                else:
                    # quiet hours, stop words etc can be modified within reason
                    # For simplicity, we accept them but could add validation
                    self.policy[key] = value
            else:
                raise ValueError(f"Unknown policy key: {key}")

# Singleton instance
policy_manager = PolicyManager()