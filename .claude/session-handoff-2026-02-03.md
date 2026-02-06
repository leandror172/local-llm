# Session Handoff - 2026-02-03

**Session Duration:** ~1.5 hours
**Phases Completed:** 0, 1, 2
**Next Phase:** 3 (Configuration & Optimization)

---

## Executive Summary

Successfully installed and verified a local LLM (Ollama + Qwen2.5-Coder-7B) on Windows with WSL2 GPU passthrough. The setup exceeds performance expectations (67 tok/s vs 40-60 target). Ready for Phase 3 configuration.

---

## What Was Accomplished

### Phase 0: Verification (completed in previous session)
- Identified WSL2 conversion blocker: `hypervisorlaunchtype=Off`
- Fixed with `bcdedit /set hypervisorlaunchtype auto` + restart
- GPU passthrough verified working

### Phase 1: WSL2 Environment Setup
- **systemd**: Already enabled by default in WSL 2.6.3 (no action needed)
- **CUDA Toolkit**: Skipped (not needed for Ollama - it bundles its own runtime)
- **GPU verification**: RTX 3060 visible, 12GB VRAM, driver 591.74

### Phase 2: Native Ollama Installation
- **Ollama installed**: v0.15.4 via official install script
- **Model pulled**: qwen2.5-coder:7b (4.7 GB, ID: dae161e27b0e)
- **Performance verified**:
  - 100% GPU allocation
  - 67-69 tokens/second generation
  - First load: ~41s (model → VRAM)
  - Subsequent loads: ~78ms (cached)

---

## Technical Details Discovered

### Hardware Configuration
- **GPU**: NVIDIA GeForce RTX 3060 (12288 MiB / 12 GB)
- **Driver**: 591.74 (Windows) / 590.52.01 (WSL SMI interface)
- **CUDA**: 13.1 (maximum supported by driver)
- **Compute capability**: 8.6 (Ampere architecture)
- **Available VRAM**: ~8.6 GB (after Windows desktop usage)

### WSL2 Configuration
- **WSL Version**: 2.6.3.0
- **Kernel**: 6.6.87.2-1
- **Distro**: Ubuntu-22.04 (WSL2)
- **systemd**: Enabled by default (PID 1 = systemd)
- **CUDA libraries**: `/usr/lib/wsl/lib/libcuda.so*` (from Windows driver passthrough)

### Ollama Configuration (current defaults)
- **Binary**: `/usr/local/bin/ollama`
- **Service**: `/etc/systemd/system/ollama.service`
- **User**: `ollama` (dedicated system user)
- **Port**: 127.0.0.1:11434 (localhost only by default)
- **Model cache**: `~/.ollama/models/` (default location)
- **Keep alive**: 5 minutes (default - model unloads after inactivity)

### Performance Benchmarks
| Metric | Value | Notes |
|--------|-------|-------|
| Generation speed | 67-69 tok/s | Exceeds 40-60 target |
| First load time | ~41s | Model loading into VRAM |
| Warm load time | ~78ms | Model already in VRAM |
| VRAM usage | 4.9 GB | With 4K context window |
| Prompt eval | 4-7 tok/s | Lower when run via pipe (normal) |

---

## User Preferences Observed

### Interaction Style
- Prefers detailed explanations ("like a practical tutorial")
- Wants to understand "why" not just "how"
- Appreciates tables and structured information
- Likes insights about interesting technical details

### Workflow
- Step-by-step, never auto-proceed to next phase
- Wants configuration files built incrementally (not dumped whole)
- Prefers to run interactive commands (sudo, password) in WSL terminal directly
- Appreciates being given commands to copy-paste when needed

### Technical Background
- Backend-focused software engineer
- Interested in AI/ML
- Looking for employment (README is portfolio piece)
- Comfortable with Linux, Docker, systemd concepts but wants explanations

### Output Style
- Using "Explanatory" mode
- 80% technical/professional, 20% approachable
- Wants Insight boxes for interesting technical details

---

## Files Created/Modified This Session

