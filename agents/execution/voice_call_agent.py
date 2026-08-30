"""
Voice Call Agent: executes a Hinglish voice call using TTS, then simulates/parses response.
Falls back to text nudge if voice fails.
"""
from typing import Dict, Any
from datetime import datetime, timezone
from services.llm_service import llm_service
from services.voice_service import voice_service
from utils.idempotency import generate_idempotency_key
from utils.audit import add_ledger_entry
from config.channel_costs import get_channel_cost
from config.logger import logger

def voice_call(state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a voice call and handle response."""
    state["node_history"].append("voice_call")
    event_id = state["event_id"]
    attempt = state.get("attempts_contact", 0)
    idem_key = generate_idempotency_key(event_id, "voice_call", attempt)

    # Idempotency check
    for entry in state.get("ledger", []):
        if entry.get("idempotency_key") == idem_key:
            state["gates_blocked"].append("duplicate_voice_call")
            add_ledger_entry(state, "voice_call_blocked", {"reason": "duplicate idempotency key"}, idem_key, 0.0)
            return state

    # Generate voice script
    script = llm_service.generate_voice_script(state)

    # Execute voice call (simulate or real TTS+call)
    voice_result = voice_service.execute_voice_call(script, state.get("customer_phone", ""))

    if not voice_result.get("success", False):
        # Voice failed; fallback to text nudge
        state["errors"].append(f"voice_call_failed: {voice_result.get('reason')}")
        add_ledger_entry(state, "voice_call_failed_fallback_to_text", {"reason": voice_result.get("reason")}, idem_key, 0.0)
        logger.warning(f"Voice failed for {event_id}, falling back to text nudge")
        return send_text_nudge(state)  # reuse text nudge; will increment attempt

    # Voice succeeded; parse customer response
    transcript = voice_result.get("transcript", "")
    # Use LLM to parse transcript into structured outcome
    parsed = llm_service.parse_customer_response(transcript)
    parsed_type = parsed.get("type", "no_answer")
    parsed_date = parsed.get("date")
    confidence = parsed.get("confidence", 0.0)

    # Record call cost
    cost = get_channel_cost("voice", state["amount_paise"])
    add_ledger_entry(state, "voice_call_completed", {"transcript": transcript, "parsed": parsed}, idem_key, cost)
    state["attempts_contact"] += 1

    # Handle outcome
    if parsed_type == "promised":
        state["ptp_date"] = parsed_date
        state["ptp_count"] += 1
        add_ledger_entry(state, "ptp_recorded", {"promised_date": parsed_date}, None, 0.0)
    elif parsed_type == "paid_now":
        # Assume customer paid via some method; we'll verify later
        state["recovered_amount_paise"] = state["amount_paise"]
        state["status"] = "recovered"
    elif parsed_type == "refused":
        state["status"] = "stopped"
        state["stopped_reason"] = "Customer refused to pay"
    elif parsed_type == "do_not_contact":
        state["do_not_contact"] = True
        state["status"] = "stopped"
        state["stopped_reason"] = "Customer requested no further contact"
        # Also update global DND flag in DB later

    return state