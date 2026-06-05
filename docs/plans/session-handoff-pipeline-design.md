# Session-Handoff Pipeline — Design

> Status: **design frozen, not yet built** (session 83, 2026-06-04).
> Supersedes the all-in-Claude `session-handoff` skill flow. No pipeline code written yet.
> **Active scope = A (deterministic spine, NO local model).** The register made the model
> unnecessary for the base case; the local-model "Placer" layer is a **deferred enhancement** —
> see `session-handoff-placer-enhancement.md` (`ref:handoff-placer-enhancement`). This doc now
> describes the spine only; model-specific material moved to that doc.
> **Home: the `session-tracking` overlay** (`overlays/session-tracking/`) — session-handoff
> already ships there; the pipeline + register are an enhancement of that overlay, not a
> repo-local one-off. Build here, propagate via overlay install.

<!-- ref:handoff-pipeline-design -->
## One-paragraph summary

Today the `session-handoff` skill makes Claude do three things: **decide** the handoff
content, **read** every tracking file to find where edits go, and **write** each section
via many Edit round-trips. Only *decide* is irreducibly Claude's. This design keeps *decide*
with Claude and collapses *read + write* into a single **deterministic** pipeline invocation.
Localization is supplied by a **per-repo register** keyed on the existing handoff `ref:` blocks
(no new in-file markers); Claude **authors each full block**; deterministic code locates the
register-defined region, splices the content (replace / prepend / append / check-off-by-id),
verifies that nothing outside the region changed, and commits all-or-nothing. From Claude's
side the entire apply step is **one Bash call** returning a summary — and it eliminates the
file *reads* entirely. (A future enhancement adds a local model to also expand *terse intent*
into prose, saving Claude's authoring tokens — see `ref:handoff-placer-enhancement`.)
<!-- /ref:handoff-pipeline-design -->

## Why

Cost in the current skill is concentrated in *read + write*, not *decide*:
- **Reads:** pulling `session-log.md` / `session-context.md` / `tasks.md` fully into context
  only to learn *where* to insert. `session-log.md`'s `**Previous logs:**` header alone is
  ~40 archive paths on one line — pure noise per read.
- **Writes:** 6–8 separate Edit round-trips, each expensive on Opus.

The content Claude generates is the same either way — that's the irreducible part. The win is
eliminating the reads and collapsing the writes into one call.

## No model in Scope A — why the spine is deterministic

The register eliminated the model's original reason to exist. The model was first conceived as a
**Placer** doing *semantic localization* ("find the right spot by meaning"). But the per-repo
register now supplies location deterministically, and Claude **authors each full block**, so
every operation reduces to `replace` / `prepend` / `append` / `check-off-by-id` — all
deterministic, no Ollama call. `replace` needs no old content; inserts take an authored block;
check-off flips by task ID. **The base-case pipeline therefore needs no model at all.**

The model re-earns its place for one *different* value proposition — expanding Claude's *terse
intent* into prose (saving authoring tokens, not just read tokens) — which is the **deferred
enhancement** (`ref:handoff-placer-enhancement`). All Placer-altitude reasoning, the verdict
model, and DPO logging live there.

## Frictions any safe auto-editor faces

Root cause: localizing edits in evolving markdown files. (The register + verifier below answer
these for the spine; #3 is purely a model-layer concern, noted for the enhancement.)

1. **Fuzzy localization** — matching intent to a `## heading` breaks when headings drift,
   repeat, or differ from the intent label. Corruption danger zone: the `Previous logs:` line.
2. **Append-vs-replace + ordering** are per-file conventions the model can't infer
   (`session-log` is newest-first; a section may be newest-last; "status"=replace,
   "decision"=append).
3. **Intent-tagging burden** lands on Claude's output — too loose → model guesses; too rigid
   → Claude is back to specifying positions (the cost we're killing).
4. **Faithful preservation + verification** — the obvious check (read the file back) pulls it
   into Claude's context, defeating the saving.
5. **Deterministic/judgment boundary + multi-file atomicity** — rotation, session-number,
   date, header bumps must NOT go through the model; and a half-applied multi-file edit is a
   broken handoff.

## Structural solutions — reuse existing ref blocks, driven by a register (NO new markers)

The session-tracking system **already** uses a named set of `ref:` blocks as its localization
contract: `resume.sh` *reads* `ref:current-status`, `ref:active-decisions`, `ref:user-prefs`,
`ref:quick-pointers`, etc. The handoff pipeline is the **symmetric *write* side of that same
contract** — so the write-slots are the **already-present ref blocks**, not new markup. Adding
`<!-- handoff:slot -->` markers was rejected: it would pollute the LTG corpus (the extractor /
embedder ingests `.claude/` + `.memories/`) for no gain.

Per-repo presence varies — **verified**: this repo's `session-context.md` has `current-status`,
`active-decisions`, `user-prefs`, but **not** `quick-pointers` (which lives in `index.md` here).
So localization is driven by a **register**, never hardcoded paths.

| Move | Role |
|------|------|
| **S1 — Register** (per-repo, overlay-shipped): maps handoff role -> `{file, ref-key OR structural locator, mode}`. **Shared by `resume.sh` (read) and the pipeline (write)** so they can't drift | kills #1 *without touching files* |
| **S2 — Mode lives in the register** (`replace`/`prepend`/`append`/`nomodel`) | #2; #3 shrinks to "name the role" |
| **S3 — Locator self-checks**: "expect exactly one match for this ref-key/heading -> else abort + fall back to Claude" | drift between register and a renamed block is *detected*, never committed |
| **S4 — Task IDs in-file** (`(T-83a)`) — the **lone** new in-file element (confirmed in-file); makes check-off deterministic (flip `[ ]`->`[x]` by id) | #1/#3 for `tasks.md` |
| **S5 — Only register-defined regions are mutable; F4 hashes everything else** | enables #4 (below) |

**S5 is the lever:** the model may only touch register-defined regions, so a deterministic check
hashes everything *outside* them before/after — unchanged hash = proof nothing load-bearing
moved, without pulling the file into Claude's context. Same seam gives cross-file atomicity:
edit all regions -> validate all -> commit, else roll back none.

**Pollution resolved:** reusing existing ref blocks adds zero markup; task IDs are the only new
in-file tokens (minimal, arguably useful content).

**The register doubles as the repo-customization seam.** The set of handoff ref-key *names*
differs per repo; the register is where that variance lives, and it distinguishes
**handoff-owned keys (writable)** from **all other ref keys (content / LTG anchors — never
touched)**. That boundary is also the natural basis for a future *portable-handoff* capability
in the overlay (defer building it).

## Functional decomposition

| # | Capability | Model? | Job |
|---|-----------|--------|-----|
| **F1** | Locator | no | For each register entry, find its region (existing `ref:` block or structural locator) + mode + current interior; self-check exactly-one-match |
| **F2** | Placer | **deferred** | *Enhancement only* — expands terse intent → region interior. Not in Scope A. See `ref:handoff-placer-enhancement` |
| **F3** | Applier | no | Splice new interior between markers; cannot touch outside-slot bytes |
| **F4** | Verifier | no | Hash outside-slot regions before/after; assert markers paired, modes honored → pass/fail |
| **F5** | Mechanics | no | Rotation, next session-number, date, header-field bumps (in `nomodel` fence) |
| **F6** | Orchestrator | no | Stage across files → place → verify all → commit-or-rollback (atomic) → summary + git warning + idempotency guard |
| **F7** | Contract | n/a | Payload shape Claude emits (`slot-id → content`), validated before anything runs; lives as the skill's output schema |

**Crux (Scope A):** *zero* pieces touch a model — the spine is fully deterministic. **F4 is
still the safety gate**: it hashes everything outside the register-defined region and rejects any
edit that touched anything else, so even a buggy applier can't silently corrupt a file. (When the
enhancement adds F2, that same gate becomes the *trust boundary* that lets an untrusted local
model run — see `ref:handoff-placer-enhancement`.)

## Inventory — have vs. build

| # | Status | Asset / gap |
|---|--------|-------------|
| F1 | **partial** | `ref-lookup.sh` already parses `<!-- ref:KEY -->`; need slot+mode semantics |
| F2 | **deferred (enhancement)** | Not built in Scope A. Plumbing exists (`retrieval/model_client.py`); see `ref:handoff-placer-enhancement` |
| F3 | **new** | Small deterministic splice |
| F4 | **new** | Small deterministic hash + marker assertions |
| F5 | **mostly have** | `rotate-session-log.sh` exists + already greps `## 20` entries (reuse for session N); date trivial; header bumps new-but-trivial |
| F6 | **new — real glue** | Atomic transaction; **rollback is free — it's a git repo** (verify-fail → `git checkout` tracking files) |
| F7 | **skill exists** | Rewrite `session-handoff/SKILL.md` body to define + validate the payload schema |

**Genuinely new build surface** (Scope A, all deterministic): F1 Locator, F3 Applier, F4
Verifier (safety core), F6 Orchestrator (transaction). F5 reuses `rotate-session-log.sh`; F7 is
a SKILL.md rewrite. **F2 (Placer) is not built in Scope A.**

*(The pipeline-internal Ollama-call constraint and its "model chatter is free from Claude's
context" consequence apply only once F2 lands — see `ref:handoff-placer-enhancement`.)*

## Logging (Scope A)

Each handoff writes one **per-run artifact directory** (shared key = `session-N + timestamp`):

```
<run>/
  input.md    <- Claude's exact F7 payload (authored blocks + roles). Ground-truth intent;
                 retrievable; doubles as a recovery artifact (retry a half-failed run).
  report.md   <- final report: committed?/rolled-back(+reason), regions touched (role+mode),
                 per-region before->after, verify results. Feeds resume/audit.
```

Placement: lean `.claude/local/handoff-runs/<run>/` (gitignored per CLAUDE.md; machine-local,
cross-session-retrievable).

These two artifacts already enable the **input ↔ report** check (did the pipeline faithfully
apply what Claude asked) for audit. The **DPO `calls.jsonl`**, the **L0/L1 layered verdict**, and
the **report ↔ reality / path (b)** signal are all **model-layer concerns deferred to the
enhancement** (`ref:handoff-placer-enhancement`) — Scope A makes no Ollama call, so there is no
call to score.

## Open questions / next (build order — Scope A, not yet started)

- **B1.** Register pass: author `registry.yaml` (role -> file, ref-key/structural-locator, mode)
  in `overlays/session-tracking/`; add task IDs to `tasks.md`. (No in-file slot markers; no model.)
- **B2.** Build F1 (Locator) + F3 (Applier) + F4 (Verifier) — the deterministic safety core — TDD.
- **B3.** Build F6 (Orchestrator): stage -> apply -> verify-all -> commit-or-rollback (git
  checkout on fail) -> summary; per-run `input.md` + `report.md`.
- **B4.** Rewrite `session-handoff/SKILL.md` to emit the F7 payload (authored blocks per role)
  instead of doing the edits itself.
- **Enhancement (separate, deferred):** the local-model Placer + verdict/DPO logging — full plan
  in `ref:handoff-placer-enhancement` (steps E1–E6).

### Decisions

- **Scope = A** (deterministic spine, no model). Localization = reuse existing handoff `ref:`
  blocks via a shared per-repo register; **no new in-file markers**. **Task IDs in-file.**
  **Home = `session-tracking` overlay.** Register doubles as the repo-customization seam
  (handoff-owned vs content/LTG ref keys); portable-handoff feature deferred.
- L1 verdict (when the model lands) = **deferred labeling (a)**; `input.md` + `report.md` are
  logged now to support it.

### Still open

- Run-artifact placement (lean `.claude/local/handoff-runs/`); whether `report.md` also appends
  to committed `session-log.md`; whether `session-context.md` is in the first cut or
  `tasks.md` + `session-log` only; whether `resume.sh` is refactored onto the shared register
  now or in a follow-up (B1 lean: later).
```
