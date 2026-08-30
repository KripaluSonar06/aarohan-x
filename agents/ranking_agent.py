"""
Ranking Agent: uses RecoveryRanker for failed payments and CheckoutRanker for checkout events.
"""

from typing import Dict, Any
from datetime import datetime, timezone
from models.ranker_model import RecoveryRanker
from models.checkout_ranker import CheckoutRanker
from core.state import EventClass
from config.logger import logger

# Singleton instances
recovery_ranker = RecoveryRanker()
checkout_ranker = CheckoutRanker()

def build_failed_payment_features(state: Dict[str, Any]) -> Dict[str, Any]:
    """Features for the failed payment ranker."""
    diagnosed = state.get("diagnosed_class")
    return {
        "amount_paise": state.get("amount_paise", 0),
        "day_of_month": datetime.now(timezone.utc).day,
        "cycle_number": state.get("cycle", 0),
        "prior_broken_ptps": 1 if state.get("ptp_broken", False) else 0,
        "customer_tenure_days": 365,  # placeholder
        "last_success_days_ago": 30,
        "is_funds_class": 1 if diagnosed == EventClass.FUNDS else 0,
        "is_downtime_class": 1 if diagnosed == EventClass.DOWNTIME else 0,
        "is_mandate_dead": 1 if diagnosed == EventClass.MANDATE_DEAD else 0,
        "is_instrument_dead": 1 if diagnosed == EventClass.INSTRUMENT_DEAD else 0,
        "is_limit_class": 1 if diagnosed == EventClass.LIMIT else 0,
        "attempts_so_far": state.get("attempts_silent_retry", 0) + state.get("attempts_contact", 0),
        "has_prior_contact": 1 if state.get("attempts_contact", 0) > 0 else 0,
    }

def build_checkout_features(state: Dict[str, Any]) -> Dict[str, Any]:
    """Features for checkout abandonment ranker."""
    return {
        "time_since_abandonment_minutes": state.get("time_since_abandonment_minutes", 999),
        "return_visit_signal": state.get("return_visit_signal", False),
        "amount_paise": state.get("amount_paise", 0),
        "discount_eligible": state.get("discount_eligible", False),
    }

def rank(state: Dict[str, Any]) -> Dict[str, Any]:
    """Compute recovery probability and attach to state."""
    state["node_history"].append("rank")
    if state.get("event_type") == "checkout_abandoned":
        features = build_checkout_features(state)
        prob = checkout_ranker.predict_proba(features)
        state["model_confidence"] = 0.7  # heuristic
    else:
        features = build_failed_payment_features(state)
        prob = recovery_ranker.predict_proba(features)
        state["model_confidence"] = 0.8  # placeholder

    state["recovery_probability"] = prob
    amount_inr = state.get("amount_paise", 0) / 100.0
    state["expected_gross_value"] = prob * amount_inr
    return state