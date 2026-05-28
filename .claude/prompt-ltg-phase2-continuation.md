# Continuation Prompt — LTG Phase 2 Implementation

You are continuing work started in a prior Opus session. Branch is checked out, deps installed, Tasks 1-2 of 9 done. Your job is Tasks 3-9.

**Branch:** `feature/ltg-phase2-implementation` (off `master`). Verify with `rtk git status` first.

---

## Read in this order (don't skip; don't expand)

Each entry: file, why, exact lines (or "full").

### Tier 1 — orientation (read fully)
1. **`.memories/QUICK.md`** — repo status. ~50 lines, full.
2. **`retrieval/.memories/QUICK.md`** — LTG status + sequential constraint. ~50 lines, full.
3. **`.claude/overlays/local-model-conventions.md`** — Ollama discipline (verdicts, TDD, retry budget, cold-start, persona switching). Full file. Also reachable via `.claude/tools/ref-lookup.sh local-model-conventions`.

### Tier 2 — authoritative plan
4. **`docs/plans/ltg-phase2-implementation-v2.md`** — **this is the plan**. Read these sections:
   - Lines 33-49 (Architectural Context)
   - Lines 84-99 (Decisions In Force)
   - Lines 136-194 (Revised LanceDB Schema — 16 fields)
   - Lines 213-337 (Script 1: embed.py)
   - Lines 340-389 (Script 2: store.py)
   - Lines 393-469 (Script 3: inspect.py)
   - Lines 472-563 (Bash wrappers + preflight.sh)
   - Lines 567-606 (Expanded Acceptance Tests)
   - Lines 686-697 (Index and Memory Updates — post-completion checklist)
