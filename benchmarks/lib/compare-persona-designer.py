#!/usr/bin/env python3
"""
compare-persona-designer.py — Compare persona designer quality across models.

Runs the same test descriptions through multiple designer backends and generates
a side-by-side quality report, useful for evaluating the cost/benefit of upgrading
from qwen3:8b to qwen3:14b or using a Claude frontier model as the designer.

Models tested (by default):
  - my-persona-designer-q3  (qwen3:8b via persona, 16K ctx, ~51 tok/s)
  - qwen3:14b               (direct, 4K ctx, ~32 tok/s)
  - claude-haiku-4-5-20251001
  - claude-sonnet-4-6

Usage:
  benchmarks/compare-persona-designer.sh
  benchmarks/compare-persona-designer.sh --skip-claude
  benchmarks/compare-persona-designer.sh --skip-14b
  benchmarks/compare-persona-designer.sh --verbose
  benchmarks/compare-persona-designer.sh --cases benchmarks/prompts/persona-designer-test-cases.txt
"""

import argparse
import importlib.util
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────

SCRIPT_DIR  = Path(__file__).resolve().parent        # benchmarks/lib/
REPO_ROOT   = SCRIPT_DIR.parent.parent               # repo root
PERSONAS_DIR = REPO_ROOT / "personas"
PROMPTS_DIR  = REPO_ROOT / "benchmarks" / "prompts"
RESULTS_DIR  = REPO_ROOT / "benchmarks" / "results"

DEFAULT_CASES_FILE = PROMPTS_DIR / "persona-designer-test-cases.txt"

# ─── Import helpers from build-persona.py ─────────────────────────────────────
# build-persona.py has a hyphen in its name → importlib required.
# We need build_initial_prompt() to give all models the same engineered prompt,
# and PERSONA_SPEC_SCHEMA for Ollama structured output enforcement.

sys.path.insert(0, str(PERSONAS_DIR))  # lets "from lib.X" and "from models" work

_bp_spec = importlib.util.spec_from_file_location(
    "build_persona", PERSONAS_DIR / "build-persona.py"
)
_bp_mod = importlib.util.module_from_spec(_bp_spec)
_bp_spec.loader.exec_module(_bp_mod)

build_initial_prompt = _bp_mod.build_initial_prompt
PERSONA_SPEC_SCHEMA  = _bp_mod.PERSONA_SPEC_SCHEMA

from lib.ollama_client import ollama_chat  # noqa: E402 (after sys.path setup)

# ─── Model registry ───────────────────────────────────────────────────────────

OLLAMA_MODELS = [
    {"id": "my-persona-designer-q3", "label": "8b-persona"},
    {"id": "qwen3:14b",              "label": "14b-direct"},
]

CLAUDE_MODELS = [
    {"id": "claude-haiku-4-5-20251001", "label": "haiku"},
    {"id": "claude-sonnet-4-6",         "label": "sonnet"},
]

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# System prompt for Claude: ask for JSON, but don't over-constrain the instruction-following.
# Claude receives the full build_initial_prompt() text (same as Ollama), so the detailed
# instructions and examples are already in the user message.
CLAUDE_SYSTEM = (
    "You are an AI persona specification designer for Ollama language models. "
    "When given a description, return ONLY a valid JSON object — no prose, no markdown fences. "
    "Follow the schema and instructions in the user message exactly."
)

# ─── Result helpers ───────────────────────────────────────────────────────────

def empty_result(label: str) -> dict:
    return {"label": label, "spec": None, "ms": 0, "tokens": 0, "error": None}


# ─── Ollama caller ────────────────────────────────────────────────────────────

