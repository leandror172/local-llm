<!-- ref:kv-quant-vram-contention -->
# T-90 resolved — the "KV quant inactive" anomaly is VRAM contention, not a config regression

**Date:** 2026-07-15 (session 118)
**Trigger:** Session 117 observed `my-python-q25c14` loading at 15.2 GB total / 8.8 GB VRAM
(≈6 GB spilled to CPU RAM → 2× sync timeouts) and hypothesized that
`OLLAMA_KV_CACHE_TYPE=q8_0` had drifted inactive (an f16-KV-sized footprint).

## Verdict: hypothesis disproven

KV quantization is **active and correct**. Flash Attention is **enabled**. The systemd
override is **applied to the running unit**. The CPU offload is caused by **insufficient
free VRAM at load time** — the RTX 3060 12 GB also drives the Windows desktop, and ~2.8–3 GB
was already held by host processes before Ollama loaded a byte.

## Evidence

Running-service env (`systemctl show ollama.service -p Environment`) — both live:
`OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`.

Runner load line (`journalctl -u ollama`) for `my-python-q25c14` at `num_ctx=32768`:

```
load request="{... FlashAttention:Enabled KvSize:32768 KvCacheType:q8_0 ...}"
using device CUDA0 (RTX 3060) - 9199 MiB free      <-- only ~9 GB free of 12 GB
offloaded 23/49 layers to GPU                       <-- 26 layers spilled to CPU
llama_context: flash_attn = enabled
llama_kv_cache: size = 3264.00 MiB (32768 cells, 48 layers), K (q8_0): 1632, V (q8_0): 1632
```

A q8_0 KV cache at 32K is **3.26 GB**; an f16 cache would be **~6.5 GB**. The measured 3.26 GB
proves quantization is working. `ollama ps` confirmed the symptom: `15 GB, 42%/58% CPU/GPU`.

NVML at load reported `free: 9646632960` (9.0 GiB) of `total: 12884901888` (12.0 GiB) →
**~3 GB held by the host before load.** With the model unloaded, `nvidia-smi.exe` idle baseline
was **2,863 MiB used / 9,251 free** — the same ~3 GB, independently.

## Why the 2026-05-30 probe said "fits at 32K"

That probe (`retrieval/probes/ctx-probe-2026-05-30.md`) measured qwen2.5-coder:14b at 32K
leaving 2,790 MiB free — but on a near-empty card (~12 GB available). This model's full 32K
footprint (~7.7 GB weights + 3.26 GB q8_0 KV + ~1 GB compute ≈ 12 GB) needs essentially the
**whole** card. On WSL2-over-desktop, available VRAM fluctuates with what Windows is doing;
~9 GB free is the realistic working figure, not 12 GB. **The "14B fits 32K" fact is
host-VRAM-dependent, not absolute.**

## What is using the VRAM (WDDM caveat)

Linux `nvidia-smi` inside WSL2 **cannot** attribute per-process VRAM for host apps (shows
`[Not Found]`). Use the Windows binary + perf counters:

```bash
# per-process dedicated VRAM, named
nvidia-smi.exe --query-compute-apps=pid,used_memory,process_name --format=csv   # names (used_memory N/A under WDDM)
powershell.exe -NoProfile -Command "(Get-Counter '\GPU Process Memory(*)\Dedicated Usage').CounterSamples | ? {\$_.CookedValue -gt 30MB} | sort CookedValue -Desc | %% { '{0,8:N0} MB  {1}' -f (\$_.CookedValue/1MB), \$_.InstanceName }"
```

**Helper:** `~/workspaces/scripts/gpu-vram-windows.sh` wraps both queries — names each PID,
sums over engines, drops the pid-0 shared pool, and prints reclaim tips. Run it any time the
14B offloads unexpectedly.

Idle baseline 2026-07-15 (instance name `pid_<PID>_luid_..._phys_0`, mapped via the CSV):

| VRAM | Process | Closable? |
|---|---|---|
| ~1,039 MB | `nvcontainer.exe` (NVIDIA app / overlay / ShadowPlay) | yes — disable overlay/instant-replay |
| 775 MB | Chrome | yes |
| 641 MB | `dwm.exe` (desktop compositor, permission-blocked name) | no — structural floor |
| 135/93/86/70/67 MB | Windows Terminal / VS Code / GitKraken / explorer / Claude desktop | mostly |

Killing nvcontainer + Chrome reclaims ~1.8 GB — enough to fit 32K fully on-GPU.
(`dwm` shows as `[Insufficient Permissions]` under `nvidia-smi.exe` but resolves via the
PowerShell counter — it's the desktop compositor, ~0.6–0.9 GB, structural.)

### CLI control of the NVIDIA overlay (the ~1 GB lever)

No supported NVIDIA CLI toggles the overlay/ShadowPlay *feature flags* (GUI/registry only).
But the hosting Windows service is CLI-controllable — **requires Administrator elevation**
(a `powershell.exe` call from WSL runs unelevated and will fail; run these in an elevated
Windows shell):

```powershell
Stop-Service NvContainerLocalSystem                     # free ~1 GB now (restarts on reboot)
Set-Service  NvContainerLocalSystem -StartupType Disabled  # persist across reboots
# reverse:
Set-Service  NvContainerLocalSystem -StartupType Automatic; Start-Service NvContainerLocalSystem
```

`NvContainerLocalSystem` = NVIDIA app container (overlay/ShadowPlay) — safe to stop.
**`NVDisplay.ContainerLocalSystem` = the display driver container — do NOT stop it.**
Surgical GUI alternative: NVIDIA app → Settings → Features → Overlay OFF (persists, keeps the
service running).

## Levers (in order of ROI)

1. **Route long/32K local work through `submit_run` (async).** Offload just makes it slower;
   async is where slow tok/s is fine (this is exactly the T-89 routing convention). No env change.
2. **Disable the NVIDIA app overlay / ShadowPlay** — reclaims ~1 GB persistently.
3. **Drop interactive `num_ctx` to 16–24K** for `my-*-q25c14` when a full-GPU fit matters more
   than context length.
4. Close Chrome before heavy interactive local runs.

## NOT explained by this finding

The sync-truncation asymmetry (sync `generate_code` hit EOS mid-code at eval 490/755 twice,
while `submit_run` produced complete files) is **separate** — offload slows generation, it does
not truncate it. Tracked independently (see tasks.md, split out of T-90).
<!-- /ref:kv-quant-vram-contention -->
