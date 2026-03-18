"""AI merge planner: deterministic plan executor + AI orchestration."""

import difflib
import json
import re
import shutil
from pathlib import Path

from .backends import Backend, SchemaMode, resolve_backend
from .report import record


def apply_plan(plan: dict, existing_content: str, open_marker: str,
               section_content: str, close_marker: str, dest_rel: str) -> str:
    """Apply a merge plan deterministically. Returns new file content."""
    lines = existing_content.splitlines(keepends=True)
    insert_after = plan["insert_after_line"]  # 1-indexed

    # Apply deletes in reverse order so earlier line numbers stay valid
    for r in sorted(plan.get("delete_ranges", []), key=lambda r: r["start"], reverse=True):
        start_idx = r["start"] - 1   # 1-indexed → 0-indexed
        end_idx = r["end"]            # end inclusive, slice end exclusive
        removed = "".join(lines[start_idx:end_idx]).rstrip()
        preview = removed.splitlines()[0][:60] if removed else ""
        record(
            "DELETE", dest_rel,
            f"lines {r['start']}–{r['end']}: {r.get('reason', 'no reason given')}",
            f"first line: {preview!r}" if preview else "",
        )
        del lines[start_idx:end_idx]
        deleted_before = sum(
            1 for i in range(r["start"], r["end"] + 1) if i <= insert_after
        )
        insert_after -= deleted_before

    # Markers are always added by the script, never the AI
    section_block = f"{open_marker}\n{section_content}\n{close_marker}\n"
    lines.insert(max(0, insert_after), section_block)
    return "".join(lines)


def _find_overlay_ranges(content: str) -> list[tuple[int, int]]:
    """Return (start, end) 1-indexed line pairs for all existing overlay blocks.

    Used to prevent the AI planner from choosing an insert_after_line that falls
    inside an already-installed overlay block.
    """
    ranges, start = [], None
    for i, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if re.match(r'^<!-- overlay:\S+ v\d+ -->$', stripped):
            start = i
        elif re.match(r'^<!-- /overlay:\S+ -->$', stripped) and start is not None:
            ranges.append((start, i))
            start = None
    return ranges


def ai_merge(
    dest: Path,
    existing_content: str,
    section_content: str,
    open_marker: str,
    close_marker: str,
    merge_hint: str,
    backend_id: str,
    model_override: str | None,
    backends: list[Backend],
    prompts_dir: Path,
    yes: bool,
    dry_run: bool,
    do_backup: bool,
    debug: bool = False,
):
    dest_rel = dest.name

    backend = resolve_backend(backends, backend_id, model_override)
    if backend is None:
        record("TODO", dest_rel,
               "AI merge skipped — no backend available",
               "add section manually per APPLY.md")
        return

    prompt_path = prompts_dir / "merge-plan.txt"
    if not prompt_path.exists():
        record("TODO", dest_rel, f"AI merge skipped — prompt template missing: {prompt_path}")
        return
    prompt = (
        prompt_path.read_text()
        .replace("<<EXISTING_CONTENT>>", existing_content)
        .replace("<<SECTION_CONTENT>>", section_content)
        .replace("<<MERGE_HINT>>", merge_hint)
    )

    schema_path = prompts_dir / "merge-plan-schema.json"
    if not schema_path.exists():
        record("TODO", dest_rel, f"AI merge skipped — schema missing: {schema_path}")
        return
    schema = json.loads(schema_path.read_text())

    if backend.schema_mode == SchemaMode.PROMPT_INJECTION:
        prompt += f"\n\nRespond with a JSON object matching this schema:\n{json.dumps(schema, indent=2)}"

    if dry_run:
        record("MERGE:AI", dest_rel,
               f"would call {backend.id} for merge plan (dry-run — no AI call made)")
        return

    print(f"\n  Calling AI backend ({backend.id}) for merge plan of {dest_rel}...")
    fmt = schema if backend.schema_mode == SchemaMode.FORMAT_PARAM else None
    plan_text = backend.call(prompt, fmt=fmt, model_override=model_override, debug=debug)

    if plan_text is None:
        record("TODO", dest_rel, "AI merge failed — add section manually per APPLY.md")
        return

    try:
        plan = json.loads(_extract_json(plan_text))
    except json.JSONDecodeError as e:
        record("TODO", dest_rel, f"AI returned invalid JSON: {e}",
               "add section manually per APPLY.md")
        return

    # Validate insert_after_line is not inside an existing overlay block.
    # The AI cannot reliably detect overlay boundaries from the raw file content,
    # so we enforce this deterministically as a post-processing step.
    overlay_ranges = _find_overlay_ranges(existing_content)
    insert_line = plan.get("insert_after_line", 0)
    for ov_start, ov_end in overlay_ranges:
        if ov_start <= insert_line < ov_end:
            plan["insert_after_line"] = ov_end
            record("WARN", dest_rel,
                   f"AI chose insert_after_line={insert_line} (inside overlay block "
                   f"lines {ov_start}–{ov_end}); auto-corrected to {ov_end}")
            break

    delete_ranges = plan.get("delete_ranges", [])
    print(f"  Plan: insert after line {plan['insert_after_line']}, "
          f"delete {len(delete_ranges)} range(s) — {plan.get('reasoning', '')}")
    if not delete_ranges:
        record("WARN", dest_rel,
               "AI inserted section but removed nothing — verify no superseded content remains",
               "check for older/simpler versions of this section and remove manually if found")

    merged = apply_plan(plan, existing_content, open_marker, section_content,
                        close_marker, dest_rel)

    diff = list(difflib.unified_diff(
        existing_content.splitlines(keepends=True),
        merged.splitlines(keepends=True),
        fromfile=f"{dest.name} (before)",
        tofile=f"{dest.name} (after)",
        n=3,
    ))

    if yes:
        if do_backup:
            _backup(dest)
        dest.write_text(merged)
        record("MERGE:AI", dest_rel, f"merged via {backend.id} (--yes, no confirmation)")
    else:
        print("\n--- AI merge plan diff ---")
        print("".join(diff[:80]), end="")
        if len(diff) > 80:
            print(f"\n  ... ({len(diff) - 80} more lines)")
        print("--- end diff ---\n")
        try:
            ans = input("Apply? [y/N] ").strip().lower()
        except EOFError:
            record("TODO", dest_rel,
                   "AI merge ready but no interactive stdin — re-run with --yes to apply")
            return
        if ans == "y":
            if do_backup:
                _backup(dest)
            dest.write_text(merged)
            record("MERGE:AI", dest_rel, f"merged via {backend.id} (confirmed by user)")
        else:
            record("TODO", dest_rel, "AI merge rejected by user — add section manually")


def _extract_json(text: str) -> str:
    """Strip markdown code fences if present, then return the JSON text."""
    text = text.strip()
    # Strip ```json ... ``` or ``` ... ```
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop first line (```json or ```) and last line (```)
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        return "\n".join(inner).strip()
    return text


def _backup(path: Path) -> Path:
    import shutil
    bak = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, bak)
    return bak
