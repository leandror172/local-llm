# Knowledge Index

**Purpose:** Map of where all project information lives. Read this to find anything.

<!-- ref:indexing-convention -->
### Indexing Conventions (Two-Tier System)

| Tier | Notation | When to Use | Lookup Method |
|------|----------|-------------|---------------|
| **Active reference** | `<!-- ref:KEY -->` + `[ref:KEY]` | Agent needs this during work; CLAUDE.md rules point here | `.claude/tools/ref-lookup.sh KEY` (machine-lookupable) |
| **Navigation pointer** | `§ "Heading"` | Index/docs pointing to sections for background reading | Open file, find heading (human/agent reads) |

**Active refs** are for high-frequency, runtime lookups (model selection rules, bash wrapper lists, MCP config).
**§ pointers** are for low-frequency, "read when needed" navigation (research findings, decision rationale, historical context).

**Single-responsibility rule:** One ref block per concept — don't wrap an entire file in one block.
Keep blocks narrow enough that `ref-lookup.sh KEY` returns only what's needed for the task.
<!-- /ref:indexing-convention -->

---

## Quick Pointers (Active Work)

Moved to `.claude/session-context.md` (`ref:quick-pointers`). It is a handoff-owned
register region, and every other such region lives in `session-context.md`; this file
is content the pipeline must not touch. See `docs/plans/resume-config-steps.md`.

---

## Architecture & Strategy

