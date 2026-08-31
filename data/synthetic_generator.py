"""
Synthetic data generator for Aarohan-X.
Creates a realistic mixed batch of failed payments and checkout abandonments with ground truth.
"""

import random
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from config.settings import settings

class SyntheticGenerator:
    def __init__(self, seed=42):
        random.seed(seed)

    def generate_batch(self, size=150, output_path=None):
        events = []
        classes = {
            "funds": 35,
            "downtime": 20,
            "mandate_dead": 15,
            "instrument_dead": 10,
            "customer_cancel": 10,
            "risk": 8,
            "limit": 7,
            "checkout_abandoned": 20,
            "unknown_messy": 15,
        }
        event_counter = 0
        for class_name, count in classes.items():
            for _ in range(count):
                event_counter += 1
                event = self._create_event(event_counter, class_name)
                events.append(event)
        if output_path:
            self._save_to_csv(events, output_path)
        return events

    def _create_event(self, idx, class_name):
        event_id = f"EVT_{idx:04d}"
        if class_name == "checkout_abandoned":
            return self._make_checkout_event(event_id, idx)
        else:
            return self._make_failed_payment_event(event_id, idx, class_name)

    def _make_failed_payment_event(self, event_id, idx, class_name):
        amount = random.choice([19900, 49900, 99900, 199900, 499900])
        failure_code, failure_desc = self._get_failure_details(class_name)
        if class_name == "funds":
            recoverable = random.random() < 0.6
        elif class_name == "downtime":
            recoverable = random.random() < 0.7
        elif class_name == "mandate_dead":
            recoverable = random.random() < 0.3
        elif class_name == "instrument_dead":
            recoverable = random.random() < 0.2
        else:
            recoverable = False
        return {
            "event_id": event_id,
            "event_type": "failed_payment",
            "merchant_id": f"merchant_{random.randint(1,5):03d}",
            "merchant_name": random.choice(["Netflix India", "Spotify", "Hotstar", "GymFlex", "EMI Card"]),
            "customer_id": f"cust_{random.randint(1,100):03d}",
            "customer_phone": f"+91{random.randint(7000000000, 9999999999)}",
            "customer_name": f"Customer {idx}",
            "amount_paise": amount,
            "currency": "INR",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "mandate_id": f"mandate_{random.randint(1,50):03d}",
            "cycle": random.randint(1,12),
            "original_failure_code": failure_code,
            "original_failure_desc": failure_desc,
            "cart_id": None,
            "cart_value_paise": None,
            "time_since_abandonment_minutes": None,
            "return_visit_signal": False,
            "discount_eligible": False,
            "ground_truth_recoverable": recoverable,
            "ground_truth_class": class_name if class_name != "unknown_messy" else random.choice(["funds", "downtime", "limit"]),
        }

    def _make_checkout_event(self, event_id, idx):
        cart_value = random.choice([99900, 149900, 299900, 599900])
        time_since = random.randint(5, 1440)
        return_visit = random.random() < 0.3
        recoverable = return_visit and time_since < 60
        return {
            "event_id": event_id,
            "event_type": "checkout_abandoned",
            "merchant_id": f"merchant_{random.randint(1,5):03d}",
            "merchant_name": random.choice(["Myntra", "Amazon", "Flipkart", "Nykaa"]),
            "customer_id": f"cust_{random.randint(1,100):03d}",
            "customer_phone": f"+91{random.randint(7000000000, 9999999999)}",
            "customer_name": f"Customer {idx}",
            "amount_paise": cart_value,
            "currency": "INR",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "mandate_id": None,
            "cycle": None,
            "original_failure_code": None,
            "original_failure_desc": None,
            "cart_id": f"cart_{idx}",
            "cart_value_paise": cart_value,
            "time_since_abandonment_minutes": time_since,
            "return_visit_signal": return_visit,
            "discount_eligible": random.random() < 0.5,
            "ground_truth_recoverable": recoverable,
            "ground_truth_class": "abandoned",
        }

    def _get_failure_details(self, class_name):
        mapping = {
            "funds": ("BAD_REQUEST", "Insufficient funds in customer account"),
            "downtime": ("BAD_REQUEST", "Payment timed out at bank gateway"),
            "mandate_dead": ("BAD_REQUEST", "Mandate has been revoked by customer"),
            "instrument_dead": ("BAD_REQUEST", "Card has expired"),
            "customer_cancel": ("BAD_REQUEST", "Payment cancelled by user"),
            "risk": ("BAD_REQUEST", "Transaction flagged for risk review"),
            "limit": ("BAD_REQUEST", "Daily UPI limit exceeded for customer"),
            "unknown_messy": ("BAD_REQUEST", random.choice([
                "UPI txn failed due to 05 error at NPCI",
                "DEEMED_APPROVAL_FAILED at issuer end",
                "Customer bank not responding to debit request",
                "Technical decline from acquiring bank",
                "RBI mandate validation failed"
            ])),
        }
        return mapping.get(class_name, ("BAD_REQUEST", "Unknown failure"))

    def _save_to_csv(self, events, path):
        # Collect union of all keys
        fieldnames = []
        for ev in events:
            for k in ev.keys():
                if k not in fieldnames:
                    fieldnames.append(k)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for ev in events:
                # Fill missing keys with empty string
                writer.writerow({k: ev.get(k, '') for k in fieldnames})