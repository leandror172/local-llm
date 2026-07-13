"""AI merge planner: deterministic plan executor + AI orchestration.

Two-verb stage/apply split (T-81): `stage_merge` calls the model, computes the
plan, prints a diff, and writes a durable plan-handle file WITHOUT touching the
target. `apply_staged_plan` re-reads that handle, verifies the target has not
changed since staging (the staleness invariant), and applies deterministically.
"""

import difflib
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .backends import Backend, SchemaMode, resolve_backend
from .report import record

PLAN_SCHEMA = "overlay-merge-plan/v1"
_DEFAULT_PLAN_DIR = ".claude/local/overlay-merge-plans"
_DIFF_CAP = 400


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


def _compute_merge_plan(
    existing_content: str,
    section_content: str,
    merge_hint: str,
    backend: Backend,
    prompts_dir: Path,
    model_override: str | None,
    open_marker: str,
    close_marker: str,
    dest_rel: str,
    debug: bool = False,
) -> tuple[dict, str] | None:
    """Shared core: prompt → parsed, overlay-range-corrected plan + merged content.

    Used by both `stage_merge` and the immediate (`--yes`/interactive) `ai_merge`
    path, so there is exactly ONE code path that produces a plan. Records a `TODO`
    (mirroring today's behaviour) and returns None on any failure — no backend
    prompt asset, model returned None, or invalid JSON. The returned plan is the
    corrected plan (insert_after_line moved out of any existing overlay block);
    the returned merged text is `apply_plan` applied to that corrected plan, so a
    caller's diff and a later `apply` from the stored plan agree by construction.
    """
    prompt = _build_prompt(prompts_dir, existing_content, section_content, merge_hint,
                           backend, dest_rel)
    if prompt is None:
        return None

    print(f"\n  Calling AI backend ({backend.id}) for merge plan of {dest_rel}...")
    schema = _load_schema(prompts_dir, dest_rel)
    fmt = schema if backend.schema_mode == SchemaMode.FORMAT_PARAM else None
    plan_text = backend.call(prompt, fmt=fmt, model_override=model_override, debug=debug)

    if plan_text is None:
        record("TODO", dest_rel, "AI merge failed — add section manually per APPLY.md")
        return None

    try:
        plan = json.loads(_extract_json(plan_text))
    except json.JSONDecodeError as e:
        record("TODO", dest_rel, f"AI returned invalid JSON: {e}",
               "add section manually per APPLY.md")
        return None

    _correct_insert_line(plan, existing_content, dest_rel)

    delete_ranges = plan.get("delete_ranges", [])
    print(f"  Plan: insert after line {plan['insert_after_line']}, "
          f"delete {len(delete_ranges)} range(s) — {plan.get('reasoning', '')}")
    if not delete_ranges:
        record("WARN", dest_rel,
               "AI inserted section but removed nothing — verify no superseded content remains",
               "check for older/simpler versions of this section and remove manually if found")

    merged = apply_plan(plan, existing_content, open_marker, section_content,
                        close_marker, dest_rel)
    return plan, merged


def _build_prompt(prompts_dir: Path, existing_content: str, section_content: str,
                  merge_hint: str, backend: Backend, dest_rel: str) -> str | None:
    """Render the merge-plan prompt template; None (with TODO) if an asset is missing."""
    prompt_path = prompts_dir / "merge-plan.txt"
    if not prompt_path.exists():
        record("TODO", dest_rel, f"AI merge skipped — prompt template missing: {prompt_path}")
        return None
    prompt = (
        prompt_path.read_text()
        .replace("<<EXISTING_CONTENT>>", existing_content)
        .replace("<<SECTION_CONTENT>>", section_content)
        .replace("<<MERGE_HINT>>", merge_hint)
    )
    schema_path = prompts_dir / "merge-plan-schema.json"
    if not schema_path.exists():
        record("TODO", dest_rel, f"AI merge skipped — schema missing: {schema_path}")
        return None
    if backend.schema_mode == SchemaMode.PROMPT_INJECTION:
        schema = json.loads(schema_path.read_text())
        prompt += f"\n\nRespond with a JSON object matching this schema:\n{json.dumps(schema, indent=2)}"
    return prompt


def _load_schema(prompts_dir: Path, dest_rel: str) -> dict:
    return json.loads((prompts_dir / "merge-plan-schema.json").read_text())


