# Overlay Distribution Options

<!-- ref:overlay-distribution-options -->
**Date:** 2026-06-09
**Context:** Session-tracking overlay ships Python pipeline files (locator.py, payload.py, etc.)
via `files:` → `.claude/tools/handoff/` in each target repo. Every source change
requires a manual sync to all installed repos. This doc evaluates alternatives.

## Problem

The `files:` manifest section copies files verbatim to each target repo. When the source
changes, all copies drift until the installer is re-run or files are manually synced.
Today (2026-06-09): 3 repos × 2 files = 6 stale copies after a single pipeline change.

## Options

### A — Symlinks instead of copies

Installer creates symlinks: `<repo>/.claude/tools/handoff/locator.py → <overlay-source>/locator.py`.
Changes to source are instantly live in all repos.

- **Pro:** Zero drift, no sync step, lowest complexity.
- **Con:** Absolute paths — breaks on a different machine or Windows host. All repos share the same version (no per-repo pinning).

### B — Shared `~/.claude/tools/handoff/` (user-level install)

Move `handoff/*.py` from `files:` (per-repo copy) to `user_files:` (shared user-level install), matching how `SKILL.md` already works. One copy on disk; all repos reference it.

- **Pro:** Matches existing SKILL.md pattern; no per-repo copies; installer already supports `user_files:`.
- **Con:** Not in any repo — harder to track version per machine. Requires re-install on each new machine.

### C — Thin shim per repo, source stays canonical

Each repo gets a small `run-handoff.sh` that locates and delegates to the canonical source:

```bash
HANDOFF_SRC=$(cat ~/.claude/handoff-source 2>/dev/null \
  || echo "$HOME/workspaces/llm/overlays/session-tracking/files/handoff")
exec python3 "$HANDOFF_SRC/handoff.py" "$@"
```

Only the shim is installed per-repo; the `.py` files are never copied.

- **Pro:** Repos stay thin; one config file makes the path machine-portable.
- **Con:** Runtime dependency on the source path existing. If the llm repo moves, all repos break.

### D — pip editable install

Package the handoff pipeline as a Python package (`pyproject.toml` + `handoff` CLI entry point).
Install once with `pip install -e <overlay-source>/`. `run-handoff.sh` becomes `exec handoff "$@"`.

- **Pro:** Standard packaging; editable install means source changes are immediately live; version-pinnable; publishable to PyPI.
- **Con:** Adds packaging boilerplate to a standalone script cluster; editable installs are machine-local.

### E — Installer `--check` / `--sync` mode (keep copies, automate sync)

Keep the copy-per-repo model; extend `install-overlay.py` with `--check` (reports stale files)
and `--sync` (resyncs without full reinstall).

- **Pro:** No architectural change; repos remain self-contained (clone → works); lowest risk.
- **Con:** Copies still exist; sync step still required — just automated rather than manual.

### F — MCP tool via existing ollama-bridge

Expose `run_handoff(payload, registry_path, dry_run)` as an MCP tool in the existing
`mcp-server/` (ollama-bridge). The SKILL.md calls the MCP tool; only `registry.yaml` and
a one-liner shim are installed per-repo.

- **Pro:** Zero Python per-repo; leverages existing MCP infrastructure; instant updates when server restarts.
- **Con:** Runtime dependency on MCP server being up. Circular dependency for the llm repo itself (server lives here). Couples handoff availability to Ollama availability.

### G — Dedicated handoff MCP server (standalone)

Same as F but a minimal standalone FastMCP server (`~30 lines`) for the handoff pipeline only.
Configured once in `~/.claude/mcp.json`; all repos share it.

- **Pro:** Clean separation; no Ollama dependency; one config entry covers all repos; version boundary = server restart.
- **Con:** Adds a process to manage. MCP stdio transport means it's spawned per-session anyway (not a persistent daemon).

### H — Claude Code plugin (cozempic pattern)

Package as a proper Claude Code plugin (Python package with `claude_code_plugin` entry point).
Registers the `/session-handoff` skill + hooks. Installed once globally; no files per-repo.

- **Pro:** First-class Claude Code citizen; skills + hooks + CLI in one package; `pip upgrade` updates all repos simultaneously; publishable.
- **Con:** Highest setup cost; plugin API contract to learn and maintain. Registry.yaml remains per-repo regardless.

