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

**T6 contract:** `ensure_worker` spawns WITHOUT claiming the pidfile — the worker must
claim as its FIRST act and exit if it loses. Until a worker claims, concurrent submits
may briefly double-spawn; the pidfile race decides the survivor.

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
