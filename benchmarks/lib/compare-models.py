#!/usr/bin/env python3
"""
compare-models.py — Send the same prompt to multiple Ollama models and display results.

Designed for Layer 5+ multi-model comparison: generates (prompt, response_A, response_B)
pairs that feed directly into the Layer 7 DPO fine-tuning pipeline.

Usage (via wrapper — do not call directly):
  benchmarks/lib/run-compare-models.sh --models my-go-q3,my-go-q25c14 --prompt "Write a Go HTTP handler"
  benchmarks/lib/run-compare-models.sh --models my-go-q3,my-go-q25c14,my-go-q3-30b --prompt-file prompts/go-01.md
  benchmarks/lib/run-compare-models.sh --models my-go-q3,my-go-q25c14 --prompt-file prompts/go-01.md --no-verdict

Verdicts:
  After each pair, you are asked to rate each response:
    A — ACCEPTED (used as-is)
    I — IMPROVED (used with modifications — describe changes)
    R — REJECTED (not usable — describe failure)
  These are written to stdout and optionally to a results file for DPO pair extraction.
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Allow import from personas/lib without installing
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "personas" / "lib"))

from ollama_client import ollama_chat

SEPARATOR = "─" * 72
THICK_SEP = "═" * 72

# Default comparison prompts for quick smoke-testing
DEFAULT_PROMPTS = {
    "go-struct": (
        "Write a Go struct `ExpenseRecord` with fields: "
        "ID (string), Amount (float64), Currency (string), "
        "Description (string), Category (string), Date (time.Time). "
        "Include a constructor `NewExpenseRecord` that validates Amount > 0 "
        "and returns an error if invalid."
    ),
    "go-http": (
        "Write a Go HTTP handler function `HandleClassify` that reads a JSON body "
        "with field `description` (string), calls a local function "
        "`classifyExpense(ctx context.Context, desc string) (string, error)`, "
        "and returns the category as JSON `{\"category\": \"...\"}` or a 500 error."
    ),
}


def parse_args():
    p = argparse.ArgumentParser(
        description="Compare same prompt across multiple Ollama models."
    )
    p.add_argument(
        "--models",
        required=True,
        help="Comma-separated list of Ollama model names (e.g. my-go-q3,my-go-q25c14)",
    )
    p.add_argument("--prompt", help="Prompt text (inline)")
    p.add_argument("--prompt-file", help="Path to .md or .txt prompt file")
    p.add_argument(
        "--preset",
        choices=list(DEFAULT_PROMPTS.keys()),
        help="Use a built-in comparison prompt preset",
    )
    p.add_argument(
        "--no-verdict",
        action="store_true",
        help="Skip interactive verdict collection (output-only mode)",
    )
    p.add_argument(
        "--think",
        action="store_true",
        default=False,
        help="Enable Qwen3 thinking mode (slower, may improve quality)",
    )
    p.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Per-model timeout in seconds (default: 300 — allow for 30B hybrid loading)",
    )
    p.add_argument(
        "--output",
        help="Optional JSON file to append results to (for DPO pair extraction)",
    )
    return p.parse_args()


def load_prompt(args) -> str:
    if args.prompt:
        return args.prompt.strip()
    if args.prompt_file:
        text = Path(args.prompt_file).read_text().strip()
        # Strip YAML frontmatter if present
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end != -1:
                text = text[end + 4:].strip()
        return text
    if args.preset:
        return DEFAULT_PROMPTS[args.preset]
    print("ERROR: provide --prompt, --prompt-file, or --preset", file=sys.stderr)
    sys.exit(1)


def query_model(model: str, prompt: str, think: bool, timeout: int) -> dict:
    """Call model, return result dict with content + timing + metadata.

    Uses keep_alive="0" so each model evicts from VRAM after responding,
    giving the next model a clean 12GB to work with.
    """
    start = time.monotonic()
    try:
        result = ollama_chat(prompt, model=model, think=think, timeout=timeout, keep_alive="0")
        elapsed = time.monotonic() - start
        tokens = result.get("eval_count", 0)
        tok_s = tokens / (result.get("total_duration_ms", 1) / 1000) if tokens else 0
        return {
            "model": model,
            "content": result["content"],
            "tokens": tokens,
            "elapsed_s": round(elapsed, 1),
            "tok_s": round(tok_s, 1),
            "error": None,
        }
    except Exception as e:
        elapsed = time.monotonic() - start
        return {
            "model": model,
            "content": "",
            "tokens": 0,
            "elapsed_s": round(elapsed, 1),
            "tok_s": 0.0,
            "error": str(e),
        }


def collect_verdict(model: str, response: str, index: int) -> dict:
    """Interactively collect verdict for a single model response."""
    print(f"\n  Verdict for Model {index} ({model}):")
    print("    [A] ACCEPTED  — used as-is")
    print("    [I] IMPROVED  — used with modifications")
    print("    [R] REJECTED  — not usable")
    print()

    while True:
        choice = input("  Your verdict (A/I/R): ").strip().upper()
        if choice in ("A", "I", "R"):
            break
        print("  Please enter A, I, or R.")

    verdict_map = {"A": "ACCEPTED", "I": "IMPROVED", "R": "REJECTED"}
    verdict = verdict_map[choice]

    note = ""
    if choice in ("I", "R"):
        note = input(f"  Notes ({verdict}): ").strip()

    return {"verdict": verdict, "note": note}


def print_response(result: dict, index: int):
    """Print a single model's response with header."""
    model = result["model"]
    print(f"\n{THICK_SEP}")
    if result["error"]:
        print(f"  MODEL {index}: {model}  [ERROR]")
        print(THICK_SEP)
        print(f"\n  ✗ {result['error']}")
        print(f"  Elapsed: {result['elapsed_s']}s")
    else:
        print(
            f"  MODEL {index}: {model}  "
            f"[{result['tokens']} tokens · {result['tok_s']} tok/s · {result['elapsed_s']}s]"
        )
        print(THICK_SEP)
        print()
        print(result["content"])


