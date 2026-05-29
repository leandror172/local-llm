# Continuation Prompt — LTG Phase 2 Implementation

> **STATUS: COMPLETE (2026-05-28, session 72).** All 9 tasks done. Branch `feature/ltg-phase2-implementation` awaiting PR → master. See `ref:ltg-phase2-findings` for results. Next: Phase 3 anchor integration.

~~You are continuing work started in prior sessions. Tasks 1–6 of 9 done. Your job is Tasks 7–9.~~

**Branch:** `feature/ltg-phase2-implementation` (off `master`). Verify with `rtk git status` first.

---

## Session startup sequence — follow in order, do not skip

> **GATE: do not call any tool that writes, edits, or generates code until every step
> below is complete. Reading and `rtk git` commands are the only permitted actions until Step 7.**

**Step 1 — Confirm branch**
`rtk git status` + `rtk git log --oneline -5`. Branch must be `feature/ltg-phase2-implementation`
with the 4 session-71 commits visible.

**Step 2 — Read Tier 1** (exact files in "Read in this order" → Tier 1 below)
`.memories/QUICK.md` · `retrieval/.memories/QUICK.md` · `.claude/overlays/local-model-conventions.md`

**Step 3 — Read Tier 2** (exact line ranges in "Read in this order" → Tier 2 below)
`docs/plans/ltg-phase2-implementation-v2.md` (5 sections) · `docs/ideas/ltg-model-registry-design.md` (2 sections)

**Step 4 — Read Tier 3** (exact ref blocks in "Read in this order" → Tier 3 below)
`retrieval/DECISIONS.md` (3 ref blocks) · `retrieval/.memories/KNOWLEDGE.md` (2 ref blocks)

**Step 5 — Read Tier 4** (exact ranges in "Read in this order" → Tier 4 below)
`retrieval/embed.py` · `retrieval/store.py` · `retrieval/tests/test_embed.py`

**Step 6 — Check task list**
Run `TaskList`. If tasks exist → mark Task 7 `in_progress` and continue to Step 7.
If empty → recreate using the "Task recreation" section before continuing.

**Step 7 — Report and wait**
Summarise in 3–5 bullet points what you learned from the reading (one line each: a key constraint,
frozen decision, or open question that shapes inspect.py). Then send a `PushNotification` with
headline "Orientation complete — ready for Task 7" and **wait for the user to confirm before
warming the model or writing any code.**

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
   - Lines 393-469 (Script 3: inspect.py — your next task)
   - Lines 567-606 (Expanded Acceptance Tests)
   - Lines 686-697 (Index and Memory Updates — post-completion checklist)
