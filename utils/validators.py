from typing import Any, Dict, List


def validate_event(raw: Dict[str, Any]) -> List[str]:
    """Return actionable validation errors for an incoming recovery event."""
    if not isinstance(raw, dict):
        return ["event must be an object"]
    errors = []
    if not raw.get("event_id"):
        errors.append("event_id is required")
    event_type = raw.get("event_type", "failed_payment")
    if event_type not in {"failed_payment", "checkout_abandoned"}:
        errors.append(f"unsupported event_type: {event_type}")
    amount_key = "cart_value_paise" if event_type == "checkout_abandoned" else "amount_paise"
    amount = raw.get(amount_key)
    if amount is None:
        errors.append(f"{amount_key} is required")
    else:
        try:
            if int(amount) <= 0:
                errors.append("amount must be greater than zero")
        except (TypeError, ValueError):
            errors.append("amount must be an integer")
    if event_type == "failed_payment" and not any(
        raw.get(key) for key in (
            "failure_code", "original_failure_code",
            "failure_desc", "original_failure_desc",
        )
    ):
        errors.append("failure code or description is required")
    return errors