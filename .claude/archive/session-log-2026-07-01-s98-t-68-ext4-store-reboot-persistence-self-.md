## 2026-07-01 - Session 98: T-68 — ext4 store reboot-persistence self-heal (udev) + 162 GB reclaim

### Context

Opened from `resume.sh` and picked T-68 (validate ext4 store reboot-persistence, then reclaim the old 162 GB on I:). A real reboot had already happened since session 98, so the "waiting for a reboot" precondition was already met — and it exposed a failure.

### What Was Done

- Root-caused a post-reboot store detach: the `WSL-Ollama-ext4-store` logon task fired at boot but returned `LastTaskResult=1` — its chained in-WSL `systemctl restart` raced the cold WSL/systemd boot, leaving the vhd unattached; ollama correctly refused to start (the loud-fail `Requires=`/guard chain held instead of serving an empty store).
- Recovered the live store (manual `wsl --mount` + `systemctl restart` → `PASS`, 81 models).
- Fixed persistence (Option A, commit `a64f211`): thinned the logon task to attach-only; added a udev rule `99-ollama-store.rules` (matched by `ID_FS_UUID` → `SYSTEMD_WANTS`) + a oneshot `ollama-store-recover.service` (`reset-failed` + `start ollama`, which pulls the mount, which pulls the now-present device).
- Live-verified the self-heal non-destructively (`udevadm trigger --action=add /dev/sde`: `FAIL → PASS`, no manual mount).
- Real reboot cold `PASS` with zero manual steps — and the device came back as `/dev/sdd` (not `sde`); UUID matching held.
- Reclaimed the old store: `rm -rf /mnt/i/ollama-models` (162 GB; I: 233 → 394 GB free), verified the live store unaffected (running ollama `OLLAMA_MODELS=/mnt/ollama-store/models`, API serves 81). Close-out doc commit `717c9ae`.

### Decisions Made

- Chose Option A (event-driven udev self-heal) over Option B (race-proof polling glue in the logon task): recovery belongs in systemd (which already owns the loud-fail guard), not in Windows-side timing. Decompose along the seam — Windows does the one thing only it can (hypervisor attach), WSL reacts to the *result* (device-add), not to a timing assumption.
- Match the device by `ID_FS_UUID`, never `/dev/sdX` — the reboot proved the letter is volatile (sde→sdd).
- No `tasks.md` checkoff for T-68: it lives in current-status "Open deferred tasks", marked done there (strikethrough), not as a `[ ]` line.

### Next

- LTG Phase 4 — graph + communities (the standing next task): `alias_of` lists relocate to an edge table; anchor↔anchor edges from `index.md` cross-refs land here; `networkx + leidenalg`; build on the fresh 1018-row full-corpus index on master.

### Gotchas

- The logon task trigger is `-AtLogOn` (Windows sign-in), NOT WSL start — a bare `wsl --shutdown` + reopening a terminal will NOT fire it; only a real Windows sign-out/in (or a restart) does.
- `powershell.exe` interop is unavailable from the agent's WSL shell (`Exec format error`) — Windows Task Scheduler queries (`Get-ScheduledTask*`) must be run by the user, not via Bash.
