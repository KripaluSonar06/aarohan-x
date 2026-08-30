"""
Idempotency key generation for all money/contact actions.
Keys are unique per (event, action, attempt) to prevent duplicates.
"""
from typing import Optional

def generate_idempotency_key(
    event_id: str,
    action: str,
    attempt: int,
    mandate_id: Optional[str] = None,
    cart_id: Optional[str] = None,
) -> str:
    """
    Create a deterministic idempotency key.
    Format: {event_id}:{action}:{attempt}:{extras}
    """
    base = f"{event_id}:{action}:{attempt}"
    if mandate_id:
        base += f":{mandate_id}"
    if cart_id:
        base += f":{cart_id}"
    return base