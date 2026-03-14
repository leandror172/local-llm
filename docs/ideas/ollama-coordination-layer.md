# Ollama Coordination Layer

**Status:** Design only (session 42, 2026-03-14). Not yet implemented.
**Related:** warm-up MCP tool (bundled Option 1 built first), deferred-infra tasks.

## Problem

Multiple independent processes (MCP bridge instances, Aider, scripts, hooks) share
Ollama's VRAM. No single process owns the resource. Without coordination:

- Warm-up evicts a model mid-generation from another session
- Two Claude Code sessions load different models simultaneously, thrashing VRAM
- A `SessionStart` hook can't safely pre-warm a model without knowing if Ollama is busy

## Current State (Ollama API limitations)

- **`GET /api/ps`** returns loaded models with `name`, `size`, `size_vram`, `expires_at`
- **No field indicates active processing** — only what's loaded, not what's busy
- **Unload:** `POST /api/chat` with `messages: []` and `keep_alive: 0`
- **Concurrent behavior is undocumented** — unknown what happens if you unload during generation

## Proposed Design: Shared Directory Contract

A directory at a well-known path (e.g., `/tmp/ollama-inflight/`) where each in-flight
request is represented by a file. Presence = busy, absence = idle.

### File naming convention

```
/tmp/ollama-inflight/
├── 12345-qwen3-8b-a1b2c3d4    # {PID}-{model-sanitized}-{request-id}
└── 12345-qwen3-8b-e5f6g7h8
```

File content (optional JSON): `{"started": "...", "caller": "ollama-bridge"}`

### Contract

```python
INFLIGHT_DIR = "/tmp/ollama-inflight"

def register(model: str, caller: str) -> Path:
    """Create a lock file before sending a request to Ollama."""
    safe_model = model.replace(":", "-")
    path = Path(INFLIGHT_DIR) / f"{os.getpid()}-{safe_model}-{uuid4().hex[:8]}"
    path.write_text(json.dumps({"started": now(), "caller": caller}))
    return path

def deregister(path: Path):
    """Remove the lock file after receiving a response."""
    path.unlink(missing_ok=True)

def is_busy(model: str = None) -> bool:
    """Check if any (or a specific) model has in-flight requests."""
    for f in Path(INFLIGHT_DIR).iterdir():
        pid = int(f.name.split("-")[0])
        if not pid_alive(pid):
            f.unlink()  # cleanup stale
            continue
        if model is None or model.replace(":", "-") in f.name:
            return True
    return False
```

### Properties

- **Zero contention:** file creation/deletion are atomic on Linux; no locking needed
- **Crash-safe:** PID liveness check (`kill -0 pid`) cleans stale files
- **Language-agnostic:** bash can participate with `touch`/`rm`
- **Self-cleaning:** every `is_busy()` call reaps dead entries

### Participants

| Caller | Registers? | Checks? |
|---|---|---|
| MCP bridge (`_call_ollama`) | Yes — register before, deregister after | No (warm_model checks) |
| `warm_model` MCP tool | No | Yes — checks before evicting |
| Aider (via bash wrapper) | Yes (future) | No |
| `SessionStart` hook | No | Yes — checks before pre-warming |
| bash scripts / cron | Optional | Optional |

## Why Not Yet

- Only the MCP bridge is a regular Ollama consumer today
- Aider usage is sporadic; no concurrent sessions observed yet
- The bundled Option 1 (in-process tracking inside MCP bridge) covers 95% of cases
- Extracting from Option 1 to this design is straightforward — the `_call_ollama()`
  register/deregister calls just switch from dict ops to file ops

## Alternatives Considered

### JSON state file + flock
Single `/tmp/ollama-inflight.json` with `fcntl.flock` for atomic read/write.
Rejected: single contention point, flock can block if holder dies (though OS releases on exit).

### SQLite (WAL mode)
`/tmp/ollama-state.db` with an `inflight` table.
Rejected for now: over-engineered for 0-3 concurrent requests. Revisit if we want
historical analytics (VRAM contention frequency, model load patterns).

### Unix domain socket
MCP bridge runs a status server on `/tmp/ollama-bridge.sock`.
Rejected: only useful while MCP server is running, requires protocol implementation
in every caller. Could be added as a convenience layer on top of the directory contract.

## Migration Path (Option 1 → Option 2)

1. Option 1 ships with in-process `_inflight` dict in the MCP server
2. When a second consumer emerges (Aider wrapper, hook, second MCP instance):
   a. Extract `register/deregister/is_busy` into `lib/ollama-inflight.py`
   b. Replace dict ops with directory ops
   c. Add bash wrapper `lib/ollama-inflight.sh` for shell callers
   d. MCP bridge imports the library instead of using internal dict
3. Warm-up tool works identically — just reads from directory instead of dict
