# Verdict capture repair — plan

**Session 125 · 2026-07-21 · PLAN, not executed**
Findings + evidence: `docs/findings/verdict-coverage-collapse-2026-07-21.md`

---

## Context

Local-model verdicts (0/1/2) are the raw material for Layer-7 distillation. Coverage is
**9.9 %** (56/564). Investigation found the capture harness works correctly but was never fed:
every durable document teaches an inline phrase (`2 — ~300 est. Claude tokens saved`) while the
capture regex accepts only a `[VERDICT prompt_hash=…]` block taught **nowhere durable**.

**Honest scope:** the documentation defect explains the ~49 judgments that were *made and
discarded*. It does not explain the **81.4 % of calls where no judgment was ever made**. This
plan fixes the discard path and makes the residue *measurable*; it deliberately does **not**
add enforcement yet.

### Decisions carried in

| # | Decision | Rationale |
|---|---|---|
| V-D1 | **Judgeable = `generate_code` + oficina run deliverables** | The calls whose output is reviewed anyway. Excludes summarize/translate/classify, warm-ups, sweeps. |
| V-D2 | **Different granularity per source** | `generate_code` → per-call. oficina → **per-run** on the finished deliverable (`run_result`), never per loop iteration. |
| V-D3 | **Measure first, gate later** | PostToolUse can't block; a `Stop` block forces continuation → forced ≠ considered verdicts. Revisit only if the docs fix fails to move coverage. |
| V-D4 | **Real identity key, not a patched hash** | `prompt_hash` is content-addressing reused as identity (1 hash = 24 calls / 8 models). |
| V-D5 | **Docs converge on the block; no tolerant reader live** | A tolerant reader can't recover `prompt_hash` from prose. Positional association is acceptable for the one-off back-fill only. |

---

## Phase 0 — Verify the harness contract (blocking prerequisite)

The `Stop`/PostToolUse schema details came from a delegated doc summary that got `tool_output`
wrong (`oficina-watch-hook.py:31` reads `tool_response` and demonstrably works). **Do not build
on unverified schema.**

- Add a temporary throwaway hook that dumps its stdin JSON to the scratchpad for `PostToolUse`
  and `Stop`; trigger one `generate_code` call; inspect.
- Confirm: exact field name for the tool result, presence of `last_assistant_message` on `Stop`,
  and whether user-level + project-level hooks on the same event **both** fire (empirically they
  do — the verdict hooks are user-level while project-level PostToolUse hooks also run).
- **Acceptance:** a recorded sample of each payload in
  `scratchpad/hook-payloads/{posttooluse,stop}.json`. Remove the probe hook afterwards.

### Phase 0 RESULTS (executed 2026-07-21) — three corrections

| Finding | Consequence |
|---|---|
| **`tool_response` is the field; `tool_output` is ABSENT.** The delegated doc summary was wrong. | Phase 1 must read `tool_response` (a JSON string `{"result": …}`). Had the summary been trusted, the new hook would have silently never matched. |
| **`tool_use_id` exists** in the PostToolUse payload — a harness-side unique per-call id. | Weigh against the planned server-side `call_id`; the join still needs a server field, but this may simplify hook-side association. |
| **`last_assistant_message` exists but is the FINAL message only.** | The transcript scan **must stay** — see Phase 1. |

Other captured facts: `Stop` keys = `background_tasks, cwd, effort, hook_event_name,
last_assistant_message, permission_mode, prompt_id, session_crons, session_id,
stop_hook_active, transcript_path`. `SubagentStop` adds `agent_id, agent_transcript_path,
agent_type` — but **`agent_type` came through as an empty string**, so agent-type matchers
should not be relied on without re-probing. Verdict capture verified live (56→57), and a
`reason` containing a literal `[/VERDICT]` parsed correctly.

**Regex constraint for Phase 1:** the pattern requires `([a-f0-9]+)`, so any `call_id` must be
lowercase hex (no dashes, no uppercase) or the regex changes in the same commit.

---

## Phase 1 — Call identity (fixes D4 + D5 + D10)

**One architectural change, not three patches.**

`mcp-server/src/ollama_mcp/client.py:312-333` (`_log_call`) — add two fields:

- `call_id`: unique per call (uuid4 hex, 12 chars is enough)
- `tool`: the originating tool name (`generate_code`, `ask_ollama`, …) or `oficina` for
  `run_id`-bearing calls

`tool` must be threaded from `server.py`'s tool functions into `client.chat(...)`; `run_id`
already threads this way, so follow that exact seam (`client.py:268`).

Then `.claude/hooks/ollama-post-tool.py`:
- Stop guessing. Replace the log-tail read (`:43-47`) with **association by returned content** —
  match the hook's tool result against the `response` field (97.5 % unique: 547/563 distinct).
  Fall back to log-tail only if no match.
