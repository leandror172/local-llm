# Plan: Move Ollama model store to ext4 (T-67)

**Status:** EXECUTED session 98 (2026-06-30). Store live at `/mnt/ollama-store/models` (ext4).
**T-68 CLOSED (2026-07-01):** reboot-persistence made self-healing (Option A: udev
`SYSTEMD_WANTS` → `ollama-store-recover.service`; logon task thinned to attach-only) —
survived a real reboot cold `PASS` (device letter shifted sde→sdd, UUID matching held);
old `/mnt/i/ollama-models` reclaimed (162 GB → I: now 394 GB free). Artifacts +
verified runbook: `~/workspaces/ollama-infra/` (machine-local, moved out of the repo 2026-07-02).
**Author:** session 98 (2026-06-30).
**Trigger:** `my-go-qcoder` HTTP 500 root-caused as host-RAM ENOMEM (see `.memories/KNOWLEDGE.md` "Host-RAM budget").
**2026-07-09:** a `FAIL — serves only 0 models` from `ollama-store-check` turned out **not** to be a
store fault at all, but a canonical-port squatter. See § "Failure mode: canonical-port squatter".

## ⚠ OUTCOME — the central premise was partly wrong

The plan assumed **ext4 re-enables mmap → host-RAM cost drops to ~0**. It does NOT.
Measured after execution: Ollama keeps `UseMmap:false` on ext4 too, because it
disables mmap whenever a model is **partially offloaded** (GPU+CPU layer split) —
a loader rule independent of filesystem. The ~10–15 GiB host read remains; the
`.wslconfig memory=24GB` cap **stays load-bearing**. `use_mmap:true` in the API
request is ignored.

**What the move actually delivered:** cold load **33 s → 15.6 s** (10.2 s
cache-warm) from ext4 read speed + page-cache reuse, and a clean store with no 9p
quirks. A latency/robustness win, not a RAM fix. Kept because it's net-positive and
already done; old `/mnt/i/ollama-models` retained as rollback until a reboot test
passes. Execution artifacts + runbook: `~/workspaces/ollama-infra/` (machine-local, moved out of the repo 2026-07-02). Health check:
`make -C ~/workspaces ollama-store-check` (namespace-robust: systemd + API).

---

## Context — why this is even on the table

`my-go-qcoder` (qwen3-coder:30b, 18 GB blob, 19.3 GiB load footprint, ~29/49 layers
offloaded to CPU) was returning HTTP 500 on load. Root cause: the model store lives on
`/mnt/i` (a **9p** Windows mount), where Ollama cannot `mmap` blobs → it sets
`UseMmap:false` → it **reads the entire blob into host RAM** instead of paging from disk.
WSL2's old 15.5 GiB cap couldn't hold the ~12 GiB host-side read → `cannot allocate
memory` panic → runner `exit status 2` → 500.

**Already mitigated (session 98):** raised WSL `.wslconfig` to `memory=24GB`. The 30B now
loads (verified HTTP 200, 23 GiB RAM, 8.5 GiB headroom). **The OOM is fixed.** This plan is
about the *proper* fix — re-enabling mmap — which is an optimization, not a bug fix.

---

## Decisive facts (researched session 98)

