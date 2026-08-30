"""
Ranking Agent: uses RecoveryRanker to compute recovery probability and expected values.
"""
from typing import Dict, Any
from datetime import datetime, timezone
from models.ranker_model import RecoveryRanker
from core.state import EventClass
from config.channel_costs import get_channel_cost
from config.logger import logger

# Singleton ranker (will be loaded or trained elsewhere)
ranker = RecoveryRanker()

def build_features(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract features from state for the ranker."""
    diagnosed = state.get("diagnosed_class")
    return {
        "amount_paise": state.get("amount_paise", 0),
        "day_of_month": datetime.now(timezone.utc).day,
        "cycle_number": state.get("cycle", 0),
        "prior_broken_ptps": 1 if state.get("ptp_broken", False) else 0,
        "customer_tenure_days": 365,  # placeholder; could be from profile
        "last_success_days_ago": 30,  # placeholder
        "is_funds_class": 1 if diagnosed == EventClass.FUNDS else 0,
        "is_downtime_class": 1 if diagnosed == EventClass.DOWNTIME else 0,
        "is_mandate_dead": 1 if diagnosed == EventClass.MANDATE_DEAD else 0,
        "is_instrument_dead": 1 if diagnosed == EventClass.INSTRUMENT_DEAD else 0,
        "is_limit_class": 1 if diagnosed == EventClass.LIMIT else 0,
        "attempts_so_far": state.get("attempts_silent_retry", 0) + state.get("attempts_contact", 0),
        "has_prior_contact": 1 if state.get("attempts_contact", 0) > 0 else 0,
    }

def rank(state: Dict[str, Any]) -> Dict[str, Any]:
    """Compute recovery probability and attach to state."""
    state["node_history"].append("rank")
    features = build_features(state)
    prob = ranker.predict_proba(features)
    state["recovery_probability"] = prob
    state["model_confidence"] = 0.8  # could be based on data coverage; placeholder

    # Compute gross expected value (amount * prob)
    amount_inr = state.get("amount_paise", 0) / 100.0
    state["expected_gross_value"] = prob * amount_inr

    # We'll compute net_expected_value in policy agent after selecting action,
    # but we can precompute here for allowed actions later.
    return state