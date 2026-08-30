"""
Train the recovery probability ranker on synthetic data.
"""

import argparse
import pickle
import pandas as pd
from pathlib import Path
from data.synthetic_generator import SyntheticGenerator
from models.ranker_model import RecoveryRanker
from config.settings import settings
from config.logger import logger

FEATURES = [
    "amount_paise",
    "day_of_month",
    "cycle_number",
    "prior_broken_ptps",
    "customer_tenure_days",
    "last_success_days_ago",
    "is_funds_class",
    "is_downtime_class",
    "is_mandate_dead",
    "is_instrument_dead",
    "is_limit_class",
    "attempts_so_far",
    "has_prior_contact",
]

def event_to_features(event: dict) -> dict:
    """Convert a raw event dict to ranker features."""
    class_name = event.get("ground_truth_class", "")
    return {
        "amount_paise": event.get("amount_paise", 0),
        "day_of_month": 15,  # placeholder, could derive from created_at
        "cycle_number": event.get("cycle", 0),
        "prior_broken_ptps": 0,  # placeholder, would need customer history
        "customer_tenure_days": 365,  # placeholder
        "last_success_days_ago": 30,  # placeholder
        "is_funds_class": 1 if class_name == "funds" else 0,
        "is_downtime_class": 1 if class_name == "downtime" else 0,
        "is_mandate_dead": 1 if class_name == "mandate_dead" else 0,
        "is_instrument_dead": 1 if class_name == "instrument_dead" else 0,
        "is_limit_class": 1 if class_name == "limit" else 0,
        "attempts_so_far": 0,  # initial attempts are zero
        "has_prior_contact": 0,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=1000, help="Number of training samples")
    parser.add_argument("--output", type=str, default="models/saved_models/ranker.pkl", help="Model save path")
    args = parser.parse_args()

    logger.info("Generating training data...")
    generator = SyntheticGenerator(seed=123)
    events = generator.generate_batch(size=args.size)

    X_list = []
    y_list = []
    for ev in events:
        # For training, we only use failed payment events (not checkout)
        if ev.get("event_type") == "failed_payment":
            feat = event_to_features(ev)
            X_list.append(feat)
            y_list.append(1 if ev.get("ground_truth_recoverable") else 0)

    X = pd.DataFrame(X_list)
    y = pd.Series(y_list)

    logger.info(f"Training ranker on {len(X)} samples...")
    ranker = RecoveryRanker()
    ranker.train(X, y)

    # Save model
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(ranker, f)
    logger.info(f"Model saved to {output_path}")

if __name__ == "__main__":
    main()