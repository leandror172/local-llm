# overlays/ — Knowledge (Semantic Memory)

*Overlay system decisions. Read on demand.*

## Why Overlays Exist (2026-03)

Three repos need the same operational patterns: ref-indexing for documentation lookups,
session tracking for continuity across Claude Code sessions, local model conventions
for verdict recording and retry policy. Copying files manually drifts. Overlays make
cross-repo consistency installable and version-tracked.

**Rationale:** The alternative was documenting conventions and hoping each repo
implements them correctly. Overlays encode conventions as installable packages.
**Implication:** New cross-cutting patterns should become overlays, not wiki pages.

## Merge Markers for Versioning (2026-03)

Overlay content injected into shared files (like CLAUDE.md) is wrapped in markers:
`<!-- overlay:ref-indexing v1 -->`. On update, the installer detects the old version,
removes the old content, and inserts the new version.

**Rationale:** CLAUDE.md is a shared file — multiple overlays and manual content coexist.
Markers let the installer find and replace its own content without touching the rest.
**Implication:** Manual edits inside overlay markers will be overwritten on update.
Customizations should go outside the markers.

## AI-Assisted Merge Mode (2026-03)

When `--mode ai` is used, an LLM plans where to insert overlay sections into existing
files. The planner outputs structured JSON (insert_after_line, delete_ranges), which
is then applied deterministically — the AI plans, code executes.

Backends (priority order): Ollama qwen3:14b with thinking, Ollama deepseek-r1:14b,
Claude CLI subprocess, Claude API direct.

**Rationale:** CLAUDE.md files have varying structure. Hard-coding insertion points
would break across repos. AI reads the target file and decides the right location.
**Implication:** AI merge is optional — manual mode always works. AI mode saves time
on initial install but manual review is still recommended.

## Manifest Schema (2026-03)

Each overlay has a `manifest.yaml` defining what to install:
- `files` — copy to destination (tools, scripts)
- `templates` — create only if missing (user-managed after creation)
- `merge_sections` — inject into shared files with merge hints
- `append_lines` — idempotent append to .gitignore, .githooks, etc.
- `manual_if_exists` — flag files that need human judgment if already present

**Rationale:** Declarative manifest over imperative script. The installer interprets
the manifest; the overlay author declares intent.
**Implication:** Adding a new overlay requires only a manifest and content files,
no changes to the installer itself.

## User-Level vs Project-Level Skills (2026-03)

Some overlays install Claude Code skills. `--skill-level user` puts them in
`~/.claude/skills/` (available in all repos). `--skill-level project` puts them
in the repo's `.claude/skills/` (repo-specific). Default is user-level.

**Rationale:** Skills like session-handoff and create-persona are useful everywhere,
not just in one repo. User-level avoids duplicating them across projects.
**Implication:** User-level skills are not version-controlled per repo. Changes
require updating the user-level installation separately.

## Session-Handoff Pipeline Architecture (2026-06)

The `session-tracking` overlay's handoff pipeline (`files/handoff/`) replaces the token-heavy
"Claude reads every tracking file and writes each section via many Edits" skill with a
register-driven deterministic transaction. Scope A uses **NO local model**.

- **Register** (`registry.yaml`): per-repo source of truth mapping each handoff-owned region to a
  file + locator (4 kinds: ref_block / structural / field / checklist) + write mode (replace /
  prepend / append / checkoff / nomodel). It also draws the safety boundary — every OTHER ref key is
  content / LTG anchor the pipeline MUST NOT touch.
- **F1 Locator → F3 Applier → F4 Verifier** (safety core): pure functions over `(role/Region, text)`.
  `Region(start,end,interior)` is the single boundary source of truth. F4 = recompute-and-compare
  (re-derive expected text byte-exact, independent of apply) + ref-marker multiset invariant — the
  trust boundary that will let an untrusted model run in the deferred enhancement.
