#!/usr/bin/env python3
"""Generate a markdown benchmark report from summary.json.

Reads the summary produced by run-benchmark.sh and outputs a formatted
comparison report following the style of docs/model-comparison-hello-world.md.

Usage:
  python3 generate-report.py summary.json report.md
"""

import json
import sys
from collections import defaultdict


def load_summary(path):
    with open(path) as f:
        return json.load(f)


def format_perf(r):
    """Format performance as 'N tok, X tok/s, Ys'."""
    return f"{r['eval_count']} tok, {r['tok_s']:.1f} tok/s, {r['total_seconds']:.1f}s"


def generate_report(summary):
    lines = []
    w = lines.append

    w("# Benchmark Report: Qwen2.5-Coder vs Qwen3 Personas")
    w("")
    w(f"**Date:** {summary['timestamp']}")
    w(f"**Run ID:** {summary['run_id']}")
    w("")
    w("---")
    w("")

    results = summary['results']
    models_info = summary['models']

    # Group results by category
    backend_results = [r for r in results if r['category'] == 'backend']
    visual_results = [r for r in results if r['category'] == 'visual']

    # --- Performance Summary ---
    w("## Performance Summary")
    w("")

    for category, cat_results, model_pairs in [
        ("Backend Prompts", backend_results,
         [("my-coder", "Qwen2.5-7B"), ("my-coder-q3", "Qwen3-8B")]),
        ("Visual Prompts", visual_results,
         [("my-creative-coder", "Qwen2.5-7B"), ("my-creative-coder-q3", "Qwen3-8B")]),
    ]:
        if not cat_results:
            continue

        m1_name, m1_label = model_pairs[0]
        m2_name, m2_label = model_pairs[1]

        w(f"### {category} ({m1_name} vs {m2_name})")
        w("")
        w(f"| Prompt | {m1_name} ({m1_label}) | {m2_name} ({m2_label}) |")
        w("|--------|" + "-" * (len(m1_name) + len(m1_label) + 5) + "|" +
          "-" * (len(m2_name) + len(m2_label) + 5) + "|")

        # Group by prompt_id
        by_prompt = defaultdict(dict)
        for r in cat_results:
            by_prompt[r['prompt_id']][r['model']] = r

        m1_speeds = []
        m2_speeds = []

        for prompt_id in sorted(by_prompt.keys()):
            prompt_results = by_prompt[prompt_id]
            desc = prompt_results.get(m1_name, prompt_results.get(m2_name, {})).get(
                'description', prompt_id)

            m1_r = prompt_results.get(m1_name)
            m2_r = prompt_results.get(m2_name)

            m1_cell = format_perf(m1_r) if m1_r and m1_r['status'] == 'success' else 'N/A'
            m2_cell = format_perf(m2_r) if m2_r and m2_r['status'] == 'success' else 'N/A'

            if m1_r and m1_r['status'] == 'success':
                m1_speeds.append(m1_r['tok_s'])
            if m2_r and m2_r['status'] == 'success':
                m2_speeds.append(m2_r['tok_s'])

            w(f"| {desc} | {m1_cell} | {m2_cell} |")

        # Average row
        m1_avg = f"{sum(m1_speeds)/len(m1_speeds):.1f}" if m1_speeds else "N/A"
        m2_avg = f"{sum(m2_speeds)/len(m2_speeds):.1f}" if m2_speeds else "N/A"
        w(f"| **Average tok/s** | **{m1_avg}** | **{m2_avg}** |")
        w("")

    # --- Detailed Results ---
    w("## Detailed Results")
    w("")

    by_prompt_all = defaultdict(list)
    for r in results:
        by_prompt_all[r['prompt_id']].append(r)

    for prompt_id in sorted(by_prompt_all.keys()):
        prompt_runs = by_prompt_all[prompt_id]
        desc = prompt_runs[0].get('description', prompt_id)
        w(f"### {prompt_id}")
        w(f"**Prompt:** {desc}")
        w("")

        for r in sorted(prompt_runs, key=lambda x: x['model']):
            model = r['model']
            base = models_info.get(model, {}).get('base_model', 'unknown')
            status = r['status']

            w(f"#### {model} ({base})")

            if status == 'success':
                w(f"**Performance:** {r['tok_s']:.1f} tok/s | "
                  f"{r['eval_count']} tokens | {r['total_seconds']:.1f}s total")
                if r.get('extracted_file'):
                    w(f"**Output:** `{r['extracted_file']}` "
                      f"({r.get('extracted_lines', '?')} lines)")
                if r.get('think_tokens'):
                    w(f"**Thinking tokens:** {r['think_tokens']}")
            elif status == 'success_no_extract':
                w(f"**Performance:** {r['tok_s']:.1f} tok/s | "
                  f"{r['eval_count']} tokens | {r['total_seconds']:.1f}s total")
                w("**Output:** No valid code/HTML extracted from response")
            elif status == 'timeout':
                w(f"**Status:** Timed out after {r.get('timeout', '?')}s")
            else:
                w(f"**Status:** {status}")

            w("")

    # --- Visual Results Table ---
    if visual_results:
        w("## Visual Results")
        w("")
        w("HTML files can be opened directly in a browser:")
        w("")
        w("| File | Model | Prompt |")
        w("|------|-------|--------|")
        for r in sorted(visual_results, key=lambda x: (x['prompt_id'], x['model'])):
            if r.get('extracted_file'):
                w(f"| `{r['extracted_file']}` | {r['model']} | {r.get('description', r['prompt_id'])} |")
        w("")

    # --- Observations ---
    w("## Observations")
    w("")
    w("_To be filled after reviewing outputs._")
    w("")

    return '\n'.join(lines)


def main():
    if len(sys.argv) < 3:
        print("Usage: generate-report.py summary.json report.md", file=sys.stderr)
        sys.exit(2)

    summary = load_summary(sys.argv[1])
    report = generate_report(summary)

    with open(sys.argv[2], 'w') as f:
        f.write(report)

    print(f"Report written: {sys.argv[2]}")


if __name__ == '__main__':
    main()
