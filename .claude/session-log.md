# Session Log

**Current Session:** 2026-02-09
**Phase:** Layer 0 — Foundation Upgrades

---

## 2026-02-10 - Session 8: Structured Output Testing (Task 0.7)

### Context
Continued Layer 0 from Session 7. Previous session (from Git Bash) designed the test suite but failed at execution due to `wsl -- bash -c` glob mangling. This session ran from WSL2 natively, picking up where the run failed.

### What Was Done

**Task 0.7 — Structured output (JSON schema) with Ollama:**
- Verified all 10 files from previous session landed correctly (5 prompts + 5 schemas in `prompts/structured/`)
- Verified probe tool extensions (`--format-file`, `--no-think`, JSON validation column)
- Created `lib/run-structured-tests.sh` — thin wrapper for whitelisting without authorizing all Python
- Ran full test matrix: 5 prompts × 2 models × 2 variants = 20 API calls
- All 10 format=on responses: valid JSON, schema-compliant, correct enum values
- All 10 format=off responses: zero JSON produced — coding personas wrote code instead
- Key insight: `format` parameter changes model behavior qualitatively, not just formatting
- No speed penalty: per-token throughput identical with/without constrained decoding
- No hallucinations in any constrained response across both models

### Decisions Made
- Structured output is mandatory (not optional) for any task requiring JSON from coding personas
- Safe to use in hot paths — no meaningful throughput impact
- Combine with `think: false` for fastest structured responses

### Artifacts Created/Modified
| File | Action |
|------|--------|
| `benchmarks/lib/run-structured-tests.sh` | Created — test runner wrapper |
| `benchmarks/results/structured/*.json` | Created — 10 result files (gitignored) |
| `.claude/plan-v2.md` | Updated — Task 0.7 findings section |
| `.claude/tasks.md` | Updated — 0.7 marked complete |
| `.claude/session-context.md` | Updated — checkpoint |

### Next
- Task 0.4: Create few-shot example library for common coding tasks
- Task 0.9: Prompt decomposition for visual tasks
- Task 0.10: Runtime validation (headless browser smoke test)
- 3 tasks remain to complete Layer 0

---

## 2026-02-09 - Session 7: Thinking Mode, Skeleton Prompts, 14B Testing (Tasks 0.8, 0.3, 0.5)

### Context
Continued Layer 0 from Session 6 (benchmark complete). Picked up at task 0.8 (thinking mode management), which was the highest-impact finding from the benchmark.

### What Was Done

**Task 0.8 — Qwen3 thinking mode management:**
- Discovered `/no_think` in user messages does NOT disable thinking (soft hint only, model ignores it)
- Only the API-level `think: false` parameter truly suppresses reasoning
- Measured overhead: 3.2x (simple) to 6.9x (complex) speedup with `think: false`
- Decided default strategy: `think: false` everywhere, escalate to `think: true` for complex reasoning or retries
- Trivial example: 674 tokens / 11.8s with thinking vs 3 tokens / 0.04s without — 225x difference

**Task 0.3 — Skeleton prompt rewrite:**
- Rewrote all 4 Modelfiles (my-coder, my-coder-q3, my-creative-coder, my-creative-coder-q3) from soft-language prose to ROLE/CONSTRAINTS/FORMAT skeleton format
- Each MUST/MUST NOT constraint targets a real failure from benchmark 0.2 (hallucinated imports, over-engineering, variable shadowing, incomplete code)
- ~95 tokens per prompt (under 200-token ceiling from closing-the-gap spec)
- Recreated all 4 models in Ollama, smoke-tested

