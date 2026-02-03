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
- **Phase 1:** 🔜 Next (WSL2 environment setup)
- **Last checkpoint:** 2026-02-03 - Ready to begin Phase 1

---

## Quick Resume Checklist

When starting a new session:
1. Read this file (`session-context.md`)
2. Check `tasks.md` for current progress
3. Check `session-log.md` for recent decisions/context
4. Review `plan.md` for the current phase details
5. Ask user: "Ready to continue from [current task]?"

---

## Pending Decisions (for Phase 1)

These were discussed but not finalized - ask user before proceeding:

1. **CUDA Toolkit (Phase 1.2):** Skip or install?
   - Install if: User wants to develop CUDA code, or use tools requiring nvcc
   - Skip if: Just running Ollama (works fine with Windows driver's libcuda)

2. **Docker phase (Phase 4):** Do now or defer?
   - Recommendation: Complete Phases 1-3 first (native install), then add Docker as portable option
