# Technology Conventions

Reusable technology decisions established in this project.
Query `ref:patterns-index` for a summary of all patterns; drill into any
`ref:patterns-*` key for details.

**Split policy:** When this file exceeds ~400 lines, extract each `ref:patterns-*`
block into its own file under `docs/patterns/`. Update the index to point
to file paths instead of anchor keys.

---

<!-- ref:patterns-index -->
## Patterns Index

| Key | Decision | One-liner | Revisit? |
|-----|----------|-----------|----------|
| `patterns-python-tooling` | uv + pyproject.toml | No requirements.txt, no pip, `uv run --project` for everything | Monorepo needs, C extensions, Poetry-specific features |
| `patterns-mcp-development` | mcp[cli] (FastMCP) + httpx | Official Python SDK, stdio transport, async HTTP client | Non-Python repo, HTTP transport needed, SDK v2 breaking change |
| `patterns-ollama-api` | /api/chat, stream: false | Programmatic access conventions, structured output, thinking control | Streaming UX, different inference backend, new Ollama API params |
| `patterns-script-conventions` | Bash wrappers over direct python3 | `./script.sh` form, whitelist-safe, PATH portability | — (security invariant) |
| `patterns-git-workflow` | Worktrees, safety protocol, branch naming | Parallel work without branch switching | Team size grows, repo size causes worktree slowness |
| `patterns-persona-naming` | my-\<role\>[-model-suffix] | Registry as source of truth, naming rules | Non-Ollama backend, model ecosystem consolidation |
| `patterns-licensing` | Check + honor + attribute | ATTRIBUTIONS.md for required attributions | — (hard requirement) |
<!-- /ref:patterns-index -->

---

<!-- ref:patterns-python-tooling -->
## Python Tooling

**Decision:** uv + pyproject.toml (PEP 621)

**Why:**
- `uv run --project <dir>` creates venv, syncs deps, and runs — one command, zero manual activation
- `pyproject.toml` is the standard; no requirements.txt, no setup.py, no poetry.lock
- Build backend: `uv_build` (replaces setuptools/hatchling for simple projects)
- Python version: `>=3.10` (WSL2 Ubuntu 22.04 ships 3.10; 3.12 upgrade deferred)

**How to apply in a new project:**
```bash
# Initialize
uv init --name my-project
# Add dependencies
uv add "mcp[cli]>=1.0.0" "httpx>=0.27.0"
# Run
uv run python -m my_module
# Or via bash wrapper (preferred — see patterns-script-conventions)
```

**pyproject.toml template:**
```toml
[project]
name = "project-name"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []

[build-system]
requires = ["uv_build>=0.10.2,<0.11.0"]
build-backend = "uv_build"
```

**Revisit when:**
- Project needs workspace-level dependency management across multiple packages (monorepo) — uv workspaces may cover this, but evaluate against alternatives
- A dependency requires Poetry-specific features (dependency groups for deployment, plugin system)
- `uv_build` backend lacks a feature needed by the project (C extensions, complex build steps) — switch to hatchling or setuptools

**Established in:** Layer 1 (MCP server, `mcp-server/pyproject.toml`)
<!-- /ref:patterns-python-tooling -->

---

<!-- ref:patterns-mcp-development -->
## MCP Development

**Decision:** `mcp[cli]` (official Python MCP SDK / FastMCP) + httpx

