"""
Razorpay test-mode client wrapper.
Provides methods to simulate retries, create payment links, and verify payments.
"""
import razorpay
from config.settings import settings
from config.logger import logger

class RazorpayTestClient:
    def __init__(self):
        self.client = None
        if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            logger.info("Razorpay test client initialized.")
        else:
            logger.warning("Razorpay keys not set. Using simulation mode.")

    def create_payment_link(self, amount_paise: int, customer_phone: str, customer_name: str, reference_id: str) -> Optional[str]:
        """Create a payment link for re-auth or manual payment. Returns short URL or None."""
        if not self.client:
            # Simulate returning a dummy link for demo
            return f"https://rzp.io/i/sim_{reference_id}"
        try:
            payment_link = self.client.payment_link.create({
                "amount": amount_paise,
                "currency": "INR",
                "description": f"Recovery for {reference_id}",
                "customer": {"name": customer_name, "contact": customer_phone},
                "notify": {"sms": True, "email": False},
                "reminder_enable": False,
                "callback_url": "https://example.com/callback",
                "callback_method": "get"
            })
            return payment_link.get("short_url")
        except Exception as e:
            logger.error(f"Failed to create Razorpay payment link: {e}")
            return None

    def verify_payment(self, payment_id: str) -> bool:
        """Check if payment was successful (captured)."""
        if not self.client:
            # Simulation: assume payment succeeded if id contains 'success'
            return "success" in payment_id.lower()
        try:
            payment = self.client.payment.fetch(payment_id)
            return payment["status"] == "captured"
        except Exception as e:
            logger.error(f"Razorpay verify payment failed: {e}")
            return False

    def simulate_retry_result(self, state: dict) -> bool:
        """
        Simulate whether a silent retry would succeed.
        In test mode, we use a deterministic heuristic based on class and attempt.
        This is only for demo when no real API is available.
        """
        event_class = state.get("diagnosed_class")
        attempt = state.get("attempts_silent_retry", 0)
        if event_class == "downtime":
            return True  # usually recovers
        elif event_class == "funds":
            # simulate ~30% success on first retry, ~20% on second
            import random
            prob = 0.3 if attempt == 0 else 0.2
            return random.random() < prob
        elif event_class == "limit":
            return False
        else:
            return False

# Singleton
razorpay_client = RazorpayTestClient()