# ollama-scaffolding overlay

Packages the local model usage conventions for any project using the ollama-bridge
MCP server. Designed to be installed alongside `ref-indexing`.

## What it installs

| Target | Content |
|--------|---------|
| `CLAUDE.md` (merge) | Prompt style, when-to-call, serialization, verdict protocol, imperfect output decision tree, stubs-then-Ollama pattern, cold-start grace period |
| `.claude/overlays/local-model-conventions.md` (file) | Runtime-accessible `ref:local-model-conventions` block — full before/after-call usage policy. Overlay-owned; re-install propagates updates |

## Prerequisites

- ollama-bridge MCP server configured globally (`~/.claude/.mcp.json`)
- Ollama running with at least one model pulled
- Verdict capture hooks installed (user-level `~/.claude/settings.json`)

## Usage

```bash
# Dry run
./overlays/install-overlay.py ollama-scaffolding --target ~/workspaces/expenses/code --dry-run

# Install with AI-assisted merge
./overlays/install-overlay.py ollama-scaffolding --target ~/workspaces/expenses/code --mode ai --yes

# Install with manual merge (prints TODO for CLAUDE.md placement)
./overlays/install-overlay.py ollama-scaffolding --target ~/workspaces/expenses/code

# Re-install to propagate doc updates — pass --backup to keep a .bak of any
# locally-modified copy of local-model-conventions.md before it is overwritten
./overlays/install-overlay.py ollama-scaffolding --target ~/workspaces/expenses/code --backup
```

## Design rationale

The full design rationale (DPO training implications, prompt cost analysis, conceptual
defect taxonomy) lives in `docs/scaffolding-template.md`. This overlay extracts the
operational rules — what an agent needs at runtime — into a self-contained section.