5. **`docs/ideas/ltg-model-registry-design.md`** — model_client.py interface contract. Lines 84-105 (load_config + ModelClient interface) and 121-138 (Phase 2 Interim — matches the config.yaml that's already written).

### Tier 3 — frozen decisions
6. **`retrieval/DECISIONS.md`** — read three ref blocks:
   - `ref:ltg-embedding` (lines ~22-44) — bge-m3 + VRAM probe outcome
   - `ref:ltg-vector-store` (lines ~48-58) — LanceDB rationale
   - `ref:ltg-storage-layout` (lines ~124-147) — schema conventions
7. **`retrieval/.memories/KNOWLEDGE.md`** — `ref:ltg-vram-probe` (lines 8-55) for sequential constraint mechanism; `ref:ltg-phase1-summary` (lines 59-103) for extractor routing.

### Tier 4 — existing implementations (mirror their style)
8. **`retrieval/embed.py`** — lines 1-40 (imports + constants) + lines 95-116 (build_output_row — the 16-field dict that inspect.py will read back). Mirror style.
9. **`retrieval/store.py`** — lines 1-65 (SCHEMA definition). inspect.py must match these field names exactly.
10. **`retrieval/tests/test_embed.py`** — full file. Style reference for writing test_inspect.py.

### Tier 5 — on demand only
11. **`.claude/session-context.md`** lines 46-79 (current-status block) — only if you need session history.
12. **`.claude/tasks.md`** lines 62-72 (LTG Phase 2 tasks) — only if updating tasks.md at the end.
13. **`.claude/index.md`** lines 116-178 (`ref:bash-wrappers`) — only when adding `run-inspect.sh` post-completion.
14. **`docs/research/latent-topic-graph.md`** — concept paper, full. Only if you find yourself asking "why are topics not files?"

**Don't read v1** (`docs/plans/ltg-phase2-implementation.md`). v2 is a strict superset.

---

## What's done

- **Branch created:** `feature/ltg-phase2-implementation` off master.
- **Deps installed:** httpx 0.28.1 (pre-existing), **lancedb 0.25.0** (pinned; 0.29.x is broken), pyarrow 24.0.0.
- **`.gitignore` updated:** `retrieval/index/`, `retrieval/index.bak/`, `retrieval/embeddings.jsonl` added.
- **`retrieval/config.yaml` written** (flat shape, embedding role, bge-m3 dim 1024).
- **Task 3 — `retrieval/model_client.py`:** `load_config()` + `ModelClient` (embed_dim, embed_texts). 13 tests green. Commit `db6ec0b`.
- **Task 4 — `retrieval/preflight.sh` + `run-preflight.sh`:** 5 checks pass (deps, Ollama, bge-m3, JSONL, disk). Commit `db6ec0b`.
- **Task 5 — `retrieval/embed.py` + `run-embed.sh`:** Reads Phase 1 JSONL, routes by extension, batches embed via bge-m3, writes 16-field embedding JSONL. Sequential constraint header comment included. 23 tests green. Commit `7ecd148`.
- **Task 6 — `retrieval/store.py` + `run-store.sh`:** 16-field PyArrow SCHEMA, load/convert/backup/write/validate pipeline. 11 tests green. Commit `58af787`.
- **Claude Code task list:** Tasks 3–9 were created in a prior session but task state does not always survive restarts. Run `TaskList` at Step 6 — if empty, see "Task recreation" below.

---

## Remaining tasks (7 → 9)

Mark Task 7 `in_progress` before writing any code. If `TaskList` was empty at Step 6, create the three tasks now:

**Task recreation** (only if TaskList returned empty):
- Task 7: subject="Write retrieval/inspect.py (5 modes) — TDD + Ollama" — mark `in_progress` immediately
- Task 8: subject="Run acceptance: embed → store → inspect --acceptance, verify <5s" — blocked by Task 7
- Task 9: subject="Post-completion doc updates: DECISIONS / .memories / index / tasks" — blocked by Task 8

| # | Subject | TDD? | Ollama? |
|---|---------|------|---------|
| 7 | `retrieval/inspect.py` (5 modes: --query / --list / --stats / --relate / --acceptance) | yes | yes |
| 8 | Run acceptance: 4 recall + 2 negative + 1 relate-preview | n/a | n/a |
| 9 | Post-completion: update DECISIONS / .memories / session-context / index / tasks | n/a | n/a |

For the spec, see Tier 2 plan sections above.

---

> **⚠ TIMEOUT PROTOCOL — read before any Ollama call**
>
> - A timeout is **not a verdict**. Do not count timeouts toward the 3–4 attempt budget.
> - Escalate only on explicit `0` (rejected) verdicts.
> - **First call after model switch** → label `TIMEOUT_COLD_START`, retry once (model was loading).
> - **Warm model times out** → prompt + context is too large. Split: generate helpers first, then main(). Do not retry the same large prompt.
> - **Still timing out after split** → escalate to tier 2 (`my-python-q3-14b` = qwen3:14b).
> - **Writing the code yourself is a last resort**, only after 3–4 explicit `0` verdicts, not timeouts.

## How to do TDD + Ollama (per `ref:local-model-conventions`)

**For Task 7 (implementation):**

1. **Tests first — delegate to Ollama too.** Write `retrieval/tests/test_inspect.py` by calling `generate_code` with a behavioral prompt describing what each test must verify. Run; confirm red. (Session 71 user feedback: test files should also go to Ollama, not just implementations.)
2. **Warm the model** at session start: `warm_model('qwen2.5-coder:14b')`.
3. **Delegate implementation** via `mcp__ollama-bridge__generate_code`:
   - Persona: `my-python-q25c14` (qwen2.5-coder:14b).
   - `context_files`: test file + `retrieval/store.py` (for SCHEMA field names) + `retrieval/embed.py` (lines 1-40 for style) + `retrieval/model_client.py`.
   - **Behavioral prompt only** — describe what the code must do, not how. Do NOT send code stubs or function signatures with inline comments. Stubs = you wrote the code and the model transcribed it.
   - Include CONSTRAINTS block:
     ```
     CONSTRAINTS (apply to all generated code):
     - Each function has exactly one responsibility — if its name would need "and", split it
     - Name functions after what they return or do (no process_data, no handle_X)
     - Function bodies read as delegated steps: call named helpers, combine, return
     - Max ~15 lines per function body; extract longer logic into named helpers
     ```
   - Add to every httpx prompt: "use `httpx.post(url, json=payload, timeout=120.0)` — NOT async, NOT `await`, NOT `httpx.Client`"
4. **Verdict every call.** `2` accepted / `1` improved / `0` rejected, with rough token estimate `(prompt chars + response chars) / 4`.
5. **On `0`:** improve the prompt OR escalate to tier 2 (`my-python-q3-14b` = qwen3:14b). Budget 3-4 attempts before writing it yourself.
6. **Tests green** → task done.

---

## Per-task gate

After each task completes:

1. `TaskUpdate` status=completed.
2. Send `PushNotification` with a one-line status (under 200 chars) + the next task's headline.
3. **Wait for user to confirm before starting the next task.** Do not chain through tasks autonomously.

---

## Considerations (all sessions)

1. **v2 plan + session 70 additions = authoritative.** The v2 plan covers schema/scripts/probes; session 70 added `model_client.py` + `config.yaml` + Option B embed_dim validation. Both together, not either alone.
2. **Sequential constraint is policy, not mechanism.** Header comment in `embed.py` is enough. Cite `ref:ltg-vram-probe`.
3. **Vector field name `"vector"` (not `"embedding"`).** LanceDB's default ANN builder convention.
4. **`spans` and `scope_tags` are JSON-encoded strings**, not nested struct types.
5. **Forward-compat fields** (`node_kind`, `scope_tags`, `segment_id`, `segment_range`) written with defaults in Phase 2. Already in store.py SCHEMA.
6. **bge-m3 unit-norm assumption:** verify on first embed run (`np.linalg.norm(vector) ≈ 1.0`). The relate-preview's cosine math depends on it.
7. **Don't re-litigate frozen decisions.** qwen3-embedding:8b is M-P0b — after Phase 2, not before.
8. **Probes and run-logs are committed evidence.** Index + embeddings.jsonl are not (.gitignored).
9. **AskUserQuestion has a rendering bug** — ask clarifications in plain text instead.
10. **LanceTable API:** `.column("field")` does not exist. Use `.to_arrow().column("field").to_pylist()`. `table.count_rows()` works directly.
11. **httpx async slip:** qwen2.5-coder generates `async def`/`await httpx.post()` even in sync contexts. Always write "use `httpx.post()` — NOT async" in the prompt. Two-site fix if it slips through.
12. **Large prompt timeouts are real, not cold-start:** If model is warm but times out, the context is too large. Split into: (a) helper functions call, (b) main() call. Don't keep retrying the same large prompt.
13. **Behavioral prompts only:** do NOT send code stubs or pseudocode to Ollama. Describe behavior, constraints, and the interface — let the model write the code. Stubs defeat the purpose of delegation and produce transcription, not generation.

---

> See **"Session startup sequence"** at the top of this file. Follow it in order.