**Task 0.5 — Qwen3-14B testing:**
- 14B loads on 12GB VRAM (10.4 GB used), but context limited to ~4K tokens
- 32 tok/s (1.7x slower than 8B's 56 tok/s)
- 14B is more concise: 14% fewer tokens on same prompt, 40% less thinking
- Best for: complex single-question tasks. Not for multi-file/long context work

**Tooling:**
- Saved `benchmarks/lib/ollama-probe.py` — reusable A/B test tool for Ollama API parameters
- Addresses security concern: saved scripts are safe to "don't ask again" vs inline `python3 -c` which whitelists all Python

### Decisions Made
- Default thinking mode: `think: false` for all tasks, escalate to `think: true` for complex or retries
- 14B role: escalation model for complex single questions, not general-purpose (VRAM limit)
- Tooling pattern: save scripts to `benchmarks/lib/` instead of inline Python for security and reuse

### Known Issues
- Probe tool only varies one parameter at a time — can't cross model × think in single run

### Artifacts Created/Modified
| File | Action |
|------|--------|
| `benchmarks/lib/ollama-probe.py` | Created — A/B test tool |
| `modelfiles/coding-assistant.Modelfile` | Rewritten — skeleton format |
| `modelfiles/coding-assistant-qwen3.Modelfile` | Rewritten — skeleton format |
| `modelfiles/creative-coder-qwen25.Modelfile` | Rewritten — skeleton format |
| `modelfiles/creative-coder-qwen3.Modelfile` | Rewritten — skeleton format |
| `.claude/plan-v2.md` | Updated — 0.8 + 0.5 findings sections |
| `.claude/tasks.md` | Updated — 0.3, 0.5, 0.8 marked complete |

### Next
- Task 0.7: Test structured output (JSON schema) with Ollama — foundational for MCP server (Layer 1)
- Task 0.4: Create few-shot example library
- Tasks 0.9, 0.10: Visual decomposition and runtime validation

---

## 2026-02-09 - Session 6: Benchmark Qwen3-8B vs Qwen2.5-Coder-7B (Task 0.2)

### Context
Layer 0 tasks 0.1a and 0.6 (model downloads) were complete from previous session. This session created benchmark personas, built the full benchmark framework, ran the benchmark, and analyzed results with frontier review.

### What Was Done

**Research phase:**
- Investigated Harbor Bench (LLM-as-judge with YAML tasks, OpenAI-compatible API)
- Found LocalLLM Visual Code Test (7-prompt automated benchmark, KoboldCpp backend)
- Analyzed viral animation coding challenges (Reddit bouncing balls in heptagon, Towards AI rotating box)
- Collected the exact Reddit prompt (20 balls, 20 specific hex colors, spinning heptagon, Python/tkinter)

**Persona creation (task 0.1b):**
- Created `my-creative-coder` (Qwen2.5-Coder:7b) and `my-creative-coder-q3` (Qwen3:8b)
- Same sampling params as my-coder for fair comparison (temp 0.3, top_p 0.9, repeat_penalty 1.1, 16K context)
- HTML/CSS/JS creative coding system prompt (Canvas API, physics, single-file output)
- Also created `my-coder-q3` (Qwen3:8b with my-coder's Java/Go prompt)

**Benchmark framework (task 0.2):**
- Built `benchmarks/run-benchmark.sh` (~350 lines): CLI with --models, --prompts, --dry-run, --no-skip, --open
- Created 6 prompt files: 3 backend (Go LRU cache, Java CSV parser, Merge intervals) + 3 visual (bouncing ball, heptagon, aquarium)
- Python helpers: `extract-html.py` (4 extraction strategies), `extract-code.py` (language inference), `generate-report.py`
- Prompt metadata format with YAML frontmatter (id, category, models, timeout, description, source)

**Benchmark execution:**
- Dry-run: verified 4 models × 6 prompts = 24 combinations (12 eligible per model-category match)
- Full run 1: 10 PASS, 2 FAIL (Qwen3 backend timeouts at 120s)
- Re-run with 300s timeouts: Go LRU cache succeeded (9372 tokens, 183s), Java CSV still timed out

**Analysis — key discovery: hidden thinking tokens:**
- Qwen3's `<think>` blocks are stripped by Ollama from `message.content` but counted in `eval_count`
- 75–88% of Qwen3's tokens are invisible reasoning
- Chars/token diagnostic: Qwen2.5 ~3.5 chars/tok (normal for code), Qwen3 0.42–1.75 chars/tok (inflated)
- Effective visible throughput: Qwen3 ~8 tok/s equivalent vs Qwen2.5 ~66 tok/s

**Frontier model review:**
- All 6 visual outputs rated poor (both models)
- Root causes: incorrect rotation transforms, broken collision math, variable shadowing crashes, ugly procedural shapes
- Qwen3 aquarium crashes on frame 1: `for (let fish of fish)` shadowing bug
- Best backend output: merge intervals from both models (A-)
- Go LRU cache: use-after-delete bug (Qwen2.5), overcomplicated struct (Qwen3)

**Three new tasks identified:**
- 0.8: Qwen3 thinking mode management (`/no_think` testing, per-task strategy)
- 0.9: Prompt decomposition for visual tasks (closing-the-gap #3 applied)
- 0.10: Runtime validation (headless browser smoke test for console errors)

### Known Issues
- `explorer.exe` returns exit 126 from WSL background processes — Chrome path identified (`/mnt/c/Program Files/Google/Chrome/Application/chrome.exe`) but not yet integrated
- Java CSV parser timed out even at 300s with Qwen3 (excessive thinking)

### Decisions Made
- Visual benchmarks need separate personas (not my-coder which targets Java/Go)
- Persona name: `my-creative-coder` (combination of user's options 3 and 4)
- Keep `my-coder` name for now (rename deferred)
- Timeouts: backend 300s, visual 180s (visual extended to 300 for heptagon)

### Artifacts Created
| File | Purpose |
|------|---------|
| `modelfiles/creative-coder-qwen3.Modelfile` | Visual benchmark persona on Qwen3:8b |
| `modelfiles/creative-coder-qwen25.Modelfile` | Visual benchmark persona on Qwen2.5-Coder:7b |
| `modelfiles/coding-assistant-qwen3.Modelfile` | my-coder-q3 on Qwen3:8b |
| `benchmarks/run-benchmark.sh` | Main benchmark driver (~350 lines) |
| `benchmarks/lib/extract-html.py` | HTML extraction from model responses |
| `benchmarks/lib/extract-code.py` | Code block extraction for backend prompts |
| `benchmarks/lib/generate-report.py` | Markdown report from summary.json |
| `benchmarks/prompts/backend/*.md` (3 files) | Go LRU cache, Java CSV parser, Merge intervals |
| `benchmarks/prompts/visual/*.md` (3 files) | Bouncing ball, Heptagon, Aquarium |
| `benchmarks/results/2026-02-09T082340/` | Full benchmark run (gitignored) |
| `benchmarks/results/2026-02-09T090642/` | Qwen3 re-run with 300s timeouts (gitignored) |

### Next
- Task 0.8: Test Qwen3 `/no_think` — measure thinking overhead, decide when to enable/disable
- Task 0.3: Rewrite my-coder system prompt in skeleton format
- Task 0.9: Design decomposed visual prompts (draw → physics → animate → combine)
- Fix Chrome integration for `--open` flag in benchmark script

---

## 2026-02-08 - Session 5: Insights Review & Pre-Layer 0 Prep

### Context
New session after conversation export. Recontextualized from session tracking files and last session transcript (749a6baf).

### What Was Done
- Reviewed insights report (`/insights` from last session): friction analysis, feature suggestions, CLAUDE.md recommendations
- **Git housekeeping:** Committed test artifacts and Phase 0 files; moved redundant research (`bios.md`, `enable-wsl2.md`) to `.claude/local/`; added `.gitignore` pattern for conversation exports
- **CLAUDE.md hardening:** Added 3 new sections from insights analysis:
  - Troubleshooting Approach (ask before suggesting, check prior context)
  - Environment Context (Windows/WSL2/MINGW stack, path mangling, sudo limitations)
  - Git Operations (safety protocol: explain → backup → dry-run → verify; worktree pattern for parallel work)
- **Agent interaction principles:** Created `docs/agent-interaction-principles.md` — 7 behavioral standards for any agent in the stack (verification gates, explain-then-execute, scope discipline, isolation, structured communication)
- Session tracking updated

### Decisions Made
- Git worktrees identified as the right pattern for multi-agent parallel work
- Agent interaction principles are a reusable reference for persona creation (Layer 3) — not just Claude Code rules
- Closing-the-gap techniques integrate with agent principles (structured output, decomposition, few-shot)
- `/session-handoff` custom skill created (available from next session onward)
- Hooks (post-edit validation) deferred until Go/YAML coding begins
- Claude Desktop data export: do it now, analyze in Layer 4.6 as first evaluator use case
- Plan v2 updated: Task 4.6 added (conversation insights pipeline)

### Artifacts Created
| File | Purpose |
|------|---------|
| `docs/agent-interaction-principles.md` | 7 behavioral standards for any agent in the stack |
| `.claude/skills/session-handoff/SKILL.md` | Custom skill for end-of-session workflow |

### Commits (4)
- `e4faae1` — Phase 0 verification report, test artifacts, WSL2 troubleshooting history
- `6bfa97d` — CLAUDE.md hardening + agent interaction principles
- `bfc16ab` — /session-handoff custom skill
- `878ffa4` — Layer 4.6 conversation insights pipeline task

### Next
- Begin Layer 0 (foundation upgrades: Qwen3-8B, structured prompts, benchmarks)
- Export Claude Desktop data to `.claude/local/exports/` for future analysis
- `/session-handoff` skill available for first use

---

## 2026-02-03 - Session 2: Phase 0 Completion & Tracking System Setup

### Context
Resumed after system restart. Previous session identified WSL2 conversion blocker (`hypervisorlaunchtype=Off`) and applied fix.

### Verified
- ✅ `wsl -d Ubuntu-22.04 -e nvidia-smi` now works
- ✅ Ubuntu-22.04 confirmed as WSL version 2 (`wsl -l -v`)
- ✅ GPU passthrough functional

### Decisions Made

1. **Session tracking system created**
   - `.claude/tasks.md` - simple progress checklist
   - `.claude/session-log.md` - detailed history (this file)
   - `.claude/session-context.md` - agent handoff instructions
   - `.claude/local/` - gitignored folder for sensitive data

2. **Log rotation policy:** By phase (rename logs when phase completes)

3. **Sensitive data handling:** Hardware specs moved to `.claude/local/hardware-inventory.md`

4. **Output style:** Explanatory (not Learning) - interactive tutorial approach

5. **Pending decisions for Phase 1:**
   - CUDA Toolkit: install or skip? (user unsure, needs recommendation)
   - Docker phase: do after native install (Phases 1-3 first)

### Files Created/Modified
| File | Action |
|------|--------|
| `.gitignore` | Created - excludes `.claude/local/`, `settings.local.json` |
| `.claude/local/hardware-inventory.md` | Created - sensitive hardware details |
| `.claude/session-context.md` | Created - agent handoff instructions |
| `.claude/tasks.md` | Created - progress checklist |
| `.claude/session-log.md` | Created - this file |
| `CLAUDE.md` | Updated - added session tracking docs, fixed output style |
| `.claude/progress.md` | Renamed → `wsl2-setup-history.md` |
| `verification-report.md` | Updated - marked Phase 0 complete |

### Next Steps
- User will commit files to git
- User will say "Begin Phase 1" to start
- Phase 1.1: Enable systemd in WSL2

---

## Phase 1: WSL2 Environment Setup

**Started:** 2026-02-03 ~20:05
**Status:** ✅ Complete

### Step 1.1: systemd Check
- Result: Already enabled (default in WSL 2.6.3+)
- PID 1 is `systemd`
- Services running: dbus, cron, journald, etc.
- No wsl.conf needed

### Step 1.2: CUDA Toolkit
- Decision: Skipped
- Rationale: Ollama bundles its own CUDA runtime, only needs libcuda.so from driver

### Step 1.3: GPU Verification
- nvidia-smi: ✅ Working
- GPU: RTX 3060, 12288 MiB VRAM
- Driver: 591.74 (Windows) / 590.52.01 (WSL SMI)
- CUDA: 13.1 (max supported)
- Memory available: ~9GB (3.3GB used by Windows)
- CUDA libraries: Present in /usr/lib/wsl/lib/

### Outcome
WSL2 environment is ready for Ollama installation.

---

## Phase 2: Native Ollama Installation

**Started:** 2026-02-03 ~20:30
**Status:** ✅ Complete

### Step 2.1: Install Ollama
- Command: `curl -fsSL https://ollama.com/install.sh | sh`
- Ran interactively in WSL terminal (requires sudo)
- Version installed: 0.15.4
- GPU detected: NVIDIA GeForce RTX 3060
- Service: enabled and running

### Step 2.2: Pull Model
- Command: `ollama pull qwen2.5-coder:7b`
- Size: 4.7 GB
- Model ID: dae161e27b0e

### Step 2.3: Initial Test
- GPU allocation: 100% GPU ✅
- VRAM usage: 4.9 GB
- Generation speed: 67-69 tok/s (exceeds 40-60 target!)
- First load: ~41s (model loading into VRAM)
- Subsequent loads: ~78ms (model cached)

### Outcome
Ollama running with Qwen2.5-Coder-7B on GPU. Ready for Phase 3 configuration.

---

## Session End: 2026-02-03

**Status:** Paused at Phase 2 complete
**Next:** Phase 3 - Configuration & Optimization
**Handoff:** See `session-handoff-2026-02-03.md` for detailed context

### Summary of What Works
- ✅ WSL2 with GPU passthrough
- ✅ Ollama v0.15.4 running as systemd service
- ✅ Qwen2.5-Coder-7B loaded and tested
- ✅ 100% GPU allocation, 67 tok/s generation

### To Resume
1. Read `session-handoff-2026-02-03.md`
2. Confirm with user
3. Begin Phase 3.1 (directory structure)

---

## 2026-02-06 - Session 3: Phase 3 Configuration, Phase 4 Docker, Phase 5 Verification

### Context
Resumed from Phase 2 complete. This session covered three full phases across two context windows (compacted mid-Phase 4).

### Phase 3: Configuration & Optimization ✅
- **3.1** Created directory structure: `modelfiles/`, `scripts/`, `docker/`, `docs/`
- **3.2** Built `modelfiles/coding-assistant.Modelfile` incrementally (7 settings)
  - Created sampling visualization (`docs/sampling-temperature-top-p.png`)
  - Created educational docs (`docs/sampling-parameters.md`, `docs/modelfile-reference.md`)
- **3.3** Created custom model `my-coder` via `ollama create`
  - Gotcha: Git Bash path mangling required `wsl -- bash -c` pattern
- **3.4** Configured systemd override (OLLAMA_HOST, CORS, Flash Attention, Keep Alive)
- **3.5** Created `scripts/setup-ollama.sh` (idempotent setup script)

### Phase 4: Docker Portable Setup ✅
- **4.1** Installed Docker CE 29.2.1 + Compose 5.0.2 + NVIDIA Container Toolkit
  - User ran sudo commands manually in WSL terminal
  - GPU verified inside Docker container via `docker run --gpus all ubuntu nvidia-smi`
- **4.2** Built `docker/docker-compose.yml` incrementally (4 steps)
  - GPU reservation, named volume, healthcheck, env parity with native
- **4.3** Created `docker/init-docker.sh` (self-starting, timeout guard, idempotent)
- **4.4** End-to-end Docker test: 64.26 tok/s, 100% GPU
  - ANSI escape codes in CLI output — used API (`stream: false`) for clean output
- **4.5** Model quality comparison: Qwen 7B vs Claude Opus on same prompt
  - User requested sub-agent comparison with same persona
  - Saved to `docs/model-comparison-hello-world.md`
  - Created gap analysis report: `docs/closing-the-gap.md` (7 categories, 14 techniques)

### Phase 5: Verification & Testing ✅
- **5.1** Service verification: active, enabled, override loaded, all env vars confirmed
- **5.2** Model verification: both models present, 100% GPU, 16K context
- **5.3** Performance: 63.1-63.3 tok/s sustained (1191 tokens LRU cache benchmark)
- **5.4** API: `/`, `/api/tags`, `/api/generate`, `/api/chat` — all pass
- **5.5** Created `scripts/verify-installation.sh` — 14/14 PASS, 0 FAIL, 0 WARN

### Decisions Made
- Docker Engine (not Docker Desktop) — free, lighter, more portable
- Test output via API not CLI — avoids ANSI escape code garbling
- Port conflict strategy: stop one service before starting the other

### Gotchas Added
6. `ollama run --verbose` through WSL pipes emits raw ANSI escape codes — use API
7. Docker + native Ollama conflict on port 11434 — stop one first

### Phase 6: Documentation & Artifacts ✅
- **6.1** Updated CLAUDE.md: directory tree (added docs/), actual perf numbers, constraints, project status table
- **6.2** Verified directory structure: 19/19 core files match, all paths correct

### Outcome
All 6 phases complete. All 7 success criteria met.

### Planning Discussion (post-Phase 6)
User initiated next-steps discussion covering four directions:
1. **OpenClaw** — autonomous agent framework, useful for non-coding (Telegram, chat), needs security project
2. **Closing the gap** — techniques from `docs/closing-the-gap.md`, mix of principles (ongoing) and tasks (build once)
3. **AirLLM** — runs 70B models on 4GB via layer decomposition. Assessment: too slow for interactive use (~0.5-2 tok/s), useful only for offline quality benchmarking. Last commit Aug 2024, maintenance uncertain. Not a priority.
4. **Personas & agents** — user's richest idea. Conversational persona creation, codebase-aware agent recruitment, multi-agent collaboration, PT-BR translator pattern, memory/learning, idle-time self-improvement

Key refinements from user:
- **Routing is three patterns, not one:** (A) local-first escalate up, (B) frontier delegates down to local via MCP, (C) chat interface routes both ways
- **MCP server** for Ollama is highest-value routing implementation — enhances ClaudeCode directly
- **Multiple models** needed: not just best coder, but right model per role (14B for reasoning, 3-4B for classification, separate for writing/translation)
- **Closing-the-gap techniques** are both principles (applied everywhere) and tasks (built once, reused)
- **OpenClaw** deferred until security planning is done; expense classifier can work without it first

Documents created:
- `docs/vision-and-intent.md` — goals, 8 design principles, 5 use cases, risks
- `.claude/plan-v2.md` — 10 layers, 70+ tasks, dependency graph, CTG integration
- `docs/model-strategy.md` — multi-model inventory, VRAM budgets, persona-to-model mapping

---

## 2026-02-02/03 - Session 1: Initial Verification (Phase 0)

### Summary
Ran Phase 0 verification checks. Identified blocker preventing WSL2 conversion.

### Blocker Found
- **Symptom:** `wsl --set-version Ubuntu-22.04 2` failed with `HCS_E_HYPERV_NOT_INSTALLED`
- **Root cause:** `bcdedit` showed `hypervisorlaunchtype Off`
- **Resolution:** `bcdedit /set hypervisorlaunchtype auto` + restart

### Verification Results
- GPU: RTX 3060 12GB, driver 591.74 ✅
- VT-x: Enabled in BIOS ✅
- WSL: Version 2.6.3.0 ✅
- Ubuntu-22.04: Installed (was WSL1, needed conversion)
- Disk: I: drive designated for LLM storage (562GB free)

### Artifacts Created
- `verification-report.md` - detailed findings
- `.claude/progress.md` - troubleshooting log (now `wsl2-setup-history.md`)
