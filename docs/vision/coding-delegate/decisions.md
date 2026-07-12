# Decisions: settled stances + open register

<!-- ref:delegate-stances -->
## Settled stances (vision-level; each phase plan may refine, not silently reverse)

Each stance cites its evidence — reverse only with new evidence (house rule).

- **S1 — One call, one deliverable (Horizon 1).** A test call delivers the test, not
  test+implementation. User course-correction 2026-07-11; supported by verdict data (bigger
  asks degrade: verdict-1 outputs average 1145 est. tokens vs ~700 for 2s and 0s).
- **S2 — Claude gates every deliverable in H1** (quality + plan conformance) — crucial when
  tests are delegated, since tests determine the rest. The loop only erases what the
  evaluator can prove broken.
- **S3 — Tests-first ordering:** test deliverable → Claude review → implementation
  deliverable against those tests. Institutionalizes the existing feedback-memory practice.
- **S4 — Deterministic spine; models at the edges.** Handoff-pipeline lesson + Agentless
  external validation (`ref:delegate-evidence-prior-art`).
- **S5 — Structured output only; no free-form tool use by local models.** Layer-0 `format`
  finding + mini-swe-agent proof + open-multi-agent's own design (regex extraction is a
  fallback safety net there, never primary).
- **S6 — Async substrate: bespoke run_id + offset-delta polling.** Forced by measurement:
  Claude Code MCP client is blocking-only, ignores progress notifications; MCP Tasks primitive
  is in spec flux (2026-07-28 RC pulls it to an extension). Adopt the Tasks *state names*
  only. `ref:delegate-evidence-mcp`.
- **S7 — Detached worker, disk state; survives session, does not resume mid-run after reboot**
  (reruns cheap; revisit with usage — user 2026-07-11).
- **S8 — Event-sourced JSONL ledger; no event-store DB.** Named upgrade trigger:
  multi-worker/multi-machine or subscription fan-out (`ref:delegate-ledger`).
- **S9 — Application-level FIFO queue; Ollama's queue is the collision absorber.** Single run
  at a time in v1 (user confirmed 2026-07-11).
- **S10 — Phase batching; ~3 model swaps per run, never per iteration; same-base judge
  persona where quality permits.** `ref:delegate-gpu-policy`.
- **S11 — Iteration budget ≈ 3 + one fresh start; fresh start triggers on repetition
  signature, not only exhaustion; auto-submit best attempt on exhaustion.**
  `ref:delegate-evidence-selfrepair` + LoopDetector pattern + SWE-agent pattern.
- **S12 — 14B floor for the coder-in-loop role.** 7B does not reliably converge
  (SWE-Dev 23.4% @7B vs 36.6% @32B; SLM verifier-hybrid signal).
- **S13 — Intake rejection over model questioning.** Underspecified specs are refused
  deterministically before any model call; the model-initiated `blocked` escape (schema
  union) is P5 and mapped to `input_required`.
- **S14 — Approval gate is the first question channel:** one structured pause after assembly
  ("criteria/tests I'll hold the code to"), auto-proceed configurable. User confirmed.
- **S15 — Workspace seam `in_place | worktree`, worktree default when acceptance executes
  code; deliverable = branch + diff report.** Parameterizable (user 2026-07-11).
- **S16 — Delta-scoped evaluation:** blame only regressions the current iteration caused
  (claude-code snapshot/diff pattern).
- **S17 — Judge-gates-DPO-labels:** any iteration logged as a DPO *chosen* example must pass
  the Phase-2 judge, regardless of sparse judge cadence elsewhere. Keep `auto_verdict` and
  `curated_verdict` as separate fields. `ref:delegate-evidence-dpo`.
- **S18 — Own thin loop; adapters as experiment arms.** Aider embeds via subprocess only
  (Python API explicitly unstable); mini-swe-agent is the vendorable reference (~100 lines,
  MIT); OpenHands SDK is the heavyweight option. Benchmark arms later *with the evaluator
  itself*.
