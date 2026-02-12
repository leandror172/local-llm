# Phases 0-6 Completion Archive

**Archived from:** `.claude/tasks.md` and `.claude/session-context.md` (2026-02-11)
**Status:** All phases complete
**Index:** See `.claude/index.md` for topic-to-file map

---

## Phase 0: Verification (Complete)
- Hardware verification (GPU, RAM, disk)
- WSL2 verification (version, distro)
- GPU visibility in WSL2 (nvidia-smi)
- Existing software check
- Created verification report

**Blocker resolved:** `hypervisorlaunchtype=Off` → fixed with `bcdedit /set hypervisorlaunchtype auto`

## Phase 1: WSL2 Environment Setup (Complete)
- systemd already enabled by default in WSL 2.6.3
- CUDA Toolkit skipped — not needed for Ollama
- GPU verified: RTX 3060 12GB, driver 591.74, CUDA 13.1

## Phase 2: Native Ollama Installation (Complete)
- Ollama v0.15.4 installed, GPU detected, service running
- Qwen2.5-Coder-7B pulled (4.7 GB, ID: dae161e27b0e)
- Initial test: 100% GPU, 67 tok/s (exceeds 40-60 target)

## Phase 3: Configuration & Optimization (Complete)
- Project directory structure created (modelfiles/, scripts/, docker/, docs/)
- Modelfile created: temp 0.3, 16K ctx, Java/Go system prompt
- Custom model `my-coder` registered (shares base weights)
- systemd override: host, CORS, flash attn, keep alive
- Setup script: `scripts/setup-ollama.sh` (idempotent)

**Decisions:**
- Config storage: I: drive repo (version-controlled, portable)
- Custom model name: `my-coder`
- System prompt focus: Java/Go backend — more personas planned later (frontend, architect, etc.)
- User understands the multi-Modelfile pattern for creating additional personas
- Build Modelfiles incrementally, explain each setting
- CUDA Toolkit skipped (Phase 1) — not needed for Ollama

## Phase 4: Docker Portable Setup (Complete)
- Docker CE 29.2.1, Compose 5.0.2, NVIDIA Container Toolkit
- docker-compose.yml: GPU reservation, healthcheck, named volume
- docker/init-docker.sh: starts container, waits for API, pulls model
- Docker GPU test: 64.26 tok/s, 100% GPU in container
- Model quality comparison: Qwen 7B vs Claude Opus

## Phase 5: Verification & Testing (Complete)
- Service verification: active, enabled, override loaded, Flash Attention on
- Model verification: both models present, 100% GPU, 16K context, 30m keep-alive
- Performance: 63.1-63.3 tok/s (exceeds 40-60 target)
- API verification: root, /api/tags, /api/generate, /api/chat — all pass
- Created `scripts/verify-installation.sh` — 14/14 pass

## Phase 6: Documentation & Artifacts (Complete)
- CLAUDE.md updated with actual perf numbers, constraints, project status
- Final directory structure verified (19/19 core files)

---

## Success Criteria (All Met)
- `nvidia-smi` shows RTX 3060 in WSL2 (12288 MiB, driver 591.74)
- `ollama ps` shows "100% GPU"
- Generation speed 63-67 tok/s (target was 40-60)
- API responds at `http://localhost:11434`
- Custom model `my-coder` working
- Docker setup runs independently (64 tok/s)
- All artifacts version-controlled and portable (19 core files)

---

## Artifacts Created

### Phase 3
| File | Purpose |
|------|---------|
| `modelfiles/coding-assistant.Modelfile` | Custom model config: temp 0.3, 16K ctx, Java/Go system prompt |
| `scripts/setup-ollama.sh` | Idempotent setup script (install + configure + pull + create) |
| `docs/modelfile-reference.md` | Configuration rationale for all Modelfile settings |
| `docs/sampling-parameters.md` | Educational: temperature & top-p explained |
| `docs/sampling-temperature-top-p.png` | Visual chart of sampling distributions |

### Phase 4
| File | Purpose |
|------|---------|
| `docker/docker-compose.yml` | GPU-enabled Ollama: ports, volumes, env, healthcheck, NVIDIA reservation |
| `docker/init-docker.sh` | Idempotent: starts container, waits for API, pulls model, creates my-coder |
| `docs/model-comparison-hello-world.md` | Side-by-side: Qwen 7B vs Claude Opus on same prompt |
| `docs/closing-the-gap.md` | 7 techniques to minimize quality gap, priority matrix, sources |

### Phase 5
| File | Purpose |
|------|---------|
| `scripts/verify-installation.sh` | 14-check verification: GPU, service, models, API, benchmark |

---

## Useful Commands

### Verification
```bash
# Automated (recommended)
./scripts/verify-installation.sh    # 14 checks: GPU, service, models, API, benchmark

# Manual spot checks
nvidia-smi                          # GPU visible? Need driver 545+
ollama ps                           # Shows "100% GPU"? Good
curl -s http://localhost:11434/     # "Ollama is running"

# Performance check (use API, not CLI, for clean output)
curl -s http://localhost:11434/api/chat -d '{
  "model": "my-coder",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": false
}' | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{d[\"eval_count\"]/d[\"eval_duration\"]*1e9:.1f} tok/s')"
```

### Git Worktrees for Parallel Work
When multiple agents or tasks need to work on different branches simultaneously, use `git worktree` instead of switching branches:
```bash
git worktree add ../llm-feature-branch feature-branch
git worktree add ../llm-experiment experiment-branch
```
Each worktree is an isolated checkout sharing the same `.git` object store. Prefer worktrees over branch switching when doing parallel agent work, evaluation comparisons, or any workflow where multiple branches need to be checked out at once.

---

## Technical Learnings

### What Works
- WSL 2.6.3 has systemd enabled by default (no wsl.conf needed)
- CUDA Toolkit not needed for Ollama (it bundles its own runtime)
- GPU passthrough uses `/usr/lib/wsl/lib/libcuda.so` from Windows driver
- Claude Code runs from WSL2 natively (Node.js via nvm, npm global install)

### Performance Achieved
- Generation: 67-69 tok/s native (exceeds 40-60 target)
- First load: ~41s (model → VRAM)
- Warm load: ~78ms (cached in VRAM)
- VRAM usage: 4.9 GB for 7B model
- Docker: 64.26 tok/s (near-identical to native)

### Gotchas Discovered
1. sudo must be run in WSL terminal directly (Claude Code can't handle password prompts)
2. Ollama's "low vram mode" message is informational, not an error
3. Terminal escape codes appear in piped output (harmless)
4. Git Bash mangles Linux paths — use `wsl -- bash -c "..."` to avoid
5. `ollama create` can't read Modelfiles from `/mnt/` directly
6. `ollama run --verbose` emits raw ANSI escape codes — use API for clean output
7. Docker + native Ollama conflict on port 11434 — stop one before starting the other
8. Puppeteer's bundled Chromium needs ~12 system libs in WSL2
9. Always invoke benchmark Python scripts via bash wrappers
10. Go 1.16+ requires `go mod init` before `go build`