def call_ollama(description: str, model_id: str, label: str, verbose: bool) -> dict:
    """Call an Ollama model with the engineered designer prompt."""
    prompt = build_initial_prompt(description, None)

    if verbose:
        print(
            f"\n[VERBOSE/{label}] Prompt ({len(prompt)} chars):\n"
            f"{prompt[:600]}...\n",
            file=sys.stderr,
        )

    r = empty_result(label)
    t0 = time.time()
    try:
        resp = ollama_chat(prompt, model=model_id, format_schema=PERSONA_SPEC_SCHEMA)
        r["ms"]     = (time.time() - t0) * 1000
        r["tokens"] = resp["eval_count"]
        if verbose:
            print(f"[VERBOSE/{label}] Raw response:\n{resp['content']}\n", file=sys.stderr)
        r["spec"] = json.loads(resp["content"])
    except Exception as e:
        r["ms"]    = (time.time() - t0) * 1000
        r["error"] = str(e)

    return r


# ─── Claude API caller ────────────────────────────────────────────────────────

def call_claude(description: str, model_id: str, label: str, api_key: str, verbose: bool) -> dict:
    """
    Call the Claude Messages API with the same engineered prompt Ollama receives.

    Claude doesn't support Ollama's format_schema enforcement, so we append
    an explicit JSON instruction and strip any accidental markdown fences.
    The system prompt is kept minimal — the detailed instructions are already
    in build_initial_prompt().
    """
    base_prompt = build_initial_prompt(description, None)
    prompt = base_prompt + "\n\nReturn ONLY valid JSON. No prose, no markdown fences."

    if verbose:
        print(
            f"\n[VERBOSE/{label}] Prompt ({len(prompt)} chars):\n"
            f"{prompt[:600]}...\n",
            file=sys.stderr,
        )

    r = empty_result(label)
    payload = {
        "model": model_id,
        "max_tokens": 1024,
        "system": CLAUDE_SYSTEM,
        "messages": [{"role": "user", "content": prompt}],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        CLAUDE_API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read())
        r["ms"]     = (time.time() - t0) * 1000
        r["tokens"] = body.get("usage", {}).get("output_tokens", 0)
        raw = body["content"][0]["text"]

        if verbose:
            print(f"[VERBOSE/{label}] Raw response:\n{raw}\n", file=sys.stderr)

        # Strip accidental markdown fences (defensive — Claude usually follows instructions)
        clean = raw.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            clean = "\n".join(lines[1:])
        if clean.endswith("```"):
            clean = clean[:-3]

        r["spec"] = json.loads(clean.strip())

    except urllib.error.HTTPError as e:
        r["ms"]    = (time.time() - t0) * 1000
        r["error"] = f"HTTP {e.code}: {e.read().decode()[:200]}"
    except Exception as e:
        r["ms"]    = (time.time() - t0) * 1000
        r["error"] = str(e)

    return r


# ─── Report printer ───────────────────────────────────────────────────────────

W = 72  # report width


