# session-tracking handoff pipeline — development history (episodic)

Per-round narrative for the `session-tracking` overlay's handoff pipeline, evicted from
`overlays/session-tracking/.memories/KNOWLEDGE.md` (session 110, 2026-07-08) when that file
was consolidated into concept-organized semantic memory — the same treatment LTG's
`.memories/KNOWLEDGE.md` received as task L-08, per web-research
`docs/research/memory-architecture-design.md`.

**What lives here:** the *stories* — what broke, who reported it, which session fixed it, what
the fix superseded. **What does not:** the durable invariants those stories produced. Those were
consolidated into `overlays/session-tracking/.memories/KNOWLEDGE.md`, which points back here.

Read this when asking **"why is it this way?"** or **"has this been tried?"**. For **"how does it
work?"**, read KNOWLEDGE.md instead.

Provenance (llm repo commits, newest last):
- Sessions 86–90: `33f0400`, `0a799ee` — stage/promote redesign, session-29 field report, latest-only
- Session 93: `f83fea7` — failure-clarity rollout (overlay v7)
- Sessions 106–108: `25e1002`, `75f8bf6`, `14942fd` — split stance, v9 bug sweep, shim gotcha retired
- Session 109: `e94be13`, `36f4b36` — T-61 customizable seam, memory split

---

## Scope-A build-out (sessions ~80–87)

Scope A of the handoff pipeline (F1 locator → F3 applier → F4 verifier → F5 mechanics →
F6 orchestrator → F7 payload/entrypoint) used **no local model**. Completed B1–B4 by session 87:
77 tests, dog-food-validated against a clone run on real content + register. Shipped as **PR #50**,
stacked on `feature/ltg-phase3-anchors` and retargeted to master after the LTG PR merged.

---

## Session-86 dog-food learning — the missing-newline gap

F4's invariants are *out-of-region bytes* + *ref-marker multiset*. **Neither sees a missing
newline before a present marker.** A payload's last `## role:` section has no trailing blank, so
`payload.py` returned non-newline-terminated content, and append/replace/prepend glued the content
line onto the closing marker.

Fixed at the seam (`_normalize_block` in `_collect_edits`), **not** in the safety core: the applier
and verifier share an implicit "content is newline-terminated" contract and must stay byte-identical,
so the normalization happens once upstream, where both consume the same `items`.

→ Consolidated as the **newline-termination contract** invariant.

---

## Sessions 89–90 — stage/promote redesign

Replaced the `--dry-run --payload` two-step with **rename-on-ingest + stage/promote**. Planned in
session 89 (`~/.claude/plans/handoff-redesign-rename-on-ingest.md`, branch
`feature/handoff-redesign-stage-promote`), implemented across 89–90. **PR #52**, 126 tests green,
overlay v5 propagated to 3 repos (byte-verified).

