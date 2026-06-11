# Handoff Pipeline — MCP Migration + Structured Role Schema

**Status:** Deferred. Design discussion captured session 89.
**Task:** `(T-55)` in `tasks.md` → `.claude/deferred-infra`

---

## Problem being solved

The current flow requires two tool calls:
1. Model writes content to `.claude/local/handoff-pending.md` (a well-known path)
2. Model calls `run-handoff.sh --payload .claude/local/handoff-pending.md`

If a previous session's pending file is still there (failed run, interrupted session), it is
silently overwritten. The well-known path is also a contention point if multiple sessions ever
run in the same repo.

---

## UUID + inline content (operational fix — can be done at CLI level)

The tool accepts content directly (inline, not via a pre-written file):
- Assigns a UUID to the run on entry
- Saves a pending file named after the UUID + status: `<uuid>-pending.md`
- On success: renames/marks as `<uuid>-success.md`; outputs UUID + success path + report path
- On failure: leaves `<uuid>-pending.md` as-is; outputs UUID + pending path + error detail

### Pending file lifecycle

No auto-cleanup. The success output includes a count of pending and success files so the
**user** can decide when to prune. The model reports counts but never deletes autonomously.

### Retry semantics

Two distinct cases:

| Failure type | Content OK? | Retry action |
|---|---|---|
| Environmental (dirty tree, locate failed) | Yes | Pass `--id <uuid>` — tool re-runs original content |
| Content error (bad role, wrong format) | No | Submit new inline content (new UUID) — model already has the content in context |

The pending file serves as a **recovery artifact** for the content-fix case only when the
model's context has been compressed and the model can no longer recall what it authored.
For fresh retries within the same session, re-authoring inline is always simpler.

---

## MCP migration (bigger change — changes distribution model)

Converting the CLI to an MCP tool (or MCP server) enables:

1. **Structured schema per role** — each role gets a typed contract instead of a markdown
   section with a text description:
   - `log_entry`: named fields (`context`, `what_was_done`, `decisions`, `next`) instead of
     templated freetext — the model can't mis-format what the tool validates at call time
   - `checkoffs`: already a list; becomes a proper `string[]` arg
   - `current_status`, `active_decisions`, `reading_guide`: free-text blobs — schema is
     `content: string`, no richer than today; main win is still validation, not structure

2. **No pre-write step** — the MCP tool call IS the submission; no Write → Bash round-trip

3. **Structured output** — success/failure comes back as a proper tool result, not stdout
   text the model has to parse

### Distribution trade-off

Today the pipeline is an **installable CLI** — the overlay copies it into `.claude/tools/`;
no server needed, works in any repo. An MCP tool requires the MCP server to be running.
That changes the dependency model for every repo that installs the `session-tracking` overlay.

Options when designing:
- A: Standalone MCP server for handoff only (new process per repo)
- B: Add handoff as tools on the existing `ollama-bridge` MCP server
  (centralized, but couples handoff to the LLM bridge — wrong separation)
- C: Keep CLI as the execution engine; write an MCP shim that calls the CLI
  (best of both: structured args + no new server dependency)

Option C is probably the right path — the CLI already has the safety core; the MCP layer
just translates structured args into a payload and delegates.

---

## Related tasks

- `(T-56)` — "add deferred task" append tool (same meta-problem: single-line writes shouldn't
  require reading the whole file)
- `(T-53)` B5.1 preflight check — independent, but a natural companion to the UUID approach
  (preflight could also be exposed as an MCP tool call)
