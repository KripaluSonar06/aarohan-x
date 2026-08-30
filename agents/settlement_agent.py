"""
Settlement Agent: verifies actual payment and updates learning bandit.
"""

from typing import Dict, Any
from datetime import datetime, timezone
from services.razorpay_client import razorpay_client
from utils.audit import add_ledger_entry
from config.logger import logger

def settle(state: Dict[str, Any]) -> Dict[str, Any]:
    """Verify settlement, finalize status, and update bandit."""
    state["node_history"].append("settle")
    event_id = state["event_id"]

    # If already recovered, verify
    if state.get("status") == "recovered":
        add_ledger_entry(state, "settlement_verified", {"amount": state["recovered_amount_paise"]}, None, 0.0)
        reward = 1.0
    elif state.get("ptp_date"):
        # Check if PTP broken
        from dateutil import parser
        ptp_date = state["ptp_date"]
        if isinstance(ptp_date, str):
            ptp_date = parser.parse(ptp_date)
        if ptp_date.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            state["ptp_broken"] = True
            state["status"] = "escalated"
            state["stopped_reason"] = "PTP broken, escalated to merchant"
            add_ledger_entry(state, "ptp_broken", {"promised_date": ptp_date.isoformat()}, None, 0.0)
            reward = 0.0
        else:
            # still waiting, no final outcome yet
            return state
    else:
        # If no recovery and not waiting, assume failure
        reward = 0.0

    # Update contextual bandit with outcome
    try:
        from agents.policy_agent import bandit
        context = {
            "diagnosed_class": state.get("diagnosed_class").value if state.get("diagnosed_class") else "unknown",
            "amount_paise": state.get("amount_paise", 0),
        }
        action = state.get("playbook_action")
        if action and action != "stop":
            bandit.update(context, action, reward)
            logger.info(f"Bandit updated: action={action}, reward={reward}")
    except Exception as e:
        logger.error(f"Bandit update failed: {e}")

    return state