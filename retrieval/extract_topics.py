#!/usr/bin/env python3
"""
Phase 1 topic extractor spike runner.

Runs the extraction prompt against a set of models × corpus files, records
raw results + mechanical rubric scores, and prints a summary table.

Usage:
    python3 retrieval/extract_topics.py
    python3 retrieval/extract_topics.py --model qwen3:14b
    python3 retrieval/extract_topics.py --file .memories/QUICK.md
    python3 retrieval/extract_topics.py --model qwen3:14b --file .memories/QUICK.md
    python3 retrieval/extract_topics.py --runs 3   # determinism re-runs on all combos

Output: retrieval/runs/YYYYMMDD-HHMMSS.jsonl  (one JSON object per line)
        retrieval/runs/YYYYMMDD-HHMMSS-summary.txt  (human-readable table)
"""

import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    import httpx
except ImportError:
    print("httpx not found. Install with: pip install httpx", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = Path(__file__).parent / "prompts"
RUNS_DIR = Path(__file__).parent / "runs"
OLLAMA_URL = "http://localhost:11434/api/chat"
TIMEOUT_S = 240  # generous — 14B models can be slow on large files

# Models to sweep. Each entry: model_tag → extra top-level payload keys.
# Options that go inside Ollama's "options" dict are nested under "options".
DEFAULT_MODELS = [
    "gemma3:12b",
    "qwen3:14b",
    "qwen2.5-coder:14b",
    "qwen3:8b",
]

MODEL_EXTRA_PARAMS: dict[str, dict] = {
    "qwen3:14b": {"think": False},
    "qwen3:8b": {"think": False},
}

OLLAMA_OPTIONS = {
    "num_ctx": 8192,
    "temperature": 0.1,
}

# Corpus: (repo-relative path, role label)
CORPUS: list[tuple[str, str]] = [
    ("docs/research/smart-rag-repowise.md",  "long_research_doc"),
    (".memories/QUICK.md",                   "short_memory_file"),
    ("docs/research/smart-rag-index.md",     "cross_reference_index"),
    (".claude/plan-v2.md",                   "multi_topic_plan"),
    ("personas/persona-template.md",         "structured_template"),
    (".memories/KNOWLEDGE.md",               "medium_mixed_content"),
    ("docs/ideas/smart-rag3.md",             "architectural_design_doc"),
    ("personas/build-persona.py",            "code_file"),
]

# JSON schema for Ollama format= parameter (structured output)
FORMAT_SCHEMA = {
    "type": "object",
    "properties": {
        "topics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name":        {"type": "string"},
                    "description": {"type": "string"},
                    "spans": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "minItems": 2,
                            "maxItems": 2,
                        },
                    },
                },
                "required": ["name", "description", "spans"],
            },
            "minItems": 3,
            "maxItems": 10,
        }
    },
    "required": ["topics"],
}

# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def load_prompt_template() -> str:
    path = PROMPTS_DIR / "extract.txt"
    return path.read_text(encoding="utf-8")


def build_prompt(template: str, filepath: Path, content: str) -> str:
    lines = content.splitlines()
    numbered = "\n".join(f"{i+1:4d}  {line}" for i, line in enumerate(lines))
    return template.format(
        filename=filepath.name,
        line_count=len(lines),
        content=numbered,
    )


# TODO(deferred): extract a ModelCaller Protocol so the runner isn't coupled to Ollama HTTP.
#   class ModelCaller(Protocol):
#       def __call__(self, model: str, prompt: str) -> dict: ...
#   Thread `caller: ModelCaller = call_ollama` through run_single/run_sweep.
#   Enables: Ollama HTTP, MCP bridge, OpenAI-compatible API, mock for tests.
#   See ref:deferred-infra in .claude/tasks.md.
def call_ollama(model: str, prompt: str) -> dict:
    """
    Call Ollama /api/chat with stream=False.
    Returns the full response dict or raises on network/timeout error.
    """
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "format": FORMAT_SCHEMA,
        "stream": False,
        "options": OLLAMA_OPTIONS,
    }
    for k, v in MODEL_EXTRA_PARAMS.get(model, {}).items():
        payload[k] = v

    with httpx.Client(timeout=TIMEOUT_S) as client:
        resp = client.post(OLLAMA_URL, json=payload)
        resp.raise_for_status()
        return resp.json()


