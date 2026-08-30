"""
Text Nudge Agent: sends a Hinglish SMS/WhatsApp nudge with payment link.
Used for funds (after retries), checkout abandonment, and as fallback from voice.
"""
from typing import Dict, Any
from datetime import datetime, timezone
from services.llm_service import llm_service
from utils.idempotency import generate_idempotency_key
from utils.audit import add_ledger_entry
from config.channel_costs import get_channel_cost
from config.logger import logger

def send_text_nudge(state: Dict[str, Any]) -> Dict[str, Any]:
    """Send a text nudge with payment link."""
    state["node_history"].append("text_nudge")
    event_id = state["event_id"]
    attempt = state.get("attempts_contact", 0)
    idem_key = generate_idempotency_key(event_id, "text_nudge", attempt)

    # Idempotency check
    for entry in state.get("ledger", []):
        if entry.get("idempotency_key") == idem_key:
            state["gates_blocked"].append("duplicate_text_nudge")
            add_ledger_entry(state, "text_nudge_blocked", {"reason": "duplicate idempotency key"}, idem_key, 0.0)
            return state

    # Generate message (Hinglish)
    message = llm_service.generate_hinglish_text(state, message_type="nudge")
    # If message contains payment_link placeholder, we should have already generated a link.
    # For simplicity, we assume a payment link exists or we generate a generic link.
    # In real flow, the link may be generated separately; here we include a dummy if not present.
    if "{payment_link}" in message:
        # Create a payment link if not already done
        from services.razorpay_client import razorpay_client
        short_url = razorpay_client.create_payment_link(
            state["amount_paise"],
            state.get("customer_phone", ""),
            state.get("customer_name", "Customer"),
            state.get("event_id")
        )
        message = message.replace("{payment_link}", short_url or "https://rzp.io/i/fallback")

    # Simulate sending SMS (cost = settings.SMS_COST)
    cost = get_channel_cost("sms", state["amount_paise"])
    add_ledger_entry(state, "text_nudge_sent", {"message": message}, idem_key, cost)
    state["attempts_contact"] += 1
    logger.info(f"Text nudge sent for {event_id}: {message[:50]}...")

    return state