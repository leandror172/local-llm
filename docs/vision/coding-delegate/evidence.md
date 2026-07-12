# Evidence base

Everything below was gathered 2026-07-11 (two research subagents + a clones-survey subagent +
verdict-data mining). Full artifacts:
- `docs/research/coding-subagent-prior-art.md` (frontier web arm)
- `docs/research/coding-subagent-prior-art-webresearch.md` (web-research MCP arm + per-call
  operational appendix)
- `docs/research/coding-subagent-clones-survey.md` (local clones, file-path-cited)
- Cross-repo side product: `~/workspaces/web-research/docs/reports/2026-07-11-field-report-llm-prior-art-run.md`
  (5 web-research defects + fixes; D2 = non-discriminating auditor verdict, triage first).

<!-- ref:delegate-evidence-verdicts -->
## Our own verdict data (the strongest evidence for the loop)

Source: `~/.local/share/ollama-bridge/calls.jsonl`. Regenerate with
`.claude/tools/ollama-stats.py` and `.claude/tools/ollama-verdicts.py`.
Snapshot 2026-07-11: 506 records, 457 calls, 49 verdicts (2026-02-27 → 2026-07-10).

- **Coverage 10.7%** — the manual verdict protocol does not execute reliably; one recorded
  verdict even logs a cold-start timeout as a 0, violating the protocol's own
  TIMEOUT_COLD_START rule. Mechanization argument, measured.
- **Distribution 16.3% / 67.3% / 16.3%** (2 accepted / 1 improved / 0 rejected). Avg est.
  tokens: 2→696, 1→1145, 0→656 — bigger asks degrade (supports S1 one-deliverable scoping).
- **~1/3 of "improved" reasons are compile-class** (unused/missing imports, declared-unused
  vars — Go compile errors) and **~half of rejections are typo/runtime failures**
  (`html23text` ×2, `trafiladora` ×2, TYPE_CHECKING-only imports) — all catchable by
  evaluator Phase 1 / smoke execution. **The loop's first automated iteration converts these
  from "Claude fixes it" to "nobody fixes it."**
- **Recent trend:** 2026-06/07 verdicts are almost all 1s with a *single mechanical defect*
  each — today's typical output is one compile error away from a 2.
- **Context quality already fixed a defect class:** the March re-declaration cluster
  (models re-declaring types instead of importing) disappeared after the conventions started
  requiring protocol files + callers in context. What remains for Claude: over-engineering
  (4 cases), convention drift (missing sibling doc comments), design judgment.
- **The DPO preview:** the 2026-03-20 block is a compare-models run — identical prompts, two
  personas, per-output verdicts = ready-made preference pairs.
- Model usage skew: my-python-q3 (122), my-go-qcoder (81), my-python-q25c14 (61) of 457.
- **Caveat:** n=49, self-selected (verdicts recorded when Claude remembered) — directional,
  not precise.
<!-- /ref:delegate-evidence-verdicts -->

<!-- ref:delegate-evidence-prior-art -->
## Prior art: harnesses and loops (licenses verified per source)

- **Aider** (Apache-2.0, Python): repo-map via tree-sitter, diff/whole/architect edit formats
  (architect = its own planner+implementer split), `--auto-test`/`--test-cmd` loop, LiteLLM
  transport, no sandboxing, ~108 deps. **Python API (`Coder.create`/`run`) explicitly
  unstable/undocumented; repair depth hard-coded (`max_reflections=3`).** Embedding = CLI
  subprocess in headless mode, or nothing. → S18.
- **mini-swe-agent** (MIT, Princeton/Stanford SWE-bench team): ~100-line loop, **zero
  tool-calling-schema dependency** (plain `subprocess.run`), >74% SWE-bench Verified; flat
  linear history (good for fine-tuning data). The vendorable reference for our loop. → S5, S18.
- **SWE-agent** (same lineage): the Agent-Computer Interface thesis — the agent gets a small
  set of high-level tools (windowed file viewer, edit+lint-with-rollback, bounded search,
  explicit submit tool), not raw bash. Termination: success / budget exhaustion (auto-submit
  best attempt as degraded success) / malformed-action requery ladder. Deliberately no
  semantic stuck-detection. Runtime layer spun out as SWE-ReX (Docker/local/remote).
