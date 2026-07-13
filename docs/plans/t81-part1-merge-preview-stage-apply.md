# T-81 Part 1 — AI-merge preview: stage → apply split

**Status:** PLAN (ready to build). Owner task: **T-81** (part 1 of 2).
**Implementer:** Sonnet subagent, high effort. Self-contained; read the cited files, don't guess.
**Sibling plan:** `docs/plans/t81-part2-merge-completion-tuning.md` (independent; can land in either order — Part 1 is built + tested with a **mocked** backend and needs no live model).
**No oficina.** This is a pure client-side refactor of the overlay installer's AI-merge path. Decided 2026-07-12 with the user: install-overlay is a one-shot CLI with nothing to do while the GPU works, so the async substrate buys it nothing here; its only wins (no transport timeout, durable plan) are obtained more cheaply — the timeout in Part 2, the durable plan by the staging file below.

---

## 1. Problem (T-81 defect **a**)

`overlays/install-overlay.py --mode ai` merges an overlay section into a target file that exists but has no overlay marker (the only case that reaches `ai_merge`; see `handle_merge_sections` in `overlays/lib/actions.py`, the `else: if mode == "ai"` branch). Two problems, this plan fixes the first:

- **(a) No preview before it writes.** `ai_merge`'s `dry_run` branch (`overlays/lib/planner.py:104-107`) only records `"would call … (dry-run — no AI call made)"`. The *only* way to see what the AI would do is to let it do it — on a repo's most load-bearing file (`CLAUDE.md`). There is no plan-then-apply seam.

## 2. Goal

Split the AI merge into **stage** and **apply**, mirroring the session-handoff pipeline's stage/promote shape (`ref:handoff-cli-surface` in `overlays/session-tracking/.memories/KNOWLEDGE.md`), which solved exactly this: validate + build the result in memory, emit a **durable handle**, mutate real files only on a second call.

- **Stage** (`--stage`): call the model, compute the merge, **print a unified diff**, write a **plan-handle file**, and **do not touch the target**.
- **Apply** (`--apply-plan <handle>`): re-read the handle, **verify the target has not changed since staging**, apply deterministically, back up, write.

`--yes` keeps today's one-shot stage+apply (no prompt); the interactive `Apply? [y/N]` path stays too. The new capability is the *decoupled* stage/apply.

### Design decision D1 — two explicit verbs (`--stage` / `--apply-plan`), keep `--dry-run` pure (DECIDED)

`--stage` and `--apply-plan` are **symmetric early-branches** in `main()`, exactly like `--verify` (`install-overlay.py:121-126`): each does only the merge work and exits, touching none of the other handlers. `--dry-run` stays **pure and cheap** — it previews the full install sequence and, for an unmarked `--mode ai` target, records `"would AI-merge <dest> — run --stage to preview"` **without calling the model or writing anything**.

This was decided over the alternative of overloading `--dry-run` to *be* the stage. Reasons (advisor + `feedback_special_case_comments` / `feedback_config_over_keep_regions`):
- `handle_merge_sections` runs inside the *full* handler sequence (`install-overlay.py:135`) and receives `dry_run`. Overloading it would make an ordinary `--mode ai --dry-run` full-sequence preview **fire a multi-minute GPU call and write a plan file as a side effect** — dry-run doing an expensive, file-writing thing. That is a special-case behavior bolted onto a general mechanism, the exact smell those memories name.
- It matches the handoff pipeline's two-verb `--payload`→`--id` shape (`ref:handoff-cli-surface`), the precedent the task itself points to. The task line "a separate `--apply <plan>`" implies a stage step that *produces* the named `<plan>` — a two-verb shape. "`--dry-run` should call the model" is satisfied in spirit by the pure preview line above without producing a durable handle.

So: **`--stage` = stage (early-branch), `--apply-plan <handle>` = apply (early-branch), `--dry-run` = pure preview.** `--stage` requires `--mode ai` (error otherwise) and operates on the manifest's `merge_sections` for the given overlay/target.

## 3. The staleness invariant (re-derive this, do not trust the tests)

Per `feedback_review_rederive_invariants`: state the property first, check it against the code directly.

> A merge plan (`insert_after_line` + `delete_ranges`) is a set of **line numbers valid only against the exact pre-image it was computed from.** Applying it to any other file version silently corrupts (line numbers shift under edits).

Therefore the handle **must** carry `target_pre_sha256 = sha256(pre-image)`, and **apply must abort** unless `sha256(current target) == target_pre_sha256`. This is the one genuinely new safety element; everything else is plumbing. Test it directly (a test that only exercises the happy path would pass while this hole is open — the exact failure mode the memory warns about).

