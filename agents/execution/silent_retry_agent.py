"""
Silent Retry Agent: attempts a silent retry of the failed payment.
Uses Razorpay test client or simulation. Never contacts customer.
"""
from typing import Dict, Any
from datetime import datetime, timezone
from services.razorpay_client import razorpay_client
from utils.idempotency import generate_idempotency_key
from utils.audit import add_ledger_entry
from config.logger import logger

def silent_retry(state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a silent retry for a failed payment."""
    state["node_history"].append("silent_retry")
    event_id = state["event_id"]
    attempt = state.get("attempts_silent_retry", 0)
    idem_key = generate_idempotency_key(event_id, "silent_retry", attempt, mandate_id=state.get("mandate_id"))

    # Check idempotency: if this key already exists in ledger, skip
    for entry in state.get("ledger", []):
        if entry.get("idempotency_key") == idem_key:
            # Duplicate attempt; block
            state["gates_blocked"].append("duplicate_silent_retry")
            add_ledger_entry(state, "silent_retry_blocked", {"reason": "duplicate idempotency key"}, idem_key, 0.0)
            return state

    # Increment attempt counter
    state["attempts_silent_retry"] = attempt + 1

    # Decide whether retry succeeds (simulation or real API)
    success = razorpay_client.simulate_retry_result(state)

    if success:
        # Mark recovered
        state["status"] = "recovered"
        state["recovered_amount_paise"] = state["amount_paise"]
        add_ledger_entry(state, "silent_retry_success", {"amount_paise": state["amount_paise"]}, idem_key, 0.0)
        logger.info(f"Silent retry succeeded for {event_id}")
    else:
        add_ledger_entry(state, "silent_retry_failed", {"attempt": state["attempts_silent_retry"]}, idem_key, 0.0)
        logger.info(f"Silent retry failed for {event_id}")

    return state