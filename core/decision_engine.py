"""
Decision Engine: computes Expected Net Value for each allowed action,
selects the optimal action, and provides explanations.
"""
from typing import Dict, List, Optional, Any
from config.channel_costs import get_channel_cost
from core.state import EventClass

# Intervention ladder for failed payments (ordered from cheapest to most expensive)
FAILED_PAYMENT_LADDER = [
    "silent_retry",
    "payment_link",       # includes reauth_link and update_instrument_link
    "text_nudge",
    "voice_call",
    "merchant_escalation",
    "stop"
]

# Intervention ladder for checkout abandonment
CHECKOUT_LADDER = [
    "retarget_nudge",     # immediate nudge if return visit
    "text_nudge",         # SMS with payment link
    "discount_link",      # SMS with discount
    "stop"
]

def get_intervention_ladder(event_type: str) -> List[str]:
    """Return appropriate ladder for event type."""
    if event_type == "checkout_abandoned":
        return CHECKOUT_LADDER
    return FAILED_PAYMENT_LADDER

def compute_ev(recovery_probability: float, amount_paise: int, channel_cost: float) -> float:
    """
    Expected Net Value = P(recovery) * Amount - Channel Cost.
    Amount is converted from paise to INR.
    """
    amount_inr = amount_paise / 100.0
    return recovery_probability * amount_inr - channel_cost

def select_optimal_action(
    state: Dict[str, Any],
    allowed_actions: List[str],
    recovery_probability: float,
    channel_costs: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Given the state, list of allowed actions, and recovery probability,
    compute EV for each action and return the optimal one.
    Also returns explanations and counterfactuals.
    """
    if not isinstance(state, dict):
        raise TypeError(f"state must be dict, got {type(state)}")
    amount_paise = state.get("amount_paise", 0)
    if channel_costs is None:
        channel_costs = {}
        for action in allowed_actions:
            channel_costs[action] = get_channel_cost(action, amount_paise)

    # Compute EV for each allowed action
    ev_list = []
    for action in allowed_actions:
        cost = channel_costs.get(action, 0.0)
        ev = compute_ev(recovery_probability, amount_paise, cost)
        ev_list.append({
            "action": action,
            "cost": cost,
            "ev": ev,
            "probability": recovery_probability,
            "net_positive": ev > 0,
        })

    # Sort by EV descending
    ev_list.sort(key=lambda x: x["ev"], reverse=True)

    # Select best action with EV > 0, else "stop"
    selected = "stop"
    selected_ev = 0.0
    selected_cost = 0.0
    for item in ev_list:
        if item["net_positive"]:
            selected = item["action"]
            selected_ev = item["ev"]
            selected_cost = item["cost"]
            break

    return {
        "selected_action": selected,
        "selected_ev": selected_ev,
        "selected_cost": selected_cost,
        "all_ev": ev_list,
        "recovery_probability": recovery_probability,
    }

def generate_decision_explanation(
    decision_result: Dict[str, Any],
    state: Dict[str, Any],
    allowed_actions: List[str]
) -> Dict[str, Any]:
    """
    Produce human-readable explanation: why selected, why not others,
    and counterfactual conditions.
    """
    selected = decision_result["selected_action"]
    amount_inr = state.get("amount_paise", 0) / 100.0
    prob = decision_result["recovery_probability"]
    selected_ev = decision_result["selected_ev"]
    selected_cost = decision_result["selected_cost"]

    explanation = {
        "selected_action": selected,
        "amount_at_risk": amount_inr,
        "recovery_probability": prob,
        "expected_net_value": selected_ev,
        "channel_cost": selected_cost,
        "why": [],
        "why_not": [],
        "counterfactuals": [],
    }

    # Why selected
    explanation["why"].append(
        f"Selected {selected} because it has the highest positive expected net value (EV = ₹{selected_ev:.2f})."
    )
    if selected == "stop":
        explanation["why"].append("No action had positive EV, so stopping is the best financial decision.")
    else:
        explanation["why"].append(
            f"Recovery probability is {prob:.0%}, amount at risk ₹{amount_inr:.2f}, channel cost ₹{selected_cost:.2f}."
        )

    # Why not others
    for item in decision_result["all_ev"]:
        if item["action"] != selected and item["action"] in allowed_actions:
            explanation["why_not"].append(
                f"{item['action']}: EV = ₹{item['ev']:.2f} (cost ₹{item['cost']:.2f}), "
                f"{'not positive' if item['ev'] <= 0 else 'lower than selected'}"
            )

    # Counterfactuals: what would change the decision?
    if selected != "voice_call":
        # If amount crossed voice threshold, voice might become eligible
        voice_threshold = 500.0  # could be fetched from policy
        if amount_inr < voice_threshold and "voice_call" in allowed_actions:
            explanation["counterfactuals"].append(
                f"If amount were ≥ ₹{voice_threshold}, voice call might be considered."
            )
    if prob < 0.12:
        explanation["counterfactuals"].append(
            "If recovery probability were below 12%, we would stop all automated actions."
        )
    if state.get("do_not_contact"):
        explanation["counterfactuals"].append(
            "Customer has DND flag, so no contact actions are permitted."
        )
    if state.get("attempts_contact", 0) >= 2:
        explanation["counterfactuals"].append(
            "Contact attempt limit reached; no further messages or calls allowed."
        )
    if selected == "silent_retry":
        explanation["counterfactuals"].append(
            "If silent retry succeeds, no customer contact will be needed."
        )

    return explanation

def decide_action(
    state: Dict[str, Any],
    allowed_actions: List[str],
    recovery_probability: float,
) -> Dict[str, Any]:
    """
    Main entry point: compute decision, explanation, and return combined result.
    """
    decision_result = select_optimal_action(state, allowed_actions, recovery_probability)
    explanation = generate_decision_explanation(decision_result, state, allowed_actions)
    decision_result["explanation"] = explanation
    return decision_result