- **OpenHands** (MIT): embedding-first SDK (`openhands.sdk`: LLM/Agent/Conversation/
  Workspace; arXiv 2511.03690), one-line `LocalWorkspace`→`DockerWorkspace` swap (→ our
  workspace seam, S15), MCP-native tool-schema conversion, RouterLLM, stuck-loop detection,
  secret masking. The heavyweight arm if ever wanted.
- **Agentless** (MIT): deterministic localize→repair→validate phases around narrow LLM calls,
  no agentic loop — best cost/performance on SWE-bench-lite among compared systems. External
  validation of S4, and the evidenced fallback: if iterations flail, *narrow the coder step*,
  don't add agency.
- **AutoCodeRover — EXCLUDED.** Post Sonar acquisition (March 2025): "SONAR Source-Available
  License v1.0" explicitly forbids AI systems ingesting/training on/interacting with its code
  or outputs. Hard blocker, not an attribution matter. → S21.
- **Planner/coder two-small-model split: evidence thin.** Nothing located tests this exact
  configuration; adjacent support only (DAG-compiler planning, multi-agent failure
  taxonomies). Treat as hypothesis (V-D2). Aider's architect mode is the nearest practice.
<!-- /ref:delegate-evidence-prior-art -->

<!-- ref:delegate-evidence-mcp -->
## MCP constraints (measured, not assumed)

- **Claude Code's MCP client treats every tool call as blocking and ignores progress
  notifications** — anthropics/claude-code issue #31893, closed "not planned". Polling is the
  only channel; status must carry the narrative (→ offset-delta events, S6).
- **MCP Tasks primitive**: experimental in the 2025-11-25 spec; being **pulled from core into
  an extension in the 2026-07-28 release**; the new spec text recommends exactly the
  "mint a handle from a tool, pass it back as an ordinary argument" pattern. Its state
  vocabulary (`working/input_required/completed/failed/cancelled`, cooperative cancellation,
  capability negotiation, no long-lived connection) is worth adopting as *names*
  (→ `ref:delegate-state-machine`). Spec extension page:
  modelcontextprotocol.io/extensions/tasks; repo: github.com/modelcontextprotocol/experimental-ext-tasks;
  design ancestor: MCP GitHub Discussion #491 ("Asynchronous Operations in MCP").
