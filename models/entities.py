"""
SQLAlchemy ORM models for Aarohan-X.
Defines CustomerProfile, RecoveryEvent, LedgerEntry, and PTPRecord tables.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from utils.db import Base

class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

    id = Column(String, primary_key=True)                # customer_id
    phone = Column(String, nullable=False)
    name = Column(String, nullable=True)
    do_not_contact = Column(Boolean, default=False)      # global DND flag
    broken_ptp_count = Column(Integer, default=0)        # total broken promises
    total_ptp_count = Column(Integer, default=0)         # total promises made
    tenure_days = Column(Integer, default=0)             # days since first seen
    last_success_days_ago = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    events = relationship("RecoveryEvent", back_populates="customer")
    ptp_records = relationship("PTPRecord", back_populates="customer")


class RecoveryEvent(Base):
    __tablename__ = "recovery_events"

    id = Column(String, primary_key=True)                # event_id (unique)
    event_type = Column(String, nullable=False)          # "failed_payment" or "checkout_abandoned"
    merchant_id = Column(String, nullable=False)
    merchant_name = Column(String, nullable=False)
    customer_id = Column(String, ForeignKey("customer_profiles.id"), nullable=True)
    customer_phone = Column(String, nullable=True)
    customer_name = Column(String, nullable=True)
    amount_paise = Column(Integer, nullable=False)
    currency = Column(String, default="INR")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Failed payment specific
    mandate_id = Column(String, nullable=True)
    cycle = Column(Integer, nullable=True)
    original_failure_code = Column(String, nullable=True)
    original_failure_desc = Column(String, nullable=True)

    # Checkout abandonment specific
    cart_id = Column(String, nullable=True)
    cart_value_paise = Column(Integer, nullable=True)
    time_since_abandonment_minutes = Column(Integer, nullable=True)
    return_visit_signal = Column(Boolean, default=False)
    discount_eligible = Column(Boolean, default=False)

    # Diagnosis
    diagnosed_class = Column(String, nullable=True)       # string of EventClass enum
    diagnosis_confidence = Column(Float, nullable=True)
    diagnosis_source = Column(String, nullable=True)     # "rules" | "llm" | "dl"

    # Ranking
    recovery_probability = Column(Float, nullable=True)
    expected_gross_value = Column(Float, nullable=True)
    channel_cost = Column(Float, nullable=True)
    net_expected_value = Column(Float, nullable=True)
    voice_worth_it = Column(Boolean, default=False)

    # Policy / Action
    playbook_action = Column(String, nullable=True)      # selected action
    attempts_silent_retry = Column(Integer, default=0)
    attempts_contact = Column(Integer, default=0)
    ptp_date = Column(DateTime, nullable=True)
    ptp_count = Column(Integer, default=0)
    ptp_broken = Column(Boolean, default=False)
    broken_ptp_rate_global = Column(Float, nullable=True)

    # Status
    status = Column(String, default="active")            # active|recovered|stopped|escalated|needs_human|waiting
    recovered_amount_paise = Column(Integer, default=0)
    stopped_reason = Column(String, nullable=True)

    # Relationships
    customer = relationship("CustomerProfile", back_populates="events")
    ledger = relationship("LedgerEntry", back_populates="event", cascade="all, delete-orphan")
    ptp_records = relationship("PTPRecord", back_populates="event")

    def to_dict(self):
        """Return a dict representation for UI."""
        return {
            "event_id": self.id,
            "event_type": self.event_type,
            "merchant_name": self.merchant_name,
            "customer_name": self.customer_name,
            "amount_paise": self.amount_paise,
            "diagnosed_class": self.diagnosed_class,
            "recovery_probability": self.recovery_probability,
            "playbook_action": self.playbook_action,
            "status": self.status,
            "recovered_amount_paise": self.recovered_amount_paise,
            "ledger_count": len(self.ledger) if self.ledger else 0,
        }


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, ForeignKey("recovery_events.id"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    action = Column(String, nullable=False)              # e.g., "silent_retry_success", "text_nudge_sent"
    detail = Column(JSON, nullable=True)                 # extra context as JSON
    idempotency_key = Column(String, nullable=True)
    cost = Column(Float, default=0.0)

    event = relationship("RecoveryEvent", back_populates="ledger")


class PTPRecord(Base):
    __tablename__ = "ptp_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, ForeignKey("recovery_events.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customer_profiles.id"), nullable=False)
    promised_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    broken = Column(Boolean, default=False)
    broken_at = Column(DateTime, nullable=True)

    event = relationship("RecoveryEvent", back_populates="ptp_records")
    customer = relationship("CustomerProfile", back_populates="ptp_records")