- `--payload` (stage): validate → ingest (copy payload into run dir) → locate+apply+verify in
  memory → emit JSON handle; dir stays `-pending`; the original payload is deleted only on success
  (unlink is the LAST op — crash-safe; a failed stage leaves the author's file in place).
- `--id` (promote): find `-pending` run → idempotency check by commit-title suffix → `run_handoff`
  → rename dir to `-success` / `-failed`.
- Run-dir status suffix (`-pending` / `-success` / `-failed`) replaced the old "writes nothing in
  dry-run" invariant. The `--dry-run` flag was dropped.
- Two failure branches: validation-fail = no handle (re-edit the same file); stage-fail = handle
  exists in a `-failed` dir (author fresh content).
- **Idempotency key insight:** check the commit-title suffix, NOT the session number — after the
  first commit the header updates and `peek_session_number` returns N+1, a false-miss on
  crash-recovery.
- **T-57 fix:** `_effective_range` in `verifier.py` collapses append→insertion-point and
  checkoff→3-byte range; the reconstruction sort matches the applier's stable-sort-descending for
  equal-start regions.

---

## Session-29 feedback round (2026-06-12) — five fixes from the expenses field report

The first real-world run in expenses (its session 29) surfaced 5 problems (P1–P5; report at
`~/workspaces/expenses/code/.claude/local/handoff-pipeline-feedback-session29.md`). Root-cause
analysis found **two meta-failures beyond the pipeline itself**:

- (a) commit `75886bb` *claimed* the SKILL.md rewrite (T5) but only touched `manifest.yaml` — the
  work never existed, so every SKILL.md still taught the removed `--dry-run`;
- (b) the v4 propagation was **partial** — expenses had a stale `verifier.py` without
  `_effective_range`, so they hit the already-fixed T-57 overlap on the most common payload shape
  (checkoffs + tasks-append).

Fixes (commits `f6d1116`, `771ea5c`, `bba6cce`, `0fdb42f`, `979f66f`):

- **Error specificity (P-msg):** overlap errors name both regions `role(target)@file:line`;
  validation errors state WHY ("required because this run bumps the Current Session header").
  Rationale: converts every failure from "read pipeline source" (~5 calls) into "fix payload" (1 call).
- **`--amend` (P4+P5):** a follow-up run attached to the LAST COMMITTED session N (derived, never
  typed); append+checkoff modes only (prepend excluded — a log-entry prepend would duplicate the
  session heading); scalars not required; no header write; idempotency check skipped; commit suffix
  `— amend`. **Design principle: the recovery path is strictly LESS powerful than the happy path** —
  the worst possible amend mistake is a duplicate appended task. Mode persisted in a `<run_dir>/mode`
  sidecar.
- **`--abort <handle>`:** renames `-pending` → `-aborted`. Every missing CLI verb becomes an ad-hoc
  `rm` invented under pressure; this closed that gap.
- **Copy-don't-move (P3):** stage copies the payload to `input.md` up front; unlink-original is the
  final step, on success only. A failed or crashed stage never consumes the author's file.
- **SKILL.md (P1):** rewritten for the real CLI; exact pre-flight one-liner with correct
  empty-output semantics; the 3 copies (overlay source / llm project / user-level) unified
  byte-identical — the overlay + user copies also carried a WRONG checkoff description (claimed
  bolded ids fail; `locator.py` is flexible) that the project copy had right.

**Process learnings from this round:**
1. Overlay propagation needs a verify step — per-file `cmp` against source caught nothing wrong
   that time only because we ran it. Installer `--verify` mode landed later (T-58, 2026-06-26).
2. "Task done" claims in commit messages and memory are unverified — T5 was recorded done in
   QUICK.md *and* in a commit message while no diff existed.
3. Subagent review must re-derive invariants, not trust green tests: review caught an amend
   stage/promote session-number mismatch (N+1 vs N — would have recreated the exact "session 30
   surprise") and the prepend allowlist hole, both behind passing tests.

→ (2) and (3) promoted to user-level `feedback` memory; they are behavioural, not repo-specific.

---

## Session-90 redesign (2026-06-16) — latest-only topology + value-only + harvest

This round cut the *token cost of AUTHORING a handoff* (the prior work cut the mechanical apply
cost). Three increments + a one-time data migration; manifest v5→v6 (clean break, decision D2).
126 → 166 tests green.

- **Latest-only topology (P1):** `session-log.md` holds exactly the newest entry.
  `rotate-session-log.sh` archives EACH spilled entry into its own
  `session-log-<date>-s<N>-<slug>.md` (slug = lowercased, alnum→hyphen, ≤40 chars; fallback `sNN`)
  and runs with `--keep 1`. The `header-previous-logs` role was dropped from `registry.yaml` and the
  ~46-ref `Previous logs:` pointer line is gone — the archive dir + slugged filenames ARE the index.
  Rationale: the single growing file + giant pointer line was the bloat; self-identifying per-entry
  files mirror the user's `/export` naming and pair with exported transcripts.
- **Value-only payload (P2, decision D1 = "2-full"):** `log-entry` became structured snake_case
  sub-slots; the pipeline renders ALL scaffold (the `## <date> - Session N: <title>` heading from
  date + derived N + `session_title`, plus `### Context / What Was Done / Decisions Made / Next /
  Gotchas` + bullets). New: `LogEntry` dataclass + `render_log_entry()` (mechanics.py),
  `HandoffPayload.log_entry` + slot parser (payload.py); the orchestrator computes `header_values`
  once and renders log-entry with the SAME `session_number`. CRITICAL: `parse()` excludes log-entry
  from `payload.blocks` to prevent double-apply; the session-86 newline contract is double-guarded
  (`render_log_entry` rstrips then re-adds one `\n`; `_normalize_block` still wraps). Field names
  kept aligned with the deferred local-model Placer schema (forward-compatible). Clean break: the
  old free-block `log-entry` form is rejected with a migration error.
- **Git-log harvest (P3):** `handoff-harvest.sh` = `git log <newest chore(session-handoff):>..HEAD
  --format=%s` (fallback: last 20 + a stderr note). Seeds `what_was_done` deterministically — zero
  model, zero re-read. SKILL step 2 calls it as the skeleton; step 3 adds "reuse replace-mode
  interiors already resident in context rather than re-`ref-lookup`" (attacks the
  duplicate-resident-content failure mode iii).
- **Propagation (P4):** manifest v5→v6; installed into expenses/code, web-research, career-search;
  every `files:` entry byte-verified with `cmp` (14/14 per repo — the ONLY safety net, targets ship
  no tests). SKILL is per-consumer: the global `~/.claude/skills/` copy serves web-research +
  career-search; expenses/code and llm have project-level copies that SHADOW the global (force-cp
  each — `user_files` is skip-if-present). llm runs the engine from source but calls rotate by the
  INSTALLED path, so its installed rotate + harvest were refreshed too. Target registries left
  untouched (`manual_if_exists`) — confirmed safe: the pipeline only walks payload→register, never
  register→payload, so the orphaned `header-previous-logs` role is inert.
- **Data migration (one-time, all 4 repos):** live `session-log.md` migrated to latest-only via
  `rotate --keep 1` + an `awk` that drops the `Previous logs:` block (handles single-line AND
  multi-line WRAPPED pointers — expenses/code's spanned ~40 lines). career-search had a
  byte-identical duplicate `Session 56`; the migration collapsed it to one archive (heal, not loss).
  Discipline: inspect → dry-run → byte-diff → verify, before writing any live tracking file — it
  turned two latent corruptions into verified-safe ops.

**Why this mattered:** the handoff is expensive at the worst moment (context near-full, end of
session, maybe Sonnet, maybe a usage-limit cliff). Value-only + harvest move authoring cost OFF the
main window; latest-only keeps the resident file small. The value schema is also the contract the
deferred local-model Placer (E1–E2) will fill via structured output. Increment-4 (separate-window
synthesis sourced from the persisted transcript JSONL, for the budget-cliff case) is documented
only — build later.

---

## Session-93 fix (2026-06-17) — append↔checkoff consistency + failure clarity

An expenses-user report: a payload with BOTH `tasks-append` AND `checkoffs:` in one run failed with
an opaque "Modified text does not match the expected text" message, requiring a 5-file investigation
to recover. Two defects fixed; changes to `applier.py`, `verifier.py`, `orchestrator.py`,
`locator.py`, `handoff.py` ONLY — payload schema, register, mechanics, rotator unchanged.
166 → 173 tests green. Manifest v6→v7.

- **Defect 1 — correctness (append + checkoff in one file):** `applier.py` inserts at `region.end`
  for append (correct); `verifier.py` was doing `replace([start,end], region.interior + content)`
  (wrong). The interior snapshot was stale — any nested edit (a checkoff flip) applied earlier in
  the descending-sort loop was lost when the verifier reconstructed with the old interior. Fix: the
  verifier's reconstruction loop special-cases `append` and `prepend` as zero-width insertions (like
  the applier), preserving bytes already mutated by nested edits. `_effective_range` already returned
  zero-width for insertion modes; reconstruction now agrees. Prepend had the identical hazard; fixed
  too. Test: `test_append_region_enclosing_checkoff_verifies`.
- **Defect 2 — diagnostics (the failure was unreadable):** the error named no file, no roles, and
  gave no diff. Requirement adopted: every failure message must answer WHERE (file + role[s]),
  WHOSE FAULT (a payload error the author can fix vs an internal tool bug to report), and WHAT (diff
  or specifics). Mechanism: a `kind` attribute on exceptions (`kind="payload"` / `kind="internal"`,
  defaulted per exception type). Sweep through all raises: `locator.py` names file + id +
  found-vs-expected count; `verifier.py` adds `_first_diff()` (first differing byte + context) plus
  `_edits_label()`; `applier.py`'s unsupported-mode message names the role; `orchestrator.py`
  handlers prefix reasons with `[payload]` / `[internal]` so `handoff.py` can extract `kind` and emit
  status `payload_error` / `internal_tool_bug` (replacing the flat `stage_failed`). The overlap
  message is prefixed "two payload edits target overlapping bytes:" so the reader knows it's
  author-fixable. Internal failures append "report with input.md" so the author never re-authors a
  tool bug.

**Implication:** the append+checkoff pattern became safe and useful (e.g. completing a complex task
discovery in one handoff). Failure diagnosis shifted from "read pipeline source" to "read the error
message".

---

## Sessions 106–109 — distribution fixes and the customization seam

- **B+C distribution (2026-06-17):** pipeline modules always user-level at `~/.claude/tools/handoff/`
  (new `always_user_files:` manifest key); shim + SKILL.md follow `--install-level` (renamed from
  `--skill-level`). `run-handoff.sh` rewritten as a thin shim. Three target repos migrated: old `.py`
  copies removed, shim written. Option D (pip editable) deferred; G/H remain long-term targets.
- **Home-repo shim `--registry` (T-62, v9, 2026-07-06):** before v9 the shim guarded on
  `[ -f "$_root/.claude/handoff/registry.yaml" ]` and hard-`exec`d the user-level `handoff.py`, so it
  silently `exit 0`'d in the llm home repo (no per-repo registry) and ignored `--registry`. Fixed: the
  shim bypasses the registry-file guard when an explicit `--registry` is passed, and prefers a
  `handoff.py` co-located with the shim (source tree / dev home repo) over the user-level install.
  The "call `handoff.py` directly" workaround was retired.
- **T-78 (v9):** wrapped-bullet parser continuation-join in `payload.py`; 174 → 178 tests.
- **T-61 (v9 half):** the reading-guide block (§2b) was backported into the overlay source
  `resume.sh`, so source ⊇ installed and a reinstall no longer drops it in the llm repo. career-search
  kept its deliberate "What to read first" §2b variant (different title + lighter output filter),
  preserved on the v9 sync (shim-only) rather than flattened. That divergence was the open half.
- **T-61 (v10, 2026-07-08, session 109):** closed by the general `customizable:` install category —
  overlay owns the file except named `overlay-keep:<name>` regions, which are repo-owned. See
  `docs/plans/overlay-customizable-regions.md`; propagation to consumers tracked as T-79 in
  `docs/plans/overlay-v10-propagation.md`.