def _correct_insert_line(plan: dict, existing_content: str, dest_rel: str) -> None:
    """Move insert_after_line out of any existing overlay block, in place.

    The AI cannot reliably detect overlay boundaries from raw file content, so we
    enforce this deterministically as a post-processing step. This mutation lands
    in the STORED plan, so apply (which trusts the plan verbatim) matches the diff.
    """
    overlay_ranges = _find_overlay_ranges(existing_content)
    insert_line = plan.get("insert_after_line", 0)
    for ov_start, ov_end in overlay_ranges:
        if ov_start <= insert_line < ov_end:
            plan["insert_after_line"] = ov_end
            record("WARN", dest_rel,
                   f"AI chose insert_after_line={insert_line} (inside overlay block "
                   f"lines {ov_start}–{ov_end}); auto-corrected to {ov_end}")
            break


def _unified_diff(dest: Path, before: str, after: str) -> list[str]:
    return list(difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"{dest.name} (before)",
        tofile=f"{dest.name} (after)",
        n=3,
    ))


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
    """Immediate one-shot merge (the `--yes`/interactive path).

    `--dry-run` stays PURE (D1): it makes NO model call and writes nothing — it
    only records a pointer to `--stage`. The decoupled stage/apply verbs live in
    `stage_merge` / `apply_staged_plan`; this function is the legacy inline path.
    """
    dest_rel = dest.name

    if dry_run:
        record("MERGE:AI", dest_rel,
               f"would AI-merge {dest_rel} — run --stage to preview")
        return

    backend = resolve_backend(backends, backend_id, model_override)
    if backend is None:
        record("TODO", dest_rel,
               "AI merge skipped — no backend available",
               "add section manually per APPLY.md")
        return

    result = _compute_merge_plan(existing_content, section_content, merge_hint, backend,
                                 prompts_dir, model_override, open_marker, close_marker,
                                 dest_rel, debug)
    if result is None:
        return
    plan, merged = result
    diff = _unified_diff(dest, existing_content, merged)

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


# ── stage / apply (T-81) ──────────────────────────────────────────────────────


def stage_merge(
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
    plan_file: Path,
    debug: bool = False,
) -> Path | None:
    """Call the model, build the plan, print the diff, write the handle. Never
    touches `dest`. Returns the handle path, or None on failure (a TODO is
    recorded, so staging degrades to a message + reason exactly like install)."""
    dest_rel = dest.name

    backend = resolve_backend(backends, backend_id, model_override)
    if backend is None:
        record("TODO", dest_rel,
               "AI merge skipped — no backend available",
               "add section manually per APPLY.md")
        return None

    result = _compute_merge_plan(existing_content, section_content, merge_hint, backend,
                                 prompts_dir, model_override, open_marker, close_marker,
                                 dest_rel, debug)
    if result is None:
        return None
    plan, merged = result

    _print_diff(_unified_diff(dest, existing_content, merged))

    handle_path = _write_plan_handle(
        Path(plan_file), dest, open_marker, close_marker, section_content,
        plan, existing_content, backend.id,
    )
    _, version = _parse_open_marker(open_marker)
    record("STAGE", dest_rel, f"plan staged → {handle_path}",
           f"apply with: --apply-plan {handle_path}  "
           f"(staged overlay v{version}; re-stage if the overlay has since bumped)")
    return handle_path


def apply_staged_plan(plan_file: Path, do_backup: bool) -> None:
    """Read a staged handle, verify the target has not changed since staging (the
    staleness invariant), then apply deterministically and back up. Aborts —
    writing NOTHING — with a STALE record if the pre-image hash no longer matches."""
    plan_file = Path(plan_file)
    if not plan_file.exists():
        record("ERROR", str(plan_file), "plan handle not found")
        return
    try:
        handle = _read_plan_handle(plan_file)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        record("ERROR", str(plan_file), f"plan handle is not valid JSON: {e}")
        return
    if handle.get("schema") != PLAN_SCHEMA:
        record("ERROR", str(plan_file),
               f"unrecognized plan schema {handle.get('schema')!r}; expected {PLAN_SCHEMA!r}")
        return

    dest = Path(handle["dest"])
    dest_rel = handle["dest_rel"]
    if not dest.exists():
        record("ERROR", dest_rel, f"target no longer exists: {dest}")
        return

    from .actions import _read_text_eol, _write_text_eol  # deferred: avoid import cycle

    current, crlf = _read_text_eol(dest)
    if _hash_pre_image(current) != handle["target_pre_sha256"]:
        record("STALE", dest_rel,
               f"target changed since plan was staged ({handle.get('staged_at')}); "
               "re-stage with --stage")
        return

    merged = apply_plan(handle["plan"], current, handle["open_marker"],
                        handle["section_content"], handle["close_marker"], dest_rel)
    if do_backup:
        _backup(dest)
    _write_text_eol(dest, merged, crlf)
    bak_note = f"backup: {dest_rel}.bak" if do_backup else "no backup (use --backup to enable)"
    record("APPLY", dest_rel,
           f"merged via {handle.get('backend_id')} from staged plan", bak_note)