5. **`docs/ideas/ltg-model-registry-design.md`** — model_client.py interface contract. Lines 84-105 (load_config + ModelClient interface) and 121-138 (Phase 2 Interim — matches the config.yaml that's already written).

### Tier 3 — frozen decisions
6. **`retrieval/DECISIONS.md`** — read three ref blocks:
   - `ref:ltg-embedding` (lines ~22-44) — bge-m3 + VRAM probe outcome
   - `ref:ltg-vector-store` (lines ~48-58) — LanceDB rationale
   - `ref:ltg-storage-layout` (lines ~124-147) — schema conventions
7. **`retrieval/.memories/KNOWLEDGE.md`** — `ref:ltg-vram-probe` (lines 8-55) for sequential constraint mechanism; `ref:ltg-phase1-summary` (lines 59-103) for extractor routing.

### Tier 4 — patterns / data shape
8. **`retrieval/extract_topics.py`** — full file. The Phase 1 script that produced our input JSONL; matches our standalone-script + bash-wrapper + httpx convention. Mirror its style.
9. **`retrieval/runs/20260416-181839.jsonl`** — first 3 lines only (large file). Confirms actual row shape — `raw_response` is a JSON string you parse, not a dict.

### Tier 5 — on demand only
10. **`.claude/session-context.md`** lines 46-79 (current-status block) — only if you need session history context.
11. **`.claude/tasks.md`** lines 62-72 (LTG Phase 2 task + adjacent deferreds) — only if updating tasks.md at the end.
12. **`.claude/index.md`** lines 116-178 (`ref:bash-wrappers`) — only when adding the 4 new wrappers post-completion.
13. **`docs/research/latent-topic-graph.md`** — concept paper, full. Only if you find yourself asking "why are topics not files?" — `node_kind` / `scope_tags` / files-as-containers all justified here.

**Don't read v1** (`docs/plans/ltg-phase2-implementation.md`). v2 is a strict superset.

---

## What's done

- **Branch created:** `feature/ltg-phase2-implementation` off master.
- **Deps installed:** httpx 0.28.1 (pre-existing), **lancedb 0.25.0** (pinned in plan; 0.29.x is broken), pyarrow 24.0.0.
- **`.gitignore` updated:** `retrieval/index/`, `retrieval/index.bak/`, `retrieval/embeddings.jsonl` added; probes + run logs stay tracked.
- **`retrieval/config.yaml` written** (flat shape, embedding role, bge-m3 dim 1024, comment documents upgrade trigger).
- **v2 plan pin tightened** to `>=0.20,<0.29` in 3 places (Decisions table, install hint, preflight script literal). Rationale in the Decisions table cell.
- **`.memories/QUICK.md`** fix: prior note said "Use qwen3-embedding:8b" — wrong; **Phase 2 uses bge-m3**, qwen3-embedding:8b probe deferred to M-P0b (after Phase 2). The plan + tasks.md were always correct; only QUICK.md was stale. Now consistent.
- **Commit:** `feature/ltg-phase2-implementation` HEAD is the bootstrap commit.

---

## Remaining tasks (3 → 9)

Recreate this as a Claude Code task list (`TaskCreate` × 7) at the start of your session. Set dependencies: 3 blocked by 2 (done); 4 blocked by 1 (done); 5 blocked by 3+4; 6 by 5; 7 by 6; 8 by 7; 9 by 8.

| # | Subject | TDD? | Ollama? |
|---|---------|------|---------|
| 3 | `retrieval/model_client.py` isolation layer | yes | yes |
| 4 | `retrieval/preflight.sh` + `run-preflight.sh` | no (manual run) | yes |
| 5 | `retrieval/embed.py` (v2 schema, batched, --embed-mode flag) | yes | yes |
| 6 | `retrieval/store.py` (auto-backup, mode='overwrite' only) | yes | yes |
| 7 | `retrieval/inspect.py` (5 modes: --query / --list / --stats / --relate / --acceptance) | yes | yes |
| 8 | Run acceptance: 4 recall + 2 negative + 1 relate-preview | n/a | n/a |
| 9 | Post-completion: update DECISIONS / .memories / session-context / index / tasks | n/a | n/a |

For each detailed spec, see the v2 plan sections in the reading list.

---

## How to do TDD + Ollama (per `ref:local-model-conventions`)

**For every implementation task (3, 5, 6, 7):**

1. **Tests first.** Write `retrieval/tests/test_*.py` covering each spec'd behavior + edge case. Run; confirm red.
2. **Warm the model** at session start (only once per base model): `warm_model('qwen2.5-coder:14b')`. Don't re-warm when switching between same-base personas — that evicts the model you're about to use.
3. **Delegate to Ollama** via `mcp__ollama-bridge__generate_code`:
   - Persona: `my-python-q25c14` (qwen2.5-coder:14b).
   - `context_files`: test file path + the relevant existing files (e.g., for `embed.py`: tests, `model_client.py`, `config.yaml`, fixture JSONL, `pyproject.toml`).
   - **Behavioral prompt** — describe what the code must do, not how. Include this CONSTRAINTS block:
     ```
     CONSTRAINTS (apply to all generated code):
     - Each function has exactly one responsibility — if its name would need "and", split it
     - Name functions after what they return or do (no process_data, no handle_X)
     - Function bodies read as delegated steps: call named helpers, combine, return
     - Max ~15 lines per function body; extract longer logic into named helpers
     ```
4. **Verdict every call.** `2` accepted / `1` improved / `0` rejected, with rough token estimate `(prompt chars + response chars) / 4`.
5. **On `0`:** improve the prompt OR escalate to tier 2 (`my-python-q3-14b` = qwen3:14b) — NOT straight to Claude. Budget 3-4 attempts before writing it yourself.
6. **Cold-start timeout** (first call to a model in session) ≠ verdict. Label `TIMEOUT_COLD_START` and retry once.
7. **Tests green** → task done.

**Task 4 (preflight.sh)** is bash; no pytest. Acceptance = run the script, all 5 checks print "ok", exit 0. Still delegate to Ollama, still verdict the output.

---

## Per-task gate

After each task completes:

1. `TaskUpdate` status=completed.
2. Send `PushNotification` with a one-line status (under 200 chars) + the next task's headline.
3. **Wait for user to confirm before starting the next task.** Do not chain through tasks autonomously.

Example:
```
PushNotification: "LTG Phase 2 Task 3/9 done: model_client.py — 12 tests green, my-python-q25c14 verdict 2 (~1100 tok saved). Proceed to Task 4 (preflight.sh)?"
```

If notification suppressed (user active), still ask in plain text after.

---

## Considerations from the prior session

1. **v2 plan + session 70 additions = authoritative.** The v2 plan covers schema/scripts/probes; session 70 added `model_client.py` + `config.yaml` + Option B embed_dim validation. Both together, not either alone.
2. **Sequential constraint is policy, not mechanism.** A header comment in `embed.py` is enough — don't build locking. Cite `ref:ltg-vram-probe`.
3. **Vector field name `"vector"` (not `"embedding"`).** LanceDB's default ANN builder convention.
4. **`spans` and `scope_tags` are JSON-encoded strings**, not nested struct types. Flatness aids LanceDB filter pushdown. (v2 plan §"A non-obvious schema decision".)
5. **Forward-compat fields (`node_kind`, `scope_tags`, `segment_id`, `segment_range`)** must be written by Phase 2 with defaults (`"extracted"`, `"[]"`, `null`, `null`). Adding columns later is supported by LanceDB; making a null column non-null later is not.
6. **bge-m3 unit-norm assumption:** verify on first embed run (`np.linalg.norm(vector) ≈ 1.0`). If not, normalize in `embed.py` before writing — the relate-preview's cosine math depends on it.
7. **Don't re-litigate frozen decisions.** If you find yourself wanting to (e.g., "should we switch to qwen3-embedding:8b now?") — read M-P0b in `tasks.md`. The answer is no until after Phase 2 acceptance passes.
8. **Probes and run-logs are committed evidence** (small markdown + JSONL). Index + embeddings.jsonl are not (.gitignored). Match the v2 plan's `.gitignore` discipline.
9. **AskUserQuestion has a rendering bug** — don't use it for clarifications. Ask in plain text instead.

---

## First actions in your session

1. `rtk git status` + `rtk git log --oneline -3` — confirm branch + bootstrap commit.
2. Tier-1 reading (3 files, ~120 lines total).
3. Tier-2 plan sections (lines listed above).
4. `TaskCreate × 7` for Tasks 3-9 with dependencies wired.
5. Mark Task 3 in_progress; start TDD cycle for `model_client.py`.

Good luck. The schema is the only irreversible commitment in Phase 2 — get the 16 fields right and everything downstream is mechanical.