**Why:**
- Layer 1 evaluated all 10 official SDK languages (TS, Python, Go, Java, Kotlin, C#, Swift, Ruby, Rust, PHP)
- Python won on: lowest tool friction, best ecosystem for general-purpose tasks, FastMCP decorator API
- httpx chosen over requests for async support + connection pooling
- Full research: `.claude/archive/layer-1-research.md`

**Key conventions:**
- **Transport:** stdio (Claude Code spawns server as subprocess, JSON-RPC over stdin/stdout)
- **Registration:** `claude mcp add --transport stdio <name> -- <command>` → writes to `~/.claude.json`
- **Timeouts:** `MCP_TIMEOUT=120000` in `~/.bashrc` (default 10s is too short for LLM calls)
- **Project-level:** `.mcp.json` at repo root for repo-specific servers
- **System-wide:** `~/.claude/.mcp.json` for servers available everywhere (e.g., ollama-bridge)

**Server structure (proven pattern):**
```
mcp-server/
├── pyproject.toml          # uv project with mcp[cli], httpx
├── run-server.sh           # Bash wrapper (whitelist-safe entry point)
├── src/
│   └── my_mcp/
│       ├── __init__.py
│       ├── __main__.py     # Entry point: from .server import mcp; mcp.run()
│       ├── server.py       # @mcp.tool() decorated functions
│       ├── client.py       # Async HTTP client (httpx) for backend API
│       └── config.py       # Defaults, env var overrides
```

**Revisit when:**
- Building an MCP server in a repo that is primarily Go or TypeScript — the SDK exists for both; Python adds a runtime dependency that may not be justified
- Streamable HTTP transport is needed (e.g., server must be shared across machines or run as a standalone service rather than a subprocess)
- The `mcp` SDK makes a breaking v2 change — check migration path before upgrading

**Established in:** Layer 1 (`mcp-server/`), expanded in sessions 42-45
<!-- /ref:patterns-mcp-development -->

---

<!-- ref:patterns-ollama-api -->
## Ollama API Conventions

**Decision:** `/api/chat` with `stream: false` for all programmatic access

**Why:**
- `ollama run` (CLI) is for humans; `/api/chat` is for code
- `stream: false` returns a single JSON response (no SSE parsing needed)
- Streaming adds complexity with no benefit for non-interactive tools

**Key conventions:**
- **Structured output:** Always use `format` param with JSON schema — 100% valid JSON, no speed penalty
- **Thinking control:** `think: false` as top-level payload param (NOT inside `options{}` — Ollama silently ignores unknown keys there)
- **Default strategy:** `think: false` for all tasks; escalate to `think: true` for complex reasoning or retries
- **Model eviction:** Use `keep_alive: "0"` between different model calls to free VRAM
- **Cold starts:** Use `warm_model` MCP tool before time-sensitive calls
- **Custom models:** Lightweight Modelfile manifests (~few KB) sharing base weight layers

**Minimal call pattern:**
```python
async with httpx.AsyncClient(base_url="http://localhost:11434") as client:
    resp = await client.post("/api/chat", json={
        "model": "my-go-q3",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": False,
    }, timeout=120.0)
    result = resp.json()["message"]["content"]
```

**Revisit when:**
- Building a chat UI where token-by-token streaming is needed for UX — `stream: true` becomes justified
- Switching inference backend (vLLM, llama.cpp server, TGI) — API surface differs; abstract behind a client interface
- Ollama adds new top-level API params — check release notes; the `think`-inside-`options{}` silent-ignore bug cost a full session to diagnose

**Established in:** Layer 0 findings, Layer 1 client (`mcp-server/src/ollama_mcp/client.py`)
<!-- /ref:patterns-ollama-api -->

---

<!-- ref:patterns-script-conventions -->
## Script Conventions

**Decision:** Bash wrappers for all Python entry points; `./script.sh` invocation form

**Why:**
- Claude Code can whitelist `./specific-script.sh` per-script for "don't ask again"
- `bash script.sh` shows as generic `bash` — whitelisting it whitelists ALL bash invocations
- Direct `python3 script.py` whitelists ALL Python execution (security risk)
- Wrappers handle PATH setup for non-interactive shells (Claude Desktop via `wsl --`)

**Wrapper template:**
```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"
exec uv run --project "$SCRIPT_DIR" python -m my_module "$@"
```

**Rules:**
- Every Python script gets a `run-*.sh` wrapper
- Wrapper is the only approved way to invoke the script
- Use `python3 -u` (unbuffered) when output ordering matters (subprocess + print mixing)
- Never use inline `python3 -c` for non-trivial operations

**Established in:** Layer 1 (`mcp-server/run-server.sh`), refined in Layers 3-5
<!-- /ref:patterns-script-conventions -->

---

<!-- ref:patterns-git-workflow -->
## Git Workflow

**Decision:** Worktrees for parallel work, safety protocol for destructive ops

**Why:**
- Worktrees share `.git` object store — no redundant clones, instant branch access
- Safety protocol prevents data loss from force-pushes and hard resets
- Feature branches named `feature/<topic>` for clarity

**Conventions:**
- **Parallel work:** `git worktree add ../repo-feature-branch feature-branch`
- **Safety protocol:** explain → backup → dry-run → execute → verify
- **Backup before destructive ops:** `git branch safety-backup-$(date +%s)`
- **Verify after:** `git fsck --full && git log --oneline -5`
- **Worktree cleanup for other tools:** Strip `.claude/` when using non-Claude-Code tools (Aider, OpenCode) — their models read CLAUDE.md and get confused

**Revisit when:**
- Team grows beyond solo developer — may need trunk-based development, PR review gates, or CI-enforced branch protections that change the worktree workflow
- Repo grows large enough that worktrees become slow (shared object store still requires full index scan)

**Established in:** Phase 6, refined across all layers
<!-- /ref:patterns-git-workflow -->

---

<!-- ref:patterns-persona-naming -->
## Persona Naming

**Decision:** `my-<role>` base pattern with model-specific suffixes

**Why:**
- `my-` prefix distinguishes custom personas from base models in `ollama list`
- Role name matches the domain (go, java, python, shell, classifier)
- Suffixes encode model variant for DPO comparison work

**Naming rules:**
- Base: `my-<role>-q3` (Qwen3-8B default)
- Alternative base: `my-<role>-q25c14` (Qwen2.5-Coder-14B)
- Quantization variant: `my-<role>-q3-q8` (Q8 quantization)
- Size variant: `my-<role>-q3-30b` (30B model)
- Source of truth: `personas/registry.yaml`
- Creation: always via `personas/run-create-persona.sh` (never `ollama create` directly)

**Revisit when:**
- Switching away from Ollama to a backend that doesn't use Modelfiles (e.g., vLLM with LoRA adapters) — the naming convention still applies but creation mechanics change entirely
- Model ecosystem consolidates enough that per-model suffixes become noise (e.g., if only one model family is used)

**Established in:** Layer 3
<!-- /ref:patterns-persona-naming -->

---

<!-- ref:patterns-licensing -->
## Licensing Compliance

**Decision:** Always check + honor licenses; track attributions centrally

**Why:**
- Layer 1 decision after evaluating multiple open-source MCP servers for patterns
- Legal hygiene — especially important when borrowing architectural patterns

**Rules:**
- Check license before using or referencing external code/projects
- If attribution required: add entry to `docs/ATTRIBUTIONS.md`
- Never skip this step, even for "just inspiration"

**Established in:** Layer 1 decisions
<!-- /ref:patterns-licensing -->
