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

<!-- ref:quick-pointers -->
## Quick Pointers (Active Work)

| What | Where |
|------|-------|
| Current layer tasks & progress | `.claude/tasks.md` |
| Active execution plan | `.claude/plan-v2.md` |
| Session log (current) | `.claude/session-log.md` |
| Agent preferences & resume checklist | `.claude/session-context.md` |
| Project rules & constraints | `CLAUDE.md` (repo root) |
| Cross-session memory | `~/.claude/projects/.../memory/MEMORY.md` |
<!-- /ref:quick-pointers -->

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
| Scaffolding template (portable) | `docs/scaffolding-template.md` | `.claude/` convention: directory structure, file purposes, ref:KEY system, setup checklist |
| **Claude Code dynamic workflows guide** | `.claude/workflows-feature-guide.md` | What workflows are (script-orchestrated subagents at scale), when to use vs not, commands (`/deep-research`, `/workflows`, `ultracode`), limits, repo-specific candidates. Captured session 81. |
| **Cache-warmed subagent fan-out pattern** | `docs/patterns/cache-warmed-subagent-fanout.md` | Manual (Agent + SendMessage) fan-out that caches one large shared context per model tier via turn-boundary breakpoints; deferred task injection (copy-to-unique + `copied` ack); planner(Opus)→implementer(Sonnet/worktree) tiers; when this beats a workflow. Ready-to-use shared prompts. `ref:cache-warmed-fanout`. |
| **Technology conventions** | `docs/patterns/technology-conventions.md` | Reusable decisions: Python/uv, MCP, Ollama API, scripts, git, personas, licensing. Self-indexed via `ref:patterns-index` |
| **Code design conventions** | `docs/patterns/code-design-conventions.md` | Structural patterns: named semantic methods over role strings. Self-indexed via `ref:patterns-code-design-index` |
| **LTG ENGINE — MOVED to sibling repo `latent-topic-graph`** | `/mnt/i/workspaces/latent-topic-graph/` | T-33 split (session 107): engine code (`src/ltg/` package), tests, ALL phase plans (master plan + phases 2/2.5/3/4/5 + extractor retrofit), `DECISIONS.md`, `probes/`, spike results, Phase 4 dataflow diagram — moved with full git history. llm keeps the **instance** at `ltg/` (corpus.yaml, config.yaml, index/, wrappers). Split record stays here: `docs/plans/ltg-repo-split.md`. |
| **Session-handoff pipeline design** | `docs/plans/session-handoff-pipeline-design.md` | **Scope A (deterministic spine, NO model):** replace the all-in-Claude handoff with a register-driven pipeline — reuse existing handoff `ref:` blocks as write-slots (no new markers), deterministic locate/apply/verify/commit, git rollback, per-run `input.md`+`report.md` logging. Register shared with `resume.sh`; lives in `session-tracking` overlay. `ref:handoff-pipeline-design`. Frozen, not built (session 83). |
| **Session-handoff Placer enhancement** | `docs/plans/session-handoff-placer-enhancement.md` | **[FUTURE]** the deferred local-model layer on top of Scope A: model expands *terse intent* → prose (saves authoring tokens). Placer altitude, F4 trust boundary, L0/L1 layered verdict, deferred-labeling (a), input↔report vs report↔reality deltas, DPO `calls.jsonl`, model pick, E1–E6 build steps. `ref:handoff-placer-enhancement`. |
| **Session-handoff failure-clarity fix** | `docs/plans/session-handoff-failure-clarity.md` | append↔checkoff consistency fix (verifier `_segment`/loop insertion semantics) + full failure-clarity sweep (where/whose/what triad via `kind`-on-exception, `payload_error`/`internal_tool_bug` statuses). Two-agent dispatch plan. Triggered by expenses bug report (session 93). |
| **LTG repo split (T-33) — FROZEN plan, ready to execute** | `docs/plans/ltg-repo-split.md` | Session 107: S-D1–S-D7 frozen (`ref:ltg-split-frozen-decisions`) — uv path-dep consumption, `ltg/` instance dir, moves/stays/copies table (filter-repo non-destructive extraction), day-one self-index as decoupling acceptance, MCP in new repo, packaging flip during split, single-repo cadence + task migration. Execution: SP-1–SP-14 over 2 sessions. Open input: repo name. |
| **LTG repo split (T-33) discovery — superseded by frozen plan** | `docs/plans/ltg-repo-split-discovery.md` | Session 106: split-before-Phase-6 lean + drivers (workflow decoupling primary), verified dependency map (`store.py:44` REPO_ROOT landmine, corpus/convention coupling), scope lean (engine moves; corpus.yaml+index stay; pluggable-source stance rides along; T-76 registry OUT), open decision register **S-D1–S-D7** (`ref:ltg-split-decisions`: consumption path, instance residency, DECISIONS.md ref-coupling, new-repo bootstrap, MCP placement, packaging flip, session cadence). Freeze + author `ltg-repo-split.md` in a fresh session after PR #67 merges. Companion: `ltg-model-registry-design.md` Part 2. |
| Overlay system plan | `docs/plans/overlay-system-plan.md` | Portable repo augmentation: packaging patterns as installable/updatable overlays. 4 phases, manifest-driven, AI-assisted merge |
| Verdict numeric migration plan | `docs/plans/verdict-numeric-migration.md` | Replace ACCEPTED/IMPROVED/REJECTED string verdicts with 0/1/2 integers across all repos, hooks, data, docs, and memory. 8 phases. |
| **Attributions & license tracking** | `docs/ATTRIBUTIONS.md` | External-dependency license table per CLAUDE.md licensing rule. Note: leidenalg GPL-3 / python-igraph GPL-2+ (copyleft — tracked in the `latent-topic-graph` repo's license decision). |
| patch_file acceptance test results | `docs/plans/ollama-bridge-patch-file-acceptance-results.md` | Session 67 live test results: 10/10 scenarios pass (6 original + tilde fix + 3 user scenarios). `ref:mcp-patch-file-acceptance-results` |
| Overlay wizard idea | `docs/ideas/overlay-wizard.md` | Deferred: running overlay install interactively inside an AI CLI; wizard pattern generalization; eventual local TUI |
| Claude Code source + related repos | `docs/ideas/claude-code-python-port.md` | Leaked TS source (cloned locally), open-multi-agent (MIT TS framework). Key files: `services/mcp/normalization.ts` (MCP response format), `services/autoDream/` (memory consolidation). open-multi-agent supports Ollama via baseURL; verified tool-calling with Gemma 4 + Qwen 3. |
| ollama-scaffolding overlay | `overlays/ollama-scaffolding/` | Local model usage conventions: verdict protocol, decision tree, stubs-then-Ollama, cold-start policy |
| Ollama coordination layer | `docs/ideas/ollama-coordination-layer.md` | Deferred: shared directory contract for multi-process VRAM coordination; migration path from bundled Option 1 |
| Per-language error handling + logging conventions | `docs/ideas/persona-error-handling-conventions.md` | Analysis + proposed Modelfile directives for Python/Java/Go. Covers `basicConfig()` antipattern, catch-log-reraise noise, language-specific rules. Pair with backfill-persona-constraints session. |
| LTG model registry design + shared-library decision | `docs/ideas/ltg-model-registry-design.md` | Part 1 (IMPLEMENTED): two-level `models:` + `roles:` config for `retrieval/config.yaml`; naming convention (property enumeration). Part 2 (session 106, T-76 DEFERRED): registry/roles shared-library extraction — prior-art survey (LiteLLM/any-llm/AbstractCore), two-layer conclusion (transport=commodity, registry layer=build), dependency topology (layer-0 primitives), product tiers, triggers + discipline rules (`ref:model-registry-library-decision`). |
| Ollama eviction/concurrency findings | `docs/findings/ollama-eviction-concurrency-findings.md` | Empirical test results: Ollama queues unloads (no correctness risk); PR #9392 may replace file layer |
| **Ollama KV prefix cache findings** | `docs/findings/ollama-kv-prefix-cache-findings.md` | How implicit prefix reuse works; keep_alive rationale; num_keep analysis; what Ollama exposes vs llama-server. `ref:ollama-kv-prefix-cache`, `ref:ollama-explicit-cache-api` |
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
| Overlays | `overlays/.memories/QUICK.md` | `overlays/.memories/KNOWLEDGE.md` |
| LTG instance | `ltg/.memories/QUICK.md` | `ltg/.memories/KNOWLEDGE.md` (corpus-specific: calibration values, scope rules, retrieval gaps; engine memories live in the `latent-topic-graph` repo) |

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
| Hardware specs | `.claude/local/hardware-inventory.md` | RTX 3060 12GB, detailed system info (gitignored) |
| Verification | `scripts/verify-installation.sh` | `./scripts/verify-installation.sh` (14 checks); manual: `nvidia-smi`, `ollama ps` |
| **Ollama monitoring stack** | `docs/findings/ollama-monitoring-setup.md` | Prometheus + Grafana via ollama-metrics proxy (port-swap pattern); WSL2 networking gotcha; dashboard import. `ref:ollama-monitoring` |
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
| `.claude/tools/ref-lookup.sh KEY` | Print a ref block by key; `--list` = all keys; `--paths` = KEY→repo-relative-path map (`.claude/local/` excluded) | Any time a `[ref:KEY]` tag is needed; `--paths` for programmatic key→file lookup |
| `overlays/ref-indexing/files/tests/test-ref-lookup-paths.sh` | Fully hermetic tests for `ref-lookup.sh` (`--paths`/`--list`/single-key/glob): builds its own fixture corpus via `--root`, no repo coupling (9 tests, exit 0 = all pass). Run via `make -C overlays test-ref-indexing`; installs to consumer repos as `.claude/tools/tests/...` | After any change to `ref-lookup.sh` |
| `.claude/tools/rotate-session-log.sh` | Archive old session-log entries (keep last 3) | Auto-called by session-handoff skill |
| `.claude/tools/handoff-harvest.sh` | Emit commit subjects since the last `chore(session-handoff): session ` commit (tighter than bare prefix — avoids false boundaries from other `chore(session-handoff):` uses); fallback to last 20 if none found | Run at handoff Step 2 to seed `what_was_done` |
| `.claude/tools/benchmark-status.sh` | Rubrics/prompts/personas/results overview | Before any benchmark session |
| `.claude/tools/ollama-stats.py` | DPO evaluation stats: total calls, model usage, verdict distribution | After evaluating local model outputs; track progress |
| `.claude/tools/ollama-verdicts.py` | Detailed verdict analysis: reasons, patterns, rejection heuristics | Finding which models/prompts need improvement |
| `overlays/session-tracking/files/handoff/run-handoff.sh` | Session-handoff pipeline entrypoint (wraps `handoff.py`): `--payload` (stage) / `--id` (promote) / `--payload --amend` (additive follow-up to last committed session) / `--abort` / `--repo-root` / `--registry`. Lives in the overlay source; installs to `.claude/tools/handoff/run-handoff.sh` in target repos | Running the deterministic handoff transaction; stage emits a JSON handle, promote commits |
| `overlays/Makefile` | Overlay dev test runner — delegates to `scripts/`: `make test` (all 196), `make test-ref-indexing` (9), `make test-session-tracking` (174), `make test-installer` (13). `ARGS='-k x'` passes pytest filters. Default `make` prints help | Before committing overlay changes |
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
| `mcp-server/run-server.sh` | Launch Ollama MCP server (stdio transport) | Claude Code MCP config, testing |

### Setup & Infrastructure Scripts
| Script | Purpose | When to Use |
|--------|---------|-------------|
| `scripts/run-ctx-probe.sh` | Context-window ceiling probe for 14B models — loads model at 16K/24K/32K, measures VRAM + tok/s per ctx size | Before raising num_ctx on any 14B+ model; re-run if KV cache type changes |
| `scripts/setup-ollama.sh` | Idempotent Ollama install + configure + pull + create | Fresh setup or re-setup |
| `scripts/verify-installation.sh` | 14-check verification (GPU, service, models, API, benchmark) | After setup or to diagnose issues |
| `scripts/pull-layer0-models.sh` | Tiered model downloader (Tier 1-3) | Adding new models |
| `docker/init-docker.sh` | Docker container setup (start, wait, pull, create) | Docker-based deployment |

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

## Web Research Tool (Session 44+)

| What | Where | Ref Key |
|------|-------|---------|
| **Start here** | `docs/research/QUICK-MEMORY.md` | `quick-memory-web-research` |
| Full file catalogue | `docs/research/INDEX.md` | — |
| Vision & architecture | `docs/research/web-research-tool-vision.md` | `vision-web-research` |
| Technical analysis (10 parts) | `docs/research/web-research-tool-analysis.md` | `analysis-web-research` |
| LDR assessment (build-vs-fork) | `docs/research/local-deep-research-assessment.md` | `ldr-assessment` |