## 4. Files & exact seams

Read before editing (use the Read tool — you will Edit these; `feedback_read_before_edit`):

| File | What's there now | Change |
|---|---|---|
| `overlays/lib/planner.py` | `ai_merge(...)` (l.59-179), `apply_plan(...)` (l.13-39, **pure — keep**), `_find_overlay_ranges`, `_extract_json`, `_backup` | Refactor `ai_merge`; add `stage_merge`, `apply_staged_plan`, `_compute_merge_plan`, `_write_plan_handle`, `_read_plan_handle`, `_hash_pre_image` |
| `overlays/install-overlay.py` | arg parser (l.54-84), `--verify` early-branch (l.121-126), handler calls (l.128-140) | Add `--stage` (flag) + `--apply-plan PATH` + `--plan-file PATH` (optional); two early-branches mirroring `--verify`; make `--dry-run` record the pure "would AI-merge … run --stage" line in `handle_merge_sections` |
| `overlays/lib/report.py` | `record(action, target, reason="", details="")` (l.9) | Use new actions `STAGE` / `APPLY` / `STALE`; no signature change |
| `overlays/lib/actions.py` | `handle_merge_sections(...)` calls `ai_merge` (l.315) | No behavior change; it already passes `dry_run` — `ai_merge` now branches on it into `stage_merge` |

`apply_plan` is already a pure `(plan, existing_content, markers) -> merged` function. **Do not change its signature or behavior** — both stage (for the diff) and apply reuse it. This is why the split is cheap.

### Named methods (honor `feedback_code_as_documentation`)

Public/semantic names; hide generic dispatch privately:

- `stage_merge(dest, existing_content, section_content, open_marker, close_marker, merge_hint, backend_id, model_override, backends, prompts_dir, plan_file, debug) -> Path | None` — call model, build plan, print diff, write handle, **never touch dest**. Returns the handle path. Invoked from the `--stage` early-branch (which walks `merge_sections` like `handle_merge_sections` does, but only stages).
- `apply_staged_plan(plan_file: Path, do_backup: bool) -> None` — read handle, verify pre-image hash, `apply_plan`, backup, write.
- `_compute_merge_plan(existing_content, section_content, merge_hint, backend, prompts_dir, model_override, open_marker, close_marker, dest_rel, debug) -> tuple[dict, str] | None` — the shared "prompt → parsed, overlay-range-corrected plan + merged content" core, factored out of today's `ai_merge` body (lines 84-146). Used by `stage_merge` **and** the existing immediate (`--yes`/interactive) path, so there is one code path for producing a plan.
- `_write_plan_handle(...)`, `_read_plan_handle(path) -> dict`, `_hash_pre_image(text) -> str` (sha256 hexdigest of the exact string handed to `apply_plan`).

## 5. Plan-handle schema (`overlay-merge-plan/v1`)

JSON, written by stage, read by apply. Everything needed to re-apply deterministically + the staleness guard + provenance:

```json
{
  "schema": "overlay-merge-plan/v1",
  "overlay": "session-tracking",
  "version": 11,
  "dest": "/abs/path/to/target/CLAUDE.md",
  "dest_rel": "CLAUDE.md",
  "open_marker": "<!-- overlay:session-tracking v11 -->",
  "close_marker": "<!-- /overlay:session-tracking -->",
  "section_content": "…the section to insert (verbatim)…",
  "plan": { "insert_after_line": 42, "delete_ranges": [{"start": 10, "end": 14, "reason": "…"}], "reasoning": "…" },
  "target_pre_sha256": "<hex of the exact pre-image string>",
  "backend_id": "local-qwen3-14b",
  "staged_at": "2026-07-12T23:40:00+00:00"
}
```

Store the **plan + pre-image hash**, not the merged blob: transparent, reviewable, small; and since `apply_plan` is pure, recomputing at apply == stage-time result *provided* the pre-image matches (which the hash enforces). `staged_at` uses `datetime.now(timezone.utc).isoformat()` — this is ordinary Python (the `Date.now()` ban is workflow-scripts only).

### Handle location

Default dir: **`<target_root>/.claude/local/overlay-merge-plans/`** — `.claude/local/` is already gitignored in every consumer repo (CLAUDE.md: "Sensitive data: `.claude/local/` (gitignored)"), so handles never pollute a tracked tree and need no new `.gitignore`. Filename: `<overlay>__<dest_rel_slug>.json` where `dest_rel_slug = dest_rel.replace("/", "__")`. Overridable with a new `--plan-file PATH` arg (optional; default computed as above). `mkdir(parents=True, exist_ok=True)` the dir on stage.

