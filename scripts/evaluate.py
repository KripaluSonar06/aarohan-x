"""
Compute additional evaluation metrics from batch results.
Assumes run_batch.py has already generated evaluation_results.json.
"""

import json
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=str, default="data/evaluation_results.json", help="Path to results JSON")
    args = parser.parse_args()

    results_path = Path(args.results)
    if not results_path.exists():
        print("Run run_batch.py first.")
        return

    with open(results_path) as f:
        results = json.load(f)

    total_at_risk = results["total_at_risk_paise"]
    gross_recovered = results["gross_recovered_paise"]
    net_recovered = results["net_recovered_paise"]

    gross_rate = (gross_recovered / total_at_risk * 100) if total_at_risk else 0
    net_rate = (net_recovered / total_at_risk * 100) if total_at_risk else 0

    print("\n--- Evaluation Metrics ---")
    print(f"Gross recovery rate: {gross_rate:.1f}%")
    print(f"Net recovery rate: {net_rate:.1f}%")
    print(f"Wasted contacts: {results['wasted_contacts']}")
    print(f"Broken PTPs: {results['broken_ptps']}")
    print(f"Events recovered: {results['events_recovered']}")
    print(f"Events stopped: {results['events_stopped']}")

    # Placeholder for incremental lift: assumes baseline natural recovery = 40% of at-risk
    # In a real evaluation, you'd run a control group.
    natural_recovery_paise = int(total_at_risk * 0.40)
    incremental = gross_recovered - natural_recovery_paise
    print(f"Estimated incremental recovery (vs 40% natural): ₹{incremental/100:.2f}")

if __name__ == "__main__":
    main()