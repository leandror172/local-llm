# Session-Handoff — Topology + Value-Only Payload + Git-Harvest

> Status: **IMPLEMENTED (session 90, 2026-06-16).** Increments 1–3 built, propagated to all
> 3 target repos, and the live `session-log.md` migrated to latest-only in all 4 repos.
> Manifest v6, 166 tests green, PR #52. Increment 4 (separate-window synthesis) remains
> documented-only. Builds on the deterministic spine (`ref:handoff-pipeline-design`) and the
> deferred Placer (`ref:handoff-placer-enhancement`).

## Problem

The handoff is expensive at the worst moment (end of session, context near-full). Four
observed failure modes:

- (i) main window full (Sonnet sessions) — no room for synthesis;
- (ii) uncached tokens make the handoff costly;
- (iii) costly re-reads that **duplicate already-resident content in a different form**
  (a `Read` of what was already pulled via `ref`, or vice-versa);
- (iv) usage-limit cliff — the handoff costs more than the budget left.

These mostly collapse to one move: **don't do expensive *new* work in the main window at
handoff time** — harvest what already exists, emit only values, and (for the hard cliff)
move synthesis to a separate window.

## Increment 1 — Latest-only topology + slugged per-handoff archives

**Goal:** `session-log.md` holds exactly the **latest** entry. Each handoff rotates the
prior entry out to a self-identifying archive file. Drop the bloated `Previous logs:`
pointer line entirely — the archive dir + slugged filenames *is* the index.

**Why low-risk:** `run_handoff` already calls `rotate()` after write; `next_session_number`
derives N from the log entries present (one entry still yields the right N). So:

- Change the orchestrator's rotation call to **`--keep 1`** (entry N stays; N-1 spills).
- Rewrite **`rotate-session-log.sh`**: archive each spilled entry into its **own**
  `archive/session-log-<date>-s<N>-<slug>.md`, where `<slug>` derives from the entry's
  `## <date> - Session <N>: <title>` heading. Mirrors the user's `/export` naming so the
  archive entry and the exported transcript share a stem and are pairable.
- Stop maintaining the `Previous logs:` line; **remove `header-previous-logs`** from
  `registry.yaml`. (One-time migration: delete the existing ~46-name pointer line.)
- `resume.sh` "Last session" awk already takes the first dated heading — robust to a
  one-entry file; no change needed beyond verifying.

**Untouched:** locator, applier, verifier, payload parser, the prepend write-mode for
`log-entry`. The file briefly holds {N, N-1} between write and rotate, exactly as today.

## Increment 2 — Value-only payload (pipeline owns the scaffold)

**Goal:** Claude emits only the *values that matter*; the pipeline renders the markdown
scaffold. Removes a live redundancy: today Claude writes the `## <date> - Session N: <title>`
heading **inside** `log-entry` *and* supplies `session_title` as a scalar, and must
"determine the session number from context" — all of which the pipeline already
derives/owns.

Two altitudes (DECISION below):

- **2-min:** pipeline renders the **heading line** from `date + derived N + session_title`;
  Claude's `log-entry` body starts at `### Context`. Kills the heading/N/title redundancy.
  ~Small: one render step in `mechanics`, SKILL drops the heading line.
- **2-full:** `log-entry` becomes structured sub-slots
  (`context`, `what_was_done[]`, `decisions[]`, `next[]`, `gotchas[]`); the pipeline
  renders **all** scaffold (`### Context`, headers, bullet structure). Claude emits pure
  values. ~Larger: payload schema + parser + a renderer + SKILL rewrite + tests.

The 2-full schema is exactly what the deferred local-model Placer (E1–E2) will fill via
`format` structured output — designing it now is forward-compatible.

## Increment 3 — Git-log harvest + stop re-fetching resident interiors

**Goal:** seed "what was done" from deterministic sources already on disk; stop the
re-read duplication (failure mode iii).

- Add a tiny helper `handoff-harvest.sh`: `git log <last-handoff-commit>..HEAD --oneline`
  (last handoff commit = newest `chore(session-handoff):`), emitting the commits since
  session start. Claude folds these into `what_was_done` instead of re-deriving — zero
  model, zero re-read.
- SKILL write-path: **reuse replace-mode interiors already resident in context** rather
  than re-`ref-lookup` them a second time. Re-fetch only the interiors not already seen.

## Increment 4 — Separate-window synthesis (DOCUMENTED ONLY)

The escalation for the budget-cliff cases (i)/(iv): run synthesis in a disposable window
— a subagent (cheaper cloud model) or a model fed the persisted transcript JSONL
(`~/.claude/projects/.../*.jsonl`) — sourcing content from the **transcript**, not from a
main-Claude brief (a full brief *is* the authoring cost). Reuses the increment-2 value
schema as its output contract. Build later; spec only here.

## Decisions (RESOLVED, session 90)

- **D1 — Increment-2 altitude: (b) 2-full.** `log-entry` becomes structured sub-slots
  (`context`, `what_was_done[]`, `decisions[]`, `next[]`, `gotchas[]`); the pipeline renders
  ALL scaffold. Claude emits pure values. Field names kept aligned with
  `ref:handoff-placer-enhancement` so the deferred local-model Placer fills the same schema.
- **D2 — Back-compat: (a) clean break.** Bump pipeline + manifest v5→v6; all 3 repos migrate
  in lockstep, byte-verified with per-file `cmp`. No transition/dual-accept mode.

## Execution model (session 90)

- Implementation is **delegated to Sonnet subagent(s)**, one phase at a time. Subagents may
  call `advisor` as they see fit and MUST call it before handing back their result.
- Per `ref:local-model-conventions`: subagents attempt the **local model** (Ollama via
  `generate_code`) first for leaf Python (renderer, rotate script) with behavioral prompts,
  recording 0/1/2 verdicts — not hand-writing boilerplate.
- Main session **evaluates each subagent's result** by re-deriving invariants (session-29
  standard: do NOT trust green test counts; verify newline-termination, the F4 marker
  multiset, and N-derivation ordering explicitly).
- **Do not start any phase without explicit user go-ahead.**

## Phased execution (each phase = its own commit, pause between)

- **P0.** This doc + index entry. (durable)
- **P1.** Increment 1: rotate-session-log.sh rewrite + `--keep 1` + registry drop +
  one-time pointer-line migration. Update/extend rotate + orchestrator tests.
- **P2.** Increment 2 (per D1): mechanics renderer + payload schema (if 2-full) + SKILL.
  Extend payload/mechanics tests.
- **P3.** Increment 3: `handoff-harvest.sh` + SKILL write-path edits.
- **P4.** Manifest v5→v6; propagate overlay to expenses, web-research, career-search with
  per-file `cmp` byte-verification (the session-89 lesson: propagation needs a verify step).
- **P5.** Update memory / overlays KNOWLEDGE.md; full test run; PR.

## Risks

- **Rotation slug parsing** must be deterministic and handle missing/odd titles (fallback
  slug = `sNN`). Test with the existing backwards-range / duplicate-name archive bugs in mind.
- **Verifier:** session-log has no `ref:` blocks, so the ref-marker-count invariant is
  unaffected by topology; confirm the one-entry file still passes outside-region hashing.
- **2-full** is the schema most likely to ripple into the Placer design — keep field names
  aligned with `ref:handoff-placer-enhancement`.