- Emit `call_id` in the template instead of `prompt_hash`.
- Narrow `GENERATION_TOOLS` (`:26-34`) to the judgeable set (V-D1).

`.claude/hooks/verdict-capture.py`:
- Key verdicts on `call_id`; dedupe on `call_id` (`:104`), not `prompt_hash`.
- Keep writing `prompt_hash` too, for joinability with historical records.
- ~~Optional simplification: replace the whole-transcript re-parse at `:58` with
  `last_assistant_message`.~~ **REJECTED — Phase 0 disproved it (2026-07-21).** The field
  exists on both `Stop` and `SubagentStop`, but it holds only the turn's **final** message.
  Verdict blocks are routinely emitted **mid-turn**, before further tool calls: this session's
  own `067bd6abb296` verdict was emitted, followed by two more tool calls, and was still
  captured *because* the hook scans the full transcript. Switching to `last_assistant_message`
  would silently drop every mid-turn verdict. **Keep the transcript scan.**

**Acceptance:** a fresh `generate_code` call produces a verdict record carrying a `call_id` that
resolves to exactly one call record. A repeated *identical* prompt produces two independently
verdictable records (the 24-call-sweep failure no longer possible).

---

## Phase 2 — Reconcile the format contract (the root cause)

Make the durable docs teach what the harness parses. Edit in place:

| File | Line | Change |
|---|---|---|
| `CLAUDE.md` | 108-111 | Replace the inline-phrase instruction with the `[VERDICT …]` block; keep the chars/4 estimate rule |
| `docs/scaffolding-template.md` | 158-161 | Same |
| `overlays/ollama-scaffolding/files/local-model-conventions.md` | 144-151 | Same (overlay **source**) |
| `.claude/overlays/local-model-conventions.md` | 150 | `cp` from the overlay source — currently byte-identical, keep it so |
| `.claude/archive/handoff-session-66.md` | 136 | Correct the false claim *"Hooks expect this format"* or mark the file historical |
| `docs/plans/verdict-numeric-migration.md` | 38-41, 230 | Annotate: § "Chat-text grammar (no change needed)" was the miss; Phase 5.1 entrenched the competing form |
| `.claude/agents/impl-opus.md`, `impl-opus-med.md` | 17-19 | They defer to the inline doc — inherit the fix automatically once the overlay doc is corrected; verify |

Then reinstall the `ollama-scaffolding` overlay to the 3 downstream repos (`expenses`,
`web-research`, `career-search`).

**Acceptance:** `grep -rn "Note it inline in one phrase"` returns nothing outside archives; a
fresh session reading only CLAUDE.md emits a parseable block.

---

## Phase 3 — Back-fill the 49 (only after Phase 1)

Source: `scratchpad/recoverable-verdicts.json` (49 entries with `prompt_hash`, `model`,
`call_ts`, `matched_phrase`, ±200 chars context, source transcript).

- Associate positionally (nearest preceding generation call in the same transcript) — this is
  the one place a tolerant reader is acceptable (V-D5).
- **Skip any candidate whose `prompt_hash` is shared by more than one call** — attribution is
  ambiguous there and a wrong label is worse than a missing one.
- Mark each back-filled record with a provenance flag (e.g. `"source": "backfill-2026-07-21"`)
  so the corpus can distinguish live captures from reconstructions.
- Back up `calls.jsonl` first (precedent: `calls.jsonl.bak-verdict-migration-20260516`).

**Acceptance:** coverage rises to ~18 %; every back-filled record resolves to exactly one call;
the backup restores cleanly.

---

## Phase 4 — Oficina run verdicts (D8)

Per V-D2, judge the **deliverable**, not the iterations.

- Add `mcp__ollama-bridge__run_result` to the watched set, or a dedicated hook alongside
  `oficina-watch-hook.py`.
- The verdict keys on `run_id` (already in the log, `client.py:336-338`), not per-call.
- Reuse the existing block template; the payload identifies the run.

**Acceptance:** completing an oficina run and calling `run_result` prompts once, and the
captured verdict joins to the run's calls via `run_id`.

### Phase 4 scouting (2026-07-21) — one blocker, one simplification

**BLOCKER — `run_id` is not hex, so the current regex rejects it.** The capture group is
`([a-f0-9]+)`; real run ids are base64url-shaped (`-L-rwoCLLsoL33eirtSRzw`,
`8gXFFyziyzG-uZLs8eycJg`) — mixed case, `-`, `_`. A `[VERDICT run_id=…]` block would silently
fail to parse, reproducing the exact class of bug this whole effort is fixing. **The character
class must widen to `[A-Za-z0-9_-]+` in the same commit that introduces run-keyed blocks**, with
a test using a real run id. (`re.IGNORECASE` already admits `A-F`; it does not help here.)

