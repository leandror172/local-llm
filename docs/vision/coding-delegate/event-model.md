# Event model — oficina run ledger

*The evolving event-model artifact for the deliverable-run system (V-D1: oficina). Authored
2026-07-11 during T-84 pre-planning. This file is the place where event vocabulary churns
cheaply — BEFORE names hit the wire. Each phase plan revises this artifact first, then
promotes its events to frozen.*

**Medium:** Mermaid's native `eventmodeling` diagram type (v11.15.0+), chosen 2026-07-11 —
see "Medium decision" at the bottom for the alternatives record. Source of truth is this
markdown file; render to SVG on demand with `npx -y @mermaid-js/mermaid-cli -i <file>`
(local VS Code / GitHub Mermaid renderers may lag the 11.15 syntax — the text is the artifact).

**Notation:** `tf NN <type> Namespace.Entity` — types: `ui` / `cmd` (command) / `evt` (event)
/ `rmo` (read model) / `pcr` (processor). Swimlanes derive from each `Namespace` + type
combination. Relations between consecutive timeframes are inferred from sequence; `->>` marks
multi-source relations; `rf` (reset frame) breaks inference between slices.

---

<!-- ref:delegate-event-model -->
## Event vocabulary (status column is the freeze ladder)

Status values: **frozen** (wire format, changing it is a breaking change) · **freeze-at-P1**
(the P1 plan's freeze candidate set) · **draft-PN** (modeled now, promoted by phase N's plan).

### Envelope (freeze-at-P1 — this is what `run_status(since_offset)` actually depends on)

Every ledger line: `{offset, ts, event, payload}` — `run_id` is implicit in the file path
(`runs/<id>/events.jsonl`). Status is a fold over `event` names; unknown event names MUST be
tolerated by folds (forward compatibility — this is what lets draft events land later without
breaking P1 clients).

### Run-ledger events

| Event | Status | Emitted by | Notes |
|---|---|---|---|
| `RunSubmitted` | freeze-at-P1 | MCP surface | Spec persisted, run queued (FIFO position in payload) |
| `IntakeRejected` | freeze-at-P1 | Worker (intake) | Deterministic spec rejection; payload = which rule, terminal |
| `GenerationStarted` | freeze-at-P1 | Worker | Model + persona resolved; cold-start grace applied here |
| `GenerationFinished` | freeze-at-P1 | Worker | Payload: eval_count, duration (mirrors calls.jsonl fields) |
| `Delivered` | freeze-at-P1 | Worker (packaging) | Terminal; payload points at report + deliverable location |
| `Failed` | freeze-at-P1 | Worker (any stage) | Terminal; payload = where/whose/what triad |
| `Cancelled` | freeze-at-P1 | Worker (cooperative) | Terminal; checked between model calls |
| `AssemblyDone` | draft-P3 | Worker (assembly) | Prompt/context compile finished; P1 has trivial assembly and does NOT emit it |
| `IterationStarted` | draft-P2 | Worker (loop) | Payload: iteration k, budget remaining |
| `IterationEvaluated` | draft-P2 | Worker (loop) | Payload: validator results, failure class (mechanical/structural/conceptual), auto_verdict |
| `FreshStart` | draft-P2 | Worker (loop) | Repetition-signature trigger; payload: signature that fired |
| `ModelEscalated` | draft-P2 | Worker (loop) | Tier 1 → tier 2 ladder step |
| `Exhausted` | draft-P2 | Worker (loop) | Terminal-ish: budgets spent, best attempt attached (delivers degraded) |
| `JudgePassed` / `JudgeFailed` | draft-P4 | Worker (packaging) | Phase-2 rubric judge at packaging (cadence per V-D7) |
| `ApprovalRequested` | draft-P4 | Worker (post-assembly) | The approval gate (S14) → public state `input_required` |
| `QuestionRaised` | draft-P5 | Worker (any model stage) | Model `blocked` escape → `input_required` |
| `AnswerReceived` | draft-P5 | MCP surface (`answer_run`) | Resumes the run |

### Worker-ledger events (worker-level `events.jsonl`, not per-run — per-run ledgers do not grow after terminal state)

| Event | Status | Emitted by | Notes |
|---|---|---|---|
| `WorkerStarted` / `WorkerStopped` | freeze-at-P1 | Worker | Crash forensics anchor |
| `RetentionPruned` | freeze-at-P1 | Worker (retention pass) | V-D9 observability: what was removed, bytes freed, which policy fired. Silence = nothing pruned |

### Public state fold (MCP Tasks vocabulary, S6)

