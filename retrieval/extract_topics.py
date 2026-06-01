#!/usr/bin/env python3
"""
Phase 1 topic extractor — 2-arm production runner.

Routes each corpus file to the correct extraction model based on file extension,
calls the model via ModelClient, writes one JSONL row per file.

Usage:
    retrieval/run-extract-topics.sh
    retrieval/run-extract-topics.sh --file docs/research/smart-rag-repowise.md
    retrieval/run-extract-topics.sh --output retrieval/runs/custom.jsonl

Output: retrieval/runs/YYYYMMDD-HHMMSS.jsonl  (one JSON object per line)
"""

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    import httpx
except ImportError:
    print("httpx not found. Install with: pip install httpx", file=sys.stderr)
    sys.exit(1)

from model_client import ModelClient, load_config
from routing import route

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = Path(__file__).parent / "prompts"
RUNS_DIR = Path(__file__).parent / "runs"
CONFIG_PATH = Path(__file__).parent / "config.yaml"

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

# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def load_prompt_template() -> str:
    return (PROMPTS_DIR / "extract.txt").read_text(encoding="utf-8")


def build_prompt(template: str, filepath: Path, content: str) -> str:
    lines = content.splitlines()
    numbered = "\n".join(f"{i+1:4d}  {line}" for i, line in enumerate(lines))
    return template.format(
        filename=filepath.name,
        line_count=len(lines),
        content=numbered,
    )


def parse_topics(raw: str) -> list[dict] | None:
    try:
        data = json.loads(raw)
        topics = data.get("topics", [])
        return topics if isinstance(topics, list) else None
    except (json.JSONDecodeError, AttributeError):
        return None


def route_file(path: str) -> str:
    return route(path)


# ---------------------------------------------------------------------------
# Single file run
# ---------------------------------------------------------------------------

def run_file(rel_path: str, role: str, template: str, client: ModelClient) -> dict:
    filepath = REPO_ROOT / rel_path
    if not filepath.exists():
        return _error_record(rel_path, role, "file_not_found", str(filepath))

    content = filepath.read_text(encoding="utf-8", errors="replace")
    prompt = build_prompt(template, filepath, content)

    print(f"  {rel_path:<55} ... ", end="", flush=True)

    role_key = route_file(rel_path)
    status = "ok"
    result = None

    try:
        if role_key == "extraction_code":
            result = client.extract_code(prompt)
        else:
            result = client.extract_prose(prompt)
    except httpx.TimeoutException:
        status = "timeout"
        print("TIMEOUT")
    except httpx.HTTPStatusError as e:
        status = "http_error"
        print(f"HTTP {e.response.status_code}")
    except Exception as e:
        status = "error"
        print(f"ERROR: {e}")

    raw_content = result.content if result else ""
    topics = None
    if status == "ok":
        topics = parse_topics(raw_content)
        if topics is None:
            status = "malformed_json"
            print("MALFORMED JSON")

    if status == "ok":
        print(f"ok  topics={len(topics or [])}")

    return {
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": result.model if result else "",
        "file": rel_path,
        "file_role": role,
        "status": status,
        "parsed_topics": topics,
    }


def _error_record(rel_path: str, role: str, status: str, msg: str) -> dict:
    print(f"  {rel_path:<55} ... {status}: {msg}")
    return {
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": "",
        "file": rel_path,
        "file_role": role,
        "status": status,
        "parsed_topics": None,
    }


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_corpus(files: list[tuple[str, str]], template: str, client: ModelClient) -> list[dict]:
    records = []
    for rel_path, role in files:
        record = run_file(rel_path, role, template, client)
        records.append(record)
    print(f"\nCompleted {len(records)} file(s).")
    return records


def save_jsonl(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="LTG Phase 1 — topic extraction (2-arm)")
    parser.add_argument("--file", help="Run only this corpus file (repo-relative, repeatable)",
                        action="append")
    parser.add_argument("--output", type=Path, help="Override output JSONL path")
    args = parser.parse_args()

    files = [(p, r) for p, r in CORPUS if args.file is None or p in args.file]
    if not files:
        print("No corpus files matched. Check --file paths.", file=sys.stderr)
        sys.exit(1)

    template = load_prompt_template()
    cfg = load_config(CONFIG_PATH)
    client = ModelClient(cfg)
    tag = datetime.now().strftime("%Y%m%d-%H%M%S")

    print(f"Extracting {len(files)} file(s) via 2-arm routing")
    print(f"  prose → {cfg['extraction_prose']['model']}")
    print(f"  code  → {cfg['extraction_code']['model']}\n")

    records = run_corpus(files, template, client)

    out_path = args.output or (RUNS_DIR / f"{tag}.jsonl")
    save_jsonl(records, out_path)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
