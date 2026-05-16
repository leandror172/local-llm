#!/usr/bin/env python3
"""
Analyze verdicts from ollama-bridge calls for patterns and insights.

Verdict scale: 2 = accepted · 1 = improved · 0 = rejected

Usage:
  ./ollama-verdicts.py              # All verdicts with reasons
  ./ollama-verdicts.py 2            # Show only accepted verdicts
  ./ollama-verdicts.py 1            # Show only improved verdicts
  ./ollama-verdicts.py 0            # Show only rejected verdicts
  ./ollama-verdicts.py --summary    # Stats only
  ./ollama-verdicts.py --hints      # Common failure patterns
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

LOG_FILE = Path.home() / '.local/share/ollama-bridge/calls.jsonl'

def load_verdicts():
    """Load verdict records from log."""
    verdicts = []
    if not LOG_FILE.exists():
        print(f"Error: {LOG_FILE} not found", file=sys.stderr)
        sys.exit(1)

    with open(LOG_FILE, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    record = json.loads(line)
                    if record.get('type') == 'verdict':
                        verdicts.append(record)
                except json.JSONDecodeError:
                    pass
    return verdicts

def print_summary(verdicts):
    """Print verdict statistics."""
    verdict_counts = defaultdict(int)
    token_est = defaultdict(list)

    for v in verdicts:
        verdict = v.get('verdict', 'unknown')
        verdict_counts[verdict] += 1
        est = v.get('est_claude_tokens', 0)
        if est:
            token_est[verdict].append(est)

    print("=== VERDICT SUMMARY ===\n")
    print(f"Total evaluated: {len(verdicts)}\n")

    _label = {2: 'accepted', 1: 'improved', 0: 'rejected'}
    for verdict in [2, 1, 0]:
        count = verdict_counts[verdict]
        pct = count / len(verdicts) * 100 if verdicts else 0
        avg_tokens = sum(token_est[verdict]) / len(token_est[verdict]) if token_est[verdict] else 0
        print(f"{verdict} ({_label[verdict]}):  {count:3} ({pct:5.1f}%)  avg tokens: {avg_tokens:6.0f}")

def print_all_verdicts(verdicts, filter_type=None):
    """Print all verdicts with details."""
    print(f"\n=== ALL VERDICTS ({len(verdicts)} total) ===\n")

    for i, v in enumerate(verdicts, 1):
        verdict = v.get('verdict', 'unknown')
        if filter_type and verdict != filter_type:
            continue

        _label = {2: 'accepted', 1: 'improved', 0: 'rejected'}
        print(f"{i}. [{verdict} ({_label.get(verdict, verdict)})] {v.get('ts', 'unknown')[:10]}")
        print(f"   Hash: {v.get('prompt_hash', 'unknown')}")
        if 'reason' in v:
            reason = v['reason']
            # Wrap long reasons
            if len(reason) > 70:
                print(f"   Reason: {reason[:70]}...")
            else:
                print(f"   Reason: {reason}")
        if 'est_claude_tokens' in v:
            print(f"   Est. tokens: {v['est_claude_tokens']}")
        print()

def find_patterns(verdicts):
    """Find common patterns in rejections."""
    print("\n=== REJECTION PATTERNS ===\n")

    rejected = [v for v in verdicts if v.get('verdict') == 0]
    if not rejected:
        print("No rejections yet!")
        return

    # Extract keywords from reasons
    keywords = defaultdict(int)
    for v in rejected:
        reason = (v.get('reason') or '').lower()
        for keyword in ['logic', 'error', 'type', 'syntax', 'incomplete', 'wrong', 'missing', 'incorrect']:
            if keyword in reason:
                keywords[keyword] += 1

    print(f"Total rejections: {len(rejected)}\n")
    if keywords:
        print("Common failure reasons:")
        for keyword, count in sorted(keywords.items(), key=lambda x: -x[1]):
            pct = count / len(rejected) * 100
            print(f"  {keyword:15} {count} ({pct:.0f}%)")

def main():
    verdicts = load_verdicts()

    if not verdicts:
        print("No verdicts found in log yet.", file=sys.stderr)
        sys.exit(1)

    args = sys.argv[1:]

    if '--summary' in args:
        print_summary(verdicts)
    elif '--hints' in args:
        find_patterns(verdicts)
    elif args and args[0] in ['0', '1', '2']:
        print_summary(verdicts)
        print_all_verdicts(verdicts, filter_type=int(args[0]))
    else:
        print_summary(verdicts)
        print_all_verdicts(verdicts)

if __name__ == '__main__':
    main()
