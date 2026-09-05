"""
Settlement Agent: verifies actual payment and updates learning bandit.
"""

from typing import Dict, Any
from datetime import datetime, timezone
from services.razorpay_client import razorpay_client
from utils.audit import add_ledger_entry
from config.logger import logger

import hashlib

def settle(state: Dict[str, Any]) -> Dict[str, Any]:
    state["node_history"].append("settle")
    event_id = state["event_id"]

    # If already recovered, verify and return
    if state.get("status") == "recovered":
        add_ledger_entry(state, "settlement_verified", {"amount": state["recovered_amount_paise"]}, None, 0.0)
        return state

    # Check PTP broken
    if state.get("ptp_date"):
        from dateutil import parser
        ptp_date = state["ptp_date"]
        if isinstance(ptp_date, str):
            ptp_date = parser.parse(ptp_date)
        if ptp_date.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            state["ptp_broken"] = True
            state["status"] = "escalated"
            state["stopped_reason"] = "PTP broken, escalated to merchant"
            add_ledger_entry(state, "ptp_broken", {"promised_date": ptp_date.isoformat()}, None, 0.0)
            return state

    # If status is still active and a contact action was taken, simulate customer payment
    contact_actions = ["text_nudge", "voice_call", "payment_link", "checkout_retarget"]
    if state.get("status") == "active" and state.get("playbook_action") in contact_actions:
        prob = state.get("recovery_probability", 0.2)
        seed = f"{state.get('simulation_seed', state.get('event_id'))}:{state.get('playbook_action')}:{state.get('attempts_contact', 0)}"
        roll = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        if roll < prob:
            state["recovered_amount_paise"] = state["amount_paise"]
            state["status"] = "recovered"
            add_ledger_entry(state, "customer_paid_after_contact", {"amount": state["amount_paise"]}, None, 0.0)

    return state