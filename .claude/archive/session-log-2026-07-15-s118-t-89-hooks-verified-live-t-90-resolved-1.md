## 2026-07-15 - Session 118: T-89 hooks verified live + T-90 resolved (14B/32K offload is Windows-desktop VRAM contention, not KV-quant drift) + gpu-vram-windows helper

### Context

Session opened on "discuss next steps" (ref-lookup `--paths` + `resume.sh`). User picked the two quick items from session 117's Next: verify the T-89 hooks fire, and diagnose T-90 (the KV-quant/offload anomaly).

### What Was Done

- Verified T-89 hooks (session 117's #1 Next item): both wired in `.claude/settings.json` (SessionStart → `oficina-runs-scan.py`; PostToolUse `mcp__ollama-bridge__submit_run` → `oficina-watch-hook.py`); hermetic suite 11/11; the SessionStart scan fires and correctly stays silent on already-marked runs (the cozempic sibling in the same array proves the array executes). Verified done — no change needed.
- Resolved T-90: reproduced the 15 GB / 42%-58% CPU-GPU split at 32K, but the runner load log proves KV quant `q8_0` + Flash Attention are ACTIVE (KV cache 3.26 GB; f16 would be 6.5). Root cause = VRAM contention: the RTX 3060 also drives the Windows desktop, leaving only ~9 GB free (NVIDIA overlay/nvcontainer ~1 GB, Chrome ~0.8 GB, dwm ~0.6 GB). Not a config regression — no fix needed.
- Found what holds host VRAM via `nvidia-smi.exe` + PowerShell `GPU Process Memory` perf counters (Linux `nvidia-smi` can't attribute host VRAM under WDDM — shows `[Not Found]`).
- Built + tested `~/workspaces/scripts/gpu-vram-windows.sh` (machine-local): names each PID, sums over engines, drops the pid-0 shared pool, prints reclaim tips.
- Wrote finding `docs/findings/kv-quant-vram-contention-2026-07-15.md` (`ref:kv-quant-vram-contention`) incl. the NVIDIA-overlay service CLI-control note (`Stop-Service NvContainerLocalSystem`, elevated; do NOT touch `NVDisplay.ContainerLocalSystem`); corrected CLAUDE.md's 32K fact to host-VRAM-dependent; indexed finding + helper. Commit `1622b9f`.
- Split the still-unexplained sync-truncation asymmetry into new task **T-91**. (T-90 checkoff + T-91 append were both materialized directly in `tasks.md` this session, so neither is in this payload.)

### Decisions Made

- T-90's "KV-quant drift" hypothesis disproven — closed as resolved, not fixed. The durable correction was the CLAUDE.md assumption (32K "always fits" held only on a near-empty card), not any config change.
- The sync-truncation asymmetry is NOT explained by offload (offload slows generation, it does not truncate) → spun out as T-91 rather than folded under a "solved" T-90.

### Next

- oficina P2 / first-client + the **G-D4** gate-vs-P2 priority decision (unchanged from 116). T-90 showed *contention*, not *thrash*, so the gate's "observed thrash" trigger is NOT yet met — mild evidence for gate-after-P2.
- **T-86** oficina distribution runbook (incl. (d): re-adding the two T-89 hook entries on fresh clones — settings.json is gitignored).
- **T-91** when convenient: diff the request options the sync `generate_code` sends vs the oficina worker's `_default_generate` — check for a `num_predict` cap on the sync path.

### Gotchas

- `powershell.exe -Command -` executes a single stdin line but silently drops a multi-line heredoc — stage a `.ps1` and use `-File "$(wslpath -w …)"`.
- PowerShell `'{0:N0}'` formats with the pt-BR locale (`.` as thousands separator) — the source of the "1.039 MB" confusion; emit a plain `[int]` and format in awk.
- Linux `nvidia-smi` inside WSL2 shows host GPU processes as `[Not Found]`/`[N/A]` (WDDM) — use `nvidia-smi.exe` + the PowerShell `GPU Process Memory` counter for per-process VRAM.
- ~2.8–3 GB VRAM is held by the Windows desktop even idle; the `dwm` compositor (~0.6–0.9 GB) is irreducible, so ~11 GB free is the practical ceiling on this box.
