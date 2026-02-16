# Knowledge Index

**Purpose:** Map of where all project information lives. Read this to find anything.

### Indexing Conventions (Two-Tier System)

| Tier | Notation | When to Use | Lookup Method |
|------|----------|-------------|---------------|
| **Active reference** | `<!-- ref:KEY -->` + `[ref:KEY]` | Agent needs this during work; CLAUDE.md rules point here | `.claude/tools/ref-lookup.sh KEY` (machine-lookupable) |
| **Navigation pointer** | `§ "Heading"` | Index/docs pointing to sections for background reading | Open file, find heading (human/agent reads) |

**Active refs** are for high-frequency, runtime lookups (model selection rules, bash wrapper lists, MCP config).
**§ pointers** are for low-frequency, "read when needed" navigation (research findings, decision rationale, historical context).

---

## Quick Pointers (Active Work)

| What | Where |
|------|-------|
| Current layer tasks & progress | `.claude/tasks.md` |
| Active execution plan | `.claude/plan-v2.md` |
| Session log (current) | `.claude/session-log.md` |
| Agent preferences & resume checklist | `.claude/session-context.md` |
| Project rules & constraints | `CLAUDE.md` (repo root) |
| Cross-session memory | `~/.claude/projects/.../memory/MEMORY.md` |

---

## Architecture & Strategy

| Topic | File | Key Content |
|-------|------|-------------|
| 10-layer vision & goals | `docs/vision-and-intent.md` | Why this project exists, principles, use cases |
| Full execution roadmap | `.claude/plan-v2.md` | All 10 layers, dependency graph, cross-cutting concerns |
| Model inventory & VRAM budgets | `docs/model-strategy.md` | Which models for which roles, quantization choices |
| Closing-the-gap techniques | `docs/closing-the-gap.md` | 14 techniques to narrow local vs frontier quality gap |
| Routing patterns (A/B/C) | `docs/vision-and-intent.md` | Local-first, frontier-delegates, chat-routes-both |

---

## Layer 0 Findings (Reference)

<!-- ref:model-selection -->
### Model Selection Rules
Detailed benchmarks and selection rules → `.claude/archive/layer-0-findings.md`

