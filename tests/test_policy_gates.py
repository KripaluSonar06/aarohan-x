import pytest
from agents.risk_gate_agent import apply_risk_gates
from core.state import EventClass
from config.policy import policy_manager

def test_risk_gate_stops_customer_cancel():
    state = {
        "event_id": "T3",
        "event_type": "failed_payment",
        "diagnosed_class": EventClass.CUSTOMER_CANCEL,
        "gates_blocked": [],
        "gates_passed": [],
        "status": "active",
        "stopped_reason": None,
        "ledger": [],
        "node_history": [],
        "do_not_contact": False,
        "attempts_silent_retry": 0,
        "attempts_contact": 0,
        "ptp_broken": False,
        "amount_paise": 1000,
    }
    result = apply_risk_gates(state)
    assert result["status"] == "stopped"
    assert "hard_stop_class" in result["gates_blocked"]

def test_risk_gate_stops_dnd():
    state = {
        "event_id": "T4",
        "diagnosed_class": EventClass.FUNDS,
        "do_not_contact": True,
        "gates_blocked": [],
        "status": "active",
        "ledger": [],
        "node_history": [],
        "stopped_reason": None,
        "attempts_silent_retry": 0,
        "attempts_contact": 0,
        "ptp_broken": False,
        "amount_paise": 1000,
    }
    result = apply_risk_gates(state)
    assert result["status"] == "stopped"
    assert "dnd" in result["gates_blocked"]