def parse_topics(raw: str) -> list[dict] | None:
    """Parse the model's JSON response. Returns None if unparseable."""
    try:
        data = json.loads(raw)
        topics = data.get("topics", [])
        if not isinstance(topics, list):
            return None
        return topics
    except (json.JSONDecodeError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Rubric — mechanical dimensions only (dims 1-4, 10-11)
# Dims 5-8 (name quality, description quality, boundary sanity, mutual coverage)
# and dim 9 (determinism) require manual scoring or multiple runs.
# ---------------------------------------------------------------------------

def compute_rubric(topics: list[dict] | None, line_count: int,
                   tokens_per_sec: float) -> dict:
    if topics is None:
        return {
            "dim1_structural": False,
            "dim2_topic_count": None,
            "dim3_span_coverage": None,
            "dim4_noncontiguity_rate": None,
            "dim10_latency_tps": tokens_per_sec,
            "dim11_token_economy": None,
        }

    # Dim 1 — structural compliance
    dim1 = all(
        isinstance(t.get("name"), str) and
        isinstance(t.get("description"), str) and
        isinstance(t.get("spans"), list)
        for t in topics
    )

    # Dim 2 — topic count
    dim2 = len(topics)

    # Dim 3 — span coverage: total lines covered / file length
    covered: set[int] = set()
    for t in topics:
        for span in t.get("spans", []):
            if isinstance(span, list) and len(span) == 2:
                start, end = span
                covered.update(range(start, end + 1))
    dim3 = round(len(covered) / max(line_count, 1), 3)

    # Dim 4 — non-contiguity rate: fraction of topics with >1 span
    multi_span = sum(1 for t in topics if len(t.get("spans", [])) > 1)
    dim4 = round(multi_span / max(len(topics), 1), 3)

    return {
        "dim1_structural": dim1,
        "dim2_topic_count": dim2,
        "dim3_span_coverage": dim3,
        "dim4_noncontiguity_rate": dim4,
        "dim10_latency_tps": round(tokens_per_sec, 1),
        "dim11_token_economy": None,  # filled by caller after receiving token counts
    }


# ---------------------------------------------------------------------------
# Single run
# ---------------------------------------------------------------------------

def run_single(model: str, rel_path: str, role: str, template: str) -> dict:
    filepath = REPO_ROOT / rel_path
    if not filepath.exists():
        return _error_record(model, rel_path, role, "file_not_found", str(filepath))

    content = filepath.read_text(encoding="utf-8", errors="replace")
    line_count = content.count("\n") + 1
    char_count = len(content)
    prompt = build_prompt(template, filepath, content)

    print(f"  {model:<28} × {rel_path:<45} ... ", end="", flush=True)
    t0 = time.monotonic()
    status = "ok"
    raw_response = ""
    ollama_data: dict = {}

    try:
        ollama_data = call_ollama(model, prompt)
        raw_response = ollama_data.get("message", {}).get("content", "")
    except httpx.TimeoutException:
        status = "timeout"
        print("TIMEOUT")
    except httpx.HTTPStatusError as e:
        status = "http_error"
        raw_response = str(e)
        print(f"HTTP {e.response.status_code}")
    except Exception as e:
        status = "error"
        raw_response = str(e)
        print(f"ERROR: {e}")

    latency = time.monotonic() - t0
    prompt_tokens: int = ollama_data.get("prompt_eval_count", 0)
    output_tokens: int = ollama_data.get("eval_count", 0)
    tokens_per_sec = output_tokens / latency if latency > 0 and output_tokens > 0 else 0.0

    topics = None
    if status == "ok":
        topics = parse_topics(raw_response)
        if topics is None:
            status = "malformed_json"

    rubric = compute_rubric(topics, line_count, tokens_per_sec)
    if output_tokens > 0 and prompt_tokens > 0:
        rubric["dim11_token_economy"] = round(output_tokens / prompt_tokens, 3)

    if status == "ok":
        nc = rubric.get("dim4_noncontiguity_rate", 0) or 0
        cov = rubric.get("dim3_span_coverage", 0) or 0
        tc = rubric.get("dim2_topic_count", 0) or 0
        print(f"ok  topics={tc}  cov={cov:.0%}  noncontig={nc:.0%}  {tokens_per_sec:.1f}tok/s")
    elif status == "malformed_json":
        print("MALFORMED JSON")

    return {
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "file": rel_path,
        "file_role": role,
        "line_count": line_count,
        "char_count": char_count,
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "latency_s": round(latency, 2),
        "status": status,
        "raw_response": raw_response,
        "parsed_topics": topics,
        "rubric": rubric,
    }


def _error_record(model: str, rel_path: str, role: str,
                  status: str, msg: str) -> dict:
    print(f"  {model:<28} × {rel_path:<45} ... {status}: {msg}")
    return {
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "file": rel_path,
        "file_role": role,
        "line_count": 0,
        "char_count": 0,
        "prompt_tokens": 0,
        "output_tokens": 0,
        "latency_s": 0.0,
        "status": status,
        "raw_response": msg,
        "parsed_topics": None,
        "rubric": compute_rubric(None, 0, 0.0),
    }


# ---------------------------------------------------------------------------
# Sweep
# ---------------------------------------------------------------------------

def run_sweep(models: list[str], files: list[tuple[str, str]],
              runs_per_combo: int, template: str) -> list[dict]:
    records: list[dict] = []
    total = len(models) * len(files) * runs_per_combo
    done = 0
    for model in models:
        print(f"\nModel: {model}")
        for rel_path, role in files:
            for run_n in range(runs_per_combo):
                if runs_per_combo > 1:
                    print(f"  run {run_n+1}/{runs_per_combo}")
                record = run_single(model, rel_path, role, template)
                records.append(record)
                done += 1
    print(f"\nCompleted {done}/{total} runs.")
    return records


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save_results(records: list[dict], tag: str) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RUNS_DIR / f"{tag}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    return out_path


def print_summary(records: list[dict]) -> str:
    header = (
        f"\n{'Model':<28} {'File':<35} {'Status':<14} "
        f"{'Topics':>6} {'Cov':>5} {'NC':>5} {'TPS':>6} {'P-tok':>6} {'O-tok':>6}"
    )
    lines = [header, "-" * len(header)]

    for r in records:
        rb = r.get("rubric", {})
        tc   = rb.get("dim2_topic_count") or "-"
        cov  = f"{rb['dim3_span_coverage']:.0%}" if rb.get("dim3_span_coverage") is not None else "-"
        nc   = f"{rb['dim4_noncontiguity_rate']:.0%}" if rb.get("dim4_noncontiguity_rate") is not None else "-"
        tps  = f"{rb['dim10_latency_tps']:.1f}" if rb.get("dim10_latency_tps") else "-"
        fname = Path(r["file"]).name
        lines.append(
            f"{r['model']:<28} {fname:<35} {r['status']:<14} "
            f"{str(tc):>6} {cov:>5} {nc:>5} {tps:>6} "
            f"{r['prompt_tokens']:>6} {r['output_tokens']:>6}"
        )

    summary = "\n".join(lines)
    print(summary)
    return summary


# ---------------------------------------------------------------------------
# Manual scoring template
# ---------------------------------------------------------------------------

MANUAL_RUBRIC_TEMPLATE = """\
# Phase 1 Manual Rubric Scores
# weighted_quality = 0.35*dim5 + 0.35*dim6 + 0.20*dim7 + 0.10*dim8
# Stability bonus: +0.5 if Jaccard >= 0.85, +0.25 if >= 0.80
# Speed penalty: only if dim10_latency_tps < 15 tok/s

| run_id | model | file | dim5_name | dim6_desc | dim7_boundary | dim8_coverage | weighted_quality |
|---|---|---|---|---|---|---|---|
{rows}
"""


def print_manual_template(records: list[dict]) -> str:
    rows = []
    for r in records:
        if r["status"] == "ok":
            prefix = r["run_id"][:8]
            fname = Path(r["file"]).name
            rows.append(f"| {prefix} | {r['model']} | {fname} | - | - | - | - | - |")
    return MANUAL_RUBRIC_TEMPLATE.format(rows="\n".join(rows))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 1 topic extractor sweep")
    parser.add_argument("--model", help="Run only this model (repeatable)", action="append")
    parser.add_argument("--file",  help="Run only this corpus file (repo-relative, repeatable)",
                        action="append")
    parser.add_argument("--runs",  type=int, default=1,
                        help="Runs per (model, file) combo — use 2-3 for determinism phase")
    args = parser.parse_args()

    models = args.model or DEFAULT_MODELS
    files  = [(p, r) for p, r in CORPUS if args.file is None or p in args.file]

    if not files:
        print("No corpus files matched. Check --file paths.", file=sys.stderr)
        sys.exit(1)

    template = load_prompt_template()
    tag = datetime.now().strftime("%Y%m%d-%H%M%S")

    print(f"Sweep: {len(models)} model(s) × {len(files)} file(s) × {args.runs} run(s)")
    print(f"Output: retrieval/runs/{tag}.jsonl\n")

    records = run_sweep(models, files, args.runs, template)

    out_path     = save_results(records, tag)
    summary      = print_summary(records)
    summary_path = RUNS_DIR / f"{tag}-summary.txt"
    summary_path.write_text(summary + "\n", encoding="utf-8")

    manual_path = RUNS_DIR / f"{tag}-manual-rubric.md"
    manual_path.write_text(print_manual_template(records), encoding="utf-8")

    print(f"\nSaved: {out_path}")
    print(f"Saved: {summary_path}")
    print(f"Saved: {manual_path}")
    print("\nNext: fill in dims 5-8 in the manual rubric file, then compute weighted_quality.")


if __name__ == "__main__":
    main()