### New Files
| File | Purpose |
|------|---------|
| `.gitignore` | Excludes `.claude/local/`, `settings.local.json` |
| `.claude/local/hardware-inventory.md` | Sensitive hardware specs (gitignored) |
| `.claude/session-context.md` | Agent handoff instructions, user preferences |
| `.claude/tasks.md` | Progress checklist |
| `.claude/session-log.md` | Detailed session history |
| `.claude/session-handoff-2026-02-03.md` | This file |
| `README.md` | Professional project documentation (portfolio piece) |

### Modified Files
| File | Changes |
|------|---------|
| `CLAUDE.md` | Added session tracking docs, fixed output style |
| `verification-report.md` | Marked Phase 0 complete |
| `.claude/progress.md` → `.claude/wsl2-setup-history.md` | Renamed as historical archive |

---

## What's Next (Phase 3)

### Overview
Phase 3: Configuration & Optimization - Create configuration files and custom model

### Tasks
1. **3.1 Create project directory structure**
   ```
   ~/llm-config/{modelfiles,scripts,docker}
   ```
   Or use the repo structure directly on I: drive

2. **3.2 Create Modelfile for coding assistant**
   - File: `modelfiles/coding-assistant.Modelfile`
   - Base: qwen2.5-coder:7b
   - Parameters: num_ctx, temperature, top_p, etc.
   - System prompt for Java/Go backend development

3. **3.3 Create custom model**
   ```bash
   ollama create my-coder -f modelfiles/coding-assistant.Modelfile
   ```

4. **3.4 Configure Ollama service**
   - Create systemd override: `/etc/systemd/system/ollama.service.d/override.conf`
   - Environment variables:
     - `OLLAMA_HOST=0.0.0.0:11434` (listen on all interfaces)
     - `OLLAMA_FLASH_ATTENTION=1` (save ~30% VRAM)
     - `OLLAMA_KEEP_ALIVE=30m` (keep model loaded longer)
     - `OLLAMA_ORIGINS=*` (allow CORS for web clients)

5. **3.5 Create setup script**
   - File: `scripts/setup-ollama.sh`
   - Idempotent (can run multiple times safely)

### User Decisions Pending
- Where to store Modelfiles: WSL home dir vs I: drive (repo)?
- Custom model name: `my-coder` (from plan) or different?
- System prompt: Java/Go focus as planned, or adjust?

---

## Known Issues / Gotchas

1. **Interactive commands fail via Claude Code**
   - Commands requiring sudo password must be run in WSL terminal
   - Solution: Give user command to copy-paste

2. **First model load is slow**
   - ~41 seconds to load model into VRAM
   - Normal behavior, subsequent loads are fast

3. **"Low VRAM mode" message**
   - Ollama logs "entering low vram mode" for <20GB
   - Not a problem - just conservative memory allocation

4. **Terminal escape codes in output**
   - Ollama's spinner shows as `[?25l[1G⠙` etc.
   - Harmless, just terminal control sequences

5. **Prompt eval slower via pipe**
   - Running `echo "..." | ollama run` shows lower prompt eval rates
   - Interactive/API usage is faster

---

## Commands for Quick Verification

```bash
# Check Ollama service
wsl -d Ubuntu-22.04 -e systemctl status ollama

# Check GPU allocation
wsl -d Ubuntu-22.04 -e ollama ps

# List models
wsl -d Ubuntu-22.04 -e ollama list

# Quick test
wsl -d Ubuntu-22.04 -e ollama run qwen2.5-coder:7b "Hello"

# Check GPU in WSL
wsl -d Ubuntu-22.04 -e nvidia-smi
```

---

## Session Resume Instructions

When resuming:
1. Read this handoff file first
2. Check `tasks.md` for current progress
3. Confirm with user: "Ready to continue with Phase 3?"
4. User said: Proceed only after they confirm
5. Remember: Build config files incrementally with explanations

---

*Handoff created: 2026-02-03*
*Next session should start with Phase 3.1*