## 6. Flow detail

**Dry-run** (`handle_merge_sections`, `dry_run=True`, unmarked `--mode ai` target): record `"would AI-merge <dest_rel> — run --stage to preview"`. **No model call, no writes.** (This replaces today's `ai_merge` dry-run branch, which is now unreachable from the normal sequence.)

**Stage** (`--stage` early-branch → `stage_merge` per section):
1. `_compute_merge_plan(...)`. On any failure (no backend / bad JSON / model returned None) record a `TODO` exactly as today and return `None` — staging degrades to a message *plus* the reason.
2. Build the unified diff (reuse today's `difflib.unified_diff` block, l.148-154) and **print it** (full, not truncated to 80 lines — this is the whole point of a preview; keep a sane cap like 400 lines with a "… N more" footer).
3. `_write_plan_handle(...)` → handle path. `record("STAGE", dest_rel, f"plan staged → {handle_path}", "apply with: install-overlay … --apply-plan <path>")`.
4. Return without touching `dest`.

**Apply** (`install-overlay.py` early-branch when `--apply-plan` set → `apply_staged_plan`):
1. Read + JSON-parse the handle; validate `schema == "overlay-merge-plan/v1"` (else clear error + `record("ERROR", …)`).
2. Read current `dest` bytes → decode with the same EOL handling as `handle_merge_sections` (`_read_text_eol` in `actions.py`; import/reuse it — do **not** regress CRLF; T-29 tracks the deeper EOL gap and is out of scope, just don't worsen it).
3. **Compute `sha256(current pre-image)`; if `!= target_pre_sha256` → abort**: `record("STALE", dest_rel, "target changed since plan was staged (…staged_at); re-stage with --dry-run")`, print, exit nonzero. **Write nothing.**
4. `merged = apply_plan(plan, current_existing, open_marker, section_content, close_marker, dest_rel)`.
5. If `do_backup`: `_backup(dest)`. Write `merged` (via `_write_text_eol` to match the pre-image's EOL). `record("APPLY", dest_rel, f"merged via {backend_id} from staged plan", "backup: …")`.

Main-loop branches (mirror `--verify`, `install-overlay.py:121-126`), placed **before** the manifest/handler sequence:
```python
if args.stage:
    if args.mode != "ai":
        parser.error("--stage requires --mode ai")
    stage_all_sections(manifest, overlay_dir, target_root, prompts_dir,
                       args.backend, args.model, backends, args.plan_file, args.debug)
    print_report(args.report_format, args.report)
    sys.exit(0)   # or 1 if any section recorded ERROR/TODO
if args.apply_plan:
    apply_staged_plan(Path(args.apply_plan), args.backup)
    print_report(args.report_format, args.report)
    sys.exit(0)   # or 1 if STALE/ERROR recorded — track via report state
```
`apply_staged_plan` needs only the handle (no manifest walk, no backend load — `backend_id` is provenance already in the handle). `stage_all_sections` walks `manifest["merge_sections"]` like `handle_merge_sections` but calls `stage_merge` per unmarked target (skip already-marked ones with a SKIP, same as the install path).

**Version note (advisor):** the handle carries `version` and `section_content` captured at stage time. If the overlay bumps (v11→v12) between stage and apply, `--apply-plan` writes the **staged** section/version, not the newer one — acceptable and correct (you apply what you reviewed), but state it in the STAGE record so it isn't surprising: `"staged section is overlay v{version}; re-stage if the overlay has since bumped"`.

## 7. TDD (hermetic, mockable, no network)

New suite: **`overlays/test_merge_stage_apply.py`** (plain sync pytest; `from lib.planner import …`, `from lib.actions import _read_text_eol`; runs with `overlays/` as cwd). Wire it in: add the filename to the `pytest` line in **`overlays/scripts/test-installer.sh`**; `run-all-tests.sh` and `make test` aggregate through that runner automatically (`ref:overlay-test-convention`).

The backend is the mock seam: define a `FakeBackend` with `.id`, `.schema_mode`, **`.is_available() → True`** (else `resolve_backend` in `planner.py` drops it and the stage silently no-ops — advisor catch), and `.call(prompt, fmt=…, model_override=…, debug=…)` returning a canned plan JSON string (plus a variant returning `None`, and one returning non-JSON). Give it a call counter so tests can assert whether `.call` fired. Pass `[FakeBackend(...)]` as `backends`. All fixtures build their own tmp target file + tmp plan dir (`tmp_path`); **nothing reads the real repo** (hermeticity — `ref:overlay-test-convention`).

Test names encode the contract (write these; delegate the bodies to the local model per `feedback_delegate_test_writing` — scaffold named empty tests + a module docstring stating the contract, then `generate_code` the bodies with the scaffold as `context_files`; local-first per `feedback_ollama_workflow`):

| Test | Proves |
|---|---|
| `test_stage_calls_backend` | Defect-(a) fix: `--stage` invokes `FakeBackend.call` (assert call counter ≥ 1) |
| `test_dry_run_does_not_call_backend` | Purity of `--dry-run` (D1): under `dry_run` the counter stays 0, no handle written, only a "would AI-merge … run --stage" record |
| `test_stage_writes_handle_without_touching_target` | target bytes unchanged after stage; handle file exists |
| `test_stage_handle_records_pre_image_hash` | `target_pre_sha256 == sha256(original target)`; schema/markers/section present |
| `test_stage_prints_unified_diff` | captured stdout contains `--- …/+++ …` and the inserted section text |
| `test_stage_degrades_to_todo_on_bad_json` | `FakeBackend` returns non-JSON → `TODO` recorded, no handle written, target untouched |
| `test_apply_writes_merged_and_backs_up` | after apply, target contains markers+section; `.bak` exists when `do_backup` |
| `test_apply_aborts_when_target_changed_since_stage` | **the invariant**: mutate the target between stage and apply → apply records `STALE`, writes nothing, no `.bak` |
| `test_apply_errors_on_missing_or_wrong_schema_handle` | missing file / wrong `schema` → clear ERROR, nonzero, no write |
| `test_apply_result_equals_stage_time_merge` | **independent-path check** (`feedback_review_rederive_invariants`): compute expected merged via a second, hand-rolled path (splice section at `insert_after_line` after deletes) and assert equality with apply's output — do not just re-call `apply_plan` |
| `test_stage_then_apply_end_to_end` | full round-trip on a multi-section fixture with a `delete_ranges` entry |
| `test_apply_preserves_crlf` | CRLF target stays CRLF after apply (guards the `_read/_write_text_eol` reuse) |

## 8. Acceptance (live, after the suite is green)

Using a **copy** of a real target in `~/workspaces/tmp/` (per `feedback_use_workspaces_tmp`; never the repo's live `CLAUDE.md`). Part 1 can use a *small* target so a real model call is fast (Part 2 handles the big-file case):
1. `install-overlay session-tracking --target ~/workspaces/tmp/acc-repo --mode ai --stage` → prints a diff, writes a handle under `.claude/local/overlay-merge-plans/`, leaves the target untouched (`cmp` before/after). (Also confirm plain `--dry-run` on the same target makes **no** model call and writes no handle.)
2. `--apply-plan <handle>` → target now carries the section between markers; `.bak` written.
3. Re-run apply on the same handle → **STALE** (target now differs from the staged pre-image) — proves the guard.
4. `git`-style `diff` the applied file vs an expected fixture.

## 9. Out of scope (do NOT build here)

- Completion/latency (`num_ctx`, arm choice, timeout) — that is **Part 2**. Part 1 assumes the backend call works (mock in tests, small file in live acceptance).
- Chunking the target. Deferred in Part 2; irrelevant here.
- oficina / async. Explicitly excluded (user decision).
- Deep EOL rework (T-29) — reuse `_read/_write_text_eol`, don't regress, don't fix T-29.

## 10. Definition of done (verify, don't claim — `feedback_verify_done_claims`)

**You OWN (edit directly):** code, tests, `overlays/install-overlay.py` header usage block (it's part of the code you change), and any *new* file you create.

**You PROPOSE (in your final report — do NOT edit these; the parent applies them):** all edits to shared tracking / memory / README files. This matches the user's instruction that subagent *output* contains suggestions for updating memories/README, and avoids write-conflicts on files the sibling subagent and parent also touch.

- [ ] `make -C overlays test` green **including** the new suite (paste the count).
- [ ] Live acceptance 1-4 above pass on a tmp copy (paste the STALE-guard evidence + the dry-run-purity check).
- [ ] `overlays/install-overlay.py` header usage block documents `--stage` / `--apply-plan` / `--plan-file` and the pure-preview behavior of `--dry-run` (this you edit — it's in the code).
- [ ] **Report proposes** (with exact text/anchor): `overlays/session-tracking/.memories/KNOWLEDGE.md` `ref:overlay-ai-merge-mode` stage/apply design + staleness invariant; `.claude/index.md` rows for `overlays/test_merge_stage_apply.py` + this plan; `.claude/tasks.md` T-81 part-1 checkoff; any MEMORY.md/README suggestion.
- [ ] Report each item with the artifact (file/line/test), not a bare "done". You MAY call `advisor` before declaring done.