def main():
    args = parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    prompt = load_prompt(args)

    print(f"\n{THICK_SEP}")
    print("  MULTI-MODEL COMPARISON")
    print(THICK_SEP)
    print(f"  Models:  {' | '.join(models)}")
    print(f"  Think:   {args.think}")
    print(f"  Timeout: {args.timeout}s per model")
    print(f"\n  PROMPT:\n")
    # Indent prompt for readability
    for line in prompt.splitlines():
        print(f"    {line}")
    print(f"\n{SEPARATOR}")
    print("  Querying models... (sequential to avoid VRAM contention)")

    results = []
    for i, model in enumerate(models, start=1):
        print(f"\n  [{i}/{len(models)}] Calling {model} ...", end="", flush=True)
        result = query_model(model, prompt, args.think, args.timeout)
        results.append(result)
        if result["error"]:
            print(f" ERROR: {result['error']}")
        else:
            print(f" done ({result['elapsed_s']}s, {result['tok_s']} tok/s)")

    # Display all responses
    for i, result in enumerate(results, start=1):
        print_response(result, i)

    print(f"\n{THICK_SEP}")
    print("  END OF RESPONSES")
    print(THICK_SEP)

    # Collect verdicts
    verdicts = []
    if not args.no_verdict and sys.stdin.isatty():
        print("\n  — VERDICT COLLECTION —")
        print("  Rate each response for DPO training data collection.")
        for i, result in enumerate(results, start=1):
            if result["error"]:
                verdict = {"verdict": "REJECTED", "note": f"Error: {result['error']}"}
            else:
                verdict = collect_verdict(result["model"], result["content"], i)
            verdicts.append(verdict)

        # Summary
        print(f"\n{SEPARATOR}")
        print("  SUMMARY")
        print(SEPARATOR)
        for i, (result, verdict) in enumerate(zip(results, verdicts), start=1):
            status = "ERROR" if result["error"] else f"{result['tok_s']} tok/s"
            v = verdict["verdict"]
            note = f" — {verdict['note']}" if verdict.get("note") else ""
            print(f"  Model {i}: {result['model']:<30} {status:<18} {v}{note}")

    # Write output file
    run_record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prompt": prompt,
        "think": args.think,
        "results": [
            {
                **r,
                "verdict": verdicts[i]["verdict"] if i < len(verdicts) else None,
                "verdict_note": verdicts[i]["note"] if i < len(verdicts) else None,
            }
            for i, r in enumerate(results)
        ],
    }

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "a") as f:
            f.write(json.dumps(run_record) + "\n")
        print(f"\n  Results appended to: {args.output}")

    # Always print machine-readable summary to stdout for piping
    print(f"\n{SEPARATOR}")
    print(json.dumps(run_record, indent=2))


if __name__ == "__main__":
    main()
