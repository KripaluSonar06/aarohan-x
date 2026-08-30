"""
Checkout Retarget Agent: sends a targeted nudge for abandoned carts.
Can include a discount if eligible.
"""
from typing import Dict, Any
from datetime import datetime, timezone
from services.llm_service import llm_service
from services.razorpay_client import razorpay_client
from utils.idempotency import generate_idempotency_key
from utils.audit import add_ledger_entry
from config.channel_costs import get_channel_cost
from config.logger import logger

def checkout_retarget(state: Dict[str, Any]) -> Dict[str, Any]:
    """Send a retarget message for abandoned cart."""
    state["node_history"].append("checkout_retarget")
    event_id = state["event_id"]
    attempt = state.get("attempts_contact", 0)
    idem_key = generate_idempotency_key(event_id, "checkout_retarget", attempt, cart_id=state.get("cart_id"))

    # Idempotency check
    for entry in state.get("ledger", []):
        if entry.get("idempotency_key") == idem_key:
            state["gates_blocked"].append("duplicate_checkout_retarget")
            add_ledger_entry(state, "checkout_retarget_blocked", {"reason": "duplicate idempotency key"}, idem_key, 0.0)
            return state

    # Generate message with possible discount
    message = llm_service.generate_hinglish_text(state, message_type="retarget")
    # If discount eligible, include discount code (but we don't apply it here; just mention)
    if state.get("discount_eligible", False):
        # maybe include a discount percentage; in real system, generate a coupon
        message += " Use code SAVE5 for 5% off."

    # Create payment link for cart
    short_url = razorpay_client.create_payment_link(
        state["amount_paise"],
        state.get("customer_phone", ""),
        state.get("customer_name", "Customer"),
        state.get("cart_id") or event_id
    )
    if short_url:
        message = message.replace("{payment_link}", short_url)

    # Send (simulate)
    cost = get_channel_cost("sms", state["amount_paise"])
    add_ledger_entry(state, "checkout_retarget_sent", {"message": message}, idem_key, cost)
    state["attempts_contact"] += 1
    logger.info(f"Checkout retarget sent for {event_id}")
    return state