"""FastAPI bridge for the TypeScript recovery command center."""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func

from models.entities import LedgerEntry, RecoveryEvent
from utils.db import SessionLocal, init_db
from config.policy import policy_manager
from pathlib import Path
from scripts.run_batch import load_events
from core.orchestrator import orchestrator

init_db()
app = FastAPI(title="Aarohan-X Recovery API", version="1.0.0")
CURRENT_BATCH_SIZE = 5
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VerificationRequest(BaseModel):
    recovered: bool = True
    recovered_amount_paise: int | None = None
    note: str = "Verified by merchant"
    verified_by: str = "Kripalu Sonar"


class PolicyUpdate(BaseModel):
    max_silent_retries: int | None = None
    max_customer_contacts: int | None = None
    voice_min_amount_paise: int | None = None
    high_value_review_paise: int | None = None


def _latest_events(db) -> list[RecoveryEvent]:
    return (
        db.query(RecoveryEvent)
        .order_by(RecoveryEvent.updated_at.desc(), RecoveryEvent.created_at.desc())
        .limit(CURRENT_BATCH_SIZE)
        .all()
    )


def serialize_event(event: RecoveryEvent) -> Dict[str, Any]:
    data = event.to_dict()
    data.update({
        "customer_name": event.customer_name,
        "amount_inr": event.amount_paise / 100,
        "recovered_amount_inr": event.recovered_amount_paise / 100,
        "diagnosis_confidence": event.diagnosis_confidence,
        "attempts": event.attempts_silent_retry + event.attempts_contact,
        "attempts_silent_retry": event.attempts_silent_retry,
        "attempts_contact": event.attempts_contact,
        "stopped_reason": event.stopped_reason,
        "created_at": event.created_at.isoformat() if event.created_at else "",
    })
    return data


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "aarohan-x"}


@app.get("/api/cases")
def cases() -> list[Dict[str, Any]]:
    db = SessionLocal()
    try:
        events = _latest_events(db)
        return [serialize_event(event) for event in events]
    finally:
        db.close()


@app.get("/api/metrics")
def metrics() -> Dict[str, Any]:
    db = SessionLocal()
    try:
        latest_ids = [event.id for event in _latest_events(db)]
        total = db.query(func.coalesce(func.sum(RecoveryEvent.amount_paise), 0)).filter(RecoveryEvent.id.in_(latest_ids)).scalar()
        recovered = db.query(func.coalesce(func.sum(RecoveryEvent.recovered_amount_paise), 0)).filter(RecoveryEvent.id.in_(latest_ids)).scalar()
        latest_events = db.query(RecoveryEvent).filter(RecoveryEvent.id.in_(latest_ids)).all()
        cost = sum(
            event.attempts_contact * (5.0 if event.playbook_action == "voice_call" else 0.10)
            for event in latest_events
        )
        return {
            "total_at_risk_paise": int(total),
            "gross_recovered_paise": int(recovered),
            "contact_cost_inr": float(cost),
            "net_recovered_paise": int(recovered) - int(float(cost) * 100),
            "events_recovered": db.query(RecoveryEvent).filter(RecoveryEvent.id.in_(latest_ids), RecoveryEvent.status == "recovered").count(),
            "events_needs_human": db.query(RecoveryEvent).filter(RecoveryEvent.id.in_(latest_ids), RecoveryEvent.status == "needs_human").count(),
        }
    finally:
        db.close()


@app.get("/api/analytics")
def analytics() -> Dict[str, Any]:
    """Return explainable funnel and strategy data for the merchant dashboard."""
    db = SessionLocal()
    try:
        events = _latest_events(db)
        status_counts: Dict[str, int] = {}
        action_counts: Dict[str, int] = {}
        diagnosis_counts: Dict[str, int] = {}
        recovered_by_action: Dict[str, int] = {}
        confidence_buckets = {"high": 0, "medium": 0, "low": 0}
        for event in events:
            status_counts[event.status] = status_counts.get(event.status, 0) + 1
            action = event.playbook_action or "not_selected"
            action_counts[action] = action_counts.get(action, 0) + 1
            recovered_by_action[action] = recovered_by_action.get(action, 0) + event.recovered_amount_paise
            diagnosis = event.diagnosed_class or "unknown"
            diagnosis_counts[diagnosis] = diagnosis_counts.get(diagnosis, 0) + 1
            confidence = event.diagnosis_confidence or 0
            bucket = "high" if confidence >= 0.8 else "medium" if confidence >= 0.5 else "low"
            confidence_buckets[bucket] += 1
        return {
            "funnel": [
                {"label": "Events received", "value": len(events)},
                {"label": "Diagnosed", "value": sum(diagnosis_counts.values())},
                {"label": "Intervention selected", "value": sum(action_counts.values())},
                {"label": "Recovered", "value": status_counts.get("recovered", 0)},
                {"label": "Human review", "value": status_counts.get("needs_human", 0)},
            ],
            "statuses": status_counts,
            "actions": [{"name": key, "events": value, "recovered_paise": recovered_by_action[key]} for key, value in action_counts.items()],
            "diagnoses": diagnosis_counts,
            "confidence": confidence_buckets,
        }
    finally:
        db.close()


@app.post("/api/cases/{event_id}/verify")
def verify_case(event_id: str, request: VerificationRequest) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        event = db.query(RecoveryEvent).filter(RecoveryEvent.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Recovery case not found")
        if request.recovered_amount_paise is not None and request.recovered_amount_paise < 0:
            raise HTTPException(status_code=400, detail="Recovered amount cannot be negative")
        amount = request.recovered_amount_paise
        if amount is None:
            amount = event.amount_paise if request.recovered else 0
        event.recovered_amount_paise = min(amount, event.amount_paise)
        event.status = "recovered" if event.recovered_amount_paise > 0 else "stopped"
        event.stopped_reason = None if event.status == "recovered" else request.note
        db.add(LedgerEntry(
            event_id=event.id,
            action="human_verification",
            detail={
                "recovered": request.recovered,
                "recovered_amount_paise": event.recovered_amount_paise,
                "note": request.note,
                "verified_by": request.verified_by,
            },
            cost=0.0,
        ))
        db.commit()
        db.refresh(event)
        return serialize_event(event)
    finally:
        db.close()


@app.get("/api/policy")
def get_policy() -> Dict[str, Any]:
    return policy_manager.get_policy()


@app.patch("/api/policy")
def update_policy(request: PolicyUpdate) -> Dict[str, Any]:
    updates = request.model_dump(exclude_none=True)
    policy_manager.update_policy(updates)
    return policy_manager.get_policy()


@app.post("/api/run-batch")
def run_batch() -> Dict[str, Any]:
    """Run the same five-event evaluation sample used by the command center."""
    input_path = Path(__file__).parent / "scripts" / "data" / "batch_150.csv"
    events = load_events(input_path)[:5]
    return orchestrator.run_batch(events)