- **F5 Mechanics** (`mechanics.py`): header-field bumps through the **nomodel fence** (the applier
  *refuses* nomodel so the payload path can never write headers — only the script can; the verifier
  *accepts* nomodel as replace), next-session-N (bootstraps to 1 on a fresh repo), date, rotation invoker.
- **F6 Orchestrator** (`orchestrator.py` + injected `gitio` adapter): atomic stage → apply → verify →
  write → rotate → commit, with **two safety layers** — in-memory verify-then-write + git checkout
  rollback — guarded by a clean-tree precondition on the tracking files.
- **Per-run logging** (`runlog.py`): `.claude/local/handoff-runs/session-<N>-<ts>/` holds `input.md`
  (verbatim payload = recovery artifact) + `report.md` (audit).
- **F7 payload + entrypoint** (`payload.py` schema; `registry_io.py` PyYAML loader; `handoff.py` CLI +
  `run-handoff.sh`): payload = first-two-`---` frontmatter (`session_title`/`current_layer`/`checkoffs`)
  + `## role:` sections. `--dry-run` runs the pure half (`_stage_and_apply`) and writes nothing — the
  rehearsal and the foundation for the T-53 preflight. PyYAML is allowed only in the entrypoint glue
  (`registry_io`); the F1–F6 safety core stays stdlib-only.
- **Install layout** (`manifest.yaml`): 10 runtime modules + `run-handoff.sh` ship via `files:` →
  `.claude/tools/handoff/`; the **register** ships via `manual_if_exists` → `.claude/handoff/registry.yaml`
  (**Option C**: copy-once, then *flag-on-update* — it's load-bearing yet per-repo, so neither silent
  overwrite nor silent skip is right). `handoff.py` resolves `repo_root` via `git rev-parse`, so the
  default registry path is correct without flags in installed repos.

**Rationale:** keep *decide content* with Claude, collapse *read+write* into one deterministic
register-driven call — no new in-file markers (they would pollute the LTG corpus that ingests
`.claude/` + `.memories/`). **Implication:** the register is both the repo-customization seam and the
handoff-owned-vs-content boundary; load-bearing contracts (register, F7 schema, F6 orchestration) stay
Claude-authored, while leaf modules (F5, logging) are local-model-delegable. Status (session 87):
**B1–B4 complete — Scope A fully done, 77 tests, dog-food-validated** (clone run on real content/register).
**PR #50** open (stacked on `feature/ltg-phase3-anchors`; retarget to master after the LTG PR merges).
**Home-repo activation:** the skill is installed *project-level* in the llm repo; the pipeline code is
NOT copied into `.claude/tools/` there (would duplicate the overlay source) — the skill's home-repo note
runs `overlays/session-tracking/files/handoff/run-handoff.sh` with an explicit `--registry`. Target repos
get the canonical `.claude/tools/handoff/` layout via the installer instead.

**Planned redesign (session 89) — stage/promote:** Replaces the `--dry-run --payload` two-step with
**rename-on-ingest + stage/promote**. `--payload` ingests (renames file into run dir via `shutil.move`,
freeing the well-known path) + stages (locate+apply+verify in memory) + emits JSON handle.
`--id <handle>` promotes: finds pending run dir, recomputes everything from current files (no cached
edits), checks git for idempotency (prevents double-apply if process dies between commit and dir-rename),
applies, commits, renames dir `-pending`→`-success`. Run dir status suffix (`-pending`/`-success`/
`-failed`) replaces the old "writes nothing in dry-run" invariant. `--dry-run` flag dropped.
Two failure branches: validation-fail = no handle (re-edit same file); stage-fail = handle exists
in `-failed` dir (author fresh content). Full plan: `~/.claude/plans/handoff-redesign-rename-on-ingest.md`.
Branch: `feature/handoff-redesign-stage-promote`.

