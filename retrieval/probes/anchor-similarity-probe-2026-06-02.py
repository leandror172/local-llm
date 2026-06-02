"""
Phase 3 feasibility probe: do candidate orphan anchors embed close enough to
in-corpus topics to clear the merge threshold?

Anchors tested:
  - ref:concept-latent-topic-graph
  - ref:plan-latent-topic-graph
  - ref:ltg-corpus

Threshold reference: cosine 0.85 → L2 ~0.547 for unit-normalized 4096-dim vectors.
(conversion: L2 = sqrt(2*(1-cosine)), valid only for unit-normalized vectors)

Run from repo root:
    python3 retrieval/probes/anchor-similarity-probe-2026-06-02.py
    python3 retrieval/probes/anchor-similarity-probe-2026-06-02.py --method mechanical
    python3 retrieval/probes/anchor-similarity-probe-2026-06-02.py --method all
"""

import sys
import math
import re
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import lancedb
import numpy as np
from model_client import ModelClient, load_config

# ── Anchor keys to probe ──────────────────────────────────────────────────────

ANCHOR_KEYS = [
    "ref:concept-latent-topic-graph",
    "ref:plan-latent-topic-graph",
    "ref:ltg-corpus",
]

REPO_ROOT = Path(__file__).parent.parent.parent
INDEX_PATH = REPO_ROOT / "retrieval" / "index"
CONFIG_PATH = REPO_ROOT / "retrieval" / "config.yaml"
REF_LOOKUP = REPO_ROOT / ".claude" / "tools" / "ref-lookup.sh"

COSINE_THRESHOLD = 0.85
L2_THRESHOLD = math.sqrt(2 * (1 - COSINE_THRESHOLD))  # ~0.5477
TOP_K = 5

# ── Ref block fetching ────────────────────────────────────────────────────────

def fetch_ref_content(key: str) -> str:
    """Return the raw text of a ref block via ref-lookup.sh."""
    bare = key.removeprefix("ref:")
    result = subprocess.run(
        [str(REF_LOOKUP), bare],
        capture_output=True, text=True, cwd=str(REPO_ROOT)
    )
    return result.stdout.strip()


def parse_heading(content: str) -> str:
    """Extract the first heading line (strip leading # markers)."""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return re.sub(r"^#+\s*", "", stripped).strip()
    return ""


def parse_first_prose_line(content: str) -> str:
    """
    Extract the first non-blank, non-metadata, non-subheading prose line.

    Skips:
      - Blank lines
      - Lines that are pure italic metadata: *...*
      - Sub-headings: lines starting with ##+ (top heading already extracted)
      - Horizontal rules: ---
      - HTML comment markers: <!--, -->
    """
    heading_seen = False
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            heading_seen = True
            continue
        if not heading_seen:
            continue
        # skip horizontal rules
        if re.match(r"^-{3,}$", stripped):
            continue
        # skip HTML comment markers
        if stripped.startswith("<!--") or stripped.startswith("-->"):
            continue
        # skip pure italic metadata: *...*
        if re.match(r"^\*[^*].*[^*]\*$", stripped) or re.match(r"^\*\*\*.*\*\*\*$", stripped):
            continue
        # skip lines that are only punctuation/symbols
        if re.match(r"^[^a-zA-Z]*$", stripped):
            continue
        # first real prose line
        return stripped
    return ""

# ── Description methods ───────────────────────────────────────────────────────

def describe_handcrafted(key: str, _content: str) -> str:
    """Original hand-written descriptions from the first probe run."""
    mapping = {
        "ref:concept-latent-topic-graph": (
            "Latent Topic Graph: A Content-Relation Retrieval Substrate — "
            "A retrieval substrate where primary nodes are topics extracted by a language model, "
            "files are containers, and edges are weighted by embedding-space distance between topics."
        ),
        "ref:plan-latent-topic-graph": (
            "Implementation Plan: Latent Topic Graph (LTG) Substrate — "
            "Build a working LTG substrate in the llm repo to validate the concept and serve "
            "downstream consumers; minimum done: relate(file_a, file_b) returns a verifiable answer."
        ),
        "ref:ltg-corpus": (
            "MVP corpus scope — curated subset + two branch points — "
            "Decision: Initial MVP corpus is docs/research/, docs/ideas/, .claude/, .memories/."
        ),
    }
    return mapping[key]