### I — Git hook (post-commit)

`post-commit` hook installed per-repo delegates to canonical source (via B or C path strategy).
Zero per-repo Python; handoff triggers automatically on commit.

- **Pro:** Zero per-repo Python; integrates with existing git workflow.
- **Con:** Git hooks not committed (`.git/hooks/` is gitignored) — must reinstall per clone. Makes post-commit heavyweight; rollback is awkward if handoff fails after commit.

## Comparison

| Option | Python files per-repo | Sync on update | Runtime dependency | Setup cost |
|--------|----------------------|----------------|--------------------|------------|
| A — Symlinks | 0 (links) | No | Source path | Low |
| B — Shared `~/.claude/tools/` | 0 | Re-install on new machine | None | Low |
| C — Thin shim | 0 | No | Source path | Low |
| D — pip editable | 0 | No (`-e`) | venv/pip | Medium |
| E — Installer `--sync` | N (copies) | One command | None | Low |
| F — MCP via bridge | 0 | Server restart | MCP server up | Medium |
| G — Dedicated MCP server | 0 | Server restart | MCP server up | Medium |
| H — Claude Code plugin | 0 | `pip upgrade` | None | High |
| I — Git hook | 0 | Reinstall per clone | Source path | Low |

## Recommendation

**Near-term:** Option E (`--sync` mode on installer) — zero risk, pays off immediately.
**Medium-term:** Option B (user-level `~/.claude/tools/`) — matches existing SKILL.md pattern,
minimal change to the installer's manifest handling.
**Long-term:** Option G (dedicated MCP server) — most architecturally clean for a Claude
Code-native setup, eliminates per-repo files with no new external dependencies.
Option H if the pipeline needs to be shared outside this machine.

## Decision (2026-06-17)

**Implemented: B+C** — Python pipeline modules always user-level (`~/.claude/tools/handoff/`);
per-repo artifact is a thin `run-handoff.sh` shim that delegates there.

### Design choices made

- **`--install-level` flag** (renamed from `--skill-level`) controls shim + SKILL.md placement
  (`user` default → `~/.claude/`; `project` → per-repo `.claude/`). Python files are
  unconditionally user-level via a new `always_user_files:` manifest key — the flag does not
  affect them.
- **Registry always per-repo** — encodes repo-specific file paths, ref keys, and locator
  types. Neither user-level nor flag-controlled. Remains `manual_if_exists`.
- **Hooks always per-repo** — user-level hooks fire in ALL repos including those without the
  overlay. The shim includes a registry guard (`exit 0` if `.claude/handoff/registry.yaml`
  absent) so any hook invoking the shim is safe at user level if desired in future.
- **D (pip editable install) — ADOPTED, session 111.** The deferral rationale above ("no
  immediate benefit; adopt when H becomes concrete") was **falsified**. The real trigger was
  never H: it was *a second consumer needing the primitive*. When `resume` had to share
  `locator.py` with `handoff`, the flat directory at `~/.claude/tools/handoff/` had no package
  semantics, so the import needed `sys.path` hacks. Packaging made the extraction trivial.
  `overlays/session-tracking/pyproject.toml`, entry points `st-handoff` / `st-resume`,
  `uv tool install --editable`. `always_user_files:` removed. **Code ships as a package;
  config ships as an overlay.** Publish-escalation trigger adopted verbatim from the LTG
  split: flip to a published package only when (a) working from a machine without the
  checkout, or (b) a first external adopter appears. H is now pre-staged, as predicted.
  Lesson for the remaining options: a deferral whose trigger is guessed will fire on a
  different trigger. Record what would *force* the change, not what would make it fashionable.

### Migration performed

All 3 target repos (expenses/code, web-research, career-search) committed:
- `run-handoff.sh` rewritten as thin shim with registry guard
- 10 per-repo `.py` files deleted (now shared at `~/.claude/tools/handoff/`)
- llm home-repo unchanged (runs engine from overlay source; not installed)

### Deferred: G and H

**G (dedicated MCP server)** and **H (Claude Code plugin)** remain the long-term targets.
Both require evaluating the MCP server lifecycle and plugin API contract respectively.
Tracked as T-60. The shim is the stable per-repo seam: migrating to G or H only requires
changing one line in the shim (or regenerating it via the installer).
<!-- /ref:overlay-distribution-options -->
