import sys
from pathlib import Path
import pytest

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

@pytest.fixture
def sample_failed_payment_state():
    return {
        "event_id": "TEST_001",
        "event_type": "failed_payment",
        "merchant_id": "merchant_1",
        "merchant_name": "Test Merchant",
        "customer_id": "cust_1",
        "customer_phone": "+911234567890",
        "customer_name": "Test Customer",
        "amount_paise": 100000,
        "currency": "INR",
        "created_at": "2025-01-01T00:00:00Z",
        "mandate_id": "mandate_1",
        "cycle": 1,
        "original_failure_code": "BAD_REQUEST",
        "original_failure_desc": "Insufficient funds",
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
        "broken_ptp_rate_global": 0.0,
        "status": "active",
        "recovered_amount_paise": 0,
        "stopped_reason": None,
        "ledger": [],
        "node_history": [],
        "errors": [],
    }