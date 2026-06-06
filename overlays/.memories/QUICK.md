# overlays/ — Quick Memory

*Working memory for the overlay system. Keep under 30 lines.*

## Status

3 overlays operational, installed in expenses repo (all 3) and web-research repo (ref-indexing).
Manifest-driven installer with manual and AI-assisted merge modes.

Sessions 84–87: the `session-tracking` overlay gained a deterministic handoff pipeline under `session-tracking/files/handoff/` — F1–F7 + per-run logging + entrypoint (`handoff.py`/`registry_io.py`/`run-handoff.sh`) + manifest install layout + rewritten `SKILL.md`. **B1–B4 complete — Scope A done, 77 tests, dog-food-validated** (clone run found+fixed a newline-glue bug). Register ships via `manual_if_exists` (Option C: propagate-with-flag). Architecture → KNOWLEDGE.md.

## What Overlays Are

Installable packages of tools, documentation sections, and AI agent rules for
Claude Code projects. Each overlay solves one cross-cutting concern:

| Overlay | Purpose |
|---------|---------|
| **ref-indexing** | `<!-- ref:KEY -->` documentation blocks + lookup CLI + integrity checker |
| **ollama-scaffolding** | Local model conventions: verdict protocol, retry policy, warm-up |
| **session-tracking** | Session continuity: resume.sh, rotate-session-log.sh, handoff skill |

## Installation

```
./overlays/install-overlay.py <name> --target /path/to/repo [--mode ai]
```

Modes: manual (prints TODO list) or AI (plans + applies CLAUDE.md merges automatically).
Idempotent — re-running produces all [SKIP].

## Deeper Memory -> KNOWLEDGE.md

- **Merge Markers** — version tracking, idempotent updates
- **AI Backend Abstraction** — Ollama, Claude CLI, Claude API
- **Manifest Schema** — files, templates, sections, append_lines
- **Cross-Repo Value** — why overlays exist (consistency across 3 repos)
