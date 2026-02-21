#!/usr/bin/env python3
"""benchmark.py — Run evaluation across N personas × M prompts.

Produces a results directory with per-run eval JSONs, an aggregated
summary.json, and a human-readable report.md.

Usage:
  python3 -u evaluator/lib/benchmark.py \\
    --prompts evaluator/prompts/go \\
    --personas my-go-q3,my-coder-q3 \\
    --rubric evaluator/rubrics/code-go.yaml \\
    --judge-model my-codegen-q3 \\
    [--all-coding]          # auto-discover coding personas from registry
    [--dry-run]             # print plan without making API calls
    [--no-warmup]           # skip warmup call
    [--timeout 300]         # per-prompt Ollama timeout (seconds)
    [--skip-phase1]         # skip automated checks
    [--skip-phase2]         # skip LLM judge (generation only)
    [--results-dir DIR]     # override default evaluator/results/

Exit codes:
  0 = benchmark complete
  1 = fatal error (missing files, Ollama unreachable, etc.)
"""

import argparse
import importlib.util
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

# --- Path setup ---
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "personas" / "lib"))

from ollama_client import ollama_chat  # noqa: E402
OllamaConnectionError = ConnectionError  # stdlib ConnectionError raised by ollama_client

# Import evaluate.py functions directly (avoid subprocess overhead per eval)
_eval_path = Path(__file__).parent / "evaluate.py"
_eval_spec = importlib.util.spec_from_file_location("evaluate", _eval_path)
_eval_mod = importlib.util.module_from_spec(_eval_spec)
_eval_spec.loader.exec_module(_eval_mod)

load_rubric = _eval_mod.load_rubric
parse_prompt_file = _eval_mod.parse_prompt_file
extract_code_from_text = _eval_mod.extract_code_from_text
run_phase1 = _eval_mod.run_phase1
run_phase2 = _eval_mod.run_phase2
aggregate_scores = _eval_mod.aggregate_scores

DEFAULT_JUDGE_MODEL = "my-codegen-q3"
DEFAULT_TIMEOUT = 300
REGISTRY_PATH = REPO_ROOT / "personas" / "registry.yaml"
RESULTS_BASE = REPO_ROOT / "evaluator" / "results"


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------

def load_registry() -> dict:
    """Load personas/registry.yaml, return dict of active personas."""
    with open(REGISTRY_PATH) as f:
        raw = yaml.safe_load(f) or {}
    return {k: v for k, v in raw.items()
            if isinstance(v, dict) and v.get("status") == "active"}


def resolve_personas(names: list[str], all_coding: bool, registry: dict) -> list[str]:
    """Resolve persona names to a validated list."""
    if all_coding:
        # Coding personas: full tier, role mentions code/developer/coder/backend
        coding_keywords = {"developer", "coder", "backend", "engineer", "architect"}
        candidates = [
            name for name, attrs in registry.items()
            if attrs.get("tier") == "full"
            and any(kw in attrs.get("role", "").lower() for kw in coding_keywords)
        ]
        # Merge with any explicitly named personas
        names = list(dict.fromkeys(names + candidates))

    unknown = [n for n in names if n not in registry]
    if unknown:
        print(f"WARNING: Unknown personas (not in registry): {unknown}", file=sys.stderr)

    return [n for n in names if n in registry]


def group_by_base_model(personas: list[str], registry: dict) -> dict[str, list[str]]:
    """Group persona names by base_model to minimize VRAM reloads.

    Returns {base_model: [persona_names...]} ordered by size (smaller first).
    """
    groups: dict[str, list[str]] = {}
    for name in personas:
        base = registry.get(name, {}).get("base_model", "unknown")
        groups.setdefault(base, []).append(name)
    # Order: prefer smaller models first (alphabetic heuristic: 4b < 8b < 14b)
    return dict(sorted(groups.items()))


# ---------------------------------------------------------------------------
# Prompt collection
# ---------------------------------------------------------------------------