| Fact | Value | Why it matters |
|------|-------|----------------|
| `I:` physical media | Partition on **Disk 4 = Crucial P5 Plus NVMe** (same SSD as `C:`) | Store is *already on fast NVMe*. The move buys **no disk-speed gain** — only removes the 9p tax. |
| Store size | **162 GB** (blobs); qcoder blob = 18 GB | Whatever we move, we move ~162 GB (content-addressed store can't be cheaply split). |
| Distro ext4 (`/dev/sdd`, `/`) | 1007 GB cap, **52 GB used, 904 GB free** | Plenty of *logical* room… |
| …but its vhdx backing file | `C:\Users\Leandro\…\ext4.vhdx`, **197.9 GB on disk** | …vhdx never auto-shrinks. |
| `C:` free space | **82 GB free** (90% full) | Growing the distro vhdx by 162 GB **overflows C:**. → Cannot move store into `~/.ollama`. |
| `I:` free space | **399 GB free** | Can host a *separate* 200 GB vhdx file. |
| Session-75 intent | "C:\ no longer grows from model pulls" | The move to I: was deliberate — **keep models off C:**. Any new design must preserve this. |
| 9p tax measured | cold load = **~33 s** for 18 GB; full-RAM read | mmap would make pages file-backed + reclaimable + page-cache-reused. |

**The constraint in one line:** we need *real ext4* (for mmap) **and** the bytes must stay
*off C:* (session-75 goal) **and** C: can't grow. Only a dedicated ext4 vhdx on a
space-rich drive satisfies all three.

### Full drive map (researched session 98)

Physical disks:

| Disk | Model | Media | Size | Drive letters |
|------|-------|-------|------|---------------|
| 0 | M4-CT256M4SSD2 | SATA SSD | 238 GB | D: (sys), H: |
| 1 | ST2000DM008 | HDD | 1863 GB | E: |
| 2 | WDC WD10EZEX | HDD | 932 GB | F: |
| 3 | TOSHIBA HDWD110 | HDD | 932 GB | **unused — no letter** |
| 4 | CT2000P5PSSD8 | **NVMe SSD** | 1863 GB | C:, I:, G: |

Logical volumes (free space):

| Drive | Disk / Media | Size | Free | Free% | Verdict for a 162 GB store |
|-------|-------------|------|------|-------|----------------------------|
| C: | 4 / NVMe | 800 GB | 81 GB | 10% | No — too small + holds the distro vhdx (198 GB); re-bloats C: |
| G: | 4 / NVMe | 500 GB | 22 GB | 4% | No |
| **I:** | **4 / NVMe** | 562 GB | **399 GB** | 71% | **Yes — only roomy NVMe volume; store already here** |
| H: | 0 / SATA SSD | 238 GB | 112 GB | 47% | No — < 162 GB |
| E: | 1 / HDD | 1863 GB | 129 GB | 7% | Fits but HDD (slower loads) |
| F: | 2 / HDD | 931 GB | 56 GB | 6% | No |
| Disk 3 | HDD | 932 GB | ~932 GB | — | Whole free disk, but HDD → slower than today |

**Two consequences for the design:**
1. On the NVMe, **I: is the only volume with room** (399 GB; C: 81, G: 22). So the dedicated
   ext4 vhdx effectively *must* live on I: — the same partition the raw store occupies today.
   This is wrapping the existing bytes in ext4 *in place*, not moving to a different disk.
2. **Disk 3 (932 GB HDD) is the only candidate for a whole dedicated disk**, but it's a HDD;
   model cold-loads would get *slower* than the current NVMe-over-9p. Rejected for a
   latency-sensitive store.
3. **Migration peak**: old store (162 GB) + new vhdx (≤162 GB) both on I: peaks at ~324 GB of
   399 GB free (~75 GB margin). Fits, but verify the copy before deleting the original.

---

## Recommended approach (if we move): dedicated ext4 vhdx on I:, attached as a block device

Not the distro ext4 (C:-backed, full). Instead create a standalone ext4-formatted `.vhdx`
**file stored on I:** and attach it to the WSL2 VM through the hypervisor block layer (not
9p). Inside WSL it is a genuine ext4 filesystem → mmap works → host-RAM read collapses to
on-demand paging. The vhdx *file* sits on I: (NVMe), so C: never grows.

### What changes

1. **Create the vhdx** (Windows, PowerShell): a ~200 GB dynamic VHDX at e.g.
   `I:\wsl-ollama\ollama-ext4.vhdx`.
2. **Attach + format ext4 once**: `wsl --mount --vhd <path> --bare`, then inside WSL
   `mkfs.ext4` the new block device, mount at e.g. `/mnt/ollama-store`.
3. **Copy the store**: `rsync -a --info=progress2 /mnt/i/ollama-models/ /mnt/ollama-store/ollama-models/`
   (162 GB; preserve perms; verify with `du` + a manifest/blob count match).
4. **Repoint Ollama**: edit `/etc/systemd/system/ollama.service.d/override.conf`
   `OLLAMA_MODELS=/mnt/ollama-store/ollama-models`; replace the existing
   `Requires=/After= mnt-i.mount` ordering with a dependency on the **new ext4 mount unit**
   so Ollama never starts before the store is mounted (else it silently creates an empty
   store and "loses" all models).
5. **Persistence** — the operational cost. `wsl --mount --vhd` does **not** survive
   `wsl --shutdown`/reboot. Need one of:
   - A **Windows Task Scheduler** task at logon running `wsl --mount --vhd <path> --bare`,
     plus an `/etc/fstab` entry (by `PARTUUID`) inside WSL to mount it, ordered before
     ollama via a systemd `.mount` unit + `After=`.
   - This is the fragile part: if the attach fails, Ollama comes up storeless.
6. **Optionally relax `.wslconfig`** back toward default once mmap is confirmed (pages are
   reclaimable, so 24 GB is no longer load-bearing) — reclaims RAM for Windows. Keep
   `memory=24GB` if other local-model work benefits.
7. **Reclaim I: space**: after verification, delete `/mnt/i/ollama-models` (frees 162 GB on
   I:) — but the new vhdx consumes ~162 GB on I: anyway, so net I: usage is ~flat.
8. **Doc updates**: CLAUDE.md Key Technical Facts (store path), session-context current
   status, close/annotate T-67, this file → done.

### Verification

- Server log on load shows **no `UseMmap:false`** for the store path and **no `cannot
  allocate memory`**.
- `free -h` during 30B inference: host `used` should be **markedly lower** than the ~14 GiB
  seen with the full-RAM read (pages now in reclaimable page cache, not anonymous).
- Cold-load `load_duration` for `my-go-qcoder` drops from ~33 s.
- Re-run the canonical repro: `curl …/api/generate -d '{"model":"my-go-qcoder",…}'` → 200.
- Boot test: `wsl --shutdown`, reopen, confirm the ext4 mount auto-attaches **before**
  ollama and all 78 models resolve.

---

## Pros (the case FOR moving)

1. **mmap = robustness, permanently.** File-backed pages are reclaimable under memory
   pressure; the OOM cannot recur even if you later co-load models, run bigger MoEs, or
   other apps eat RAM. The `.wslconfig` bump is a band-aid that just raises the ceiling.
2. **~12 GiB host RAM freed** during 30B operation (pages shared with page cache vs
   anonymous full-read).
3. **Faster cold loads** — 9p protocol tax removed; page cache reused across reloads.
4. **Lets us drop the 24 GB RAM cap** and give that memory back to Windows (C:/host is
   tight elsewhere).
5. **Future-proofs** the larger candidates already on the roadmap (Qwen3-Coder-30B,
   DeepSeek R2 32B, Qwen3.5-35B-A3B) — all partial-offload, all would hit the same 9p wall.

## Cons / caveats / risks (the case AGAINST moving)

1. **The OOM is already fixed.** This is optimization, not repair — diminishing returns.
2. **No disk-speed gain.** I: is already NVMe; we only remove the 9p tax. Cold load improves
   but doesn't vanish (GPU/CPU layers still fault in on first inference).
3. **Persistence is genuinely fragile.** `wsl --mount --vhd` doesn't auto-remount; the
   logon-task + fstab + systemd-ordering chain is the real cost. A single broken link =
   **Ollama silently starts with an empty store** and every persona/model "disappears"
   until noticed. This is a worse failure mode than a clean 500.
4. **162 GB copy** is slow and must not be interrupted; content-addressed store integrity
   depends on a complete, perm-preserving copy.
5. **Another vhdx to own** — independent corruption surface, separate backup concern, and a
   second thing to remember exists during future infra work.
6. **Reverses a deliberate session-75 setup** that has worked fine for everything except the
   one 30B partial-offload case.
7. **Timing.** The local-model stack is mid-evolution (LTG, persona churn, distillation
   roadmap). Investing in storage plumbing now is arguably premature.

---

## Recommendation

**Do not move yet — keep the `.wslconfig` mitigation as the standing fix; hold this plan in
reserve.** Rationale: the failure is resolved, the only remaining wins are latency + RAM
headroom on a single model, and the move's persistence story is fragile enough that it could
trade a loud, well-understood failure (500) for a quiet, confusing one (empty store). The
move becomes worth it **when a trigger fires**:

- A second large partial-offload model becomes a daily driver (RAM cap stops being enough), **or**
- We need the 24 GB back for Windows / co-loading, **or**
- Cold-load latency on the 30B becomes a real workflow cost.

Until then, T-67 stays open with this plan attached. If/when we execute, the dedicated-vhdx-
on-I: design above is the chosen path; the distro-ext4 option is permanently ruled out by
C: capacity.

## Failure mode: canonical-port squatter (discovered 2026-07-09)

`make -C ~/workspaces ollama-store-check` reported `FAIL — http://localhost:11434 serves only 0
models`, implying the ext4 store link had broken. **It had not.** The store was mounted, intact
(163 GB), and serving all 84 models. The store was never involved.

### Mechanism

Ollama **0.17.5** made the bare `ollama` command an interactive **TUI** (it is no longer a help
screen). The TUI probes `$OLLAMA_HOST` — default `127.0.0.1:11434` — and **if nothing answers, it
spawns a detached `ollama serve` that inherits the shell environment and outlives the TUI**
(reparenting to `/init`). A login shell has no `OLLAMA_MODELS`, so that server opens the **empty
default store** at `~/.ollama/models`.

The spawned server never collides with `ollama.service`, which listens on `:11435`. It collides
with `ollama-metrics-proxy.service`, which owns `:11434` — and at boot the TUI can win that race.
The proxy then crash-loops forever on `bind: address already in use`.

Resulting signals — note that every *individual* check is telling the truth:

| Signal | Value | |
|---|---|---|
| `systemctl is-active mnt-ollama\x2dstore.mount` | `active` | true, and irrelevant |
| `systemctl is-active ollama` | `active` | true, and irrelevant |
| `systemctl is-active ollama-metrics-proxy` | `activating (auto-restart)`, `status=1/FAILURE` | the real signal |
| `curl :11434/api/tags` | `{"models":[]}` | every client sees **zero** models |
| `curl :11435/api/tags` | 84 models | the store is fine |

Verified empirically 2026-07-09 (bare `ollama` under a pty, decoy port):

| Condition | Bare `ollama` behaviour |
|---|---|
| `$OLLAMA_HOST` **unreachable** | spawns a detached `ollama serve`; empty store; survives TUI exit |
| `$OLLAMA_HOST` **reachable** | reuses it; spawns nothing |

**The hazard is therefore a boot-race window**, not a typo: running `ollama` before the proxy has
bound `:11434`. Typing `ollama serve` does the same thing, but is *not* required to reproduce it.
This is the "quiet, confusing failure" predicted in Cons §3 above, arriving from an unpredicted
direction — the mount held; a second daemon supplied the empty store.

### Detection — fixed in `~/workspaces/scripts/ollama-store-check.sh`

The old step 3 probed `localhost:11434 localhost:11435` and `break`ed on the **first host that
answered**. The second host was a fallback, not a cross-check, so a squatter's empty store masked
the real 84 models. Replaced by two steps:

- **Step 3 — endpoint identity.** `ollama-metrics-proxy.service` must be `active`; if it is, it
  necessarily holds `:11434`, since two processes cannot bind one address. Corroborated by
  comparing the port's listener PID (`ss`) against the unit's `MainPID` (`systemctl show`), which
  also *names* the culprit. An unprivileged shell cannot see root-owned listener PIDs — but a
  squatter is by construction user-owned, so the one case we are blind to cannot occur.
- **Step 4 — both ports agree.** Require `count(:11434) == count(:11435) >= MIN_MODELS`.

Both detectors fire independently on the real failure; neither alone is airtight. Verified against
an impostor server returning `{"models":[]}` on a decoy port.

### Recovery

```bash
kill <squatter-pid>                                    # the check names it
sudo systemctl restart ollama-metrics-proxy.service
make -C ~/workspaces ollama-store-check                # expect PASS, 84 models on both ports
```

### Prevention — DEPLOYED 2026-07-09

**A healthy system is self-defending.** Every hazard is conditional on the canonical endpoint being
unreachable: a reachable endpoint makes the TUI reuse it (no spawn), and makes `ollama serve` fail
loudly on `bind: address already in use`. So the guard's job is narrow — cover the window where the
endpoint is down.

Machine-local (`~/workspaces/scripts/`, outside the repo per the session-100 boundary), both sourced
from `~/.bashrc`:

- **`ollama-guard.sh`** — shadows the `ollama` CLI. **Reroute, don't refuse:**

  | Invocation | Proxy up | Proxy down, `ollama.service` up | Both down |
  |---|---|---|---|
  | `ollama` (TUI) | pass through | reroute to `:11435`, warn | **refuse** (this is the spawn) |
  | `ollama list`/`run`/`ps` | pass through | reroute to `:11435` | pass through, fails cleanly |
  | `ollama serve` | refuse (kernel would too) | **refuse** — the case that matters | pass through |

  Rerouting works because a reachable endpoint is *itself* the safety property: hand the TUI
  `:11435` and the spawn path never executes. Bypass with `OLLAMA_ALLOW_SERVE=1` or `command ollama`.
- **`ollama-motd.sh`** — runs `ollama-store-check.sh --brief` once per WSL boot (sentinel in
  `$XDG_RUNTIME_DIR`, tmpfs — the right lifetime, since a VM restart is also when the store attach
  can evaporate per T-68/T-70). Writes the sentinel **only on success**, so a broken store nags every
  new terminal until fixed. ~0.1 s on the healthy path. Retries a few times before complaining,
  because the first shell of a boot can open while the proxy is still `activating`.
- **`~/.bashrc:138` `export OLLAMA_CONTEXT_LENGTH=8192` — commented out.** It is a *server-side*
  variable; systemd never reads `.bashrc` and the override does not set it, so the export was inert.
  It appears in **no tracked file**. Origin: the 2026-02-17 CLI-tool bake-off suggested it alongside
  `GOOSE_DISABLE_KEYRING=1` "so you don't need to prefix every Goose command" — the keyring var is a
  genuine Goose client setting; this one was mis-scoped from birth. Its only possible effect was on a
  hand- or TUI-spawned server, i.e. the bug itself. If an 8192 default is ever wanted it belongs in
  `/etc/systemd/system/ollama.service.d/override.conf` as `Environment="OLLAMA_CONTEXT_LENGTH=8192"`.

**Standing rule:** never `ollama serve` by hand — systemd owns the only server. The CLI is a
*client*; on Linux no subcommand except `serve` spawns a server, and the bare TUI does so only when
it can reach nothing.

---

## Alternatives considered and rejected

- **Move store into distro ext4 (`~/.ollama`)** — impossible: needs 162 GB vhdx growth, C:
  has 82 GB free; also re-bloats C: (undoes session 75).
- **Per-blob symlink the 30B onto ext4, leave the rest on I:** — Ollama may re-verify/GC
  blobs and resolve real paths inconsistently; fragile, rejected.
- **Force mmap on 9p** (no supported "force-on" flag; mmap over 9p is unreliable by design)
  — rejected, this is *why* Ollama disables it.
- **Do nothing beyond `.wslconfig`** — the current state; the recommended default.
