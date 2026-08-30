"""
Generate synthetic batch data for Aarohan-X.
Creates a mix of failed payments and checkout abandonments with ground truth.
"""

import argparse
from pathlib import Path
from data.synthetic_generator import SyntheticGenerator

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic recovery events.")
    parser.add_argument("--size", type=int, default=150, help="Number of events to generate")
    parser.add_argument("--output", type=str, default="data/batch_150.csv", help="Output CSV path")
    parser.add_argument("--json", action="store_true", help="Also output JSON")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generator = SyntheticGenerator(seed=42)
    events = generator.generate_batch(size=args.size, output_path=output_path)

    print(f"Generated {len(events)} events.")
    print(f"Saved to {output_path}")

    if args.json:
        import json
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump(events, f, indent=2)
        print(f"Also saved to {json_path}")

if __name__ == "__main__":
    main()