def collect_prompts(prompt_dir: str) -> list[dict]:
    """Collect all *.md prompt files from a directory."""
    prompts = []
    for path in sorted(Path(prompt_dir).glob("*.md")):
        meta, body = parse_prompt_file(str(path))
        prompts.append({"path": str(path), "meta": meta, "body": body,
                         "id": meta.get("id", path.stem)})
    return prompts


# ---------------------------------------------------------------------------
# Warmup
# ---------------------------------------------------------------------------

def warmup(persona: str, timeout: int, quiet: bool) -> None:
    """Send a minimal prompt to load the model into VRAM."""
    if not quiet:
        print(f"  [warmup] loading {persona} ...", file=sys.stderr)
    try:
        ollama_chat("hi", model=persona, think=False, timeout=timeout)
    except Exception as e:
        print(f"  [warmup] WARNING: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Single generation run
# ---------------------------------------------------------------------------

def generate_output(persona: str, prompt_body: str, timeout: int) -> dict:
    """Call Ollama for one persona × prompt combination.

    Returns a result dict with content, metrics, or error.
    """
    t0 = time.time()
    try:
        resp = ollama_chat(
            prompt=prompt_body,
            model=persona,
            think=False,
            timeout=timeout,
        )
        return {
            "status": "success",
            "content": resp["content"],
            "eval_count": resp.get("eval_count", 0),
            "total_duration_ms": resp.get("total_duration_ms", 0.0),
            "tok_s": round(resp.get("eval_count", 0) / max(resp.get("total_duration_ms", 1) / 1000, 0.001), 1),
            "wall_seconds": round(time.time() - t0, 1),
        }
    except TimeoutError:
        return {"status": "timeout", "timeout": timeout,
                "wall_seconds": round(time.time() - t0, 1)}
    except OllamaConnectionError as e:
        return {"status": "error", "error": str(e),
                "wall_seconds": round(time.time() - t0, 1)}
    except Exception as e:
        return {"status": "error", "error": str(e),
                "wall_seconds": round(time.time() - t0, 1)}


# ---------------------------------------------------------------------------
# Main benchmark loop
# ---------------------------------------------------------------------------

def run_benchmark(
    prompts: list[dict],
    personas: list[str],
    rubric: dict,
    judge_model: str,
    registry: dict,
    run_dir: Path,
    timeout: int,
    skip_phase1: bool,
    skip_phase2: bool,
    do_warmup: bool,
    quiet: bool,
) -> list[dict]:
    """Run all persona × prompt combinations, evaluate, return flat results list."""
    raw_dir = run_dir / "raw"
    code_dir = run_dir / "code"
    evals_dir = run_dir / "evals"
    for d in (raw_dir, code_dir, evals_dir):
        d.mkdir(parents=True, exist_ok=True)

    groups = group_by_base_model(personas, registry)
    domain = rubric.get("domain", "general")

    # --- Phase 1: Generate outputs, grouped by base model ---
    generation_results: list[dict] = []
    warmed_bases: set[str] = set()

    for base_model, group_personas in groups.items():
        if not quiet:
            print(f"\n[benchmark] base_model={base_model} ({len(group_personas)} personas)", file=sys.stderr)

        for persona in group_personas:
            # Warmup once per base_model group
            if do_warmup and base_model not in warmed_bases:
                warmup(persona, timeout, quiet)
                warmed_bases.add(base_model)

            for prompt in prompts:
                pid = prompt["id"]
                slug = f"{persona}--{pid}"

                if not quiet:
                    print(f"  [generate] {persona} × {pid} ...", file=sys.stderr)

                gen = generate_output(persona, prompt["body"], timeout)
                gen.update({
                    "persona": persona,
                    "prompt_id": pid,
                    "prompt_path": prompt["path"],
                    "base_model": base_model,
                })

                # Save raw output
                raw_path = raw_dir / f"{slug}.json"
                raw_path.write_text(json.dumps({
                    "persona": persona, "prompt_id": pid,
                    "generation": gen,
                    "prompt_body": prompt["body"],
                }, indent=2))

                # Extract and save code
                if gen["status"] == "success":
                    code_text, lang = extract_code_from_text(gen["content"], domain)
                    if code_text and lang:
                        ext_map = {"go": ".go", "java": ".java", "python": ".py",
                                   "javascript": ".js", "typescript": ".ts", "rust": ".rs",
                                   "bash": ".sh", "shell": ".sh"}
                        ext = ext_map.get(lang, ".txt")
                        (code_dir / f"{slug}{ext}").write_text(code_text)
                    gen["extracted_code"] = code_text
                    gen["extracted_lang"] = lang
                else:
                    gen["extracted_code"] = None
                    gen["extracted_lang"] = None

                generation_results.append(gen)

    # --- Phase 2: Evaluate all outputs (defer judge model load until here) ---
    if not skip_phase2 and not quiet:
        print(f"\n[benchmark] loading judge model {judge_model} for Phase 2 ...", file=sys.stderr)
        warmup(judge_model, timeout, quiet)

    all_results = []
    for gen in generation_results:
        pid = gen["prompt_id"]
        persona = gen["persona"]
        slug = f"{persona}--{pid}"

        result = {
            "persona": persona,
            "prompt_id": pid,
            "base_model": gen["base_model"],
            "status": gen["status"],
            "generation": {
                "eval_count": gen.get("eval_count", 0),
                "tok_s": gen.get("tok_s", 0),
                "total_seconds": gen.get("wall_seconds", 0),
            },
            "evaluation": None,
        }

        if gen["status"] == "success":
            # Find prompt body
            prompt = next(p for p in prompts if p["id"] == pid)
            code_text = gen.get("extracted_code")

            p1_scores = []
            p2_scores = []
            p2_eval_count = 0
            p2_duration_ms = 0.0

            if not skip_phase1:
                if not quiet:
                    print(f"  [eval p1] {persona} × {pid}", file=sys.stderr)
                p1_scores = run_phase1(gen["content"], rubric, domain)

            if not skip_phase2:
                if not quiet:
                    print(f"  [eval p2] {persona} × {pid}", file=sys.stderr)
                p2_scores, p2_eval_count, p2_duration_ms = run_phase2(
                    prompt["body"], gen["content"], code_text,
                    rubric, judge_model, quiet
                )

            eval_result = aggregate_scores(p1_scores, p2_scores, p2_eval_count, p2_duration_ms)
            eval_result["evaluated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

            # Save per-eval JSON
            eval_path = evals_dir / f"{slug}-eval.json"
            eval_path.write_text(json.dumps(eval_result, indent=2))

            result["evaluation"] = {
                "phase1_score": eval_result["phase1"]["weighted_score"],
                "phase2_score": eval_result["phase2"]["weighted_score"],
                "overall_score": eval_result["overall"]["weighted_score"],
                "overall_percentage": eval_result["overall"]["percentage"],
                "criteria": {
                    c["name"]: {"score": c["score"], "reason": c["reason"]}
                    for c in (eval_result["phase1"]["criteria"] + eval_result["phase2"]["criteria"])
                },
            }

        all_results.append(result)

    return all_results


# ---------------------------------------------------------------------------
# Summary and report generation
# ---------------------------------------------------------------------------

def build_summary(
    results: list[dict],
    run_id: str,
    rubric: dict,
    judge_model: str,
    personas: list[str],
    registry: dict,
) -> dict:
    """Build summary.json structure with leaderboard."""
    # Build leaderboard: average scores per persona
    persona_scores: dict[str, list[float]] = {p: [] for p in personas}
    for r in results:
        if r["status"] == "success" and r.get("evaluation"):
            pct = r["evaluation"].get("overall_percentage")
            if pct is not None:
                persona_scores[r["persona"]].append(pct)

    leaderboard = []
    for persona in personas:
        scores = persona_scores[persona]
        if scores:
            leaderboard.append({
                "persona": persona,
                "avg_score": round(sum(scores) / len(scores) / 20, 3),  # /20 → 0-5 scale
                "avg_pct": round(sum(scores) / len(scores), 1),
                "prompts_evaluated": len(scores),
            })
    leaderboard.sort(key=lambda x: x["avg_pct"], reverse=True)

    return {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rubric": rubric["id"],
        "judge_model": judge_model,
        "personas": {
            p: {"base_model": registry.get(p, {}).get("base_model", "unknown"),
                "role": registry.get(p, {}).get("role", "")}
            for p in personas
        },
        "results": results,
        "leaderboard": leaderboard,
    }


def _bar(value: float, max_val: float, width: int = 30) -> str:
    """Render a simple ASCII progress bar."""
    if max_val == 0:
        return ""
    filled = int(round(value / max_val * width))
    return "█" * filled + "░" * (width - filled)


def generate_report(summary: dict) -> str:
    """Generate a human-readable markdown report."""
    lines = []
    lines.append(f"# Benchmark Report")
    lines.append(f"")
    lines.append(f"- **Run ID:** {summary['run_id']}")
    lines.append(f"- **Date:** {summary['timestamp']}")
    lines.append(f"- **Rubric:** `{summary['rubric']}`")
    lines.append(f"- **Judge model:** `{summary['judge_model']}`")
    lines.append(f"- **Personas tested:** {len(summary['personas'])}")
    lines.append(f"")

    # Leaderboard
    lines.append(f"## Leaderboard")
    lines.append(f"")
    lines.append(f"| Rank | Persona | Avg % | Avg Score (/5) | Prompts |")
    lines.append(f"|------|---------|-------|---------------|---------|")
    for i, entry in enumerate(summary["leaderboard"], 1):
        bar = _bar(entry["avg_pct"], 100, 20)
        lines.append(
            f"| {i} | `{entry['persona']}` | {entry['avg_pct']}% {bar} "
            f"| {entry['avg_score']} | {entry['prompts_evaluated']} |"
        )
    lines.append(f"")

    # Per-persona breakdown
    lines.append(f"## Per-Persona Results")
    lines.append(f"")
    personas = list(summary["personas"].keys())
    for persona in personas:
        persona_results = [r for r in summary["results"] if r["persona"] == persona]
        lines.append(f"### `{persona}`")
        lines.append(f"")
        lines.append(f"| Prompt | Status | P1 Score | P2 Score | Overall % |")
        lines.append(f"|--------|--------|----------|----------|-----------|")
        for r in persona_results:
            status = r["status"]
            if status == "success" and r.get("evaluation"):
                ev = r["evaluation"]
                p1 = f"{ev['phase1_score']:.2f}" if ev['phase1_score'] is not None else "—"
                p2 = f"{ev['phase2_score']:.2f}" if ev['phase2_score'] is not None else "—"
                pct = f"{ev['overall_percentage']}%" if ev['overall_percentage'] is not None else "—"
            else:
                p1 = p2 = pct = "—"
            lines.append(f"| `{r['prompt_id']}` | {status} | {p1} | {p2} | {pct} |")
        lines.append(f"")

    # Criterion analysis
    lines.append(f"## Criterion Analysis")
    lines.append(f"")
    lines.append(f"_Which criteria differentiate personas most?_")
    lines.append(f"")

    # Collect criterion scores per persona
    criterion_data: dict[str, dict[str, list[float]]] = {}
    for r in summary["results"]:
        if r["status"] == "success" and r.get("evaluation"):
            for crit_name, crit_data in r["evaluation"].get("criteria", {}).items():
                score = crit_data.get("score")
                if score is not None:
                    criterion_data.setdefault(crit_name, {})
                    criterion_data[crit_name].setdefault(r["persona"], []).append(score)

    if criterion_data:
        persona_cols = personas
        header = "| Criterion | " + " | ".join(f"`{p}`" for p in persona_cols) + " |"
        sep = "|-----------|" + "|---------|" * len(persona_cols)
        lines.append(header)
        lines.append(sep)

        for crit_name, persona_scores in criterion_data.items():
            avgs = []
            for p in persona_cols:
                scores = persona_scores.get(p, [])
                avg = round(sum(scores) / len(scores), 2) if scores else None
                avgs.append(f"{avg:.2f}" if avg is not None else "—")
            lines.append(f"| {crit_name} | " + " | ".join(avgs) + " |")
        lines.append(f"")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------

def print_dry_run(prompts: list[dict], personas: list[str], rubric: dict,
                  judge_model: str, registry: dict, timeout: int) -> None:
    groups = group_by_base_model(personas, registry)
    total_generations = len(prompts) * len(personas)
    total_evals = total_generations

    print(f"\n=== DRY RUN PLAN ===")
    print(f"Rubric:      {rubric['id']}")
    print(f"Judge model: {judge_model}")
    print(f"Prompts:     {len(prompts)}")
    print(f"Personas:    {len(personas)}")
    print(f"Total runs:  {total_generations}")
    print(f"")
    print(f"Execution order (grouped by base_model to minimize VRAM reloads):")
    for base_model, group in groups.items():
        print(f"  [{base_model}]  personas: {', '.join(group)}")
        for persona in group:
            for prompt in prompts:
                print(f"    generate: {persona} × {prompt['id']} (timeout={timeout}s)")
    print(f"")
    print(f"  [judge: {judge_model}]  {total_evals} evaluations")
    print(f"\nEstimated time: ~{total_generations * 30 // 60}–{total_generations * 60 // 60} min")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Run evaluation benchmark across personas × prompts.")
    parser.add_argument("--prompts", required=True, help="Directory of prompt files")
    parser.add_argument("--personas", default="", help="Comma-separated persona names")
    parser.add_argument("--rubric", required=True, help="Path to rubric YAML")
    parser.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL)
    parser.add_argument("--all-coding", action="store_true", help="Auto-discover coding personas")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without API calls")
    parser.add_argument("--no-warmup", action="store_true", help="Skip warmup calls")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--skip-phase1", action="store_true")
    parser.add_argument("--skip-phase2", action="store_true")
    parser.add_argument("--results-dir", default=str(RESULTS_BASE))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    # Load inputs
    try:
        rubric = load_rubric(args.rubric)
        registry = load_registry()
    except (FileNotFoundError, AssertionError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    persona_names = [p.strip() for p in args.personas.split(",") if p.strip()]
    personas = resolve_personas(persona_names, args.all_coding, registry)
    if not personas:
        print("ERROR: No valid personas specified. Use --personas or --all-coding.", file=sys.stderr)
        return 1

    prompts = collect_prompts(args.prompts)
    if not prompts:
        print(f"ERROR: No prompt files found in {args.prompts}", file=sys.stderr)
        return 1

    if args.dry_run:
        print_dry_run(prompts, personas, rubric, args.judge_model, registry, args.timeout)
        return 0

    # Create run directory
    run_id = datetime.now().strftime("%Y-%m-%dT%H%M%S")
    run_dir = Path(args.results_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    if not args.quiet:
        print(f"[benchmark] run_id={run_id}", file=sys.stderr)
        print(f"[benchmark] prompts={len(prompts)}, personas={len(personas)}", file=sys.stderr)
        print(f"[benchmark] results → {run_dir}", file=sys.stderr)

    results = run_benchmark(
        prompts=prompts,
        personas=personas,
        rubric=rubric,
        judge_model=args.judge_model,
        registry=registry,
        run_dir=run_dir,
        timeout=args.timeout,
        skip_phase1=args.skip_phase1,
        skip_phase2=args.skip_phase2,
        do_warmup=not args.no_warmup,
        quiet=args.quiet,
    )

    summary = build_summary(results, run_id, rubric, args.judge_model, personas, registry)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    report = generate_report(summary)
    (run_dir / "report.md").write_text(report)

    if not args.quiet:
        print(f"\n[benchmark] done → {run_dir}", file=sys.stderr)
        if summary["leaderboard"]:
            top = summary["leaderboard"][0]
            print(f"[benchmark] winner: {top['persona']} ({top['avg_pct']}%)", file=sys.stderr)

    # Print summary JSON to stdout for piping
    print(json.dumps({"run_id": run_id, "leaderboard": summary["leaderboard"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