| Topic | File | Key Content |
|-------|------|-------------|
| 10-layer vision & goals | `docs/vision-and-intent.md` | Why this project exists, principles, use cases |
| Full execution roadmap | `.claude/plan-v2.md` | All 10 layers, dependency graph, cross-cutting concerns |
| Model inventory & VRAM budgets | `docs/model-strategy.md` | Which models for which roles, quantization choices |
| Closing-the-gap techniques | `docs/closing-the-gap.md` | 14 techniques to narrow local vs frontier quality gap |
| Routing patterns (A/B/C) | `docs/vision-and-intent.md` | Local-first, frontier-delegates, chat-routes-both |
| Expense classifier vision | `docs/vision/expense-classifier-vision.md` | End-to-end Telegram→classify→Excel goal, iterative phases, domain boundaries |
| Expense classifier data inventory | `docs/vision/expense-classifier-data-inventory.md` | What exists: auto-category analysis artifacts, expense-reporter architecture, what to read |
| resume.sh ref audit & improvement plan | `docs/plans/resume-sh-ref-audit.md` | Which ref tags to add/remove + 3 structural fixes (session 60) |
| **T-81 Part 1 — AI-merge preview (stage/apply)** | `docs/plans/t81-part1-merge-preview-stage-apply.md` | `install-overlay --mode ai` split into `--stage` (call model, diff, write plan handle, no write) + `--apply-plan` (verify pre-image hash, apply); `--dry-run` stays pure. Staleness invariant. BUILT session 115 (`ref:overlay-ai-merge-mode`). |
| **T-81 Part 2 — AI-merge completion tuning** | `docs/plans/t81-part2-merge-completion-tuning.md` | Fix `num_ctx=4096` input-overflow (`fit_num_ctx` in `backends.py`), empirical arm pick (`think:false`), config-driven read+wall-clock timeouts. No oficina. BUILT session 115. |
| **oficina P2 — evaluated deliverable loop (FROZEN plan, T-92)** | `docs/plans/oficina-p2-evaluated-loop.md` | FROZEN session 119 (advisor-reviewed): coder⇄evaluator loop as a new `GenerateFn` seam. Decisions **P2-D1–P2-D13** (first slice = `function`-against-tests, Python, 3-iter; monotonic-prefix cache contract + single swappable `SEGMENTS`+guard test; rule-based in-loop classifier is cache-load-bearing; per-run reused worktree; signature = sorted normalized `error_key` set; category = failing stage via one shared parser; diversity-not-size escalation; delta-scope baseline C0 + free anti-cheat; T-91 is a P2 prereq; `input_required` declared-but-unreachable). Individually-anchored state + loop Mermaid diagrams; draft-P2→frozen event promotions; documentation-lifecycle rule (post-impl diagrams go FINAL in vision folder, plan reports result); run spec + acceptance + T1–T8 build steps. `ref:delegate-p2-goal`, `ref:delegate-p2-decisions`, `ref:delegate-p2-state-diagram`, `ref:delegate-p2-loop-diagram`, `ref:delegate-p2-events`, `ref:delegate-p2-acceptance` |
| **oficina async ergonomics — migration shape + V-D12 (T-89)** | `docs/plans/oficina-async-ergonomics.md` | DECIDED session 117: no sync facade/cutover (sync directness = v1 interactive priority); routing convention (deliverable-shaped → `submit_run`, small → sync); harness-owned monitoring (PostToolUse watch hook, SessionStart store-scan, `watch --result` check, worker `refs` parity). `ref:oficina-async-migration-shape`, `ref:oficina-async-ergonomics-scope` |
| **Overlay AI-merge latency (T-81 P2 findings)** | `docs/findings/overlay-merge-latency-2026-07-12.md` | `num_ctx=4096` truncated ~3.8K-token merge inputs (RC1); `fit_num_ctx` sizes ctx to input → 8192; `think:false` on qwen3:14b is 5.1× faster (86.9s→17.0s) + better placement (RC2); prod-chain `--stage` acceptance 4.16s. Chunking (§3.4) deferred — trigger not met. |
| **Verdict capture collapse — findings (T-105, session 125)** | `docs/findings/verdict-coverage-collapse-2026-07-21.md` | Why local-model verdict coverage is 9.9%: every durable doc teaches an inline phrase (`2 — ~300 est. …`) while the capture regex accepts only a `[VERDICT prompt_hash=…]` block **taught nowhere durable** (`verdict-capture.py:88-95` vs `CLAUDE.md:110`). Evidence-cited (file:line) register D1–D10; **49 recoverable** verdicts; **81.4% of calls carry no judgment in any form** — the format fix is the minority of the gap; `prompt_hash` is content-addressing reused as identity (1 hash = 24 calls / 8 models); `calls.jsonl` has no `tool` field so the denominator is unmeasurable. §9 records four claims the investigation got wrong + corrections. Live probe proved the harness works. `ref:verdict-coverage-findings` |
| **Verdict capture repair — plan (T-105)** | `docs/plans/verdict-capture-repair.md` | 8-phase repair. Decisions V-D1–V-D5: judgeable = `generate_code` + oficina **per-run** deliverables (oficina bypasses the MCP tool — `loop.py:260` → `GenerateFn` seam `worker.py:43`); **measure first, gate later** (PostToolUse cannot block; a `Stop` block forces turn continuation → forced ≠ considered verdict); `call_id`+`tool` in `_log_call` replace `prompt_hash` as identity. Phase 0 verifies the hook schema empirically before any hook edit; Phase 5 tests the **producer→consumer seam** (the 2026-03 fixture test was the wrong shape). `ref:verdict-capture-decisions` |
| Scaffolding template (portable) | `docs/scaffolding-template.md` | `.claude/` convention: directory structure, file purposes, ref:KEY system, setup checklist |
| **Claude Code dynamic workflows guide** | `.claude/workflows-feature-guide.md` | What workflows are (script-orchestrated subagents at scale), when to use vs not, commands (`/deep-research`, `/workflows`, `ultracode`), limits, repo-specific candidates. Captured session 81. |
| **Cache-warmed subagent fan-out pattern** | `docs/patterns/cache-warmed-subagent-fanout.md` | Manual (Agent + SendMessage) fan-out that caches one large shared context per model tier via turn-boundary breakpoints; deferred task injection (copy-to-unique + `copied` ack); planner(Opus)→implementer(Sonnet/worktree) tiers; when this beats a workflow. Ready-to-use shared prompts. `ref:cache-warmed-fanout`. |
| **Technology conventions** | `docs/patterns/technology-conventions.md` | Reusable decisions: Python/uv, MCP, Ollama API, scripts, git, personas, licensing. Self-indexed via `ref:patterns-index` |
| **Code design conventions** | `docs/patterns/code-design-conventions.md` | Structural patterns: named semantic methods; value-or-error over sentinel strings; extract-mechanism-keep-divergence-explicit; return-don't-mutate; paired-span bookkeeping via one closure. Self-indexed via `ref:patterns-code-design-index` (`ref:patterns-code-{named-methods,value-or-error,extract-keep-divergence,return-not-mutate,paired-span-bookkeeping}`) |
| **oficina write-model benchmark — full report (T-104, M2 DECIDED)** | `docs/findings/oficina-write-model-benchmark-2026-07-18.md` | Run 1 (108 gens): **null on correctness** (uniform-filler corpus was whole-file's best case; regression trap never sprang — a coverage failure, NOT "whole-file is safe") + **clean cost win for code-anchored** (size-invariant 25 tok vs whole-file 40→134→310). **Decision: M2 = code-anchored** on cost/timeout-safety (whole-file on large files is what blew the 120s ceiling twice this session), re-run declined (open axis not load-bearing). Threats-to-validity + carried caveat + future build. `ref:oficina-write-model-report` |
| **oficina write-model benchmark spec (T-104 gate)** | `docs/plans/oficina-write-model-benchmark.md` | Three-way apply-mechanism benchmark on `qwen2.5-coder:14b`: code-anchored-locator→`patch_file` vs whole-file-with-context vs model-anchored search/replace. **Pre-registered decision rule** (report by file-size bucket; adopt code-anchored if it ties/wins in medium+large). Metrics = applied ∧ target-pass ∧ no-regression, by size. Gates the M2 write-model build. `ref:oficina-write-model-benchmark` |
| **oficina P2 — Go widening (Axis A) build plan** | `docs/plans/oficina-p2-go-widening.md` | 5-phase plan, session 124. R1 (declared language, infer-as-default) / R3 (in-worktree `go build ./...`, experiment-confirmed) / R4 (compile self-attributing, test via `go test -json` `Package` field) SETTLED. Governing discipline: **duplicate Go beside Python first, extract `LanguagePack` only after** (characterize-first; Phase 4 never precedes Phase 3). Measured Go output shapes in the notes doc. Branch `feature/oficina-p2-go` off master. |
| **oficina P2 language widening — design notes (staging)** | `docs/plans/oficina-language-widening-notes.md` | Axis A (add Go) scoping, session 124. The **what-varies-across-languages** table that sizes the eventual `LanguagePack` interface (3 mechanisms + 1 rule + 2 values; flow is invariant → Template Method, not Strategy); the value-object-pack-over-ABC rationale (matches the codebase's injected-`Callable` idiom); **two warnings** (don't pull compile into the pack yet — Go's is a different execution model; don't extract the pack before Go exists concretely — Rule 3 speculative-generality, same failure as the dead `acceptance.validators` field); live bugs to fold in (`py-` prefix, `category_for` ValueError). **ABSORB:** table → widening plan; warnings → `refactoring-conventions.md` as a 2nd characterize-first proof-point. `ref:oficina-language-widening`, `ref:oficina-language-widening-warnings` |
| **Refactoring conventions** | `docs/patterns/refactoring-conventions.md` | Process (not shape) patterns for safe refactors. Seed: characterize-before-extract — write characterization tests that pass against the *current* code first, then change it (from the `_run_script` extraction over the untested persona tools). `ref:patterns-refactoring-characterize-first`; staging doc, promotion pending a second proof-point. |
| **Test authoring — executable-spec (DSL) style** | `docs/patterns/test-authoring-executable-spec.md` | given/when/then bodies + named combinators as a test DSL; 4 rules (intent-distinct constants, hide fixture conventions, accretion stopping rule, given/when taxonomy). Piloted in `test_loop.py` (session 121). `ref:test-executable-spec`; promotion tracked by T-100. |
| **LTG ENGINE — MOVED to sibling repo `latent-topic-graph`** | `/mnt/i/workspaces/latent-topic-graph/` | T-33 split (session 107): engine code (`src/ltg/` package), tests, ALL phase plans (master plan + phases 2/2.5/3/4/5 + extractor retrofit), `DECISIONS.md`, `probes/`, spike results, Phase 4 dataflow diagram — moved with full git history. llm keeps the **instance** at `ltg/` (corpus.yaml, config.yaml, index/, wrappers). Split record stays here: `docs/plans/ltg-repo-split.md`. |
| **Session-handoff pipeline design** | `docs/plans/session-handoff-pipeline-design.md` | **Scope A (deterministic spine, NO model):** replace the all-in-Claude handoff with a register-driven pipeline — reuse existing handoff `ref:` blocks as write-slots (no new markers), deterministic locate/apply/verify/commit, git rollback, per-run `input.md`+`report.md` logging. Register shared with `resume.sh`; lives in `session-tracking` overlay. `ref:handoff-pipeline-design`. Frozen, not built (session 83). |
| **Session-handoff Placer enhancement** | `docs/plans/session-handoff-placer-enhancement.md` | **[FUTURE]** the deferred local-model layer on top of Scope A: model expands *terse intent* → prose (saves authoring tokens). Placer altitude, F4 trust boundary, L0/L1 layered verdict, deferred-labeling (a), input↔report vs report↔reality deltas, DPO `calls.jsonl`, model pick, E1–E6 build steps. `ref:handoff-placer-enhancement`. |
| **Session-handoff failure-clarity fix** | `docs/plans/session-handoff-failure-clarity.md` | append↔checkoff consistency fix (verifier `_segment`/loop insertion semantics) + full failure-clarity sweep (where/whose/what triad via `kind`-on-exception, `payload_error`/`internal_tool_bug` statuses). Two-agent dispatch plan. Triggered by expenses bug report (session 93). |
| **LTG repo split (T-33) — FROZEN plan, ready to execute** | `docs/plans/ltg-repo-split.md` | Session 107: S-D1–S-D7 frozen (`ref:ltg-split-frozen-decisions`) — uv path-dep consumption, `ltg/` instance dir, moves/stays/copies table (filter-repo non-destructive extraction), day-one self-index as decoupling acceptance, MCP in new repo, packaging flip during split, single-repo cadence + task migration. Execution: SP-1–SP-14 over 2 sessions. Open input: repo name. |
| **LTG repo split (T-33) discovery — superseded by frozen plan** | `docs/plans/ltg-repo-split-discovery.md` | Session 106: split-before-Phase-6 lean + drivers (workflow decoupling primary), verified dependency map (`store.py:44` REPO_ROOT landmine, corpus/convention coupling), scope lean (engine moves; corpus.yaml+index stay; pluggable-source stance rides along; T-76 registry OUT), open decision register **S-D1–S-D7** (`ref:ltg-split-decisions`: consumption path, instance residency, DECISIONS.md ref-coupling, new-repo bootstrap, MCP placement, packaging flip, session cadence). Freeze + author `ltg-repo-split.md` in a fresh session after PR #67 merges. Companion: `ltg-model-registry-design.md` Part 2. |
| Overlay system plan | `docs/plans/overlay-system-plan.md` | Portable repo augmentation: packaging patterns as installable/updatable overlays. 4 phases, manifest-driven, AI-assisted merge |
| **Overlay `customizable:` keep-regions (T-61 option b)** | `docs/plans/overlay-customizable-regions.md` | FROZEN, not built: a `customizable:` manifest category where the overlay owns a file except named `overlay-keep:<name>` regions (repo-owned, seed-once). Explicit comment-agnostic markers (not `ref:KEY` — LTG-inert in `.sh`); no per-region version; ownership rule; decisions 1–4 + verify gating; 21 TDD cases + acceptance. Algorithmic acceptance spec `ref:overlay-customizable-acceptance`. |
| **Overlay installer: install-time baseline (lockfile)** | `docs/plans/overlay-install-baseline.md` | PLAN, B-D1–B-D8 **not frozen**. The installer records nothing about what it installed, so it cannot tell "source moved since you reconciled" from "legitimately differs" — 7 unconditional `[TODO]`s across 4 repos. Prior art is `dpkg` conffiles: a 3-way compare (BASE / OURS / THEIRS) prompts only when both moved. Lockfile at `.claude/overlays/<name>.lock`, hash-only v1, snapshot v2 (`git merge-file`). Highest-risk decision is B-D5 (bootstrap: do NOT assume five existing repos are reconciled). T-54's `--force-manual` likely shrinks to `--theirs` afterwards. **Noise fix, not a safety fix** — T-82 removed the safety stakes. |
| **Session 111 report — config-driven resume + packaging flip** | `docs/reports/session-111-report.md` | Full narrative: the five-bugs-one-shape thread (a signal collapsing two states into one), what shipped (discriminating signals, `sessiontracking` package, `resume.yaml`, `--verify`'s locator contract), the five-repo migration with three layouts, six corrections and who caught them, three tests that encoded the bug as the contract, local-model verdicts, and open state. |
| **`resume.sh` → configurable step pipeline (+ packaging flip)** | `docs/plans/resume-config-steps.md` | PLAN, R-D1–R-D9. Replace hardcoded bash sections with a `resume.yaml` step list (fixed vocabulary `text`/`region`/`log_next`/`git_log`/`git_status` + a `run:` escape hatch); `region:` steps resolve through the handoff's `registry.yaml` roles, wiring the long-deferred shared register. Forces **R-D9: distribution Option D** — code ships as a `sessiontracking` package (entry points, `register/` primitive shared by `handoff/` + `resume/`), config ships as the overlay; dissolves `always_user_files:` and `--verify`'s code-drift half. The CLAUDE.md `vN` marker **survives and disentangles** — three version facts (machine-global package `--version`, per-file `registry.yaml: version:` schema contract, per-repo config generation); the package must validate the schema key on startup. Dissolves T-80(b), absorbs T-43, makes T-54 load-bearing. Execution order + T-54/T-80(a) "discriminating-signals release" inside. |
| Verdict numeric migration plan | `docs/plans/verdict-numeric-migration.md` | Replace ACCEPTED/IMPROVED/REJECTED string verdicts with 0/1/2 integers across all repos, hooks, data, docs, and memory. 8 phases. |
| **Attributions & license tracking** | `docs/ATTRIBUTIONS.md` | External-dependency license table per CLAUDE.md licensing rule. Note: leidenalg GPL-3 / python-igraph GPL-2+ (copyleft — tracked in the `latent-topic-graph` repo's license decision). |
| patch_file acceptance test results | `docs/plans/ollama-bridge-patch-file-acceptance-results.md` | Session 67 live test results: 10/10 scenarios pass (6 original + tilde fix + 3 user scenarios). `ref:mcp-patch-file-acceptance-results` |
| Overlay wizard idea | `docs/ideas/overlay-wizard.md` | Deferred: running overlay install interactively inside an AI CLI; wizard pattern generalization; eventual local TUI |
| Claude Code source + related repos | `docs/ideas/claude-code-python-port.md` | Leaked TS source (cloned locally), open-multi-agent (MIT TS framework). Key files: `services/mcp/normalization.ts` (MCP response format), `services/autoDream/` (memory consolidation). open-multi-agent supports Ollama via baseURL; verified tool-calling with Gemma 4 + Qwen 3. |
| ollama-scaffolding overlay | `overlays/ollama-scaffolding/` | Local model usage conventions: verdict protocol, decision tree, stubs-then-Ollama, cold-start policy |
| Ollama coordination layer | `docs/ideas/ollama-coordination-layer.md` | Deferred: shared directory contract for multi-process VRAM coordination; **superseded in scope by the model-call gate (T-88)** — mechanism/findings feed its G-D5 |
| **Model-call gate (T-88)** | `docs/ideas/model-call-gate.md` | Call-level resource scheduler, layer-0 primitive: oficina is NOT the gate (run vs call altitudes); client-owns-plan/gate-owns-admission; two constraint families (capacity vs rate/budget), v1 = local Ollama; triggers + G-D1–G-D6. `ref:model-gate-altitude`, `ref:model-gate-decisions` |
| **Multi-session GPU contention (T-102)** | `docs/ideas/multi-session-contention.md` | **The founding problem, recovered (session 124).** N concurrent Claude sessions contend for one GPU; a sync call that waits its turn exhausts its own transport deadline. Provenance trace of how it was dropped in the T-21→T-88 supersession (clients reframed from *sessions* to *products*); measured evidence (sync p99 294s / max 581s against a ~600s ceiling, uncontended); **T-89 scope-limited not reopened** (it answered interactive-vs-*batch*, and a gate dissolves its priority-inversion objection); the gate's missing axis — **admission policy ≠ wait tolerance**, G-D5 conflates mechanism-location with client-contract, ticket-not-block, fail-fast admission. **The failure mode:** B times out *while still queued*, gets no reason, and every recovery amplifies the contention — the scarce resource is information, not GPU time. **MVP = T-21's busy-check, not the scheduler** (G-D8). Measurement caveats (bridge-only log; user manually serializes ⇒ trigger unfalsifiable). M-D1–M-D5 + D1/D2/D3 decomposition. `ref:multi-session-contention`, `ref:multi-session-failure-mode`, `ref:multi-session-t89-scope`, `ref:multi-session-transport-requirement`, `ref:multi-session-busy-check`, `ref:multi-session-decisions` |
| Per-language error handling + logging conventions | `docs/ideas/persona-error-handling-conventions.md` | Analysis + proposed Modelfile directives for Python/Java/Go. Covers `basicConfig()` antipattern, catch-log-reraise noise, language-specific rules. Pair with backfill-persona-constraints session. |
| LTG model registry design + shared-library decision | `docs/ideas/ltg-model-registry-design.md` | Part 1 (IMPLEMENTED): two-level `models:` + `roles:` config for `retrieval/config.yaml`; naming convention (property enumeration). Part 2 (session 106, T-76 DEFERRED): registry/roles shared-library extraction — prior-art survey (LiteLLM/any-llm/AbstractCore), two-layer conclusion (transport=commodity, registry layer=build), dependency topology (layer-0 primitives), product tiers, triggers + discipline rules (`ref:model-registry-library-decision`). |
| Ollama eviction/concurrency findings | `docs/findings/ollama-eviction-concurrency-findings.md` | Empirical test results: Ollama queues unloads (no correctness risk); PR #9392 may replace file layer |
| **Ollama KV prefix cache findings** | `docs/findings/ollama-kv-prefix-cache-findings.md` | How implicit prefix reuse works; keep_alive rationale; num_keep analysis; what Ollama exposes vs llama-server. `ref:ollama-kv-prefix-cache`, `ref:ollama-explicit-cache-api` |
| **T-90 — KV-quant "anomaly" is VRAM contention** | `docs/findings/kv-quant-vram-contention-2026-07-15.md` | q8_0 KV + Flash Attention verified ACTIVE; 14B/32K partial-offload is host-VRAM contention (RTX 3060 also drives Windows desktop → only ~9 GB free of 12). How to inspect host VRAM from WSL (`nvidia-smi.exe` + PowerShell GPU perf counter; Linux nvidia-smi can't under WDDM). Levers: async `submit_run`, disable NVIDIA overlay, lower num_ctx. `ref:kv-quant-vram-contention` |
| **Model update survey (May 2026)** | `docs/findings/model-updates-2026-05.md` | New models vs current stack: Qwen3.5 tiny (0.8B/2B/4B), Phi-4-mini, Fara-7B, DeepSeek R2 32B, Qwen3-Embedding-8B. Nemotron, Mistral-Nemo, Qwen3.6, MiMo watch entries added session 78. |
| **Leaderboard survey (Jun 2026)** | `docs/findings/leaderboard-survey-2026-06.md` | HF Open LLM Leaderboard v2 parquet (4,576 models) + Arena.ai rankings. Key finding: leaderboard stale for 2025-2026 models. Falcon3-7B notable (TII license); AceMath-7B blocked (CC-BY-NC-4.0); Kimi K2 cloud-only (1T params). |
| Portfolio document | `docs/portfolio/portfolio.md` | Unified overview of all 3 repos (llm, expense, web-research), AI/ML techniques, cross-cutting patterns |
| AI-readable engineer profile | `docs/portfolio/engineer-profile.md` | Structured doc designed for LLM context — skills, philosophy, conversation starters |
| Portfolio chatbot roadmap | `docs/portfolio/hf-space/ROADMAP-smart-chatbot.md` | 4-phase plan: static expansion → retrieval → source awareness → cross-project |
| Chatbot context sync script | `docs/portfolio/hf-space/sync-context.sh` | Copies .memories/ + READMEs from all 3 repos into context/ for chatbot |
| Cross-repo memory prompt | `docs/portfolio/hf-space/prompt-create-memories.md` | Template prompt for creating .memories/ in other repos |
| Observability/instrumentation analysis | `docs/portfolio/hf-space/observability-instrumentation.md` | How evaluator maps to Phoenix/Arize LLM-as-judge pattern |
| Per-folder memory architecture | See `~/workspaces/web-research/docs/research/memory-architecture-design.md` | Cognitive memory model: QUICK.md (working) + KNOWLEDGE.md (semantic) per folder |
| Memory layer design | See `~/workspaces/web-research/docs/research/memory-layer-design.md` | 4-tier progressive context injection (Tier 0-3) |

---

<!-- ref:memory-files -->
## Per-Folder Memory Files (.memories/)

| Folder | QUICK.md | KNOWLEDGE.md |
|--------|----------|--------------|
| Root | `.memories/QUICK.md` | `.memories/KNOWLEDGE.md` |
| MCP server | `mcp-server/.memories/QUICK.md` | `mcp-server/.memories/KNOWLEDGE.md` |
| Evaluator | `evaluator/.memories/QUICK.md` | `evaluator/.memories/KNOWLEDGE.md` |
| Personas | `personas/.memories/QUICK.md` | `personas/.memories/KNOWLEDGE.md` |
| Benchmarks | `benchmarks/.memories/QUICK.md` | `benchmarks/.memories/KNOWLEDGE.md` |
| Overlays (system) | `overlays/.memories/QUICK.md` | `overlays/.memories/KNOWLEDGE.md` (overlay SYSTEM: installer, manifest schema, `--verify`, `customizable:`, test convention, product topology) |
| session-tracking overlay | `overlays/session-tracking/.memories/QUICK.md` | `overlays/session-tracking/.memories/KNOWLEDGE.md` (handoff-pipeline concepts: map, register, invariants, payload, CLI, topology, distribution, hazards — all `ref:`-keyed) |

Both overlay KNOWLEDGE files are **concept-organized semantic memory** (session 110 dream pass,
mirroring LTG's L-08): every section is `ref:`-keyed and ends with "Source / more detail" pointers.
Per-round narrative was evicted to `.claude/archive/session-tracking-handoff-history.md`.
Write protocol: update sections in place; never append a dated block.
| LTG instance | `ltg/.memories/QUICK.md` | `ltg/.memories/KNOWLEDGE.md` (corpus-specific: calibration values, scope rules, retrieval gaps; engine memories live in the `latent-topic-graph` repo) |
| Coding-delegate (oficina) | `docs/vision/coding-delegate/.memories/QUICK.md` | `docs/vision/coding-delegate/.memories/KNOWLEDGE.md` (implementation invariants from the P1 build: ledger repair-on-append, single-writer topology, PID-reuse guard, intake rule model, FIFO details; created 2026-07-12) — `decisions.md` + `evidence.md` keep vision-level decisions |

QUICK.md = always-injected working memory (~30 lines). KNOWLEDGE.md = on-demand semantic memory (decisions + rationale). Convention from `memory-architecture-design.md`.
<!-- /ref:memory-files -->

---

## Layer 0 Findings (Reference)

Runtime ref blocks (`ref:model-selection`, `ref:thinking-mode`, `ref:structured-output`) and future model candidates → `docs/findings/layer-0-runtime-refs.md`

Other findings (benchmarks, decomposition, few-shot) → `.claude/archive/layer-0-findings.md`

---

## Infrastructure & Setup (Completed)

**Git safety + worktrees** (`ref:git-safety`, `ref:git-worktrees`) → `docs/patterns/technology-conventions.md`

| Topic | File | Key Content |
|-------|------|-------------|
| Phases 0-6 completion details | `.claude/archive/phases-0-6.md` | All setup phases, decisions, gotchas, artifacts |
| session-tracking handoff history | `.claude/archive/session-tracking-handoff-history.md` | Per-round narrative (sessions 86–109) evicted from the overlay's KNOWLEDGE.md — read for "why is it this way?", not "how does it work?" |
| Hardware specs | `.claude/local/hardware-inventory.md` | RTX 3060 12GB, detailed system info (gitignored) |
| Verification | `scripts/verify-installation.sh` | `./scripts/verify-installation.sh` (14 checks); manual: `nvidia-smi`, `ollama ps` |
| **Ollama monitoring stack** | `docs/findings/ollama-monitoring-setup.md` | Prometheus + Grafana via ollama-metrics proxy (port-swap pattern); WSL2 networking gotcha; dashboard import. `ref:ollama-monitoring` |
| **Ollama store + canonical-port squatter** | `docs/plans/ollama-store-ext4-move.md` | ext4 vhdx store; § "Failure mode: canonical-port squatter" — bare `ollama` (0.17.5 TUI) spawns an empty-store server when `:11434` is unreachable. Detection, recovery, guard |
| Installation script | `scripts/setup-ollama.sh` | Idempotent native Ollama setup |
| Docker portable setup | `docker/docker-compose.yml` | GPU config, healthcheck, named volume |
| Ollama config rationale | `docs/modelfile-reference.md` | Why each Modelfile setting was chosen |
| Sampling parameters explained | `docs/sampling-parameters.md` | Temperature & top-p educational guide |

---

<!-- ref:bash-wrappers -->
## Runnable Scripts & Tools

> **RULE: Never invoke Python scripts directly.** Always use the bash wrapper (`run-*.sh`).
> Direct `python3` invocations make "don't ask again" unsafe (whitelists all Python).

### Project Knowledge Tools
| Script | Purpose | When to Use |
|--------|---------|-------------|
| `.claude/tools/resume.sh` | ~40-line session-start summary (status + next + commits) | Every session start |
| `.claude/hooks/guard-git-add-all.py` | `PreToolUse(Bash)` guard — denies bulk `git add -A`/`.`/`--all` (stages unrelated untracked files); allows explicit paths + `git add -u`. Wired in `settings.json`; mirrored by the `block-bulk-git-add` hookify rule | Always-on; see Git Safety Protocol in CLAUDE.md |
| `.claude/hooks/oficina-watch-hook.py` | `PostToolUse(mcp__ollama-bridge__submit_run)` — extracts the accepted run_id, injects the background-`watch-run.sh` instruction (harness-driven result injection, T-89/V-D12). Fail-open | Always-on; wired in `settings.json` |
| `.claude/hooks/oficina-runs-scan.py` | `SessionStart` — scans `~/.local/share/oficina/runs/` (or `$OFICINA_ROOT`) for terminal runs without a `surfaced` marker; injects one line per run (state, origin `submitted_from`, target/answer pointer); writes markers. Stdlib-only, fail-open | Always-on; cross-session run pickup (T-89) |
| `.claude/hooks/tests/run-tests.sh` | Hermetic hook tests — runs every `test_*.py` in `.claude/hooks/tests/` via subprocess against the hook scripts (26 tests). Self-running scripts with a `__main__` block printing PASS/FAIL — **not pytest**, no fixtures | After any change to a `.claude/hooks/` script |
| `.claude/hooks/tests/test_verdict_capture.py` | Verdict-harness tests (T-105, 14): the **producer→consumer round-trip** (fills the actually-injected template and feeds it to the actual consumer — mutation-verified to fail on key drift), content-match provenance incl. the fence-stripped case, silent-on-no-match, both-keys recording, legacy `prompt_hash=` acceptance, dedupe, the sweep regression (two calls sharing one `prompt_hash` are independently judgeable), and the oficina per-run path (prompt only when a deliverable exists; silent while not terminal; `run_id`-keyed block — uses a **real base64url run id**, mutation-verified to fail against a hex-only regex). HOME-isolated via `tempfile` | After any change to `ollama-post-tool.py` or `verdict-capture.py` |
| `.claude/tools/ref-lookup.sh KEY` | Print a ref block by key; `--list` = all keys; `--paths` = KEY→repo-relative-path map (`.claude/local/` excluded) | Any time a `[ref:KEY]` tag is needed; `--paths` for programmatic key→file lookup |
| `overlays/ref-indexing/files/tests/test-ref-lookup-paths.sh` | Fully hermetic tests for `ref-lookup.sh` (`--paths`/`--list`/single-key/glob): builds its own fixture corpus via `--root`, no repo coupling (9 tests, exit 0 = all pass). Run via `make -C overlays test-ref-indexing`; installs to consumer repos as `.claude/tools/tests/...` | After any change to `ref-lookup.sh` |
| `.claude/tools/rotate-session-log.sh` | Archive old session-log entries (keep last 3) | Auto-called by session-handoff skill |
| `.claude/tools/handoff-harvest.sh` | Emit commit subjects since the last `chore(session-handoff): session ` commit (tighter than bare prefix — avoids false boundaries from other `chore(session-handoff):` uses); fallback to last 20 if none found | Run at handoff Step 2 to seed `what_was_done` |
| `.claude/tools/benchmark-status.sh` | Rubrics/prompts/personas/results overview | Before any benchmark session |
| `.claude/tools/ollama-stats.py` | DPO evaluation stats: total calls, model usage, verdict distribution | After evaluating local model outputs; track progress |
| `.claude/tools/ollama-verdicts.py` | Detailed verdict analysis: reasons, patterns, rejection heuristics | Finding which models/prompts need improvement |
| `overlays/session-tracking/files/handoff/run-handoff.sh` | Session-handoff pipeline entrypoint (wraps `handoff.py`): `--payload` (stage) / `--id` (promote) / `--payload --amend` (additive follow-up to last committed session) / `--abort` / `--repo-root` / `--registry`. Lives in the overlay source; installs to `.claude/tools/handoff/run-handoff.sh` in target repos | Running the deterministic handoff transaction; stage emits a JSON handle, promote commits |
| `overlays/test_merge_stage_apply.py` | T-81 Part 1 stage→apply suite (13 tests): staleness invariant (STALE abort before write), dry-run purity, CRLF preservation, independent-path merge check. Hermetic (mocked `FakeBackend`). Run via `make -C overlays test-installer` | After any change to `ai_merge`/stage/apply in `lib/planner.py` |
| `overlays/Makefile` | Overlay dev test runner — delegates to `scripts/`: `make test` (all 291), `make test-ref-indexing` (9), `make test-session-tracking` (214), `make test-installer` (68: `test_verify.py` + `test_customizable.py` + `test_signals.py` + `test_merge_stage_apply.py`). `ARGS='-k x'` passes pytest filters. Default `make` prints help | Before committing overlay changes |
| `overlays/scripts/run-all-tests.sh` | Aggregator — runs every overlay suite, prints a PASS/FAIL summary, exits nonzero on any failure (runs all suites even if one fails). Backs `make test` | CI / one-shot full overlay test run |
| `overlays/scripts/test-{ref-indexing,session-tracking,installer}.sh` | Per-suite runners (resolve cwd + interpreter for each suite); args pass through to the underlying test/pytest. Backs the per-suite `make` targets | Running one overlay's suite standalone |

### LTG Instance Tools (`ltg/` — engine lives in the sibling `latent-topic-graph` repo)
| Script | Purpose | When to Use |
|--------|---------|-------------|
| `ltg/run-rebuild-all.sh` | T-71 derivation-stage sequencer: store → anchors → graph → communities against the llm corpus; ONE authoritative `{index}.bak` pre-backup, stages run `--no-backup`. `--embeddings` (required). | Full derivation rebuild after extract+embed produced a fresh embeddings JSONL |
| `ltg/run-extract-topics.sh` | 2-arm extraction over the frozen manifest (qwen3:14b prose / qwen2.5-coder:14b code); passes `--repo-root ..`. | Re-extraction after corpus changes; feeds run-embed.sh |
| `ltg/run-embed.sh` | Embeds extraction JSONL via qwen3-embedding:8b (4096-dim). | After extraction; produces `runs/<tag>-embeddings.jsonl` |
| `ltg/run-store.sh` / `run-anchors.sh` / `run-graph.sh` / `run-communities.sh` | Individual derivation stages (prefer `run-rebuild-all.sh` for the full chain; ad-hoc runs use stage-suffixed backup slots). | Single-stage reruns, `--degree-probe` |
| `ltg/run-inspect.sh` | Index query CLI: `--list`, `--stats`, `--query TEXT`, `--relate`, `--acceptance`. | Debugging the llm index |
| `ltg/run-relate.sh` | Phase 5 `relate(a,b)` against the llm index (`--a`/`--b`/`--json`/`--no-summary`). | Relating two indexed llm files |
| `ltg/run-build-corpus-manifest.sh` | Freeze `corpus.yaml` intent → `corpus-manifest.yaml` (sha256 + commit); `--repo-root ..`. | After any corpus.yaml change |

All wrappers `cd` into `ltg/` (instance files are CWD-relative) and exec the engine's `ltg-*` entry points via the editable path-dependency (`ltg/pyproject.toml`).

### Personas Test Harness
| Script | Purpose | When to Use |
|--------|---------|-------------|
| `personas/run-tests.sh` | Run pytest test suite for personas module (`python3 -m pytest`) | After any change to models.py or create-persona.py |

### MCP Server
| Script | Purpose | When to Use |
|--------|---------|-------------|
| `mcp-server/Makefile` | Test + diagnostic targets: `make test` (full pytest suite), `make test-oficina` (oficina only), `ARGS='-k x'` passes pytest filters; `make logs`/`logs-raw`/`bridges` for live-bridge observation | Running mcp-server tests; diagnosing a live bridge |
| `mcp-server/run-server.sh` | Launch Ollama MCP server (stdio transport) | Claude Code MCP config, testing |
| `mcp-server/watch-run.sh` | Tail an oficina run to terminal state (`watch-run.sh <run_id>`) — 3-line wrapper over `oficina watch` (P1-D10 whitelisting seam) | Backgrounding a watch on a submitted oficina run |

### Setup & Infrastructure Scripts
| Script | Purpose | When to Use |
|--------|---------|-------------|
| `scripts/run-ctx-probe.sh` | Context-window ceiling probe for 14B models — loads model at 16K/24K/32K, measures VRAM + tok/s per ctx size | Before raising num_ctx on any 14B+ model; re-run if KV cache type changes |
| `scripts/setup-ollama.sh` | Idempotent Ollama install + configure + pull + create | Fresh setup or re-setup |
| `scripts/verify-installation.sh` | 14-check verification (GPU, service, models, API, benchmark) | After setup or to diagnose issues |
| `scripts/pull-layer0-models.sh` | Tiered model downloader (Tier 1-3) | Adding new models |
| `docker/init-docker.sh` | Docker container setup (start, wait, pull, create) | Docker-based deployment |
| `~/workspaces/scripts/gpu-vram-windows.sh` *(machine-local)* | Per-process VRAM on the shared RTX 3060 **as Windows sees it** (via `nvidia-smi.exe` + PowerShell GPU perf counters — Linux `nvidia-smi` can't attribute host VRAM under WDDM). Names each PID, sums over engines, drops pid 0 pool; prints reclaim tips. Arg = threshold MB (default 30) | Diagnosing 14B/32K CPU-offload (T-90); any "why is VRAM full" on the shared desktop GPU. Finding: `ref:kv-quant-vram-contention` |
| `~/workspaces/scripts/ollama-store-check.sh` *(machine-local)* | ext4 store health: mount + service + **canonical-port identity** + cross-port model-count agreement. `--brief` for login hooks | `make -C ~/workspaces ollama-store-check`; any "0 models" / model-not-found mystery |
| `~/workspaces/scripts/ollama-guard.sh` *(machine-local)* | Shadows the `ollama` CLI: reroutes to `:11435` when the proxy is down, refuses only when a bare `ollama` would spawn a rogue empty-store server. Bypass: `OLLAMA_ALLOW_SERVE=1` | Sourced from `~/.bashrc`; edit if the port topology changes |
| `~/workspaces/scripts/ollama-motd.sh` *(machine-local)* | One-line ollama health report per WSL boot (sentinel in `$XDG_RUNTIME_DIR`; nags until healthy) | Sourced from `~/.bashrc` (interactive only) |

### Benchmark Bash Wrappers (use these, not the .py files)
| Wrapper | Wraps | Purpose |
|---------|-------|---------|
| `benchmarks/lib/run-decomposed.sh` | `decomposed-run.py` | Multi-stage incremental build pipeline |
| `benchmarks/lib/run-validate-html.sh` | `validate-html.js` (Puppeteer) | Headless browser smoke test for HTML/JS |
| `benchmarks/lib/run-validate-code.sh` | `validate-code.py` | Code compilation/syntax gate: Go (build+vet), Shell (shellcheck), Python (compile()), Java (javac) |
| `benchmarks/lib/run-structured-tests.sh` | `ollama-probe.py` | JSON schema compliance testing |
| `benchmarks/lib/run-fewshot-test.sh` | `ollama-probe.py` | A/B test: baseline vs few-shot on same prompt |
| `benchmarks/lib/run-compare-models.sh` | `compare-models.py` | Multi-model comparison: same prompt → N models → verdict → DPO pairs |
| `benchmarks/lib/run-record-verdicts.sh` | `record-verdicts.py` | Record verdicts after the fact (when compare ran non-interactively); supports `--list`, `--entry N` |
| `benchmarks/lib/run-write-model-bench.sh` | `writemodel_bench.py` | oficina write-model benchmark (T-104): 3 apply arms (code-anchored / whole-file / model-anchored) × size-bucketed corpus × N runs; reports by size bucket. `--per-bucket`/`--arms`/`--runs`/`--limit`. Serial 14B — full sweep is a multi-hour sit; smoke with `--limit`. `ref:oficina-write-model-benchmark` |

### Benchmark Python/JS Libraries (never call directly)
| Library | Purpose |
|---------|---------|
| `benchmarks/lib/ollama-probe.py` | Core probe tool: `--model --prompt-file --vary --examples --no-think --format-file` |
| `benchmarks/lib/decomposed-run.py` | Pipeline runner for multi-stage prompts |
| `benchmarks/lib/validate-html.js` | Puppeteer headless browser (Node.js) |
| `benchmarks/lib/validate-code.py` | Multi-language validator: Go (build+vet), Shell (shellcheck), Python (compile()), Java (javac+scaffold) |
| `benchmarks/lib/extract-html.py` | Extract HTML from LLM markdown output |
| `benchmarks/lib/extract-code.py` | Extract code blocks from LLM output |
| `benchmarks/lib/generate-report.py` | Generate comparison reports from results |
| `benchmarks/lib/writemodel_apply.py` | Write-model benchmark apply layer (T-104): `locate_function` (ast), `apply_code_anchored`/`apply_whole_file`/`apply_search_replace`, SEARCH/REPLACE parser. Unit-tested in `test_writemodel_apply.py` (19 tests, model-free) |
| `benchmarks/lib/writemodel_corpus.py` | Write-model benchmark corpus generator: size-bucketed tasks (small/medium/large) with a defective target fn + filler fns each carrying a passing test (the regression surface scales with size) |
| `benchmarks/lib/writemodel_bench.py` | Write-model benchmark harness: prompt→ollama_chat→apply→pytest-split (target vs no-regression)→JSONL; `report()` by size bucket |

**Data files (runtime artifacts, not scripts):**

| Path | Content |
|------|---------|
| `~/.local/share/ollama-bridge/calls.jsonl` | All Ollama calls logged by MCP bridge. Fields: ts, model, prompt_hash, prompt, system, response, eval_count, eval_duration_ms, total_duration_ms, temperature, think, had_format. Training data for Layer 7 distillation. |
<!-- /ref:bash-wrappers -->

---

## Personas (Modelfiles)

**Registry:** `personas/registry.yaml` (machine-readable source of truth)
**Template:** `personas/persona-template.md` (spec for creating new personas)
**Full catalog (all categories + modelfiles):** `personas/personas-reference.md` [ref:personas lives here]
**Ideas / future candidates:** `personas/ideas.md`

---

## Layer 1 Implementation

| Topic | File | Key Content |
|-------|------|-------------|
| MCP server (complete project) | `mcp-server/` | FastMCP server, Ollama async client, 10 tools |
| Usage patterns & limitations docs | `mcp-server/README.md` | Architecture, tools, delegation guide, troubleshooting |
| Server config (defaults, env vars) | `mcp-server/src/ollama_mcp/config.py` | OLLAMA_URL, model, timeout, think, temps |
| Ollama async client | `mcp-server/src/ollama_mcp/client.py` | httpx connection pooling, ChatResponse, error types |
| MCP tools (10 total) | `mcp-server/src/ollama_mcp/server.py` | ask_ollama, generate_code, summarize, classify_text, translate, list_models, warm_model, query_personas, detect_persona, build_persona; ask_ollama + generate_code support context_files, refs, output_file |
| Bash wrapper | `mcp-server/run-server.sh` | `uv run` launcher (project convention) |
| Claude Code integration (project) | `.mcp.json` (repo root) | Project-level MCP server registration |
| Claude Code integration (user) | `~/.claude.json` → top-level `mcpServers` | System-wide — available in every Claude Code session |
| Claude Desktop integration | `%APPDATA%\Claude\claude_desktop_config.json` | Uses `wsl --` prefix for Windows-to-WSL bridging |
| MCP timeout config | `~/.bashrc` | `MCP_TIMEOUT=120000` (matches server-side 120s) |

---

## Layer 1 Research (Reference)

<!-- ref:mcp-integration -->
### MCP Integration Quick Reference
Full research → `.claude/archive/layer-1-research.md`

- **Transport:** stdio (subprocess, JSON-RPC over stdin/stdout)
- **Config:** `claude mcp add --transport stdio <name> -- <command>` → `~/.claude.json` (NOT settings.json!)
- **Limits:** 10s timeout (`MCP_TIMEOUT`), 25K token output (`MAX_MCP_OUTPUT_TOKENS`)
- **Language:** Python (FastMCP) — chosen for tool friction, ecosystem, community docs
- **SDK:** `mcp[cli]` (official Python SDK, v1.x stable)
<!-- /ref:mcp-integration -->

---

## Layer 2 Implementation

| Topic | File | Key Content |
|-------|------|-------------|
| Aider project config | `.aider.conf.yml` | Local default (qwen2.5-coder:7b, whole format, no-auto-commits), frontier via CLI flags |
| OpenCode project config | `opencode.json` | 3 providers: Ollama, Google Gemini, Groq |
| Qwen Code config | `~/.qwen/settings.json` | qwen3:8b via Ollama OpenAI-compat API (id = model name) |
| Goose config | `~/.config/goose/config.yaml` | qwen2.5-coder:7b, developer extension; `GOOSE_DISABLE_KEYRING=1` required in WSL2 |
| Frontier API key catalog | `.env` (gitignored) | 7 providers documented with signup URLs and limits |
| Layer 2 decisions | `.claude/archive/decisions-layers-1-3.md` | Tool selection rationale, architecture divide, deferred items |
| Test prompts | `tests/layer2-comparison/` | 3 tests: Spring Boot, visual, MCP tool |
| Test runner guide | `tests/layer2-comparison/README.md` | 5-tool setup, run commands, diff commands, cleanup |
| **Test findings & decision guide** | `docs/findings/layer2-tool-comparison.md` | Full results, failure taxonomy, when to use what |

---

## Layer 3 Implementation

| Topic | File | Key Content |
|-------|------|-------------|
| Persona template spec | `personas/persona-template.md` | Fields, defaults, skeleton, model selection, checklist |
| Persona registry | `personas/registry.yaml` | 28 active, 0 planned; machine-readable source of truth |
| Persona creator CLI | `personas/create-persona.py` | Interactive 8-step flow or `--non-interactive` flags; accepts raw float temps [0.0,2.0] (T-19) |
| Creator bash wrapper | `personas/run-create-persona.sh` | Whitelist-safe entry point (auto-approved) |
| All Modelfiles | `modelfiles/*.Modelfile` | 28 total across all categories |
| Full persona catalog | `personas/personas-reference.md` | All personas by category with modelfile + base model |
| Future persona ideas | `personas/ideas.md` | Candidates not yet built |
| Personas test harness | `personas/run-tests.sh` | `python3 -m pytest` wrapper; 21 tests across unit + integration |
| Personas pytest config | `personas/pyproject.toml` | `[tool.pytest.ini_options]` testpaths + pythonpath |
| Temperature unit tests | `personas/tests/test_temperature.py` | Tests for `parse_temperature_input` (models.py) |
| collect_from_flags tests | `personas/tests/test_collect_flags.py` | Integration tests: argparse + collect_from_flags end-to-end |

---

## Smart RAG / Content-Linking Research (Session 51, 2026-04-13)

Cluster investigating retrieval techniques beyond keyword/vector RAG — triggered by the question of how career chatbot, Claude Code, web-research, and llm repo can "note relations between any part of content." Five philosophies identified across 7 sources.

| What | Where | Ref Key |
|------|-------|---------|
| **Hub / cross-cutting patterns** | `docs/research/smart-rag-index.md` | `smart-rag-research` |
| LLM Wiki (pre-compile + typed KG) — highest relevance | `docs/research/smart-rag-llm-wiki.md` | `rag-llm-wiki` |
| Obsidian Mind (graph-first + classification hook) | `docs/research/smart-rag-obsidian-mind.md` | `rag-obsidian-mind` |
| Repowise (code-graph + git co-change) | `docs/research/smart-rag-repowise.md` | `rag-repowise` |
| Claude-Mem (hybrid observation store) | `docs/research/smart-rag-claude-mem.md` | `rag-claude-mem` |
| MemPalace (hierarchical spatial memory) | `docs/research/smart-rag-mempalace.md` | `rag-mempalace` |
| HERA arxiv (multi-agent RAG — tangential) | `docs/research/smart-rag-hera.md` | `rag-hera` |
| Dify (baseline platform — what not to build) | `docs/research/smart-rag-dify.md` | `rag-dify` |
| Prior conversation (initial survey + architecture) | `docs/ideas/smart-rag.md`, `docs/ideas/smart-rag2.md`, `docs/ideas/smart-rag3.md` | — |
| **Concept paper (publishable-grade, model-agnostic)** | `docs/research/latent-topic-graph.md` | `concept-latent-topic-graph` |
| **Implementation plan (Phases 0–9)** | moved → `latent-topic-graph` repo `docs/plans/` | (was `plan-latent-topic-graph`) |

### LTG — engine knowledge moved to the `latent-topic-graph` repo (T-33 split, session 107)

All engine reference material — the master plan (+ its 19 `ltg-plan-*` section ref keys),
Phase 0/3/4 decisions (`DECISIONS.md`: `ltg-scope`, `ltg-embedding`, `ltg-extractor`, …),
Phase 1 spike results (`spike-results.md`, `spike-rater-notes.md`, `ltg-phase1-*` keys),
probes (`ltg-phase4-*`, `ltg-phase5-acceptance`), and the Phase 4 dataflow diagram — lives
in the sibling repo `/mnt/i/workspaces/latent-topic-graph/` and its `ref-lookup.sh`.
llm keeps: the instance (`ltg/`), the split record (`docs/plans/ltg-repo-split*.md`,
`ref:ltg-split-frozen-decisions`), the registry decision (`docs/ideas/ltg-model-registry-design.md`),
and the concept + smart-rag lineage (`docs/research/`, dual-cited copies in both repos).

## Coding-Delegate Vision (2026-07-11) — async local coding-subagent

**Grand vision (system name: oficina — V-D1 decided 2026-07-11):** ollama-bridge
`generate_code`/`ask_ollama` evolve into an async **deliverable-run** system — submit → `run_id` → detached worker loops coder model against
the Layer-4 evaluator → Claude reviews each deliverable.
**Folder-local index (authoritative map):** `docs/vision/coding-delegate/index.md` — files by
recontextualization intent, all 27 `ref:delegate-*` keys, supporting research artifacts
(2 prior-art surveys, clones survey, cross-repo web-research field report), memory files.
Start here: `docs/vision/coding-delegate/README.md` · working memory:
`docs/vision/coding-delegate/.memories/QUICK.md` · phase plans: **P1 (async substrate) BUILT +
MERGED** (`docs/plans/oficina-p1-async-substrate.md`; sessions 114–115; `oficina` CLI installed
machine-wide + 4 MCP tools live). oficina is a **machine-global service, not an overlay**
(distribution model + new-machine enablement in the folder KNOWLEDGE.md; decision T-86).
**P2 FIRST SLICE BUILT (session 120, T-92, branch `feature/oficina-p2-loop`):** the evaluated
coder⇄evaluator loop for `kind: function`. New modules in `mcp-server/src/ollama_mcp/oficina/`:
`parser.py` (validator-output→`ParsedFailure`), `prompt.py` (`SEGMENTS`+`build_prompt` cache
contract), `workspace.py` (per-run git worktree), `evaluator.py` (stage-ordered evaluate +
delta-scope `attribute` + anti-cheat), `loop.py` (`EvaluatedLoop`); intake/ledger/worker/client
extended (T-91 `num_predict` fix). Plan + result report: `docs/plans/oficina-p2-evaluated-loop.md`.
Cache measurement gotcha (criterion 5): `docs/findings/oficina-p2-cache-measurement-2026-07-15.md`
(`ref:oficina-p2-cache-measurement`). Next: post-slice widening (kinds/validators, escalation ladder).
**PR #76 review (session 121):** confirmed correctness bugs fixed (parser exit-code/short-summary,
subprocess+wall-clock timeouts, symlink path canonicalization, intake kind-scoped rejections +
budgets unknown-key + `num_predict`, service Exhausted terminal + phase map, hook Exhausted case;
235 tests green). Five items deferred with tasks T-95–T-99 (loop/GenerateFn seam unification, refs
`LLM_REPO_ROOT` drop, retention worktree-prune, basename-only path scoping, `auto_verdict`→`calls.jsonl`
plan overclaim): `docs/findings/oficina-p2-review-deferred-2026-07-16.md` (`ref:oficina-p2-review-deferred`).
Loop readability refactors landed (commit 0622c26). **Next-session `/simplify` briefing** (mechanical
dedup targets + what's out of scope): `docs/plans/oficina-p2-simplify-orientation-2026-07-16.md`.

## Web Research Tool (Session 44+)

| What | Where | Ref Key |
|------|-------|---------|
| **Start here** | `docs/research/QUICK-MEMORY.md` | `quick-memory-web-research` |
| Full file catalogue | `docs/research/INDEX.md` | — |
| Vision & architecture | `docs/research/web-research-tool-vision.md` | `vision-web-research` |
| Technical analysis (10 parts) | `docs/research/web-research-tool-analysis.md` | `analysis-web-research` |
| LDR assessment (build-vs-fork) | `docs/research/local-deep-research-assessment.md` | `ldr-assessment` |

