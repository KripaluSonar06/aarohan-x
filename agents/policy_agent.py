"""
Policy Agent: selects the optimal action using the decision engine,
respecting the intervention ladder and allowed actions.
"""
from typing import Dict, Any, List
from core.decision_engine import decide_action, get_intervention_ladder
from core.state import EventClass
from config.policy import policy_manager
from config.channel_costs import get_channel_cost
from config.logger import logger

def get_allowed_actions(state: Dict[str, Any]) -> List[str]:
    """
    Determine which actions are allowed based on event type, diagnosis, and gates.
    """
    event_type = state.get("event_type")
    diagnosed = state.get("diagnosed_class")

    if event_type == "checkout_abandoned":
        # For checkout: retarget nudge, text nudge, discount link, stop
        allowed = ["retarget_nudge", "text_nudge", "discount_link"]
        if state.get("return_visit_signal") and state.get("time_since_abandonment_minutes", 999) < 60:
            pass  # retarget_nudge is allowed
        else:
            allowed.remove("retarget_nudge")
        # Discount only if eligible
        if not state.get("discount_eligible", False):
            allowed.remove("discount_link")
        # No voice
        if "voice_call" in allowed:
            allowed.remove("voice_call")
    else:
        # Failed payments
        allowed = []
        # Silent retry is allowed if attempts < max and class allows
        if state.get("attempts_silent_retry", 0) < policy_manager.get_policy()["max_silent_retries"]:
            if diagnosed in [EventClass.FUNDS, EventClass.DOWNTIME, EventClass.LIMIT]:
                allowed.append("silent_retry")
        # Payment link for mandate/instrument dead
        if diagnosed in [EventClass.MANDATE_DEAD, EventClass.INSTRUMENT_DEAD]:
            allowed.append("payment_link")
        # Text nudge for funds after retries exhausted, or for limit? Usually after retries.
        if diagnosed == EventClass.FUNDS and state.get("attempts_contact", 0) < policy_manager.get_policy()["max_customer_contacts"]:
            allowed.append("text_nudge")
        # Voice call only if not checkout and amount >= threshold and attempts contact < max
        if diagnosed == EventClass.FUNDS and \
           state.get("amount_paise", 0) >= policy_manager.get_policy()["voice_min_amount_paise"] and \
           state.get("attempts_contact", 0) < policy_manager.get_policy()["max_customer_contacts"] and \
           "below_voice_threshold" not in state.get("gates_blocked", []):
            allowed.append("voice_call")
        # Merchant escalation only if PTP broken or needs human
        if state.get("ptp_broken") or diagnosed == EventClass.NEEDS_HUMAN:
            allowed.append("merchant_escalation")
        # Always allow stop as fallback
        allowed.append("stop")

    # Remove duplicates and ensure stop present
    allowed = list(set(allowed))
    if "stop" not in allowed:
        allowed.append("stop")
    # Remove any action that is blocked by gates (like quiet hours for contact actions)
    if "quiet_hours_active" in state.get("risk_flags", []):
        # Remove contact actions
        for action in ["text_nudge", "voice_call", "retarget_nudge"]:
            if action in allowed:
                allowed.remove(action)
                state["gates_blocked"].append(f"quiet_hours_blocked_{action}")
    # Remove voice if blocked
    if "below_voice_threshold" in state.get("gates_blocked", []):
        if "voice_call" in allowed:
            allowed.remove("voice_call")
    return allowed

def select_action(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Policy Agent main: choose action using decision engine.
    """
    state["node_history"].append("policy")
    allowed = get_allowed_actions(state)
    if not allowed:
        # Nothing allowed, must stop
        state["playbook_action"] = "stop"
        state["status"] = "stopped"
        state["stopped_reason"] = "No allowed actions"
        return state

    prob = state.get("recovery_probability", 0.0)
    if prob is None:
        prob = 0.0

    # Use decision engine to select
    decision = decide_action(state, allowed, prob)
    state["playbook_action"] = decision["selected_action"]
    state["channel_cost"] = decision["selected_cost"]
    state["net_expected_value"] = decision["selected_ev"]

    # Save decision details for audit and UI
    state["decision_explanation"] = decision["explanation"]
    state["ledger"].append({
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "action": "policy_decision",
        "detail": {
            "selected": state["playbook_action"],
            "ev": state["net_expected_value"],
            "cost": state["channel_cost"],
        },
        "idempotency_key": None,
        "cost": 0.0,
    })
    return state