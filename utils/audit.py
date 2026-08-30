"""
Helper to append entries to the audit ledger.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone

def add_ledger_entry(
    state: dict,
    action: str,
    detail: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
    cost: float = 0.0,
) -> None:
    """
    Append a new entry to state['ledger'].
    Also records timestamp in ISO format.
    """
    if "ledger" not in state:
        state["ledger"] = []
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "detail": detail or {},
        "idempotency_key": idempotency_key,
        "cost": cost,
    }
    state["ledger"].append(entry)