**Dog-food learning (session 86):** F4's invariants are *out-of-region bytes* + *ref-marker multiset* —
neither sees a **missing newline before a present marker**. A payload's last `## role:` section has no
trailing blank, so `payload.py` returned non-newline-terminated content, and append/replace/prepend glued
the line onto the closing marker. Fixed at the seam (`_normalize_block` in `_collect_edits`), NOT in the
safety core: the applier/verifier share an implicit "content is newline-terminated" contract and must
stay byte-identical, so normalize once upstream where both consume the same `items`.

## Stage/promote redesign (sessions 89–90) — IMPLEMENTED

- **Status:** COMPLETE — PR #52 open, 126 tests green, overlay v5 propagated to 3 repos (byte-verified)
- **`--payload` (stage):** validate → ingest (copy payload into run dir) → locate+apply+verify in memory → emit JSON handle; dir stays `-pending`; original payload deleted only on success (unlink is the LAST op — crash-safe, failed stage leaves the author's file in place)
- **`--id` (promote):** find `-pending` run → idempotency check by commit-title suffix → `run_handoff` → rename dir to `-success`/`-failed`
- **Idempotency key insight:** check commit-title suffix, NOT session number — after first commit the header updates and `peek_session_number` returns N+1 (false-miss on crash-recovery)
- **T-57 fix:** `_effective_range` in `verifier.py` collapses append→insertion-point and checkoff→3-byte range; reconstruction sort matches applier's stable-sort-descending for equal-start regions

## Session-29 feedback round (2026-06-12) — five fixes from expenses field report

The first real-world run in expenses (session 29) surfaced 5 problems (P1–P5, report at
`~/workspaces/expenses/code/.claude/local/handoff-pipeline-feedback-session29.md`). Root-cause
analysis found TWO meta-failures beyond the pipeline itself: (a) commit 75886bb *claimed* the
SKILL.md rewrite (T5) but only touched manifest.yaml — the work never existed, so every SKILL.md
still taught the removed `--dry-run`; (b) the v4 propagation was PARTIAL — expenses had a stale
`verifier.py` without `_effective_range`, so they hit the already-fixed T-57 overlap on the most
common payload shape (checkoffs + tasks-append).

Fixes (commits f6d1116, 771ea5c, bba6cce, 0fdb42f, 979f66f):
- **Error specificity (P-msg):** overlap errors name both regions `role(target)@file:line`;
  validation errors state WHY ("required because this run bumps the Current Session header").
  Rationale: converts every failure from "read pipeline source" (~5 calls) into "fix payload" (1 call).
- **`--amend` (P4+P5):** follow-up run attached to LAST COMMITTED session N (derived, never typed);
  append+checkoff modes only (prepend excluded — a log-entry prepend would duplicate the session
  heading); scalars not required; no header write; idempotency check skipped; commit suffix `— amend`.
  Design principle: the recovery path is strictly LESS powerful than the happy path — worst possible
  amend mistake is a duplicate appended task. Mode persisted in `<run_dir>/mode` sidecar.
- **`--abort <handle>`:** renames `-pending`→`-aborted`. Every missing CLI verb becomes an ad-hoc
  `rm` invented under pressure; this closes that gap.
- **Copy-don't-move (P3):** stage copies payload to `input.md` up front; unlink-original is the final
  step on success only. Failed/crashed stage never consumes the author's file.
- **SKILL.md (P1):** rewritten for the real CLI; exact pre-flight one-liner with correct empty-output
  semantics; the 3 copies (overlay source / llm project / user-level) unified byte-identical — the
  overlay+user copies also had a WRONG checkoff description (claimed bolded ids fail; locator.py is
  flexible) that the project copy had right.

**Process learnings:** (1) overlay propagation needs a verify step — per-file `cmp` against source
caught nothing wrong this time only because we ran it; consider an installer `--verify` mode.
(2) "Task done" claims in commit messages/memory are unverified — T5 was recorded done in QUICK.md
and a commit message while no diff existed. (3) Subagent review must re-derive invariants, not trust
green tests: review caught an amend stage/promote session-number mismatch (N+1 vs N — would have
recreated the exact "session 30 surprise") and the prepend allowlist hole, both behind passing tests.

## Session-90 redesign — latest-only topology + value-only + harvest (2026-06-16) — IMPLEMENTED

This round cut the *token cost of AUTHORING a handoff* (the prior work cut the mechanical apply cost).
Three increments + a one-time data migration; manifest v5→v6 (clean break, D2). 126→166 tests green.

- **Latest-only topology (P1):** `session-log.md` holds exactly the newest entry. `rotate-session-log.sh`
  archives EACH spilled entry into its own `session-log-<date>-s<N>-<slug>.md` (slug = lowercased,
  alnum→hyphen, ≤40 chars; fallback `sNN`) and runs with `--keep 1`. The `header-previous-logs` role is
  dropped from `registry.yaml` and the ~46-ref `Previous logs:` pointer line is gone — the archive dir +
  slugged filenames ARE the index. Rationale: the single growing file + giant pointer line was the bloat;
  self-identifying per-entry files mirror the user's `/export` naming and pair with exported transcripts.
- **Value-only payload (P2, D1=2-full):** `log-entry` became structured snake_case sub-slots; the pipeline
  renders ALL scaffold (the `## <date> - Session N: <title>` heading from date + derived N + session_title,
  plus `### Context/What Was Done/Decisions Made/Next/Gotchas` + bullets). New: `LogEntry` dataclass +
  `render_log_entry()` (mechanics.py), `HandoffPayload.log_entry` + slot parser (payload.py); orchestrator
  computes `header_values` once and renders log-entry with the SAME `session_number`. CRITICAL: `parse()`
  excludes log-entry from `payload.blocks` to prevent double-apply; the session-86 newline contract is
  double-guarded (`render_log_entry` rstrips then re-adds one `\n`; `_normalize_block` still wraps). Field
  names kept aligned with the deferred local-model Placer schema (forward-compatible). Clean break: the old
  free-block `log-entry` form is rejected with a migration error.
- **Git-log harvest (P3):** `handoff-harvest.sh` = `git log <newest chore(session-handoff):>..HEAD
  --format=%s` (fallback: last 20 + stderr note). Seeds `what_was_done` deterministically — zero model,
  zero re-read. SKILL Step 2 calls it as the skeleton; Step 3 adds "reuse replace-mode interiors already
  resident in context rather than re-`ref-lookup`" (attacks the duplicate-resident-content failure mode iii).
- **Propagation (P4):** manifest v5→v6; installed into expenses/code, web-research, career-search; every
  `files:` entry byte-verified with `cmp` (14/14 per repo — the ONLY safety net, targets ship no tests).
  SKILL is per-consumer: global `~/.claude/skills/` serves web-research+career-search; expenses/code and
  llm have project-level copies that SHADOW the global (force-cp each — `user_files` is skip-if-present).
  llm runs the engine from source but calls rotate by the INSTALLED path, so its installed rotate + harvest
  were refreshed too. Target registries left untouched (`manual_if_exists`) — confirmed safe: the pipeline
  only walks payload→register, never register→payload, so the orphaned `header-previous-logs` role is inert.
- **Data migration (one-time, all 4 repos):** live `session-log.md` migrated to latest-only via
  `rotate --keep 1` + an `awk` that drops the `Previous logs:` block (handles single-line AND multi-line
  WRAPPED pointers — expenses/code's spanned ~40 lines). career-search had a byte-identical duplicate
  `Session 56`; the migration collapsed it to one archive (heal, not loss). Discipline: inspect → dry-run →
  byte-diff → verify, before writing any live tracking file — it turned two latent corruptions into
  verified-safe ops.

**Why this matters:** the handoff is expensive at the worst moment (context near-full, end of session,
maybe Sonnet, maybe usage-limit cliff). Value-only + harvest move authoring cost OFF the main window;
latest-only keeps the resident file small. The value schema is also the contract the deferred local-model
Placer (E1–E2) will fill via structured output. Increment-4 (separate-window synthesis sourced from the
persisted transcript JSONL, for the budget-cliff case) is documented only — build later.
