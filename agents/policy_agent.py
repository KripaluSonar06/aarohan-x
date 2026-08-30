"""
Policy Agent: selects the optimal action using decision engine and contextual bandit.
"""

from typing import Dict, Any, List
from core.decision_engine import decide_action, get_intervention_ladder
from core.state import EventClass
from config.policy import policy_manager
from config.channel_costs import get_channel_cost
from models.bandit_model import ContextualBandit
from config.logger import logger

# Singleton bandit
bandit = ContextualBandit(epsilon=0.1)

def get_allowed_actions(state: Dict[str, Any]) -> List[str]:
    """Same as before (unchanged)."""
    event_type = state.get("event_type")
    diagnosed = state.get("diagnosed_class")

    if event_type == "checkout_abandoned":
        allowed = ["retarget_nudge", "text_nudge", "discount_link"]
        if state.get("return_visit_signal") and state.get("time_since_abandonment_minutes", 999) < 60:
            pass
        else:
            allowed.remove("retarget_nudge")
        if not state.get("discount_eligible", False):
            allowed.remove("discount_link")
        if "voice_call" in allowed:
            allowed.remove("voice_call")
    else:
        allowed = []
        if state.get("attempts_silent_retry", 0) < policy_manager.get_policy()["max_silent_retries"]:
            if diagnosed in [EventClass.FUNDS, EventClass.DOWNTIME, EventClass.LIMIT]:
                allowed.append("silent_retry")
        if diagnosed in [EventClass.MANDATE_DEAD, EventClass.INSTRUMENT_DEAD]:
            allowed.append("payment_link")
        if diagnosed == EventClass.FUNDS and state.get("attempts_contact", 0) < policy_manager.get_policy()["max_customer_contacts"]:
            allowed.append("text_nudge")
        if diagnosed == EventClass.FUNDS and \
           state.get("amount_paise", 0) >= policy_manager.get_policy()["voice_min_amount_paise"] and \
           state.get("attempts_contact", 0) < policy_manager.get_policy()["max_customer_contacts"] and \
           "below_voice_threshold" not in state.get("gates_blocked", []):
            allowed.append("voice_call")
        if state.get("ptp_broken") or diagnosed == EventClass.NEEDS_HUMAN:
            allowed.append("merchant_escalation")
        allowed.append("stop")

    allowed = list(set(allowed))
    if "stop" not in allowed:
        allowed.append("stop")
    if "quiet_hours_active" in state.get("risk_flags", []):
        for action in ["text_nudge", "voice_call", "retarget_nudge"]:
            if action in allowed:
                allowed.remove(action)
                state["gates_blocked"].append(f"quiet_hours_blocked_{action}")
    if "below_voice_threshold" in state.get("gates_blocked", []):
        if "voice_call" in allowed:
            allowed.remove("voice_call")
    return allowed

def select_action(state: Dict[str, Any]) -> Dict[str, Any]:
    state["node_history"].append("policy")
    allowed = get_allowed_actions(state)
    if not allowed:
        state["playbook_action"] = "stop"
        state["status"] = "stopped"
        state["stopped_reason"] = "No allowed actions"
        return state

    prob = state.get("recovery_probability", 0.0)
    if prob is None:
        prob = 0.0

    # Get decision from decision engine
    decision = decide_action(state, allowed, prob)

    # Bandit tie-breaking: if top two actions have EV within 1% of amount, use bandit
    all_ev = decision["all_ev"]
    if len(all_ev) >= 2:
        # all_ev is sorted by EV descending
        top1 = all_ev[0]
        top2 = all_ev[1]
        amount_inr = state.get("amount_paise", 0) / 100.0
        margin = amount_inr * 0.01  # 1% of amount
        if (top1["ev"] - top2["ev"]) < margin:
            # Use bandit to select between top1 and top2
            context = {
                "diagnosed_class": state.get("diagnosed_class").value if state.get("diagnosed_class") else "unknown",
                "amount_paise": state.get("amount_paise", 0),
            }
            bandit_choice = bandit.select_action(context, [top1["action"], top2["action"]])
            # Override selected action if bandit choice differs
            if bandit_choice != decision["selected_action"]:
                for item in all_ev:
                    if item["action"] == bandit_choice:
                        decision["selected_action"] = bandit_choice
                        decision["selected_ev"] = item["ev"]
                        decision["selected_cost"] = item["cost"]
                        break

    state["playbook_action"] = decision["selected_action"]
    state["channel_cost"] = decision["selected_cost"]
    state["net_expected_value"] = decision["selected_ev"]
    state["decision_explanation"] = decision["explanation"]

    # Log
    state["ledger"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
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