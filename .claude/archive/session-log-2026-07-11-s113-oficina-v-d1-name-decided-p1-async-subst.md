## 2026-07-11 - Session 113: oficina — V-D1 name decided, P1 async-substrate plan frozen (PR #73)

### Context

Continuation of session 112's Next list: merge PR #72, settle the coding-delegate name (V-D1), author the P1 plan (T-84 first half).

### What Was Done

- PR #72 merged (coding-delegate vision; the V-D1 decision commit rode in on the branch)
- docs(vision): V-D1 decided — system name **oficina**; guild-roles composition demoted to narrative; decision record + metaphor boundary rule in `naming.md`; all seven "name pending" pointers updated
- docs(delegate): event model artifact `docs/vision/coding-delegate/event-model.md` (`ref:delegate-event-model`) — Mermaid-native `eventmodeling` slices, envelope + freeze ladder, run-ledger vs worker-ledger split, medium-decision record
- docs(plans): oficina P1 plan authored, concurrency-model section added after user review, then FROZEN — `docs/plans/oficina-p1-async-substrate.md` (P1-D1–D11, run-spec subset, module tree, TDD T1–T10, 6-point acceptance)
- docs(delegate): folder QUICK synced; `ref:delegate-p1-concurrency` anchor added; 5 new ref keys verified resolving
- PR #73 opened (`feature/oficina-p1-plan`, 5 commits, docs-only)
- Three Sonnet research passes (not in commits): orchestration-lib survey (V-D11 — plain Python confirmed; DBOS-with-SQLite the one zero-infra contender, rejected as replace-not-underlie), event-modeling tooling (Mermaid `eventmodeling` picked; Miro rejected — board-not-a-file + corroborated billing complaints; EventCatalog/evml watch-items), Axon Framework 5 re-check (user request — trimmable but not right-sized; record in `decisions.md`)
- `calls.jsonl` readers (`ollama-stats.py`/`ollama-verdicts.py`) verified additive-safe for the new `run_id` field (all access via `dict.get`)

### Decisions Made

- **V-D1 = oficina** (runner-up aprendiz). Deciding correction (user): identity = the delegation harness; the flywheel is a *property*, not the objective — fine-tuning is the least certain part of the design. No `my-aprendiz-*` personas (would duplicate or flatten the per-language persona matrix); `journeyman` reserved for H2. Metaphor boundary rule: prose only — never code/schema/event/CLI-verb names. Folder + `delegate-*` ref keys keep the working label.
- **P1-D1–D11 frozen** — highlights: single-writer ledger with queue-push happens-before handoff (cancel = flag file; command→event gap visible by design); machine-global storage `~/.local/share/oficina/` (calls.jsonl precedent); event `offset` = line index; lazy-daemon worker (exit-when-empty, O_EXCL pidfile storing PID+start-timestamp against PID reuse); CLI `oficina submit|status|result|cancel|watch|runs|prune`; retention = config section + `RetentionPruned` event + `prune --dry-run`.
- **IntakeAccepted stays silent** (acceptance visible as `GenerationStarted`); revisit trigger: a fold consumer needing to distinguish "accepted, waiting for GPU" from "queued".
- Event vocabulary: freeze-at-P1 subset binding; P2–P6 names modeled as draft in the event-model artifact (churn happens there, not on the wire); folds must tolerate unknown event names.

### Next

- **Merge PR #73** (docs-only: plan + event model + naming aftermath).
- **BUILD oficina P1 (T-84 second half):** T1–T10 from the frozen plan, fresh session reading the plan cold (doubles as the plan-completeness test). Suggested split: T1–T5 (ledger/ids+store/intake/fifo/workerproc), then T6–T10 (worker/MCP wiring/CLI/retention/live acceptance).

### Gotchas

- Mermaid's `eventmodeling` diagram needs v11.15+; VS Code's bundled renderer is 11.12 — the markdown source is the artifact, render SVG via `npx -y @mermaid-js/mermaid-cli` when it stabilizes. Relations are INFERRED from timeframe sequence (explicit `->>` only for multi-source); swimlanes come from `Namespace.Entity` — the subagent's sketch had explicit arrow lines, the official syntax page corrected it.
- `gh pr merge` is blocked by the permission classifier even when the user approved via an earlier option choice — the user merges themselves (`! gh pr merge …`) or re-approves with an explicit fresh instruction.
- Axon 5 (5.1.0+) split OSS Axon Framework from commercial Axoniq Framework — the "event architecture for AI" push lives on the commercial/Axon Server side; the embedded OSS path excludes exactly that layer.
