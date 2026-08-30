from agents.settlement_agent import settle
from datetime import datetime, timedelta, timezone

def test_ptp_broken_detected():
    past_date = datetime.now(timezone.utc) - timedelta(days=1)
    state = {
        "event_id": "T5",
        "status": "active",
        "recovered_amount_paise": 0,
        "ptp_date": past_date.isoformat(),
        "ptp_broken": False,
        "ledger": [],
        "node_history": [],
        "diagnosed_class": None,
        "playbook_action": "text_nudge",
    }
    result = settle(state)
    assert result["ptp_broken"] == True
    assert result["status"] == "escalated"
    assert "PTP broken" in result["stopped_reason"]