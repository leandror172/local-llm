# coding-delegate (oficina) — Knowledge (Semantic Memory)

*Implementation invariants accreted during the P1 build. Decisions/rationale at the
vision level stay in `decisions.md`; this file records what the CODE now guarantees.
Write protocol: update sections in place; never append a dated block.*

## Ledger invariants (P1-D5/D6) — 2026-07-12, T1

Offset is derived from disk on every append (count of valid events), never an in-memory
counter — this is what makes the MCP-surface→worker process handoff safe. Named emitters
(`run_submitted()`, `generation_started()`, …) are the public API; `_append` is private.

**The ledger owns its file's integrity: `_append` repairs a crashed-writer tail before
writing** — `_repair_tail` truncates any torn / blank / unterminated tail back to the end
of the last valid newline-terminated line (byte-position truncate via
`_valid_prefix_bytes`, not a rewrite). Without repair, an append onto a torn tail either
swallows the new event (no trailing newline → concatenation) or turns the tolerated tear
into permanent mid-file corruption (trailing newline → tear becomes a middle line).
Repair is race-free by the single-writer invariant. Read-side is symmetric: torn last
line tolerated, trailing blanks stripped, mid-file corruption still raises
`LedgerCorruptionError`.

*Review lesson:* the original test asserted the append's return value but never read the
ledger afterward — green while encoding the bug (`feedback_review_rederive_invariants`).

## Single-writer topology (P1-D6) — 2026-07-12

Enforced by call order, not locks: the MCP surface appends only `RunSubmitted`, then
pushes the queue marker; the worker can only discover a run through the queue →
happens-before handoff. The ONLY lock in the tree is the pidfile `O_CREAT|O_EXCL`.
Cancellation is a flag file (`runs/<id>/cancel`) precisely so non-workers never touch a
ledger.

## PID-reuse guard (P1-D9) — 2026-07-12, T5

Pidfile stores `{pid, start}`; liveness = `kill(pid, 0)` AND `/proc/<pid>/stat` field-22
start-time match (parsed after the LAST `)` — comm may contain spaces/parens). The
start-time reader is injectable, so PID-reuse is testable by feeding a wrong start-time
against a live PID; two smoke tests exercise the real `/proc` reader.

**Implemented in T6:** `ensure_worker` spawns WITHOUT claiming the pidfile — the worker
claims as its FIRST act (`Worker.run()`) and exits immediately if it loses. Until a
worker claims, concurrent submits may briefly double-spawn; the pidfile race decides
the survivor.

## Worker invariants (T6) — 2026-07-12

Generation is an **injectable seam** (`generate: GenerateFn`, mirrors T5's
`start_time_reader`); the default runs today's `generate_code`/`ask_ollama` semantics
per `deliverable.kind` and tags every call in `calls.jsonl` with `run_id` (the one
deliberate `client.py` seam — additive, `dict.get()`-safe, DPO readers unaffected).
Cold-start grace = one retry on `OllamaTimeoutError`. Cancel is cooperative between
stages (checkpoints: intake / pre_generation / pre_packaging) — never interrupts an
in-flight model call. `Failed` payload triad uses keys `where/whose/what`; intake uses
`stage/fault/detail` — same triad, two spellings, unify in P2.

**Report location:** the delivery report lives in the `Delivered` event payload
(`events.jsonl`, `ledger: forever`) — NOT in `artifacts/`. This is what keeps
`run_result` answerable after retention prunes the workspace.

**`OFICINA_ROOT`** env var overrides the storage root (default
`~/.local/share/oficina/`); tests and acceptance point it at temp dirs.

**Open P2 gaps:** P1 `in_place` runs leave `artifacts/` empty (deliverables go to
`target`), so retention is an observable no-op on real runs until worktrees (P2) or
deliverable-copying; worker's `_default_generate` supports `context.files` but not
`refs`; `_default_generate` reuses `server.py` private helpers (`_build_context_block`,
`_strip_code_fences`) — promote to a shared module when P2 touches them.

## Intake rule model (P1-D3) — 2026-07-12, T3

Pydantic models (`extra="forbid"`) are the schema of record; the allowed-key sets for
the fail-loud unknown-key checks are DERIVED from `model_fields`, so schema and check
cannot drift. Every rejection is a named rule constant + where/whose/what triad
(`stage=intake, fault=payload`). Accepted specs pass through as the same object — no
normalization. Intake returns its verdict; it never raises (the worker turns a rejection
into `IntakeRejected` whose payload IS the rejection).

## FIFO details that would be easy to break — 2026-07-12, T4

Pop order is the NUMERIC epoch-ms prefix (not lexicographic), tie-broken by name.
Run-ID recovery splits on the FIRST dash — `token_urlsafe` IDs may contain `-`.
Push is tmp+`os.rename` (atomic, same dir); markers are distinct by construction.
Pop is not concurrent-pop-safe — safe only because pidfile arbitration guarantees a
single popper.
