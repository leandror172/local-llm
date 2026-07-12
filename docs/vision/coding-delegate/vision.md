# Vision: intent, horizons, non-goals, name

<!-- ref:delegate-vision -->
## Intent and end state

**The problem, in four measured facts:**
1. Claude sessions spend tokens on mechanics local models can do — and the conventions that
   govern delegation (`ref:local-model-conventions`) are *manual policy* Claude must remember
   to follow every call.
2. The MCP tool surface is synchronous with a ~120s ceiling; real generations already exceed
   it (T-81's AI-merge attempts: 9 min timeout, then ~20 min producing zero bytes).
3. Verdict protocol compliance is 10.7% (49 verdicts / 457 calls) — the DPO training-data
   flywheel leaks because a human-executed protocol doesn't execute reliably.
4. Two-thirds of evaluated local outputs are verdict 1 (improved) — and roughly a third of
   those needed only a compile-class fix Claude performed by hand
   (`ref:delegate-evidence-verdicts`).

**The move:** an async **deliverable run** system behind the MCP bridge. Claude submits a
bounded spec → `run_id` immediately → a detached worker loops the local coder model against
the Layer-4 evaluator (compile/lint/tests every iteration) until mechanical defects are gone
or budgets exhaust → Claude reviews the delivered result against plan and quality, records the
curated verdict, and dispatches the next deliverable. The harness *is* the conventions doc,
mechanized; the models only fill content.

**Two horizons — the load-bearing scope decision (user course-correction, 2026-07-11):**

- **Horizon 1 (the buildable now): Claude-gated deliverable runs.** One call = one deliverable
  (a test file, a function, a class, a patch). A test deliverable is its own run, reviewed by
  Claude *before* the implementation run is dispatched — "the tests determine the rest."
  Claude holds the plan; the system holds the grind. The internal loop fixes only what the
  evaluator can prove broken (compile/lint/test/structure); judgment defects stay with Claude.
- **Horizon 2 (the grand version, explicitly future): autonomous plan runs.** A planner model
  operationalizes a detailed plan into a chain of deliverables, a plan-level final gate decides
  deliver/iterate/ask, and Claude reviews at plan granularity. Every H2 element is *staged* by
  H1 (the planner slot, the question channel, the report format) but none is required by it.
  The planner/coder two-small-model split is the design's most novel and least-evidenced piece
  (`ref:delegate-evidence-selfrepair`) — H2 proceeds only if H1's run logs validate it.

End state across both horizons: **Claude as coordinator and verifier; the GPU as the worker;
the evaluator as the gatekeeper; the ledger as the memory.**
<!-- /ref:delegate-vision -->

<!-- ref:delegate-first-principles -->
## First principles (carry these into every phase plan)

1. **Deterministic spine, models at the edges.** Harness code does all mechanics (locate,
   fetch, splice, verify, log); models only decide content. Direct transplant of the
   session-handoff pipeline lesson, independently validated by Agentless beating agentic
   harnesses on cost *and* correctness (`ref:delegate-evidence-prior-art`).
2. **Structured output only — no free-form tool use by local models.** Ollama's `format`
   param is 100% reliable (Layer-0 finding); 14B tool-calling is not. Models *request*
   (typed JSON); deterministic fetchers *fulfill*. mini-swe-agent's schema-free design
   (>74% SWE-bench Verified with zero tool-calling dependency) is the external proof.
3. **Async exists to buy quality, not speed.** Model swaps (~15s warm) and eval loops are
   slow on one GPU; because nobody waits synchronously, the system can afford phase batching,
   fresh starts, and judge passes. Latency is spent where it buys verdict-2 outputs.
4. **Narrow intake, hard.** Small-model repair converges on well-specified, bounded tasks and
   falls off a cliff on repo-scale ambiguity (~21% at 8B on SWE-bench). Underspecified specs
   are *rejected at intake* deterministically — most "the model should ask" cases are really
   "the harness should refuse."
5. **Everything is an event.** The run ledger is an append-only event log; status is a fold;
   polling returns offset deltas; DPO extraction is a query; failure forensics is a replay
   (`ref:delegate-ledger`).
6. **A signal that fires unconditionally carries zero bits** (session-111 principle). Every
   warning/verdict/status in this system must discriminate — the evaluator's verdict derives
   from artifacts, never from separately-tracked state.
7. **Failure reports state where/whose/what** (handoff failure-clarity lesson): which stage,
   whose fault (payload vs harness vs model vs environment), what exactly failed.
8. **Every run feeds the flywheel.** Per-iteration (prompt, response, auto-verdict) rows; the
   accepted iteration vs its failed predecessors are natural DPO pairs — gated by the judge
   rule (`ref:delegate-evidence-dpo`).
<!-- /ref:delegate-first-principles -->

<!-- ref:delegate-non-goals -->
## Non-goals (as binding as the goals)

- **Not an autonomous architect.** Objective/plan quality is the caller's responsibility in
  both horizons. The planner (H2) *operationalizes* detailed intent; it never invents scope.
  A vague objective is an intake error, not a challenge.
- **Not a general agent framework.** No free-form tool loops, no open-ended browsing, no
  multi-repo orchestration. One deliverable, one workspace, one bounded loop.
- **Not a replacement for Claude's judgment.** The loop erases mechanical defect classes;
  over-engineering, convention drift, and design errors remain Claude's to catch (the verdict
  data says exactly this — `ref:delegate-evidence-verdicts`).
- **Not built on the MCP Tasks primitive** (experimental, being pulled from spec core to an
  extension in the 2026-07-28 RC) and **not on MCP sampling** (unsupported by Claude Code,
  being deprecated). Bespoke run handles + polling; we *adopt the Tasks state names* for
  interop-friendliness only (`ref:delegate-evidence-mcp`).
- **Not a scheduler for multiple concurrent runs** (v1). Single-run FIFO; the GPU cannot
  co-host two 14B inferences anyway. Multi-run policies are a P6 topic.
- **No code reuse from the claude-code clone** — proprietary, patterns only
  (`ref:delegate-evidence-clones`). AutoCodeRover is excluded entirely (license forbids AI
  interaction with its code).
<!-- /ref:delegate-non-goals -->

## Naming (V-D1 — DECIDED: oficina)

Decided 2026-07-11: **oficina** (runner-up aprendiz). Full record in **`naming.md`** —
criteria, 13-candidate register, decision rationale (harness is the objective; the flywheel
is a property), and the metaphor boundary rule (no guild names in code/schema/CLI verbs).
Folder + `delegate-*` ref keys keep the working label; the brand carries package/CLI/narrative.
