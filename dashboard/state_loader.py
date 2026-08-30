"""
Helper functions to load data from DB for dashboard.
"""
import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from models.entities import RecoveryEvent, LedgerEntry

def load_events(db: Session, limit=20) -> List[Dict]:
    events = db.query(RecoveryEvent).order_by(RecoveryEvent.created_at.desc()).limit(limit).all()
    return [e.to_dict() for e in events]

def load_event_detail(event_id: str, db: Session) -> Dict[str, Any]:
    event = db.query(RecoveryEvent).filter(RecoveryEvent.id == event_id).first()
    if not event:
        return {}
    state = event.to_dict()
    # Add ledger entries
    ledger = []
    for entry in event.ledger:
        ledger.append({
            "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
            "action": entry.action,
            "detail": entry.detail,
            "idempotency_key": entry.idempotency_key,
            "cost": entry.cost,
        })
    state["ledger"] = ledger
    # Add gates info (stored in detail of gate actions)
    state["gates_passed"] = []
    state["gates_blocked"] = []
    for entry in ledger:
        if entry["action"] == "stopped_by_gate":
            state["gates_blocked"].append(entry["detail"].get("reason", ""))
    return state

def load_metrics(db: Session) -> Dict[str, Any]:
    total_at_risk = db.query(RecoveryEvent.amount_paise).all()
    total_at_risk = sum([a[0] for a in total_at_risk])
    gross_recovered = db.query(RecoveryEvent.recovered_amount_paise).all()
    gross_recovered = sum([a[0] for a in gross_recovered])
    # Contact cost from ledger
    contact_cost = db.query(LedgerEntry.cost).all()
    contact_cost = sum([c[0] for c in contact_cost])
    net_recovered = gross_recovered - int(contact_cost * 100)  # convert cost to paise

    # Breakdown by action (from ledger)
    breakdown = {}
    for entry in db.query(LedgerEntry).all():
        action = entry.action
        if "success" in action or "recovered" in action:
            # this is a recovery; we can attribute to action type
            pass
    # Simplified: use playbook_action from events
    actions = db.query(RecoveryEvent.playbook_action, RecoveryEvent.recovered_amount_paise).all()
    for action, amount in actions:
        if action and amount > 0:
            breakdown[action] = breakdown.get(action, 0) + amount
    # Convert to list of dicts for bar chart
    channel_breakdown = [{"channel": k, "amount": v} for k, v in breakdown.items()]

    # Class rates
    class_rates = []
    classes = db.query(RecoveryEvent.diagnosed_class, RecoveryEvent.amount_paise, RecoveryEvent.recovered_amount_paise).all()
    class_dict = {}
    for cls, at_risk, recovered in classes:
        if cls:
            if cls not in class_dict:
                class_dict[cls] = {"at_risk": 0, "recovered": 0}
            class_dict[cls]["at_risk"] += at_risk
            class_dict[cls]["recovered"] += recovered
    for cls, data in class_dict.items():
        rate = (data["recovered"] / data["at_risk"] * 100) if data["at_risk"] else 0
        class_rates.append({"class": cls, "rate": rate})

    # Incremental lift (placeholder)
    natural_rate = 0.40
    incremental_lift = max(0, gross_recovered - int(total_at_risk * natural_rate))

    return {
        "total_at_risk": total_at_risk,
        "gross_recovered": gross_recovered,
        "net_recovered": net_recovered,
        "incremental_lift": incremental_lift,
        "channel_breakdown": channel_breakdown,
        "class_rates": class_rates,
    }