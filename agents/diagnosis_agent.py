"""
Diagnosis Agent: classifies failure reason using rules first, then LLM fallback.
For checkout abandonment, class is always 'abandoned'.
"""
from typing import Dict, Any
from core.state import EventClass
from services.llm_service import llm_service
from config.logger import logger

# Deterministic rules mapping from failure codes/descriptions to EventClass
RULES = {
    "insufficient_funds": EventClass.FUNDS,
    "insufficient_balance": EventClass.FUNDS,
    "balance_insufficient": EventClass.FUNDS,
    "low_balance": EventClass.FUNDS,
    "payment_timed_out": EventClass.DOWNTIME,
    "timeout": EventClass.DOWNTIME,
    "gateway_timeout": EventClass.DOWNTIME,
    "bank_unavailable": EventClass.DOWNTIME,
    "upi_timeout": EventClass.DOWNTIME,
    "issuer_unavailable": EventClass.DOWNTIME,
    "network_error": EventClass.DOWNTIME,
    "mandate_expired": EventClass.MANDATE_DEAD,
    "mandate_paused": EventClass.MANDATE_DEAD,
    "mandate_revoked": EventClass.MANDATE_DEAD,
    "autopay_disabled": EventClass.MANDATE_DEAD,
    "subscription_cancelled": EventClass.MANDATE_DEAD,
    "card_expired": EventClass.INSTRUMENT_DEAD,
    "invalid_vpa": EventClass.INSTRUMENT_DEAD,
    "vpa_not_found": EventClass.INSTRUMENT_DEAD,
    "account_closed": EventClass.INSTRUMENT_DEAD,
    "customer_cancelled": EventClass.CUSTOMER_CANCEL,
    "user_cancelled": EventClass.CUSTOMER_CANCEL,
    "payment_cancelled_by_user": EventClass.CUSTOMER_CANCEL,
    "fraud_suspected": EventClass.RISK,
    "chargeback_risk": EventClass.RISK,
    "blocked_by_risk": EventClass.RISK,
    "high_risk_transaction": EventClass.RISK,
    "limit_exceeded": EventClass.LIMIT,
    "upi_limit": EventClass.LIMIT,
    "bank_limit": EventClass.LIMIT,
    "daily_limit": EventClass.LIMIT,
}

def diagnose_failed_payment(state: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(state, dict):
        logger.error(f"diagnose_failed_payment received non-dict state: {type(state)}")
        return {"status": "needs_human", "errors": ["invalid state"]}
    """Diagnose failed payment events using rules then LLM."""
    code = state.get("original_failure_code", "").lower().strip()
    desc = state.get("original_failure_desc", "").lower().strip()

    # Check exact code
    if code in RULES:
        state["diagnosed_class"] = RULES[code]
        state["diagnosis_confidence"] = 0.95
        state["diagnosis_source"] = "rules"
        state["diagnosis_reason"] = f"Failure code matched: {code}"
        return state

    # Check description keywords
    for keyword, event_class in RULES.items():
        if keyword in desc:
            state["diagnosed_class"] = event_class
            state["diagnosis_confidence"] = 0.85
            state["diagnosis_source"] = "rules"
            state["diagnosis_reason"] = f"Description keyword matched: {keyword}"
            return state

    # If not matched by rules, use LLM
    logger.info(f"Failure not matched by rules, using LLM for event {state['event_id']}")
    context = f"Customer ID: {state.get('customer_id')}, Amount: ₹{state['amount_paise']/100:.2f}"
    llm_result = llm_service.classify_failure(code, desc, context)
    state["diagnosed_class"] = EventClass(llm_result["class"])
    state["diagnosis_confidence"] = llm_result["confidence"]
    state["diagnosis_source"] = "llm"
    state["diagnosis_reason"] = llm_result.get("reason", "LLM classification")
    return state

def diagnose_checkout_abandonment(state: Dict[str, Any]) -> Dict[str, Any]:
    """Diagnose checkout abandonment events."""
    state["diagnosed_class"] = EventClass.ABANDONED
    state["diagnosis_confidence"] = 1.0
    state["diagnosis_source"] = "rules"
    state["diagnosis_reason"] = "Event type is checkout abandonment"
    return state

def diagnose(state: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for diagnosis agent."""
    state["node_history"].append("diagnose")
    if state["event_type"] == "checkout_abandoned":
        state = diagnose_checkout_abandonment(state)
    else:
        state = diagnose_failed_payment(state)
    # Log diagnosis
    state["ledger"].append({
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "action": "diagnosed",
        "detail": {
            "class": state["diagnosed_class"].value if state["diagnosed_class"] else None,
            "confidence": state["diagnosis_confidence"],
            "source": state["diagnosis_source"],
            "reason": state["diagnosis_reason"]
        },
        "idempotency_key": None,
        "cost": 0.0,
    })
    return state