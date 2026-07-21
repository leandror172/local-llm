# Session Log

**Current Layer:** "Layer 5+ — verdict/DPO harness (T-105); oficina P2 post-slice"
**Current Session:** 2026-07-21 — Session 125: "verdict harness repaired — coverage 9.6% → 18.7% (T-105, PR #80)"

---
## 2026-07-21 - Session 125: "verdict harness repaired — coverage 9.6% → 18.7% (T-105, PR #80)"

### Context

Started as a one-line question — "how many DPO triples do we have from ollama generate_code?" — and the 9.6% coverage answer turned into a full investigation. The user pushed back on two framings that shaped everything after: that recording verdicts is the *session's* job, not theirs, and that judgments were probably being made but not stored properly. Both were right.

### What Was Done

- **Diagnosed the verdict coverage collapse (T-105).** Every durable doc taught an inline phrase (`2 — ~300 est. Claude tokens saved`) while `verdict-capture.py` has only ever parsed a `[VERDICT …]` block **taught nowhere durable** — it existed solely as an ephemeral per-call hook injection. The harness worked; it was never fed. A live probe proved the chain end-to-end on the first try.
- **Wrote the evidence report + plan** — `docs/findings/verdict-coverage-collapse-2026-07-21.md` (every claim carries `file:line`; §9 records four claims the investigation got *wrong*, with corrections) and `docs/plans/verdict-capture-repair.md`.
- **Phase 0** — probed the hook schema live rather than trusting a delegated doc summary: the field is `tool_response` (**not** `tool_output`), `tool_use_id` exists, and `last_assistant_message` is final-message-only, so the whole-transcript scan must stay.
- **Phase 1** — `call_id` + `tool` in `_log_call`; provenance by response-content match; **no positional fallback**.
- **Phase 2 (root cause)** — CLAUDE.md, scaffolding-template and the overlay source converge on the block; `handoff-session-66.md` annotated (not rewritten) and archived; **overlay v3** propagated + committed to `expenses/code`, `web-research`, `career-search`.
- **Phase 3** — back-filled 48/49 prose verdicts, provenance-flagged; **coverage 9.6% → 18.7%** (106/566).
- **Phase 4** — oficina judged **per-run** on the deliverable via `run_result`; regex widened to `[A-Za-z0-9_-]`.
- **Phase 5** — 26 hook tests, every one mutation-verified to fail against the broken code.
- **Phase 7** — `cleanupPeriodDays: 365`; transcripts are the only audit trail for this bug class.
- **Self-audit against the pattern docs** found two violations (stringly-typed `_emit`, prefix-sniffing for failure); both fixed.
- **PR #80 opened**; T-105 registered in `tasks.md`.

### Decisions Made

- **Judgeable set narrowed:** `generate_code` + `ask_ollama` per-call; **oficina per-run**; NOT summarize/translate/classify_text — a 0/1/2 *quality* verdict is not meaningful there and yields filler that pollutes DPO.
- **Measure first, gate later.** PostToolUse structurally cannot block; a `Stop` block forces turn continuation, and a forced verdict is not a considered one. Revisit only if the docs fix fails to move coverage.
- **`call_id` replaces `prompt_hash` as identity.** `prompt_hash` is a content address — one hash covered 24 calls across 8 models, so a compare-models sweep could record exactly one verdict.
- **No positional fallback in the hook.** A stale id mislabels the corpus, and mislabeled is worse than missing.
- **Back-filled records carry no `call_id`** — those calls predate the field; inventing one would be fabrication.
- `handoff-session-66.md` **annotated, not overwritten** (user's call): it is a historical handoff, not documentation.

### Next

- **Review + merge PR #80** (12 commits). Then push the three downstream repos' `v2 → v3` commits if wanted.
- **Phase 6 (the only open part of T-105)** — after real working sessions under the fixed docs, report coverage *among judgeable calls only* (now measurable via the `tool` field) and decide whether a `Stop` gate earns its friction.
- Resume the pre-empted oficina track: **build the edit kinds on M2** (`LanguagePack.locate_unit` + loop composes `patch_file`), then Axis A Go read-side.
- **T-106** — fix the stale LTG post-commit hook message.
- **T-107** — decide overlay-vs-machine-global for the verdict hooks, then move hooks + tests out of `.claude/hooks/` together.

### Gotchas

- **Branch off master, not off an unmerged feature branch — the risk asymmetry matters.** This branch was cut from master while PR #79 was still open, which cost exactly two things: one `.claude/tasks.md` conflict (both branches append at the same deferred-infra closing boundary) and a session-number collision. Both were cheap and mechanical. Basing on the unmerged branch instead would have risked *dependency entanglement* — invisible until the parent changed. Resolution: PR #79 merged first, then `git rebase master`; the collision dissolved on its own (this handoff renumbered 124 → 125) and no history needed rewriting. Measured overlap beforehand was 4 files, all docs/memory, 3 of which auto-merged — the register design means concurrent sessions write to different regions of the same file.
- **The MCP bridge is long-lived** — `client.py` changes (`call_id`/`tool`) only take effect after the subprocess restarts. Phase 1 looked correct but inert until the session restarted mid-way.
- **Editing a `merge_sections` file does NOT propagate without a manifest `version:` bump** — the dry run reports `[SKIP] … already installed v2` and half-propagates while reporting success.
- **Overlay targets must be the real repo root** — `expenses/code` is the repo, not `expenses/`; the parent dry-ran as `[CREATE] CLAUDE.md`, i.e. it would have fabricated files in a non-repo directory.
- **`ltg/run-refresh.sh` does not exist** — the post-commit hook's suggested command is stale since the T-33 engine split; the real entry point is `/mnt/i/workspaces/latent-topic-graph/run-refresh.sh`.
- **Three bugs were found by running the thing, not reading it**: a backgrounded call producing a stale id, `generate_code` fence-stripping defeating exact match, and run ids being base64url. All three fail *silently*.
- **Local-model delegation was blocked all session** by VRAM contention (3 timeouts, including an 8B with no context files) — `my-python-q25c14` resident at 9.7 GB against ~9 GB free.
