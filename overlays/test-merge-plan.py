#!/usr/bin/env python3
"""
test-merge-plan.py — Compare AI planner output across models for a given target file.

Usage:
    ./overlays/test-merge-plan.py --target-file PATH --overlay <name> [--models m1,m2,...]

Calls the merge planner with each model, prints the resulting JSON plan.
Does NOT write anything to disk.
"""

import argparse
import json
import time
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
# Append +think to a model name to enable Qwen3 thinking mode (e.g. qwen3:14b+think).
# deepseek-r1 always thinks; think param is ignored for it.
DEFAULT_MODELS = [
    "qwen2.5-coder:14b",
    "qwen3:8b",
    "qwen3:8b+think",
    "qwen3:14b",
    "qwen3:14b+think",
    "qwen3:30b-a3b+think",  # skip think:false for 30b — testing is already slow
    "deepseek-r1:14b",
]


def call_ollama(model: str, prompt: str, schema: dict) -> tuple[dict | None, float]:
    # +think suffix enables Qwen3 thinking mode; strip it before sending to API
    think = model.endswith("+think")
    actual_model = model.removesuffix("+think")

    payload_dict = {
        "model": actual_model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "format": schema,
        "options": {"num_ctx": 4096},
    }
    # think param is Qwen3-specific; deepseek-r1 ignores it (always thinks)
    if not actual_model.startswith("deepseek"):
        payload_dict["think"] = think

    payload = json.dumps(payload_dict).encode()

    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    chunks = []
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for line in resp:
                if not line.strip():
                    continue
                chunk = json.loads(line)
                if chunk.get("message", {}).get("content"):
                    chunks.append(chunk["message"]["content"])
                if chunk.get("done"):
                    break
        elapsed = time.time() - t0
        return json.loads("".join(chunks)), elapsed
    except Exception as e:
        return None, time.time() - t0


def main():
    parser = argparse.ArgumentParser(description="Compare merge planner across models.")
    parser.add_argument("--target-file", required=True, help="File to merge into (read-only)")
    parser.add_argument("--overlay", required=True, help="Overlay name")
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS),
                        help=f"Comma-separated models (default: {','.join(DEFAULT_MODELS)})")
    args = parser.parse_args()

    target = Path(args.target_file)
    if not target.exists():
        print(f"ERROR: target file not found: {target}")
        return

    overlay_dir = SCRIPT_DIR / args.overlay
    prompts_dir = SCRIPT_DIR / "prompts"

    # Load overlay manifest to get section file and merge_hint
    import yaml
    manifest = yaml.safe_load((overlay_dir / "manifest.yaml").read_text())
    overlay_name = manifest["name"]
    spec = list(manifest.get("merge_sections", {}).values())[0]
    section_content = (overlay_dir / spec["file"]).read_text().rstrip()
    merge_hint = spec.get("merge_hint", "")

    existing_content = target.read_text()
    prompt_template = (prompts_dir / "merge-plan.txt").read_text()
    schema = json.loads((prompts_dir / "merge-plan-schema.json").read_text())

    prompt = (
        prompt_template
        .replace("<<EXISTING_CONTENT>>", existing_content)
        .replace("<<SECTION_CONTENT>>", section_content)
        .replace("<<MERGE_HINT>>", merge_hint)
    )

    models = [m.strip() for m in args.models.split(",")]

    print(f"\nTarget : {target} ({len(existing_content.splitlines())} lines)")
    print(f"Overlay: {overlay_name}")
    print(f"Prompt : {len(prompt)} chars (~{len(prompt)//4} tokens)")
    print(f"Models : {', '.join(models)}\n")
    print("=" * 70)

    for model in models:
        print(f"\n[ {model} ]")
        plan, elapsed = call_ollama(model, prompt, schema)
        if plan is None:
            print("  ERROR: call failed or timed out")
            continue

        insert_at = plan.get("insert_after_line", "?")
        deletes = plan.get("delete_ranges", [])
        reasoning = plan.get("reasoning", "")

        print(f"  insert_after_line : {insert_at}")
        if deletes:
            for r in deletes:
                print(f"  delete lines      : {r['start']}–{r['end']}  ({r.get('reason', '')})")
        else:
            print("  delete_ranges     : (none)")
        print(f"  reasoning         : {reasoning[:120]}{'...' if len(reasoning) > 120 else ''}")
        think_note = " (thinking ON)" if model.endswith("+think") else " (thinking OFF)" if any(model.startswith(p) for p in ["qwen3", "qwen2.5"]) else " (always thinks)"
        print(f"  time              : {elapsed:.1f}s{think_note}")

    print("\n" + "=" * 70)
    print("\nNote: lines from target file for reference:")
    for i, line in enumerate(existing_content.splitlines()[:10], 1):
        print(f"  {i:3}: {line}")


if __name__ == "__main__":
    main()
