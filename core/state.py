"""
State definitions for the LangGraph recovery workflow.
"""
from typing import TypedDict, Optional, List, Literal
from datetime import datetime
from enum import Enum

class EventClass(str, Enum):
    """All possible diagnosis classes."""
    FUNDS = "funds"
    DOWNTIME = "downtime"
    MANDATE_DEAD = "mandate_dead"
    INSTRUMENT_DEAD = "instrument_dead"
    CUSTOMER_CANCEL = "customer_cancel"
    RISK = "risk"
    LIMIT = "limit"
    UNKNOWN = "unknown"
    ABANDONED = "abandoned"          # for checkout abandonment
    NEEDS_HUMAN = "needs_human"

class RecoveryState(TypedDict, total=False):
    """
    The complete state object passed between graph nodes.
    Not all fields are required at every step; they get filled as the workflow progresses.
    """

    # --- Identity ---
    event_id: str
    event_type: Literal["failed_payment", "checkout_abandoned"]
    merchant_id: str
    merchant_name: str
    customer_id: Optional[str]
    customer_phone: Optional[str]
    customer_name: Optional[str]
    amount_paise: int
    currency: str
    created_at: datetime

    # --- Failed payment fields ---
    mandate_id: Optional[str]
    cycle: Optional[int]
    original_failure_code: Optional[str]
    original_failure_desc: Optional[str]

    # --- Checkout abandonment fields ---
    cart_id: Optional[str]
    cart_value_paise: Optional[int]
    time_since_abandonment_minutes: Optional[int]
    return_visit_signal: Optional[bool]
    discount_eligible: Optional[bool]

    # --- Diagnosis ---
    diagnosed_class: Optional[EventClass]
    diagnosis_confidence: Optional[float]
    diagnosis_source: Optional[str]          # "rules" | "llm" | "dl"
    diagnosis_reason: Optional[str]

    # --- Gates and risk ---
    gates_passed: List[str]
    gates_blocked: List[str]
    risk_flags: List[str]
    do_not_contact: bool

    # --- Ranking ---
    recovery_probability: Optional[float]
    expected_gross_value: Optional[float]
    channel_cost: Optional[float]
    net_expected_value: Optional[float]
    voice_worth_it: bool
    model_confidence: Optional[float]       # 0-1, from ranker

    # --- Policy / action ---
    playbook_action: Optional[str]           # selected action from intervention ladder
    attempts_silent_retry: int
    attempts_contact: int
    ptp_date: Optional[datetime]
    ptp_count: int
    ptp_broken: bool
    broken_ptp_rate_global: Optional[float]

    # --- Status ---
    status: str                              # active|recovered|stopped|escalated|needs_human
    recovered_amount_paise: int
    stopped_reason: Optional[str]

    # --- Audit and history ---
    ledger: List[dict]
    node_history: List[str]
    errors: List[str]
    strategy: str
    simulation_seed: int