def describe_mechanical(key: str, content: str) -> str:
    """D3 heuristic: heading + first non-metadata prose line."""
    heading = parse_heading(content)
    prose = parse_first_prose_line(content)
    return f"{heading} — {prose}" if prose else heading


def describe_mechanical_with_key(key: str, content: str) -> str:
    """D3 heuristic + anchor key name prepended (tests naming-taxonomy signal)."""
    bare = key.removeprefix("ref:")
    base = describe_mechanical(key, content)
    return f"{bare}: {base}"


def describe_full_content(key: str, content: str) -> str:
    """First 400 chars of the raw ref block body (after stripping the comment markers)."""
    body = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL).strip()
    return body[:400]


def describe_key_only(key: str, _content: str) -> str:
    """Key name only, hyphenated as-is: 'concept-latent-topic-graph'."""
    return key.removeprefix("ref:")


def describe_key_words(key: str, _content: str) -> str:
    """Key name only, hyphens replaced with spaces: 'concept latent topic graph'."""
    return key.removeprefix("ref:").replace("-", " ")


METHODS = {
    "handcrafted":          describe_handcrafted,
    "mechanical":           describe_mechanical,
    "mechanical+key":       describe_mechanical_with_key,
    "key_only":             describe_key_only,
    "key_words":            describe_key_words,
    "full_content":         describe_full_content,
}

# ── Probe runner ──────────────────────────────────────────────────────────────

def cosine_from_l2(l2: float) -> float:
    return 1.0 - (l2 ** 2) / 2.0


def run_probe(method_name: str, client: ModelClient, table) -> None:
    fn = METHODS[method_name]
    print(f"\n{'=' * 70}")
    print(f"METHOD: {method_name}")
    print(f"{'=' * 70}")

    contents = {key: fetch_ref_content(key) for key in ANCHOR_KEYS}
    descriptions = [fn(key, contents[key]) for key in ANCHOR_KEYS]

    vectors = client.embed_texts(descriptions, role="embedding")

    for key, desc, vec in zip(ANCHOR_KEYS, descriptions, vectors):
        vec_np = np.array(vec, dtype=np.float32)
        norm = np.linalg.norm(vec_np)
        norm_flag = "unit-norm ✓" if abs(norm - 1.0) < 0.01 else f"norm={norm:.4f} ⚠"

        print(f"\nAnchor: {key}  [{norm_flag}]")
        print(f"  Desc: {desc[:100]}{'...' if len(desc) > 100 else ''}")

        results = table.search(vec).limit(TOP_K).to_list()
        any_clears = False
        for i, row in enumerate(results):
            l2 = row["_distance"]
            cos = cosine_from_l2(l2)
            clears = "✓ CLEARS" if l2 <= L2_THRESHOLD else f"  gap={l2 - L2_THRESHOLD:+.4f}"
            file_path = row.get("file_path", "?")
            topic = row.get("topic_name", "?")
            print(f"    {i+1}. cos={cos:.4f} L2={l2:.4f}  {clears}")
            print(f"       [{file_path}] {topic}")
            if l2 <= L2_THRESHOLD:
                any_clears = True

        if not any_clears:
            best = results[0]["_distance"] if results else float("inf")
            print(f"  → No merge. Closest cos={cosine_from_l2(best):.4f} L2={best:.4f}")


def main():
    parser = argparse.ArgumentParser(description="LTG Phase 3 anchor similarity probe")
    parser.add_argument(
        "--method",
        choices=[*METHODS.keys(), "all"],
        default="all",
        help="Description method to use (default: all)",
    )
    args = parser.parse_args()

    cfg = load_config(CONFIG_PATH)
    client = ModelClient(cfg)
    db = lancedb.connect(str(INDEX_PATH))
    table = db.open_table("topics")
    total = table.count_rows()

    print(f"Index: {total} topic rows")
    print(f"Threshold: cosine ≥ {COSINE_THRESHOLD} → L2 ≤ {L2_THRESHOLD:.4f}")

    methods_to_run = list(METHODS.keys()) if args.method == "all" else [args.method]
    for method in methods_to_run:
        run_probe(method, client, table)

    print("\nDone.")


if __name__ == "__main__":
    main()
