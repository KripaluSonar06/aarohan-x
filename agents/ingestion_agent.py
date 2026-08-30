"""
Ingestion Agent: receives events (webhook or batch) and normalizes into RecoveryState.
"""
from typing import Dict, Any, List
from datetime import datetime, timezone
from config.logger import logger
from models.entities import CustomerProfile
from utils.db import SessionLocal

def normalize_failed_payment_event(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a Razorpay failed payment webhook into a base state."""
    return {
        "event_id": raw.get("event_id"),
        "event_type": "failed_payment",
        "merchant_id": raw.get("merchant_id"),
        "merchant_name": raw.get("merchant_name", "Unknown Merchant"),
        "customer_id": raw.get("customer_id"),
        "customer_phone": raw.get("customer_phone"),
        "customer_name": raw.get("customer_name", "Customer"),
        "amount_paise": int(raw.get("amount_paise", 0)),
        "currency": raw.get("currency", "INR"),
        "created_at": datetime.now(timezone.utc),
        "mandate_id": raw.get("mandate_id"),
        "cycle": raw.get("cycle"),
        "original_failure_code": raw.get("failure_code", ""),
        "original_failure_desc": raw.get("failure_desc", ""),
        "cart_id": None,
        "cart_value_paise": None,
        "time_since_abandonment_minutes": None,
        "return_visit_signal": False,
        "discount_eligible": False,
        "diagnosed_class": None,
        "diagnosis_confidence": None,
        "diagnosis_source": None,
        "diagnosis_reason": None,
        "gates_passed": [],
        "gates_blocked": [],
        "risk_flags": [],
        "do_not_contact": False,
        "recovery_probability": None,
        "expected_gross_value": None,
        "channel_cost": None,
        "net_expected_value": None,
        "voice_worth_it": False,
        "model_confidence": None,
        "playbook_action": None,
        "attempts_silent_retry": 0,
        "attempts_contact": 0,
        "ptp_date": None,
        "ptp_count": 0,
        "ptp_broken": False,
        "broken_ptp_rate_global": None,
        "status": "active",
        "recovered_amount_paise": 0,
        "stopped_reason": None,
        "ledger": [],
        "node_history": ["ingest"],
        "errors": [],
    }

def normalize_checkout_abandonment_event(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a checkout abandonment record into a base state."""
    return {
        "event_id": raw.get("event_id"),
        "event_type": "checkout_abandoned",
        "merchant_id": raw.get("merchant_id"),
        "merchant_name": raw.get("merchant_name", "Unknown Merchant"),
        "customer_id": raw.get("customer_id"),
        "customer_phone": raw.get("customer_phone"),
        "customer_name": raw.get("customer_name", "Customer"),
        "amount_paise": int(raw.get("cart_value_paise", raw.get("amount_paise", 0))),
        "currency": raw.get("currency", "INR"),
        "created_at": datetime.now(timezone.utc),
        "mandate_id": None,
        "cycle": None,
        "original_failure_code": None,
        "original_failure_desc": None,
        "cart_id": raw.get("cart_id"),
        "cart_value_paise": int(raw.get("cart_value_paise", 0)),
        "time_since_abandonment_minutes": raw.get("time_since_abandonment_minutes"),
        "return_visit_signal": raw.get("return_visit_signal", False),
        "discount_eligible": raw.get("discount_eligible", False),
        "diagnosed_class": None,
        "diagnosis_confidence": None,
        "diagnosis_source": None,
        "diagnosis_reason": None,
        "gates_passed": [],
        "gates_blocked": [],
        "risk_flags": [],
        "do_not_contact": False,
        "recovery_probability": None,
        "expected_gross_value": None,
        "channel_cost": None,
        "net_expected_value": None,
        "voice_worth_it": False,
        "model_confidence": None,
        "playbook_action": None,
        "attempts_silent_retry": 0,
        "attempts_contact": 0,
        "ptp_date": None,
        "ptp_count": 0,
        "ptp_broken": False,
        "broken_ptp_rate_global": None,
        "status": "active",
        "recovered_amount_paise": 0,
        "stopped_reason": None,
        "ledger": [],
        "node_history": ["ingest"],
        "errors": [],
    }

def enrich_with_customer_profile(state: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch customer history and set DND/PTP related fields."""
    if not state.get("customer_id"):
        return state

    db = SessionLocal()
    try:
        customer = db.query(CustomerProfile).filter(CustomerProfile.id == state["customer_id"]).first()
        if customer:
            state["do_not_contact"] = customer.do_not_contact
            # broken PTP rate
            if customer.total_ptp_count > 0:
                state["broken_ptp_rate_global"] = customer.broken_ptp_count / customer.total_ptp_count
            else:
                state["broken_ptp_rate_global"] = 0.0
        else:
            state["broken_ptp_rate_global"] = 0.0
    except Exception as e:
        logger.error(f"Error enriching customer profile: {e}")
    finally:
        db.close()
    return state

def ingest_event(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for ingestion. Determine event type and normalize."""
    event_type = raw_event.get("event_type", "failed_payment")
    if event_type == "checkout_abandoned":
        state = normalize_checkout_abandonment_event(raw_event)
    else:
        state = normalize_failed_payment_event(raw_event)
    state = enrich_with_customer_profile(state)
    state["ledger"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "ingested",
        "detail": {"event_type": state["event_type"], "amount_paise": state["amount_paise"]},
        "idempotency_key": None,
        "cost": 0.0,
    })
    return state