def stage_all_sections(
    manifest: dict,
    overlay_dir: Path,
    target_root: Path,
    prompts_dir: Path,
    backend_id: str,
    model_override: str | None,
    backends: list[Backend],
    plan_file: str | None,
    debug: bool = False,
) -> None:
    """Walk `manifest['merge_sections']` like the install path, but only STAGE each
    unmarked target. Already-marked targets get a SKIP; absent targets a TODO."""
    from .actions import _read_text_eol  # deferred: avoid import cycle

    overlay_name = manifest["name"]
    overlay_version = manifest["version"]
    open_pattern = re.compile(
        rf"<!-- overlay:{re.escape(overlay_name)} v(\d+) -->", re.MULTILINE
    )

    for dest_rel, spec in manifest.get("merge_sections", {}).items():
        section_file = overlay_dir / spec["file"]
        dest = target_root / dest_rel
        merge_hint = spec.get("merge_hint", "")

        if not section_file.exists():
            record("ERROR", dest_rel, f"section file missing in overlay: {spec['file']}")
            continue
        if not dest.exists():
            record("TODO", dest_rel,
                   "dest file absent — nothing to stage; run install to create it")
            continue

        existing, _crlf = _read_text_eol(dest)
        marked = open_pattern.search(existing)
        if marked:
            record("SKIP", dest_rel,
                   f"already installed v{int(marked.group(1))} — nothing to stage")
            continue

        section_content = section_file.read_text().rstrip()
        open_marker = f"<!-- overlay:{overlay_name} v{overlay_version} -->"
        close_marker = f"<!-- /overlay:{overlay_name} -->"
        pf = _resolve_plan_file(plan_file, target_root, overlay_name, dest_rel)
        stage_merge(dest, existing, section_content, open_marker, close_marker,
                    merge_hint, backend_id, model_override, backends, prompts_dir, pf, debug)


def _resolve_plan_file(plan_file: str | None, target_root: Path,
                       overlay_name: str, dest_rel: str) -> Path:
    """The explicit --plan-file if given, else the default gitignored location."""
    if plan_file is not None:
        return Path(plan_file)
    slug = dest_rel.replace("/", "__")
    return target_root / _DEFAULT_PLAN_DIR / f"{overlay_name}__{slug}.json"


def _print_diff(diff: list[str]) -> None:
    print("\n--- AI merge plan diff ---")
    print("".join(diff[:_DIFF_CAP]), end="")
    if len(diff) > _DIFF_CAP:
        print(f"\n  ... ({len(diff) - _DIFF_CAP} more lines)")
    print("--- end diff ---\n")


# ── plan-handle persistence (T-81) ────────────────────────────────────────────


def _hash_pre_image(text: str) -> str:
    """sha256 hexdigest of the exact pre-image string handed to apply_plan."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_open_marker(open_marker: str) -> tuple[str, int]:
    match = re.match(r"<!-- overlay:(\S+) v(\d+) -->", open_marker)
    if not match:
        raise ValueError(f"invalid open_marker format: {open_marker!r}")
    return match.group(1), int(match.group(2))


def _write_plan_handle(
    plan_file: Path,
    dest: Path,
    open_marker: str,
    close_marker: str,
    section_content: str,
    plan: dict,
    pre_image: str,
    backend_id: str,
) -> Path:
    overlay_name, version = _parse_open_marker(open_marker)
    handle = {
        "schema": PLAN_SCHEMA,
        "overlay": overlay_name,
        "version": version,
        "dest": str(dest),
        "dest_rel": dest.name,
        "open_marker": open_marker,
        "close_marker": close_marker,
        "section_content": section_content,
        "plan": plan,
        "target_pre_sha256": _hash_pre_image(pre_image),
        "backend_id": backend_id,
        "staged_at": datetime.now(timezone.utc).isoformat(),
    }
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    plan_file.write_text(json.dumps(handle, indent=2))
    return plan_file


def _read_plan_handle(path: Path) -> dict:
    return json.loads(path.read_text())


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