- **S19 — No orchestration framework for the spine.** LangChain/LangGraph add a framework
  where ~200 auditable lines are needed; transport is already owned (ollama-bridge client;
  T-76 registry direction). Libraries at the edges (pydantic schemas, inotify/watchdog).
  Final re-check scheduled at P1 plan time (V-D11).
- **S20 — Scope: code deliverables.** The async substrate serves `ask_ollama`-class jobs too
  (P1), but loop/evaluator stages are code-specific. User: no objection.
- **S21 — Licensing:** AutoCodeRover excluded entirely (Sonar source-available license
  forbids AI ingestion/interaction). claude-code clone: patterns only, never code. MIT/Apache
  sources (mini-swe-agent, OpenHands, Agentless, Aider) reusable with attribution via
  `docs/ATTRIBUTIONS.md` when code is actually adopted.
<!-- /ref:delegate-stances -->

<!-- ref:delegate-open-decisions -->
## Open decision register (V-D)

Freeze each in the phase plan that first needs it; every deferral carries a named trigger
(the guessed-trigger corollary: a deferral whose trigger is guessed fires on a different
trigger).

- **V-D1 — Name. DECIDED 2026-07-11: `oficina`** (runner-up aprendiz). Decision record +
  metaphor boundary rule in `naming.md` (`ref:delegate-naming`). Deciding correction: the
  identity is the delegation harness; the flywheel is a property, not the objective.
  Guild-roles composition demoted (no `my-aprendiz-*` personas — the existing per-language
  persona matrix stays the loop's model slot); `journeyman` reserved for H2. Folder +
  `delegate-*` ref keys keep the working label; the brand carries package/CLI/narrative.
- **V-D2 — Planner arm (H2): does a small planner model add value over Claude-authored
  briefs?** Literature is thin — nothing tests two cooperating small models in this split.
  Validate against H1 run logs (which context shapes correlate with verdict-2?). Decide at
  P6/H2 pilot.
- **V-D3 — Ledger upgrade (KurrentDB or similar).** Trigger: multi-worker/multi-machine or
  subscription fan-out. Until then JSONL.
- **V-D4 — Code residency + packaging.** Lean: worker module grows inside `mcp-server/`
  initially; apply the R-D9 principle (code ships as a package, config as overlay) if it ever
  propagates cross-repo; split-to-own-repo trigger mirrors T-33's (external adopter, or it
  competes with llm session serialization). Decide at P1 plan.
- **V-D5 — Inner-loop experiment arms.** Which to build first when P6 arrives: Aider
  subprocess arm vs vendored mini-swe-agent-style loop. Benchmark with the evaluator.
- **V-D6 — `blocked` calibration.** How to measure/tune the model's use of the question
  escape (rate per model, false-block rate). Needs P5 data; design the metric with P5.
- **V-D7 — Judge cadence + judge persona.** Once at packaging (lean) vs every K iterations;
  same-base judge persona choice. Decide at P4 plan; S17 is the only fixed constraint.
- **V-D8 — Container workspace.** Trigger: first run whose acceptance executes untrusted or
  network-touching code; until then worktree + user privileges (documented risk).
- **V-D9 — Run retention/TTL.** Runs directory growth policy, artifact pruning, and run-ID
  lifetime. Decide at P1 plan (cheap), revisit at P6 (DPO harvest wants history).
- **V-D10 — `ask_ollama` async profile details.** Same substrate, no loop — decide the spec
  subset at P1 plan.
- **V-D11 — Orchestration library final check.** Re-verify LangGraph/alternatives at P1 plan
  time against the actual state-machine size. Lean: plain Python (S19).
- **V-D12 — Hook-based monitor injection.** Optional polish after watch-run.sh proves the
  flow; adjacent to T-14. Decide when P1 ergonomics are felt in practice.
- **V-D13 — Interactive-priority yield.** Cooperative pause between iterations for
  interactive GPU use. Trigger: felt contention in real usage; T-21 is the horizon solution.
<!-- /ref:delegate-open-decisions -->