- **MCP sampling** (server asks client's LLM): unsupported by Claude Code, being formally
  deprecated in the spec. Never design against it.
- **WorkOS engineering write-up ("MCP Async Tasks")**: implementer checklist — task IDs are
  bearer-like handles (protect/scope per caller), durable storage, TTL + orphan recovery
  (→ V-D9, unguessable run IDs).
- **Adoption gap:** no shipping third-party MCP servers with a submit-then-poll pattern were
  found in production (may be a search-index limitation; both research arms failed to find
  any). We are early — copy nobody, keep it simple.
<!-- /ref:delegate-evidence-mcp -->

<!-- ref:delegate-evidence-selfrepair -->
## Small-model self-repair (what the loop can and cannot do)

- Modern 8B+ instruction-tuned models DO benefit from execution-feedback repair; **76–95% of
  gains land in the first two rounds**; the **Debugging Decay Index** paper (tests Phi-4 14B)
  shows exponential per-attempt decay and a free mitigation — the **"strategic fresh start"**
  (discard accumulated repair history, re-anchor) → S11, and it is structurally our
  stubs-then-Ollama pattern mechanized.
- **Scale caveat:** the optimistic numbers come from HumanEval/MBPP-scale tasks. Repo-scale
  small-model results are far weaker (~21% at Qwen3-8B on SWE-bench). → S13 narrow intake;
  the conventions' bounded-task rule is the boundary of where this machine works at all.
- **SWE-Dev** (arXiv 2506.07636): 23.4% @7B vs 36.6% @32B on SWE-bench-Verified → S12
  (14B floor).
- **SLM signal** (EmergentMind summary, Live-SWE-adjacent): naive iterative repair does not
  reliably converge at 7B without scaffolding (separate verifier, curriculum FT, distillation)
  — the scaffolding IS the product here.
- Classics: **Self-Debug** (Chen et al., arXiv 2304.05128) — up to ~12% improvement
  (Spider/TransCoder/MBPP), reuses failed predictions for sample efficiency. **Self-repair
  survey** (arXiv 2604.10508, 2026): three paradigms (Self-Refinement / Self-Collaboration /
  Self-Adaptation); prioritizing critical errors before style nits → 30% less repair time
  (frontier-scale numbers; direction transfers, magnitudes may not).
- **No source gives a validated "N iterations" for 7–14B** — our 2–3+fresh-start default is
  evidence-informed, to be validated against our own run logs (V-D2's data doubles here).
<!-- /ref:delegate-evidence-selfrepair -->

<!-- ref:delegate-evidence-dpo -->
## DPO from execution feedback

- **Target-DPO** line of work: preference pairs harvested in-loop are ~10x more
  sample-efficient than post-hoc mining; strong gains reported on Qwen2.5-Coder-7B.
- **Dominant pitfall + fix:** whole-block pairs teach style collapse; **token-level diff
  masking** (credit only the changed tokens) is the documented correction.
- **Reward hacking is real and multiply documented:** models game narrow tests (hardcoded
  literals, weakened assertions). The cheap per-iteration signal (tests) is precisely the most
  gameable one, and it is what would feed "chosen" labels → **S17: the judge gates every DPO
  chosen label** — integrity costs one judge call per delivered run, not per iteration.
- Layer-7 math changes: 7.9's "wait for 500+ entries ≈ a year at ~40/month" collapses to
  weeks once every run emits per-iteration labeled rows. Anthropic ToS note in plan-v2 Layer 7
  still applies to Claude-derived pairs (personal-use context; review before broader use).
<!-- /ref:delegate-evidence-dpo -->

<!-- ref:delegate-evidence-clones -->
## Local clones survey (patterns, with file paths in the full report)

Full report: `docs/research/coding-subagent-clones-survey.md` (439 lines, every claim
file-path-cited). Inventory verdicts: `claude-code/`, `open-multi-agent/` relevant;
`claude-code-sourcemap/` navigation aid; `odysseus/`, `career-ops/`, `ollama-metrics/`
irrelevant (verified by skim, not assumption).

- **claude-code** (PROPRIETARY — no license file; patterns only, NEVER code; README contains
  showman framing — the report flags code-verified vs README-only claims):
  - `Task.ts` + `utils/tasks.ts`: file-per-run JSON state, TaskStatus enum
    (pending/running/completed/failed/killed), **atomic lockfile claiming** (`wx`-flag
    exclusive create — kills TOCTOU races between claimants), **offset-tracked output
    polling** (`getTaskOutputDelta`) → near 1:1 blueprint for our run store + poll surface.
  - `ccrSession.ts` `pollForApprovedExitPlanMode`: `needs_input` derived from a quiet-idle
    heuristic (idle AND zero new events per tick) — validates the poll-phase shape; ours is
    strictly better because our worker signals `blocked` explicitly (we control it).
  - `partitionToolCalls`: consecutive read-only tool calls batched parallel under a
    concurrency cap; everything else serial → applicable to context-prep fetchers.
  - Edit safety: read-before-edit enforcement, uniqueness-count-with-ask (no silent first
    match), snapshot-before/diff-after → S16 delta-scoped evaluation.
- **open-multi-agent** (MIT — confirmed from its LICENSE file; TypeScript):
  - `LoopDetector`: deterministic signature over a sliding window of tool-calls/text,
    consecutive-repeat counting → S11's repetition-triggered fresh start.
  - Tool-calling with local models: native OpenAI-compatible `tool_calls` primary (Ollama as
    OpenAI-compatible endpoint); text/regex extraction is an explicit fallback safety net
    only — do NOT adopt the fallback as primary; our `format`-param stance stands (S5).
- Convergence note: three uncoordinated sources — the MCP Tasks spec, claude-code's internal
  task store, and our own handoff stage/promote pipeline — landed on the same job-store shape.
  P1's design risk is low; the novelty (and risk) is concentrated in V-D2.
<!-- /ref:delegate-evidence-clones -->