| Scenario | Model |
|----------|-------|
| Quick code gen, boilerplate | 8B think:false |
| Medium algorithms | 8B think:false |
| Complex architecture | 14B think:false |
| Multi-file / long context | 8B (14B can't fit ~4K ctx) |
| Retry after 8B failure | 14B think:true |
| Classification / routing | 8B or 4B |
<!-- /ref:model-selection -->

<!-- ref:thinking-mode -->
### Thinking Mode Strategy
Full measurements → `.claude/archive/layer-0-findings.md` § "Task 0.8 Findings"

- **`/no_think` does NOT work** — only API parameter `think: false` disables thinking
- Default: `think: false` for all tasks
- Escalate to `think: true` for: complex architecture, retry after failure
- Overhead: 67-84% of Qwen3 tokens are hidden thinking (3-7x slower)
- `think` is an API param, not a Modelfile setting — callers must set it
<!-- /ref:thinking-mode -->

<!-- ref:structured-output -->
### Structured Output (JSON Schema)
Full test results → `.claude/archive/layer-0-findings.md` § "Task 0.7 Findings"

- Always use `format` param — 100% valid JSON with it, 0% without it
- No speed penalty (~0-3% overhead)
- Enum enforcement is reliable — model cannot violate schema constraints
- Without `format`, coding personas write code instead of answering analytical questions
- Combine with `think: false` for fastest structured responses
<!-- /ref:structured-output -->

Other Layer 0 findings:

| Topic | File | Key Takeaway |
|-------|------|-------------|
| Qwen3 vs Qwen2.5 benchmarks | `.claude/archive/layer-0-findings.md` | 4 personas × 6 prompts; hidden thinking tokens discovery |
| 14B performance profile | `.claude/archive/layer-0-findings.md` | 32 tok/s, ~4K context, best for complex single-Q |
| Prompt decomposition results | `.claude/archive/layer-0-findings.md` | 3-stage sweet spot, reduces bug severity not count |
| Few-shot example library | `benchmarks/examples/` | 6 examples (3 backend, 3 visual), `--examples` flag |

---

## Infrastructure & Setup (Completed)

<!-- ref:verification -->
### Verification Commands
Full command snippets → `.claude/archive/phases-0-6.md` § "Useful Commands"

- Automated: `./scripts/verify-installation.sh` (14 checks)
- Manual: `nvidia-smi`, `ollama ps`, `curl localhost:11434`
- Performance: API curl + python tok/s calculation one-liner
<!-- /ref:verification -->

<!-- ref:git-safety -->
### Git Safety Protocol
1. **Explain** what the command will do → get explicit user approval BEFORE running
2. **Backup first** — `git branch safety-backup-$(date +%s)`
3. **Dry-run** when available (`--dry-run`, `--no-act`) → show output before executing
4. **Verify** after each operation: `git fsck --full` and `git log --oneline -5`
5. **If verification fails** — stop and restore from backup, do not fix forward

Double-check remote URLs before any push. Never delete `.git` contents without a backup.
<!-- /ref:git-safety -->

<!-- ref:git-worktrees -->
### Git Worktrees for Parallel Work
```bash
git worktree add ../llm-feature-branch feature-branch
git worktree add ../llm-experiment experiment-branch
```
Each worktree is an isolated checkout sharing the same `.git` object store. Prefer worktrees over branch switching for parallel agent work, evaluation comparisons, or multiple branches at once.
<!-- /ref:git-worktrees -->

Other infrastructure:

| Topic | File | Key Content |
|-------|------|-------------|
| Phases 0-6 completion details | `.claude/archive/phases-0-6.md` | All setup phases, decisions, gotchas, artifacts |
| Hardware specs | `.claude/local/hardware-inventory.md` | RTX 3060 12GB, detailed system info (gitignored) |
| Verification report | `verification-report.md` | Phase 0 GPU/WSL2 verification findings |
| Installation script | `scripts/setup-ollama.sh` | Idempotent native Ollama setup |
| Verification script | `scripts/verify-installation.sh` | 14-check automated verification suite |
| Docker portable setup | `docker/docker-compose.yml` | GPU config, healthcheck, named volume |
| Ollama config rationale | `docs/modelfile-reference.md` | Why each Modelfile setting was chosen |
| Sampling parameters explained | `docs/sampling-parameters.md` | Temperature & top-p educational guide |

---

<!-- ref:bash-wrappers -->
## Runnable Scripts & Tools

> **RULE: Never invoke Python scripts directly.** Always use the bash wrapper (`run-*.sh`).
> Direct `python3` invocations make "don't ask again" unsafe (whitelists all Python).

### MCP Server
| Script | Purpose | When to Use |
|--------|---------|-------------|
| `mcp-server/run-server.sh` | Launch Ollama MCP server (stdio transport) | Claude Code MCP config, testing |

### Setup & Infrastructure Scripts
| Script | Purpose | When to Use |
|--------|---------|-------------|
| `scripts/setup-ollama.sh` | Idempotent Ollama install + configure + pull + create | Fresh setup or re-setup |
| `scripts/verify-installation.sh` | 14-check verification (GPU, service, models, API, benchmark) | After setup or to diagnose issues |
| `scripts/pull-layer0-models.sh` | Tiered model downloader (Tier 1-3) | Adding new models |
| `docker/init-docker.sh` | Docker container setup (start, wait, pull, create) | Docker-based deployment |

### Benchmark Bash Wrappers (use these, not the .py files)
| Wrapper | Wraps | Purpose |
|---------|-------|---------|
| `benchmarks/lib/run-decomposed.sh` | `decomposed-run.py` | Multi-stage incremental build pipeline |
| `benchmarks/lib/run-validate-html.sh` | `validate-html.js` (Puppeteer) | Headless browser smoke test for HTML/JS |
| `benchmarks/lib/run-validate-code.sh` | `validate-code.py` | Go compilation + vet gate for backend code |
| `benchmarks/lib/run-structured-tests.sh` | `ollama-probe.py` | JSON schema compliance testing |
| `benchmarks/lib/run-fewshot-test.sh` | `ollama-probe.py` | A/B test: baseline vs few-shot on same prompt |

### Benchmark Python/JS Libraries (never call directly)
| Library | Purpose |
|---------|---------|
| `benchmarks/lib/ollama-probe.py` | Core probe tool: `--model --prompt-file --vary --examples --no-think --format-file` |
| `benchmarks/lib/decomposed-run.py` | Pipeline runner for multi-stage prompts |
| `benchmarks/lib/validate-html.js` | Puppeteer headless browser (Node.js) |
| `benchmarks/lib/validate-code.py` | Go build + vet scaffolding |
| `benchmarks/lib/extract-html.py` | Extract HTML from LLM markdown output |
| `benchmarks/lib/extract-code.py` | Extract code blocks from LLM output |
| `benchmarks/lib/generate-report.py` | Generate comparison reports from results |
<!-- /ref:bash-wrappers -->

---

<!-- ref:personas -->
## Personas (Modelfiles)

| Persona | Modelfile | Base Model | Role |
|---------|-----------|------------|------|
| my-coder | `modelfiles/coding-assistant.Modelfile` | Qwen2.5-Coder-7B | Java/Go backend |
| my-coder-q3 | `modelfiles/coding-assistant-qwen3.Modelfile` | Qwen3-8B | Java/Go backend (Qwen3) |
| my-creative-coder | `modelfiles/creative-coder-qwen25.Modelfile` | Qwen2.5-Coder-7B | Visual/creative coding |
| my-creative-coder-q3 | `modelfiles/creative-coder-qwen3.Modelfile` | Qwen3-8B | Visual/creative (Qwen3) |
| my-codegen-q3 | `modelfiles/codegen-qwen3.Modelfile` | Qwen3-8B | General-purpose code gen |
| my-summarizer-q3 | `modelfiles/summarizer-qwen3.Modelfile` | Qwen3-8B | Text summarization |
| my-classifier-q3 | `modelfiles/classifier-qwen3.Modelfile` | Qwen3-8B | Text classification (JSON) |
| my-translator-q3 | `modelfiles/translator-qwen3.Modelfile` | Qwen3-8B | Language translation |
<!-- /ref:personas -->

---

## Session History

| Session | Handoff File | Highlights |
|---------|-------------|------------|
| Sessions 1-4 (Phases 0-2) | `.claude/session-handoff-2026-02-03.md` | GPU passthrough, Ollama install, 67 tok/s |
| Sessions 5-7 (Phases 3-5) | `.claude/session-handoff-2026-02-06.md` | Modelfile, my-coder, Docker, verification |
| Session 8 (Plan v2) | `.claude/session-handoff-2026-02-08.md` | 10-layer plan drafted |
| Session 9 (Benchmarks) | `.claude/session-handoff-2026-02-09b.md` | Benchmark framework, Qwen3 findings |
| Sessions 10-12 (Layer 0) | `.claude/session-handoff-2026-02-11.md` | Decomposition, validation, few-shot, Layer 0 complete |
| Layer 0 full session log | `.claude/archive/session-log-layer0.md` | 717 lines, Sessions 8-12 detailed history |

---

## Layer 1 Implementation

| Topic | File | Key Content |
|-------|------|-------------|
| MCP server (complete project) | `mcp-server/` | FastMCP server, Ollama async client, 6 tools |
| Usage patterns & limitations docs | `mcp-server/README.md` | Architecture, tools, delegation guide, troubleshooting |
| Server config (defaults, env vars) | `mcp-server/src/ollama_mcp/config.py` | OLLAMA_URL, model, timeout, think, temps |
| Ollama async client | `mcp-server/src/ollama_mcp/client.py` | httpx connection pooling, ChatResponse, error types |
| MCP tools (6 total) | `mcp-server/src/ollama_mcp/server.py` | ask_ollama, list_models, generate_code, summarize, classify_text, translate |
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

| Topic | File | Key Takeaway |
|-------|------|-------------|
| MCP protocol, transports, Claude Code integration | `.claude/archive/layer-1-research.md` | stdio transport, tool descriptions are routing |
| Language comparison (Python/Go/Java/Kotlin/TS) | `.claude/archive/layer-1-research.md` § "Language Decision" | Python: lowest friction, best ecosystem |
| Existing tools landscape | `.claude/archive/layer-1-research.md` § "Existing Tools Landscape" | No drop-in; patterns to borrow from 4 projects |
| MCP server discovery registries | `.claude/archive/layer-1-research.md` § "MCP Server Discovery Resources" | mcp.so, mcpservers.org, awesome-mcp-servers, etc. |
| All 10 official SDK repos | `.claude/archive/layer-1-research.md` § "SDK Quick Reference" | TS, Python, Go, Java, Kotlin, C#, Swift, Ruby, Rust, PHP |

---

## Layer 2 Implementation

| Topic | File | Key Content |
|-------|------|-------------|
| Aider project config | `.aider.conf.yml` | Local default (qwen2.5-coder:7b, whole format), frontier via CLI flags |
| OpenCode project config | `opencode.json` | 3 providers: Ollama, Google Gemini, Groq |
| Frontier API key catalog | `.env` (gitignored) | 7 providers documented with signup URLs and limits |
| Layer 2 decisions | `.claude/session-context.md` § "Layer 2 Decisions" | Tool selection rationale, architecture divide, deferred items |

---

## Research & Background

| Topic | File |
|-------|------|
| LLM engines, OpenClaw, WSL2 setup | `local-llm_and_open-claw.md` |
| Ollama config, Docker, portability | `llm-configuration-research.md` |
| Local LLM ecosystem concepts | `docs/concepts-local-llm-ecosystem.md` |
