# Session Log

**Current Layer:** LTG retrieval substrate — Phase 4 (graph + communities) next
**Current Session:** 2026-06-30 — Session 97: my-go-qcoder HTTP 500 root-cause (host-RAM ENOMEM) + ext4 store move (T-67)

---
## 2026-06-30 - Session 97: my-go-qcoder HTTP 500 root-cause (host-RAM ENOMEM) + ext4 store move (T-67)

### Context

Triggered by an expense-repo report that `my-go-qcoder` was returning HTTP 500 / unavailable. Investigated, root-caused, fixed, then executed the deferred ext4 store move (T-67) end-to-end. An infra side-track — no LTG/handoff-pipeline work.

### What Was Done

- Root-caused the recurring `my-go-qcoder` HTTP 500 as **host-RAM ENOMEM, NOT "VRAM contention"** (the label ~6 expense sessions had inherited): the 30B partial-offload reads ~10–15 GiB of weights into host RAM, which exceeded WSL2's old 15.5 GiB. Reproduced the exact crash (`cannot allocate memory` → `exit status 2` → 500).
- Applied the load-bearing fix: WSL `.wslconfig memory=24GB` (+16G swap); verified the 30B now loads (HTTP 200, 8.5 GiB RAM headroom).
- Researched + wrote the ext4-move plan with a full physical/logical drive map (`docs/plans/ollama-store-ext4-move.md`); found I: is on the same NVMe as C: (no disk-speed gain) and the distro ext4 is C:-backed (81 GB free) so only a dedicated vhdx on I: was viable.
- Executed T-67: created a 300 GB dynamic ext4 vhdx on I:, attached via `wsl --mount --vhd`, rsync'd the 162 GB store (byte-verified: 178 blobs / 81 manifests), repointed Ollama via systemd `.mount` (UUID) + `ExecStartPre` guard; cold load 33 s → 15.6 s.
- Built `make -C ~/workspaces ollama-store-check` (namespace-robust: systemd + API) to detect the silent-empty-store failure mode; registered the Option-A logon task for reboot persistence.
- Corrected the central premise everywhere it was committed (QUICK / KNOWLEDGE / plan / both repos' session-context): ext4 did NOT re-enable mmap, so the RAM win never materialized.

### Decisions Made

- **`.wslconfig memory=24GB` is the actual fix and stays load-bearing.** The ext4 move is a latency/robustness win only — Ollama forces `UseMmap:false` for any partially-offloaded model regardless of filesystem (`use_mmap:true` is ignored), so host-RAM cost is unchanged.
- Kept the ext4 move despite the corrected premise (faster cold loads + page-cache reuse + clean store, already done). Old `/mnt/i/ollama-models` retained as rollback until the reboot test passes.
- Chose Option A (logon task) for persistence over manual re-mount — the guard + checker already make any failure loud rather than silent.

### Next

- LTG Phase 4 — graph + communities (the standing next task; this was a side-track).
- T-68: `wsl --shutdown` + re-login, confirm `make ollama-store-check` PASS (proves the logon task re-attached the vhd), then reclaim the old 162 GB on I:.

### Gotchas

- Ollama disables mmap whenever a model is **partially** offloaded (some layers GPU, some CPU) — a loader rule independent of filesystem. My initial "9p disables mmap" diagnosis was only half right.
- WSL2-with-systemd puts the ext4 mount in PID 1's namespace; interactive/agent shells are in a different namespace and see `/mnt/ollama-store` as empty (`findmnt` shows nothing) even though ollama serves it fine. Health checks must query systemd + the API, not local-shell filesystem calls.
