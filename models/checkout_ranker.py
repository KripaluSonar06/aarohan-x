"""
Checkout abandonment recovery probability model.
A simple logistic regression or rule-based scorer.
Currently not used by the main pipeline, but can be extended.
"""

class CheckoutRanker:
    def __init__(self):
        pass

    def predict_proba(self, features: dict) -> float:
        """Heuristic probability for checkout recovery."""
        time_since = features.get("time_since_abandonment_minutes", 999)
        return_visit = features.get("return_visit_signal", False)
        cart_value = features.get("amount_paise", 0) / 100
        # Simple heuristic
        prob = 0.1
        if return_visit and time_since < 60:
            prob = 0.6
        elif time_since < 1440:
            prob = 0.3
        # Adjust by cart value
        if cart_value > 1000:
            prob *= 1.2
        return min(prob, 0.95)