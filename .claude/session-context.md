# Session Context for Future Agents

**Purpose:** This file preserves user preferences and working context across Claude Code sessions. Read this first when resuming work on this project.

---

## User Preferences

### Interaction Style
- **Output style:** Explanatory (educational insights with task completion)
- **Pacing:** Interactive, wizard-style - pause after each phase for user input
- **Explanations:** Explain the "why" for each step, like a practical tutorial

### Configuration Files
- **Build incrementally:** Never dump full config files at once
- **Explain each setting:** Add a setting, explain what it does, then add the next
- **Ask before proceeding:** Give user options before making non-obvious choices

### Workflow Rules (from CLAUDE.md)
1. **DO NOT proceed to next phase automatically** - wait for explicit user permission
2. **Step-by-step configuration** - build files incrementally with explanations
3. **Learning mode preferred** - explain each step as a teaching moment

---

## File Management

### Sensitive Data
- **Location:** `.claude/local/` (gitignored)
- **Hardware details:** `.claude/local/hardware-inventory.md`
- **Rule:** Detailed system specs, paths, or personal info → write to `local/`
- **References:** Tracked files can reference local files (e.g., "see `.claude/local/hardware-inventory.md` for specs")

### Log Rotation Policy
When log files grow large or a phase completes:

**Option A: By Phase (Recommended)**
1. When completing a phase, rename current log with phase identifier:
   - `session-log.md` → `session-log-phase1-wsl2-setup.md`
2. Create fresh `session-log.md` for next phase
3. Keep most recent 3-5 phase logs; archive older ones to `local/archive/`

**Option B: By Size**
1. When `session-log.md` exceeds ~500 lines, rotate:
   - `session-log.md` → `session-log-001.md`
   - Create fresh `session-log.md`
2. Number increments: 001, 002, 003...

**Current approach:** By Phase (user preferred logical grouping)

---

## Project Context

### Objective
Install and configure a local LLM on Windows with WSL2:
- **Inference engine:** Ollama
- **Model:** Qwen2.5-Coder-7B (Q4_K_M quantization)
- **Custom model:** `my-coder` (optimized for Java/Go backend development)
- **Hardware:** RTX 3060 12GB
- **Storage:** I: drive designated for LLM models

### Key Files
| File | Purpose |
|------|---------|
| `.claude/plan.md` | Master plan with all phases |
| `.claude/tasks.md` | Simple progress checklist |
| `.claude/session-log.md` | Current session's detailed history |
| `.claude/local/hardware-inventory.md` | Sensitive hardware details |
| `verification-report.md` | Phase 0 findings (sanitized) |

### Current Status
- **Phase 0:** ✅ Complete (WSL2 + GPU passthrough verified)
- **Phase 1:** ✅ Complete (systemd ready, GPU verified)
- **Phase 2:** ✅ Complete (Ollama installed, model pulled, 67 tok/s verified)
- **Phase 3:** ✅ Complete (Modelfile, my-coder model, systemd override, setup script)
- **Phase 4:** ✅ Complete (Docker CE + NVIDIA Container Toolkit, Compose, init script, tested at 64 tok/s)
- **Phase 5:** ✅ Complete (14/14 checks pass, verify-installation.sh created)
- **Phase 6:** ✅ Complete (CLAUDE.md updated, directory structure verified)
- **Last checkpoint:** 2026-02-06 - All phases complete

---

## Quick Resume Checklist

When starting a new session:
1. Read this file (`session-context.md`)
2. Check `tasks.md` for current progress
3. Check `session-log.md` for recent decisions/context
4. Review `plan.md` for the current phase details
5. Ask user: "Ready to continue from [current task]?"

---

## Decisions Made

### Phase 1 (resolved)
- **CUDA Toolkit:** Skipped — not needed for Ollama

### Phase 3 (resolved 2026-02-06)
- **Config storage:** I: drive repo (version-controlled, portable)
- **Custom model name:** `my-coder`
- **System prompt focus:** Java/Go backend — user wants to add more personas later (frontend, architect, etc.)
- **Additional personas:** User understands the multi-Modelfile pattern and plans to create more

---

## Technical Learnings (from this session)

### What Works
- WSL 2.6.3 has systemd enabled by default (no wsl.conf needed)
- CUDA Toolkit not needed for Ollama (it bundles its own runtime)
- GPU passthrough uses `/usr/lib/wsl/lib/libcuda.so` from Windows driver

### Performance Achieved
- Generation: 67-69 tok/s (exceeds 40-60 target)
- First load: ~41s (model → VRAM)
- Warm load: ~78ms (cached in VRAM)
- VRAM usage: 4.9 GB for 7B model

### Gotchas Discovered
1. Commands requiring sudo must be run in WSL terminal directly (Claude Code can't handle password prompts)
2. Ollama's "low vram mode" message is informational, not an error
3. Terminal escape codes appear in piped output (harmless)
4. Git Bash mangles Linux paths (e.g., `/mnt/i/` → `C:/Program Files/Git/mnt/i/`) — use `wsl -- bash -c "..."` to avoid this
5. `ollama create` can't read Modelfiles from `/mnt/` directly — copy to WSL home first, or use `wsl -- bash -c` with native paths
6. `ollama run --verbose` through `wsl` pipes emits raw ANSI escape codes — use the API (`/api/chat` with `stream: false`) for clean programmatic output
7. Docker + native Ollama conflict on port 11434 — stop one before starting the other

---

### Performance (Docker)
- Generation: 64.26 tok/s (near-identical to native)
- GPU allocation: 100% GPU
- VRAM: 6.3 GB (weights + 16K context)

---

## Session Handoff Files

For detailed context on any session, check the handoff files:
- `session-handoff-2026-02-03.md` - Phase 0-2 completion, ready for Phase 3
- `session-handoff-2026-02-06.md` - Phase 3-5 completion, ready for Phase 6

## Artifacts Created (Phase 3, 2026-02-06)

| File | Purpose |
|------|---------|
| `modelfiles/coding-assistant.Modelfile` | Custom model config: temp 0.3, 16K ctx, Java/Go system prompt |
| `scripts/setup-ollama.sh` | Idempotent setup script (install + configure + pull + create) |
| `docs/modelfile-reference.md` | Configuration rationale for all Modelfile settings |
| `docs/sampling-parameters.md` | Educational: temperature & top-p explained |
| `docs/sampling-temperature-top-p.png` | Visual chart of sampling distributions |

## Artifacts Created (Phase 4, 2026-02-06)

| File | Purpose |
|------|---------|
| `docker/docker-compose.yml` | GPU-enabled Ollama: ports, volumes, env, healthcheck, NVIDIA reservation |
| `docker/init-docker.sh` | Idempotent: starts container, waits for API, pulls model, creates my-coder |
| `docker/test-output.json` | API test output from Docker run (clean JSON, no escape codes) |
| `docker/hello-world.go` | Extracted Go code from my-coder's Docker test |
| `docs/model-comparison-hello-world.md` | Side-by-side: Qwen 7B vs Claude Opus on same prompt |
| `docs/closing-the-gap.md` | 7 techniques to minimize quality gap, priority matrix, sources |

## Artifacts Created (Phase 5, 2026-02-06)

| File | Purpose |
|------|---------|
| `scripts/verify-installation.sh` | 14-check verification: GPU, service, models, API, benchmark (63.3 tok/s) |
| `docker/benchmark-output.json` | LRU cache benchmark output (1191 tokens, 63.14 tok/s) |
