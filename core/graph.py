"""
LangGraph state machine for Aarohan-X recovery workflow.
Supports optional interrupts before money-touching actions for human approval.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Dict, Any, Literal

# Import agents
from agents.ingestion_agent import ingest_event
from agents.diagnosis_agent import diagnose
from agents.risk_gate_agent import apply_risk_gates
from agents.ranking_agent import rank
from agents.policy_agent import select_action
from agents.execution.silent_retry_agent import silent_retry
from agents.execution.link_generation_agent import generate_and_send_link
from agents.execution.text_nudge_agent import send_text_nudge
from agents.execution.voice_call_agent import voice_call
from agents.execution.checkout_retarget_agent import checkout_retarget
from agents.execution.scheduler_agent import schedule_wait
from agents.settlement_agent import settle
from core.state import RecoveryState


def build_graph(interrupt: bool = True):
    """
    Build the recovery graph.

    Args:
        interrupt: If True, the graph will pause before executing any
                   customer-facing or money-touching action. The orchestrator
                   can then resume after approval. For batch processing,
                   set interrupt=False to run without pausing.
    """
    workflow = StateGraph(RecoveryState)

    # ------------------------------------------------------------
    # Node wrappers
    # ------------------------------------------------------------
    def ingest_node(raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw event into initial state."""
        return ingest_event(raw_event)

    # Add nodes
    workflow.add_node("ingest", ingest_node)
    workflow.add_node("diagnose", diagnose)
    workflow.add_node("risk_gate", apply_risk_gates)
    workflow.add_node("rank", rank)
    workflow.add_node("policy", select_action)

    # Execution agents
    workflow.add_node("silent_retry", silent_retry)
    workflow.add_node("link_generation", generate_and_send_link)
    workflow.add_node("text_nudge", send_text_nudge)
    workflow.add_node("voice_call", voice_call)
    workflow.add_node("checkout_retarget", checkout_retarget)
    workflow.add_node("schedule_wait", schedule_wait)

    # Settlement & terminal
    workflow.add_node("settle", settle)
    workflow.add_node("stop", lambda state: state)  # no-op terminal

    # ------------------------------------------------------------
    # Edges and routing
    # ------------------------------------------------------------
    workflow.set_entry_point("ingest")

    workflow.add_edge("ingest", "diagnose")
    workflow.add_edge("diagnose", "risk_gate")

    # After risk gate: if stopped, go to terminal stop; else continue to ranking
    def after_risk_gate(state: Dict[str, Any]) -> Literal["rank", "stop"]:
        return "stop" if state.get("status") == "stopped" else "rank"

    workflow.add_conditional_edges(
        "risk_gate",
        after_risk_gate,
        {"rank": "rank", "stop": "stop"}
    )

    workflow.add_edge("rank", "policy")

    # After policy: route to the appropriate execution node
    def route_after_policy(state: Dict[str, Any]) -> str:
        action = state.get("playbook_action", "stop")
        mapping = {
            "silent_retry": "silent_retry",
            "payment_link": "link_generation",
            "reauth_link": "link_generation",
            "update_instrument_link": "link_generation",
            "text_nudge": "text_nudge",
            "voice_call": "voice_call",
            "retarget_nudge": "checkout_retarget",
            "checkout_retarget": "checkout_retarget",
            "discount_link": "checkout_retarget",   # discount handled in checkout_retarget
            "merchant_escalation": "stop",          # escalation logic simplified to stop
            "stop": "stop",
        }
        return mapping.get(action, "stop")

    workflow.add_conditional_edges(
        "policy",
        route_after_policy,
        {
            "silent_retry": "silent_retry",
            "link_generation": "link_generation",
            "text_nudge": "text_nudge",
            "voice_call": "voice_call",
            "checkout_retarget": "checkout_retarget",
            "stop": "stop",
        }
    )

    # After any execution node, go to settlement
    for node in ["silent_retry", "link_generation", "text_nudge", "voice_call", "checkout_retarget"]:
        workflow.add_edge(node, "settle")

    # If schedule_wait is ever used, it goes to stop (wait is simulated outside)
    workflow.add_edge("schedule_wait", "stop")

    # After settlement, final stop
    workflow.add_edge("settle", "stop")
    workflow.add_edge("stop", END)

    # ------------------------------------------------------------
    # Compile with checkpoint and optional interrupts
    # ------------------------------------------------------------
    memory = MemorySaver()
    if interrupt:
        interrupt_before = [
            "silent_retry",
            "voice_call",
            "link_generation",
            "text_nudge",
            "checkout_retarget",
        ]
    else:
        interrupt_before = []

    app = workflow.compile(
        checkpointer=memory,
        interrupt_before=interrupt_before,
    )
    return app


# Default instance with interrupts (for interactive demo / UI)
graph_app = build_graph(interrupt=True)

# Batch instance without interrupts (for automated batch processing)
batch_graph_app = build_graph(interrupt=False)