**SIMPLIFICATION — identity needs no content matching.** `run_result(run_id: str)`
(`server.py:1544`) takes the id as an explicit argument, so the hook reads
`tool_input["run_id"]` directly. This is strictly more reliable than the `generate_code` path,
which must match on returned content.

**Granularity is a real reduction:** 18 oficina-tagged calls span 12 runs (up to 3 calls each),
so per-run judging asks for ~12 verdicts instead of 18, and asks about the thing actually
reviewed.

**Do NOT conflate with `auto_verdict`.** `loop.py:157` already records
`auto_verdict = 2 if passed else 0` into the ledger (T-99: ledger-only; the P4 DPO pass joins
ledger↔`calls.jsonl` on `run_id`). That signal is **binary and mechanical** — "did the
evaluator's tests pass". It structurally cannot express **1 (improved)**: *correct, but I had to
change it* — historically 64.8% of all verdicts and the richest DPO category. The session
verdict is a different axis and adds what `auto_verdict` cannot.

**Open decisions:**
1. Should non-`Delivered` terminal states (Failed / Exhausted) be prompted for a verdict, or is
   `auto_verdict = 0` already sufficient there? Leaning: prompt only when a deliverable exists.
2. `run_result` may be polled more than once — dedupe on `run_id` covers it, but confirm the
   hook does not prompt on the not-terminal-yet error path (`server.py:1562`).
3. Verdict records would gain a `run_id` key alongside `call_id`/`prompt_hash`; readers
   (`ollama-stats.py`, `ollama-verdicts.py`) must tolerate the heterogeneous key.

---

## Phase 5 — Tests (D7)

`.claude/hooks/tests/` currently covers both oficina hooks and **nothing** here. The new tests
must assert the **producer→consumer seam**, not the parser alone — the original Phase-1 proof
used a synthetic block (`verdict-numeric-migration.md:80`) and that is exactly why this went
unseen for five months.

Minimum cases:
1. Injected template text is *parseable by the capture regex when filled* (round-trip, not a
   hand-authored fixture).
2. `call_id` association: two identical prompts → two distinct verdictable records.
3. Content-match provenance picks the right record when the log tail is a different call.
4. Non-judgeable tools produce no template.
5. Dedupe does not suppress a legitimate second verdict.

Note the testing gotcha already documented (`verdict-numeric-migration.md:435-445`):
`CALLS_LOG` is a hardcoded `Path.home()/…` constant with no env override — isolate with
`HOME=$(mktemp -d)`.

---

## Phase 6 — Measure, then decide on enforcement

After Phases 1–5 have been live for a realistic working period:

- Report coverage **among judgeable calls only** (now possible via the `tool` field).
- If it recovers → done; the docs were the whole discard story.
- If it stays low → the residue is behavioural, and the `Stop`-gate decision (D6) returns with
  real evidence behind it. Design constraints already established: `decision:"block"` +
  `hookSpecificOutput.additionalContext`, `stop_hook_active` guard, 8-block cap
  (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`), scoped to judgeable calls only.

---

## Phase 7 — Retention (D9, independent, do early)

`cleanupPeriodDays` defaults to 30 and deletes at startup; transcripts are the only audit trail
for this class of defect. Raising it (e.g. 365) is documented as supported. Subagent transcripts
under `/tmp/claude-1000/.../tasks/` are wiped on reboot and unrecoverable regardless.

**Do this before Phase 3** — the 49-verdict recoverable set decays with every session start.

---

## Sequencing

```
Phase 7 (retention)  ─┐  do first, cheap, stops the bleed
Phase 0 (verify)     ─┘
        ↓
Phase 1 (call_id + tool + provenance)      <- unblocks back-fill
        ↓
Phase 2 (docs)  ──── the root cause
        ↓
Phase 3 (back-fill)  <- MUST follow Phase 1
        ↓
Phase 4 (oficina)  ·  Phase 5 (tests)
        ↓
Phase 6 (measure → gate decision)
```

## Risks

| Risk | Mitigation |
|---|---|
| Back-fill bakes in mislabeled pairs | Phase 1 first; skip ambiguous hashes; provenance flag; backup |
| Schema assumptions wrong | Phase 0 empirical probe before any hook edit |
| Overlay reinstall breaks 3 downstream repos | Overlay has its own test suite (`make -C overlays test`); reinstall one repo first |
| Docs fix alone judged "the fix" | Phase 6 measures explicitly; the 81.4 % residue is stated up front |

## Housekeeping

Per CLAUDE.md hard requirement *"New files of any kind — add to `.claude/index.md`"*, both this
plan and `docs/findings/verdict-coverage-collapse-2026-07-21.md` need index entries. **Pending
approval — not yet applied.**
