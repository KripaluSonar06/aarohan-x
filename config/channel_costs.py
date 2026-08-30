"""
Channel cost table (in INR) used by decision engine.
"""
from config.settings import settings

CHANNEL_COSTS = {
    "silent_retry": 0.0,
    "payment_link": settings.PAYMENT_LINK_COST,
    "sms": settings.SMS_COST,
    "whatsapp": settings.SMS_COST,  # same as SMS for demo
    "voice": settings.VOICE_COST,
    "discount": None,  # calculated as percentage of amount, capped
}

def get_channel_cost(channel: str, amount_paise: int | None = None) -> float:
    """Return the cost of a channel in INR.
    For discount, cost = min(discount_percent/100 * amount_in_inr, max_discount_amount)
    """
    if channel == "discount":
        if amount_paise is None:
            return 0.0
        # assume discount is capped at 5% of amount
        discount_percent = settings.DISCOUNT_MAX_PERCENT
        amount_inr = amount_paise / 100
        return (discount_percent / 100) * amount_inr
    return CHANNEL_COSTS.get(channel, 0.0)