def print_case_report(results: list[dict]) -> None:
    """Print one test case: standard fields table + per-model constraint lists + timing."""
    labels = [r["label"] for r in results]

    # Standard fields table
    col_w = max(14, (W - 24) // len(labels))
    header = f"  {'Field':<22}" + "".join(f"│ {lb:<{col_w}}" for lb in labels)
    print(header)
    print("  " + "─" * 22 + ("┼─" + "─" * col_w) * len(labels))

    for field in ("persona_name", "domain", "temperature", "tier"):
        vals = []
        for r in results:
            if r["spec"]:
                v = str(r["spec"].get(field, "—"))
            else:
                v = "ERROR"
            vals.append(v[:col_w - 1])
        row = f"  {field:<22}" + "".join(f"│ {v:<{col_w}}" for v in vals)
        print(row)

    # Constraints — per-model bullet lists
    print()
    print("  Constraints:")
    for r in results:
        print(f"    [{r['label']}]")
        if r["spec"]:
            for c in r["spec"].get("constraints", []):
                print(f"      • {c}")
        else:
            print(f"      ✗ FAILED: {r['error']}")
        print()

    # Role (can be long — print separately)
    print("  Role description:")
    for r in results:
        role = r["spec"].get("role", "—") if r["spec"] else "—"
        # Wrap at ~60 chars
        print(f"    [{r['label']}] {role[:120]}")
    print()

    # Timing
    parts = []
    for r in results:
        t = f"{r['ms'] / 1000:.1f}s"
        if r["tokens"]:
            t += f"/{r['tokens']}tok"
        parts.append(f"{r['label']}={t}")
    print(f"  Timing: {' │ '.join(parts)}")


def print_full_report(all_cases: list[dict]) -> None:
    """Print the complete comparison report to stdout."""
    print()
    print("═" * W)
    print("  PERSONA DESIGNER — MODEL COMPARISON REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("═" * W)

    for i, case in enumerate(all_cases, 1):
        print()
        print("─" * W)
        print(f"  Test {i:02d}: {case['description']}")
        print("─" * W)
        print()
        print_case_report(case["results"])

    print()
    print("═" * W)
    print("  END OF REPORT")
    print("═" * W)
    print()


# ─── Test case loader ─────────────────────────────────────────────────────────

def load_test_cases(path: Path) -> list[str]:
    """Load descriptions, skipping blank lines and # comments."""
    descriptions = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                descriptions.append(line)
    return descriptions


# ─── Argument parsing ─────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Compare persona designer quality across Ollama and Claude models.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  benchmarks/compare-persona-designer.sh\n"
            "  benchmarks/compare-persona-designer.sh --skip-claude\n"
            "  benchmarks/compare-persona-designer.sh --skip-14b --verbose\n"
        ),
    )
    p.add_argument(
        "--cases", metavar="FILE", default=str(DEFAULT_CASES_FILE),
        help=f"Path to test cases file (default: persona-designer-test-cases.txt)",
    )
    p.add_argument(
        "--skip-claude", action="store_true",
        help="Skip Claude API calls (run Ollama models only).",
    )
    p.add_argument(
        "--skip-14b", action="store_true",
        help="Skip qwen3:14b (useful for a quick 8b-only run).",
    )
    p.add_argument(
        "--save-dir", metavar="DIR", default=str(RESULTS_DIR),
        help="Directory to save raw JSON results (default: benchmarks/results/).",
    )
    p.add_argument(
        "--verbose", action="store_true",
        help="Print prompts and raw LLM responses to stderr.",
    )
    return p.parse_args()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    args = parse_args()

    # Claude API key check
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not args.skip_claude and not api_key:
        print(
            "[WARN] ANTHROPIC_API_KEY not set — skipping Claude models.\n"
            "       Set it or pass --skip-claude to suppress this warning.",
            file=sys.stderr,
        )
        args.skip_claude = True

    # Load test cases
    cases_path = Path(args.cases)
    if not cases_path.exists():
        print(f"[ERROR] Test cases file not found: {cases_path}", file=sys.stderr)
        return 1
    descriptions = load_test_cases(cases_path)
    print(f"[INFO] {len(descriptions)} test cases from {cases_path.name}")

    # Build active model list
    active_ollama = [
        m for m in OLLAMA_MODELS
        if not (args.skip_14b and "14b" in m["id"])
    ]
    active_claude = [] if args.skip_claude else CLAUDE_MODELS
    all_models = [("ollama", m) for m in active_ollama] + [("claude", m) for m in active_claude]

    labels = [m["label"] for _, m in all_models]
    print(f"[INFO] Models: {', '.join(labels)}")
    print()

    # Run all (description × model) combinations
    all_cases = []
    for desc in descriptions:
        print(f"[CASE] {desc[:65]}...")
        case_results = []

        for mtype, mconf in all_models:
            label = mconf["label"]
            print(f"  → {label:<16}", end=" ", flush=True)

            if mtype == "ollama":
                r = call_ollama(desc, mconf["id"], label, args.verbose)
            else:
                r = call_claude(desc, mconf["id"], label, api_key, args.verbose)

            status = "OK" if r["spec"] else f"FAIL: {(r['error'] or '')[:35]}"
            print(f"{r['ms'] / 1000:5.1f}s  [{status}]")
            case_results.append(r)

        all_cases.append({"description": desc, "results": case_results})
        print()

    # Print formatted report
    print_full_report(all_cases)

    # Save raw JSON for later analysis
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    save_path = save_dir / f"persona-designer-compare-{ts}.json"
    with open(save_path, "w") as f:
        json.dump(all_cases, f, indent=2, default=str)
    print(f"[SAVED] {save_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
