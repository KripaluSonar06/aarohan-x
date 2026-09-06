"""
LLM service: wraps Groq and Ollama for classification, script generation, and parsing.
All calls return structured outputs where needed.
"""
import json
import os
from typing import Optional, Dict, Any
from groq import Groq
from config.settings import settings
from config.logger import logger

class LLMService:
    def __init__(self):
        self.groq_client = None
        if settings.GROQ_API_KEY:
            self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        else:
            logger.warning("GROQ_API_KEY not set. LLM features will use local Ollama if available.")

    def _try_groq_models(self, prompt: str, temperature: float, max_tokens: int, json_mode: bool) -> Optional[str]:
        """Try a list of Groq models until one works."""
        models_to_try = [
            "openai/gpt-oss-120b",
            "meta-llama/llama-prompt-guard-2-86m"
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ]
        for model in models_to_try:
            try:
                kwargs = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                response = self.groq_client.chat.completions.create(**kwargs)
                logger.info(f"Groq success with model {model}")
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"Groq model {model} failed: {e}")
                continue
        return None

    def _call_ollama(self, prompt: str, temperature: float, max_tokens: int) -> Optional[str]:
        """Fallback to local Ollama."""
        try:
            import requests
            response = requests.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens}
                },
                timeout=5
            )
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as e:
            logger.warning(f"Ollama fallback failed: {e}")
        return None

    def complete(self, prompt: str, temperature: float = 0.0, max_tokens: int = 500, json_mode: bool = False) -> Optional[str]:
        """Main completion method. Tries Groq models, then Ollama."""
        result = None
        if self.groq_client:
            result = self._try_groq_models(prompt, temperature, max_tokens, json_mode)
        if result is None:
            result = self._call_ollama(prompt, temperature, max_tokens)
        return result

    def classify_failure(self, failure_code: str, failure_desc: str, context: str = "") -> Dict[str, Any]:
        """
        Classify a failed payment event into one of the EventClass values.
        Returns dict with keys: class, confidence, reason.
        """
        prompt = f"""You are a payment failure classifier for an Indian recurring payment system.
Classify this failure into exactly one category:

Class: funds - Insufficient balance. Action: silent retry, then nudge, then PTP.
Class: downtime - Bank/UPI/issuer blip. Action: silent retry only, never contact.
Class: mandate_dead - Mandate expired/paused/revoked. Action: re-auth link.
Class: instrument_dead - Card expired, VPA invalid. Action: update-instrument link.
Class: customer_cancel - Customer actively cancelled. Action: STOP.
Class: risk - Fraud-coded or chargeback-likely. Action: STOP.
Class: limit - Bank/UPI cap reached. Action: wait next cycle.
Class: needs_human - Cannot classify confidently. Action: escalate.

Failure code: {failure_code}
Failure description: {failure_desc}
Additional context: {context}

Return JSON: {{"class": "...", "confidence": 0.0-1.0, "reason": "..."}}"""
        result = self.complete(prompt, temperature=0.0, max_tokens=150, json_mode=True)
        if not result:
            return {"class": "needs_human", "confidence": 0.0, "reason": "LLM unavailable"}
        try:
            data = json.loads(result)
            # Validate class
            valid_classes = {"funds", "downtime", "mandate_dead", "instrument_dead", "customer_cancel", "risk", "limit", "needs_human"}
            if data.get("class") not in valid_classes:
                data["class"] = "needs_human"
            data["confidence"] = float(data.get("confidence", 0.0))
            return data
        except Exception as e:
            logger.error(f"Failed to parse LLM classification: {e}")
            return {"class": "needs_human", "confidence": 0.0, "reason": f"Parse error: {e}"}

    def generate_hinglish_text(self, state: Dict[str, Any], message_type: str = "nudge") -> str:
        """
        Generate a Hinglish SMS/WhatsApp message for payment recovery.
        message_type: 'nudge' (default), 'reauth', 'update_instrument', 'retarget', 'discount'
        """
        amount_inr = state.get("amount_paise", 0) / 100.0
        merchant = state.get("merchant_name", "Merchant")
        customer = state.get("customer_name", "Customer")
        event_type = state.get("event_type", "failed_payment")

        if event_type == "checkout_abandoned":
            prompt = f"""Write a short, polite Hinglish SMS to remind a customer about an abandoned cart.
Merchant: {merchant}
Customer: {customer}
Cart value: ₹{amount_inr:.2f}
Include a payment link placeholder {{payment_link}}.
Keep under 160 characters. Use natural Hinglish."""
        else:
            if message_type == "reauth":
                prompt = f"""Write a short Hinglish SMS asking customer to re-authorize a failed subscription.
Merchant: {merchant}, Amount: ₹{amount_inr:.2f}. Include {{payment_link}}. Under 160 chars."""
            elif message_type == "update_instrument":
                prompt = f"""Write a short Hinglish SMS asking customer to update their payment method.
Merchant: {merchant}, Amount: ₹{amount_inr:.2f}. Include {{payment_link}}. Under 160 chars."""
            else:
                prompt = f"""Write a short, polite Hinglish payment reminder SMS.
Merchant: {merchant}, Amount: ₹{amount_inr:.2f}. Include {{payment_link}}. Under 160 chars. Natural Hinglish."""
        
        result = self.complete(prompt, temperature=0.7, max_tokens=100)
        if not result:
            # Fallback canned template
            if event_type == "checkout_abandoned":
                return f"Namaste {customer}, aapka cart ₹{amount_inr:.2f} ka pending hai. Complete karne ke liye link: {{payment_link}}"
            elif message_type == "reauth":
                return f"Namaste {customer}, aapka {merchant} subscription ₹{amount_inr:.2f} fail ho gaya. Re-authorize: {{payment_link}}"
            else:
                return f"Namaste {customer}, aapka {merchant} payment ₹{amount_inr:.2f} pending hai. Pay now: {{payment_link}}"
        return result.strip()

    def generate_voice_script(self, state: Dict[str, Any]) -> str:
        """Generate a 20-second Hinglish voice call script."""
        amount_inr = state.get("amount_paise", 0) / 100.0
        merchant = state.get("merchant_name", "Merchant")
        customer = state.get("customer_name", "Customer")
        prompt = f"""Write a natural 20-second Hinglish voice call script for payment recovery.
Context: Merchant: {merchant}, Customer: {customer}, Amount: ₹{amount_inr:.2f}
Style: warm, understanding, one clear ask (pay now via link or promise a date).
Use Hinglish (Roman Hindi + English). Max 3 sentences."""
        result = self.complete(prompt, temperature=0.8, max_tokens=150)
        if not result:
            return f"Namaste {customer}, main {merchant} se bol rahi hoon. Aapka payment ₹{amount_inr:.2f} fail ho gaya hai. Kya main aapko payment link bhej doon?"
        return result.strip()

    def parse_customer_response(self, text: str) -> Dict[str, Any]:
        """Parse customer's spoken/written reply into structured outcome."""
        normalized = text.lower().strip()
        if any(token in normalized for token in ("stop calling", "mat call karo", "unsubscribe", "band karo")):
            return {"type": "do_not_contact", "date": None, "confidence": 0.95}
        if any(token in normalized for token in ("5 tarikh", "pay on", "de dunga", "kar dunga", "will pay")):
            from datetime import date, timedelta
            promised_date = date.today() + timedelta(days=5)
            return {"type": "promised", "date": promised_date.isoformat(), "confidence": 0.9}
        if any(token in normalized for token in ("paid now", "abhi pay", "already paid")):
            return {"type": "paid_now", "date": None, "confidence": 0.9}
        prompt = f"""Parse this customer response to a payment reminder.
Response: "{text}"
Classify into:
- promised: customer promises to pay on a date. Extract date if possible (YYYY-MM-DD).
- paid_now: customer says will pay now / already paid
- refused: refuses to pay
- no_answer: no response or wrong person
- do_not_contact: asks to stop calling

Return JSON: {{"type": "...", "date": "YYYY-MM-DD" or null, "confidence": 0.0-1.0}}"""
        result = self.complete(prompt, temperature=0.0, max_tokens=150, json_mode=True)
        if not result:
            return {"type": "no_answer", "date": None, "confidence": 0.0}
        try:
            data = json.loads(result)
            if data.get("type") not in ["promised", "paid_now", "refused", "no_answer", "do_not_contact"]:
                data["type"] = "no_answer"
            return data
        except:
            return {"type": "no_answer", "date": None, "confidence": 0.0}

# Singleton
llm_service = LLMService()