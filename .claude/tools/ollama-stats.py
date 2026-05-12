#!/usr/bin/env python3
"""
Analyze ollama-bridge calls log for DPO evaluation progress.

Usage:
  ./ollama-stats.py                # Summary of all calls
  ./ollama-stats.py --by-model     # Breakdown by model
  ./ollama-stats.py --verdicts     # Verdict distribution
  ./ollama-stats.py --all          # All reports
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

LOG_FILE = Path.home() / '.local/share/ollama-bridge/calls.jsonl'

def load_calls():
    """Load and parse all JSONL records."""
    calls = []
    if not LOG_FILE.exists():
        print(f"Error: {LOG_FILE} not found", file=sys.stderr)
        sys.exit(1)

    with open(LOG_FILE, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    calls.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return calls

def summary(calls):
    """Print overall summary."""
    call_records = [c for c in calls if c.get('type') != 'verdict']
    verdict_records = [c for c in calls if c.get('type') == 'verdict']

    print("=== OLLAMA-BRIDGE CALLS SUMMARY ===\n")
    print(f"Total records:     {len(calls)}")
    print(f"Call records:      {len(call_records)}")
    print(f"Verdict records:   {len(verdict_records)}")
    print(f"Verdict coverage:  {len(verdict_records)/len(call_records)*100:.1f}%")

    # Date range
    dates = [c.get('ts', '')[:10] for c in calls if c.get('ts')]
    if dates:
        print(f"Date range:        {min(dates)} to {max(dates)}")

def by_model(calls):
    """Print model usage breakdown."""
    call_records = [c for c in calls if c.get('type') != 'verdict']
    model_counts = defaultdict(int)

    for record in call_records:
        model = record.get('model', 'unknown')
        model_counts[model] += 1

    print("\n=== MODELS BY USAGE ===\n")
    total = len(call_records)
    for model, count in sorted(model_counts.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        print(f"{model:25} {count:3} calls ({pct:5.1f}%)")

def verdicts(calls):
    """Print verdict distribution."""
    verdict_records = [c for c in calls if c.get('type') == 'verdict']
    verdict_counts = defaultdict(int)

    for record in verdict_records:
        verdict = record.get('verdict', 'unknown')
        verdict_counts[verdict] += 1

    print("\n=== VERDICT DISTRIBUTION ===\n")
    print(f"Total evaluated:   {len(verdict_records)}")

    for verdict in ['ACCEPTED', 'IMPROVED', 'REJECTED']:
        count = verdict_counts[verdict]
        pct = count / len(verdict_records) * 100 if verdict_records else 0
        print(f"{verdict:10}  {count:3} ({pct:5.1f}%)")

def main():
    calls = load_calls()

    args = sys.argv[1:]
    if not args or '--all' in args:
        summary(calls)
        by_model(calls)
        verdicts(calls)
    else:
        if '--verdicts' in args:
            verdicts(calls)
        if '--by-model' in args:
            by_model(calls)

if __name__ == '__main__':
    main()
