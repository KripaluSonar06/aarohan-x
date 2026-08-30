"""
Scheduler Agent: schedules a wait for PTP date or salary window.
In demo, we simulate by setting a flag or directly advancing state.
"""
from typing import Dict, Any
from datetime import datetime, timedelta, timezone
from utils.audit import add_ledger_entry
from config.logger import logger

def schedule_wait(state: Dict[str, Any], wait_until: datetime, reason: str = "wait") -> Dict[str, Any]:
    """Schedule a wait and log it. The actual waiting is simulated outside the graph."""
    state["node_history"].append("schedule_wait")
    state["wait_until"] = wait_until.isoformat()
    add_ledger_entry(state, "wait_scheduled", {"until": wait_until.isoformat(), "reason": reason}, None, 0.0)
    logger.info(f"Wait scheduled for {state['event_id']} until {wait_until}")
    # In a real system, this would pause the graph and resume later.
    # For demo, we'll set status to 'waiting' and the orchestrator will re-run after time.
    state["status"] = "waiting"
    return state