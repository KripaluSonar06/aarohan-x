"""
Diagnostic script: run a single known 'funds' event through the graph and print state after each node.
"""
import json
from datetime import datetime, timezone
from core.graph import batch_graph_app
from agents.ingestion_agent import ingest_event
from agents.diagnosis_agent import diagnose
from agents.risk_gate_agent import apply_risk_gates
from agents.ranking_agent import rank
from agents.policy_agent import select_action
from agents.execution.silent_retry_agent import silent_retry
from agents.execution.text_nudge_agent import send_text_nudge
from agents.settlement_agent import settle

# A known recoverable event: insufficient funds, ₹1000
raw_event = {
    "event_id": "DEBUG_FUNDS_001",
    "event_type": "failed_payment",
    "merchant_id": "m1",
    "merchant_name": "Test Merchant",
    "customer_id": "c1",
    "customer_phone": "+911234567890",
    "customer_name": "Debug Customer",
    "amount_paise": 100000,  # ₹1000
    "currency": "INR",
    "created_at": "2025-01-01T00:00:00Z",
    "mandate_id": "mandate_debug",
    "cycle": 1,
    "original_failure_code": "BAD_REQUEST",
    "original_failure_desc": "Insufficient funds in customer account",
    "cart_id": None,
    "cart_value_paise": None,
    "time_since_abandonment_minutes": None,
    "return_visit_signal": False,
    "discount_eligible": False,
}

def print_state(state, label):
    print(f"\n--- {label} ---")
    print(f"event_id: {state.get('event_id')}")
    print(f"diagnosed_class: {state.get('diagnosed_class')}")
    print(f"diagnosis_source: {state.get('diagnosis_source')}")
    print(f"diagnosis_confidence: {state.get('diagnosis_confidence')}")
    print(f"recovery_probability: {state.get('recovery_probability')}")
    print(f"playbook_action: {state.get('playbook_action')}")
    print(f"status: {state.get('status')}")
    print(f"stopped_reason: {state.get('stopped_reason')}")
    print(f"attempts_silent_retry: {state.get('attempts_silent_retry')}")
    print(f"attempts_contact: {state.get('attempts_contact')}")
    print(f"recovered_amount_paise: {state.get('recovered_amount_paise')}")
    print(f"gates_blocked: {state.get('gates_blocked')}")
    print(f"ledger: {state.get('ledger')}")

# Run nodes manually
state = ingest_event(raw_event)
print_state(state, "After ingestion")

state = diagnose(state)
print_state(state, "After diagnosis")

state = apply_risk_gates(state)
print_state(state, "After risk gates")

state = rank(state)
print_state(state, "After ranking")

state = select_action(state)
print_state(state, "After policy")

# Execute selected action
action = state.get("playbook_action")
if action == "silent_retry":
    state = silent_retry(state)
elif action in ["text_nudge", "voice_call", "payment_link"]:
    state = send_text_nudge(state)  # simple fallback for debug

print_state(state, "After execution")

state = settle(state)
print_state(state, "After settlement")