# Phasing

<!-- ref:delegate-phasing -->
## Principles

Delivered by pieces (user requirement); every phase is independently valuable; each phase gets
its own `docs/plans/` doc (with a decision register) before execution; a phase may ship and
sit — nothing downstream is load-bearing until its own plan says so. H1 = P1–P5; H2 enters as
P6 experiments and graduates only on evidence.

## P1 — Async substrate (both tools)

- **Delivers:** `submit_run` / `run_status(since_offset)` / `run_result` / `cancel_run` around
  *today's* `generate_code` + `ask_ollama` semantics (no loop, no new model roles); detached
  worker + FIFO queue; event-ledger JSONL + offset polling; per-run artifact dir;
  `watch-run.sh` (background-Bash monitoring that works today); intake validation; run-ID +
  retention policy (V-D9).
- **Kills immediately:** the 120s MCP timeout class (T-81's 9–20-min merges become legal);
  enables Claude-works-while-GPU-works parallelism.
- **Acceptance:** submit a long generation, keep working, collect via poll; kill the Claude
  session mid-run, reattach from a new session; cancel works; ledger replays.
- **Candidate first client:** the overlay installer's `--mode ai` (T-81) — its two defects
  (no preview, timeout) are both solved by submit→review→apply against this substrate.
- **Decisions frozen here:** V-D4 (residency/packaging), V-D9, V-D10, V-D11, event names.

## P2 — Evaluated deliverable loop (the value inflection)

- **Delivers:** acceptance spec in the run spec (caller-supplied `test_cmd`/`test_files` +
  evaluator Phase 1 validators + structural checks); coder ⇄ evaluator loop with budgets
  (~3 iterations + 1 fresh start); repetition-signature fresh-start trigger; delta-scoped
  evaluation (S16); worktree workspace + deliverable-as-branch; auto-verdicts into
  `calls.jsonl` (with `run_id`); model-escalation ladder (tier 1 → tier 2) mechanized;
  failure classification (rule-based mechanical/structural/conceptual).
- **Acceptance:** a deliverable whose first generation has a compile-class defect arrives at
  Claude verdict-2-equivalent with zero Claude edits; exhaustion delivers best-attempt +
  where/whose/what report.
- **Evidence this attacks the real distribution:** `ref:delegate-evidence-verdicts` (~1/3 of
  improved + ~1/2 of rejected verdicts are Phase-1-catchable).

## P3 — Context & prompt assembly, mechanized

- **Delivers:** deterministic prompt compiler encoding the conventions (behavioral-intent
  framing, CONSTRAINTS block, callers-included rule, tests-as-context); typed context
  requests fulfilled by deterministic fetchers — files + refs (existing ollama-bridge
  features), LTG `retrieve_context`/`relate_files` (sibling repo, Phase 6), signature
  extractor when T-77 exists (this system is its second consumer); bounded re-request round;
  `steps:` support (decomposed generation — mechanizes `benchmarks/lib/decomposed-run.py`;
  Layer-0 3-stage finding).
- **Note:** in H1 the "planner" is Claude + this deterministic compiler. A planner *model* is
  NOT introduced here (V-D2 stays open).

## P4 — Judge gate + delivery report

- **Delivers:** evaluator Phase 2 rubric judge at packaging (cadence per V-D7; same-base
  judge persona for zero-swap); approval gate (`input_required` after assembly — the first
  question channel, S14); delivery report format (diff summary, iterations narrative,
  auto-verdict trail, where/whose/what on failure); S17 judge-gates-DPO-labels enforced;
  curated-verdict capture folded into Claude's review flow.

## P5 — Question channel (full)

- **Delivers:** `blocked: {reason, question, missing}` schema-union variant on model-facing
  calls at any stage (before coding included — user note 2026-07-11); `answer_run`;
  calibration metrics (V-D6: block rate per model, false-block rate). "Teaching" = the escape
  hatch is in every schema + one few-shot example; calibration is measured, not assumed.

## P6 — Flywheel & experiments (H2 on-ramp)

- **Delivers:** DPO pair extraction from the ledger (Target-DPO-style, token-level diff
  masking, S17 gate) feeding Layer 7.7–7.9; inner-loop experiment arms benchmarked by the
  evaluator (V-D5: Aider-subprocess arm, vendored mini-swe-style arm); tiny-model failure
  triage (gives M-P1b/P2 a consumer); queue policies beyond FIFO (V-D13); **planner-model
  pilot** (V-D2) — the H2 gate: does a small planner measurably beat Claude-authored briefs
  on verdict-2 rate? Only a yes graduates Horizon 2 (autonomous multi-deliverable plan runs,
  plan-level final gate).
<!-- /ref:delegate-phasing -->
