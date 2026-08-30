from agents.diagnosis_agent import diagnose_failed_payment
from core.state import EventClass

def test_diagnosis_rules_match():
    state = {
        "original_failure_code": "BAD_REQUEST",
        "original_failure_desc": "Insufficient funds",
        "event_id": "T1",
    }
    result = diagnose_failed_payment(state)
    assert result["diagnosed_class"] == EventClass.FUNDS
    assert result["diagnosis_source"] == "rules"

def test_diagnosis_llm_fallback_is_called_for_unknown():
    # We cannot actually call LLM in test; we'll mock the llm_service.
    # For simplicity, we'll test that when rules miss, it goes to LLM.
    # Since LLM may be unavailable, we expect class needs_human or unknown.
    # We'll monkeypatch llm_service.classify_failure to return a fixed value.
    import agents.diagnosis_agent as da
    da.llm_service.classify_failure = lambda *args, **kwargs: {"class": "downtime", "confidence": 0.8, "reason": "mock"}
    state = {
        "original_failure_code": "SOMETHING_WEIRD",
        "original_failure_desc": "totally unknown",
        "event_id": "T2",
        "customer_id": "cust",
        "amount_paise": 100,
    }
    result = diagnose_failed_payment(state)
    assert result["diagnosed_class"] == EventClass.DOWNTIME
    assert result["diagnosis_source"] == "llm"