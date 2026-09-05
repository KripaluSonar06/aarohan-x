"""Compare recovery strategies on the configured five-event evaluation sample."""

import argparse
import csv
import json
from pathlib import Path

from core.orchestrator import BatchOrchestrator


STRATEGIES = ("silent_retry_only", "ladder", "contact_first")


def load_events(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        events = []
        for row in reader:
            row["amount_paise"] = int(row["amount_paise"])
            row["strategy"] = "ladder"
            row["simulation_mode"] = True
            events.append(row)
        return events[:5]


def run_experiments(input_path: Path) -> dict:
    events = load_events(input_path)
    results = {}
    for strategy in STRATEGIES:
        configured = [dict(event, strategy=strategy) for event in events]
        results[strategy] = BatchOrchestrator().run_batch(configured)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="scripts/data/batch_150.csv")
    parser.add_argument("--output", default="scripts/data/experiment_results.json")
    args = parser.parse_args()
    results = run_experiments(Path(args.input))
    Path(args.output).write_text(json.dumps(results, indent=2))
    for strategy, metrics in results.items():
        recovered = metrics["gross_recovered_paise"] / 100
        print(f"{strategy}: recovered INR {recovered:.2f}, events={metrics['events_recovered']}, "
              f"cost=INR {metrics['contact_cost_inr']:.2f}")


if __name__ == "__main__":
    main()
