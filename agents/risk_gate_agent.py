"""
Risk Gate Agent: enforces all hard gates before any intervention.
"""
from typing import Dict, Any
from datetime import datetime
from config.policy import policy_manager
from core.state import EventClass
from utils.time_utils import is_quiet_hours

def apply_hard_stops(state: Dict[str, Any]) -> bool:
    """Return True if must stop immediately."""
    event_class = state.get("diagnosed_class")
    if event_class in [EventClass.RISK, EventClass.CUSTOMER_CANCEL]:
        state["gates_blocked"].append("hard_stop_class")
        state["status"] = "stopped"
        state["stopped_reason"] = f"Class {event_class.value} is non-recoverable"
        return True
    return False

def check_dnd(state: Dict[str, Any]) -> bool:
    if state.get("do_not_contact", False):
        state["gates_blocked"].append("dnd")
        state["status"] = "stopped"
        state["stopped_reason"] = "Customer has DND flag"
        return True
    return False

def check_broken_ptp(state: Dict[str, Any]) -> bool:
    if state.get("ptp_broken", False):
        state["gates_blocked"].append("broken_ptp")
        state["status"] = "stopped"
        state["stopped_reason"] = "Previous PTP broken; no further contact allowed"
        return True
    return False

def check_attempt_limits(state: Dict[str, Any]) -> bool:
    policy = policy_manager.get_policy()
    if state.get("attempts_silent_retry", 0) >= policy["max_silent_retries"] and \
       state.get("attempts_contact", 0) >= policy["max_customer_contacts"]:
        state["gates_blocked"].append("max_attempts_reached")
        state["status"] = "stopped"
        state["stopped_reason"] = "Maximum retry and contact attempts exhausted"
        return True
    return False

def check_quiet_hours(state: Dict[str, Any]) -> None:
    """Quiet hours only block customer contact actions, not silent retries."""
    if is_quiet_hours():
        # If the intended next action is customer contact, we block it.
        # Since the policy agent hasn't run yet, we set a flag to be checked later.
        state["risk_flags"].append("quiet_hours_active")

def check_voice_specific(state: Dict[str, Any]) -> None:
    """Additional gates for voice calls."""
    policy = policy_manager.get_policy()
    if state.get("event_type") == "checkout_abandoned":
        state["gates_blocked"].append("no_voice_for_checkout")
    if state.get("amount_paise", 0) < policy["voice_min_amount_paise"]:
        state["gates_blocked"].append("below_voice_threshold")

def check_stop_words(state: Dict[str, Any]) -> bool:
    """If customer has used stop words, set DND."""
    # In a real system, we'd parse customer responses for stop words.
    # For now, we check if any stop word is present in recent communications.
    # This is a placeholder: we assume the customer's DND flag already captured it.
    return False

def apply_risk_gates(state: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for risk gate agent."""
    if not isinstance(state, dict):
        logger.error(f"diagnose_failed_payment received non-dict state: {type(state)}")
        return {"status": "needs_human", "errors": ["invalid state"]}
    state["node_history"].append("risk_gate")

    if apply_hard_stops(state):
        state["ledger"].append({
            "timestamp": datetime.now().isoformat(),
            "action": "stopped_by_gate",
            "detail": {"reason": state["stopped_reason"]},
            "idempotency_key": None,
            "cost": 0.0,
        })
        return state

    if check_dnd(state) or check_broken_ptp(state) or check_attempt_limits(state):
        state["ledger"].append({
            "timestamp": datetime.now().isoformat(),
            "action": "stopped_by_gate",
            "detail": {"reason": state["stopped_reason"]},
            "idempotency_key": None,
            "cost": 0.0,
        })
        return state

    # Non-blocking flags
    check_quiet_hours(state)
    check_voice_specific(state)

    # If gates_blocked is not empty but we haven't stopped, we will pass them to policy agent
    # to decide if an alternative action is possible.
    return state