"""
Run the Aarohan-X recovery batch on synthetic data.
Loads CSV, invokes orchestrator, prints metrics, and saves results.
"""

import argparse
import csv
import json
from pathlib import Path
from core.orchestrator import orchestrator
from config.logger import logger

def load_events(csv_path: Path) -> list:
    """Load events from CSV file."""
    events = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['amount_paise'] = int(row['amount_paise'])
            if row.get('cart_value_paise'):
                row['cart_value_paise'] = int(row['cart_value_paise'])
            if row.get('time_since_abandonment_minutes'):
                row['time_since_abandonment_minutes'] = int(row['time_since_abandonment_minutes'])
            if 'return_visit_signal' in row:
                row['return_visit_signal'] = row['return_visit_signal'].lower() == 'true'
            if 'discount_eligible' in row:
                row['discount_eligible'] = row['discount_eligible'].lower() == 'true'
            events.append(row)
    return events

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="data/batch_150.csv", help="Input CSV path")
    parser.add_argument("--output", type=str, default="data/evaluation_results.json", help="Output JSON for metrics")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file {input_path} not found. Run generate_batch.py first.")
        return

    events = load_events(input_path)
    logger.info(f"Loaded {len(events)} events from {input_path}")

    results = orchestrator.run_batch(events)

    # Print summary
    print("\n" + "="*50)
    print("AAROHAN-X BATCH RESULTS")
    print("="*50)
    print(f"Total events: {results['total_events']}")
    print(f"Total at-risk ₹: {results['total_at_risk_paise']/100:.2f}")
    print(f"Gross recovered ₹: {results['gross_recovered_paise']/100:.2f}")
    print(f"Contact cost ₹: {results['contact_cost_inr']:.2f}")
    print(f"Net recovered ₹: {results['net_recovered_paise']/100:.2f}")
    print(f"Recovered events: {results['events_recovered']}")
    print(f"Stopped events: {results['events_stopped']}")
    print(f"Escalated events: {results['events_escalated']}")
    print(f"Wasted contacts: {results['wasted_contacts']}")
    print(f"Broken PTPs: {results['broken_ptps']}")
    print("="*50)

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()