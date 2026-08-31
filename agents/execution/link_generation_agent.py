"""
Link Generation Agent: creates a payment/re-auth/update-instrument link and sends a message.
Used for mandate_dead, instrument_dead, and checkout retarget (if no discount).
"""
from typing import Dict, Any
from datetime import datetime, timezone
from services.razorpay_client import razorpay_client
from services.llm_service import llm_service
from utils.idempotency import generate_idempotency_key
from utils.audit import add_ledger_entry
from config.logger import logger

def generate_and_send_link(state: Dict[str, Any], link_type: str = "payment_link") -> Dict[str, Any]:
    """
    Generate a Razorpay payment link and compose a Hinglish message.
    link_type: "payment_link" (generic), "reauth_link", "update_instrument_link"
    """
    state["node_history"].append("link_generation")
    event_id = state["event_id"]
    attempt = state.get("attempts_contact", 0)
    idem_key = generate_idempotency_key(event_id, link_type, attempt)

    # Idempotency check
    for entry in state.get("ledger", []):
        if entry.get("idempotency_key") == idem_key:
            state["gates_blocked"].append("duplicate_link_generation")
            add_ledger_entry(state, "link_generation_blocked", {"reason": "duplicate idempotency key"}, idem_key, 0.0)
            return state

    # Create payment link via Razorpay (or simulation)
    amount = state["amount_paise"]
    customer_phone = state.get("customer_phone", "")
    customer_name = state.get("customer_name", "Customer")
    reference_id = state.get("mandate_id") or event_id

    short_url = razorpay_client.create_payment_link(amount, customer_phone, customer_name, reference_id)
    if not short_url:
        state["errors"].append("razorpay_link_creation_failed")
        add_ledger_entry(state, "link_generation_failed", {"reason": "Razorpay API failed"}, idem_key, 0.0)
        return state

    # Compose message based on link type
    if link_type == "reauth_link":
        message = llm_service.generate_hinglish_text(state, message_type="reauth")
    elif link_type == "update_instrument_link":
        message = llm_service.generate_hinglish_text(state, message_type="update_instrument")
    else:
        message = llm_service.generate_hinglish_text(state, message_type="nudge")

    # Replace placeholder with actual short URL
    message = message.replace("{payment_link}", short_url)

    # Log the message (simulate sending)
    add_ledger_entry(state, f"{link_type}_sent", {"message": message, "url": short_url}, idem_key, 0.0)
    state["attempts_contact"] += 1
    logger.info(f"Link generated and message sent for {event_id}: {message[:50]}...")

    return state