`queued → working → completed | failed | cancelled` (+ `input_required` from P4/P5 events).
Internal phase within `working` is also a fold: latest of intake/assembling/looping/packaging
markers. The fold, not the worker, owns state — there is no separately-tracked status field
to drift (first-principles #6).
<!-- /ref:delegate-event-model -->

---

## Slices (P1 — freeze candidates)

### Slice: submit → intake

```mermaid
eventmodeling

tf 01 ui Claude.SubmitRun
tf 02 cmd Mcp.SubmitRun
tf 03 evt Run.RunSubmitted
tf 04 pcr Worker.IntakeValidator
tf 05 evt Run.IntakeRejected
tf 06 rmo Ledger.RunStatus
```

Reading: Claude (the `ui` lane — the MCP client) issues `SubmitRun`; the MCP surface
validates shape and persists `RunSubmitted`; the worker's intake validator applies the
deterministic rejection rules (`ref:delegate-run-spec`); rejection is an event, acceptance is
silent — the accepted path is visible as `GenerationStarted` in the next slice. `RunStatus`
is the fold every `run_status` poll reads.

### Slice: generate → deliver (P1 has no loop — this is the whole middle)

```mermaid
eventmodeling

tf 07 pcr Worker.Generator
tf 08 evt Run.GenerationStarted
tf 09 evt Run.GenerationFinished
tf 10 pcr Worker.Packager
tf 11 evt Run.Delivered
tf 12 rmo Ledger.RunStatus
tf 13 rmo Ledger.RunResult
```

`RunResult` is the read model behind `run_result` — report + deliverable location; it stays
resolvable after workspace artifacts are pruned (V-D9).

### Slice: cancel (any non-terminal point)

```mermaid
eventmodeling

tf 14 ui Claude.CancelRun
tf 15 cmd Mcp.CancelRun
tf 16 evt Run.Cancelled
tf 17 rmo Ledger.RunStatus
```

Cooperative: the command sets a flag; the worker emits `Cancelled` at the next check between
model calls. The gap between command and event is real and visible in the ledger — by design.

### Slice: retention (worker ledger — V-D9)

```mermaid
eventmodeling

tf 18 pcr Worker.RetentionSweeper
tf 19 evt WorkerLog.RetentionPruned
tf 20 rmo Ledger.DiskReport
```

`DiskReport` backs `oficina runs` (per-run footprint, prune eligibility) and
`oficina prune --dry-run` (what would fire).

## Slices (P2 — draft, revise at P2 plan time)

### Slice: the evaluated loop

```mermaid
eventmodeling

tf 21 pcr Worker.Loop
tf 22 evt Run.IterationStarted
tf 23 pcr Worker.Evaluator
tf 24 evt Run.IterationEvaluated
tf 25 evt Run.FreshStart
tf 26 evt Run.Exhausted
tf 27 rmo Ledger.RunStatus
```

Draft semantics: `IterationEvaluated` carries the failure classification and auto-verdict;
repetition signature fires `FreshStart`; budget exhaustion emits `Exhausted` and then
`Delivered` (degraded, best attempt) — exhaustion is a *quality* of the delivery, not a
different terminal state (per `ref:delegate-state-machine`).

P3–P6 slices (assembly/context requests, judge + approval gate, question channel) are
vocabulary-only for now — see the table; model them as slices when their phase plan opens.

---

## Medium decision & alternatives record (research 2026-07-11, Sonnet agent)

**Pick: Mermaid `eventmodeling` (v11.15.0+), text-in-repo.** Only surveyed option scoring top
marks on all five criteria (git-diffable / AI-authorable / viewable / zero-infra / actual
event-modeling notation). Caveat: renderer lag — VS Code's bundled Mermaid was 11.12 at
decision time; render via `mmdc` (npx) or mermaid.live until it catches up.

**Runner-up: Excalidraw** — `.excalidraw` JSON in repo + community MCP server
(`yctimlin/mcp_excalidraw`, draw→screenshot→refine loop) + VS Code extension. Use IF a
freeform whiteboard session is ever genuinely needed (many branching policies, annotation-heavy
working sessions); complement, not replacement. Costs: noisy JSON diffs, no built-in notation.

**Miro: rejected** despite an official MCP server (shipped Feb 2026). A board is not a file —
fails git-versionability outright; user-heard complaints corroborated (seat/billing traps,
AI-credit metering).

**EventCatalog (event-catalog/eventcatalog): watch-item.** Markdown-native event *dictionary*
(per-event pages: schema, producers, consumers → static docs site; markets itself as docs "for
AI agents"). Wrong tool for the modeling timeline; plausibly the right tool for documenting
the frozen vocabulary once P1 ships. Revisit at P4 (delivery-report format) or first external
consumer.

**evml (lgazo/event-modeling-tools): watch-item.** Purpose-built event-modeling DSL with VS
Code/Obsidian plugins — exactly the right notation, but early-stage (13 stars, no releases);
too risky for a durable artifact today. Re-check if Mermaid's grammar proves cramped.

**D2 / PlantUML / Structurizr / tldraw / draw.io: rejected** — respectively: no swimlanes yet
(D2 #236); no event-model notation; wrong abstraction (C4); MCP-for-Claude rollout immature;
XML fussy for AI authoring with no notation gain.
