# Verdict coverage collapse — root cause, evidence, and recoverable data

**Session 125 · 2026-07-21 · investigation only, no fixes applied**

Trigger: `.claude/tools/ollama-stats.py` reported **9.6 % verdict coverage** (54 verdicts /
562 calls). The question "why is it low, and is it getting worse?" resolved into a
documentation-contract defect that has been discarding local-model quality judgments since
2026-03-07.

Every claim below carries a `file:line` pointer or a reproducible command. Where a claim was
produced by a delegated agent and I could not verify it, it is marked **UNVERIFIED**.

---

<!-- ref:verdict-coverage-findings -->
## 1. Headline

The capture harness **works**. It was **never fed**.

The durable documentation teaches one verdict format; the capture regex accepts a different
one. Sessions followed the documentation, so judgments were written into a shape nothing
harvests. Proven end-to-end this session: emitting the regex-shaped block captured cleanly
on the first attempt (§6).

| Metric | Value | Source |
|---|---|---|
| Calls logged | 564 | `~/.local/share/ollama-bridge/calls.jsonl` |
| Verdict records | 56 (54 at session start + 2 probes) | same |
| Coverage | **9.9 %** | `.claude/tools/ollama-stats.py` |
| Recoverable from transcripts | **49** | §7 |
| Coverage after a perfect back-fill | **18.6 %** (105/564) | §1.1 |

### 1.1 The format fix addresses the MINORITY of the gap

This must not be read as "fix the docs and we're done."

```
564 calls
 -  56 captured verdicts          (9.9 %)
 -  49 recoverable from prose     (→ 18.6 % combined)
 = 459 calls (81.4 %) with NO judgment in any captured OR recoverable form
```

The documentation defect (D1) explains why *judgments that were made* were discarded. It does
**not** explain the larger population where **no judgment was ever made at all**. Perfect
capture plus full back-fill roughly doubles a small corpus and still leaves ~81 % of calls
unjudged. That residue is **behavioural**, not a format problem, and only a gate (D6) or a
narrower definition of "judgeable" (D10) touches it.
<!-- /ref:verdict-coverage-findings -->

---

## 2. Coverage over time

```
month     calls  verdicts  coverage
2026-02       5         0      0.0%
2026-03     126        29     23.0%
2026-04      54        11     20.4%
2026-05      82         0      0.0%     <-- see §7: May is dense with PROSE verdicts
2026-06     101         8      7.9%
2026-07     194         6      3.1%
```

Not a recent regression — **the ceiling was 23 %**. The rule was never substantially honored
in a machine-readable way.

Split by origin, restricted to the window covered by retained transcripts (255 interactive
calls, 2026-04-15 → 2026-07-21):

| Origin | Calls | Verdicted |
|---|---:|---:|
| Main session (call visible in a main transcript) | 218 | 12 (5.5 %) |
| Subagent-originated (not in any main transcript) | 37 | 1 (2.7 %) |

Subagents are **not** the explanation — they are 14.5 % of the gap.

---

## 3. Root cause — two formats, one captured

### 3.1 The harness was built to fix exactly this failure

`.claude/local/sessions/2026-03-07-173537-verdict-capture-hook-testing.txt` (~line 4100)
records the founding diagnosis:

> **What is NOT stored automatically:** The verdict … only appears as inline text in the
> session narrative, not linked back to the calls.jsonl entry … **There's no automatic join
> between them.**

The hook pair was built to create a machine-parseable path. It then regressed into the same
failure mode, because the machine path was taught **only** by an ephemeral runtime injection.

### 3.2 What the capture regex requires

`.claude/hooks/verdict-capture.py:88-95`

```python
pattern = re.compile(
    r"\[VERDICT prompt_hash=([a-f0-9]+)\]\s*"
    r"verdict:\s*([012])[^\n]*\n"
    r"reason:\s*([^\n]+)\n"
    r"est_claude_tokens:\s*(\d+)[^\n]*\n"
    r"\[/VERDICT\]",
    re.IGNORECASE,
)
```

### 3.3 What every durable document instructs instead

| Evidence | Content | Agrees with regex? |
|---|---|---|
| `CLAUDE.md:110` | ``- Note it inline in one phrase, e.g.: `2 — ~300 est. Claude tokens saved` `` | **No** |
| `docs/scaffolding-template.md:160` | identical wording | **No** |
| `overlays/ollama-scaffolding/files/local-model-conventions.md:150` | ``` `2 — ~300 est. Claude tokens saved` ``` | **No** |
| `.claude/overlays/local-model-conventions.md:150` | byte-identical installed copy | **No** |
| `.claude/agents/impl-opus.md:17,19` | "Read `.claude/overlays/local-model-conventions.md` and follow it … record 0/1/2 verdicts" | **No** (delegates to the inline doc) |
| `.claude/session-context.md` `ref:local-model-conventions` | scale only, no emit format | **No** |

### 3.4 The block format is taught nowhere durable

Repo-wide fixed-string search for `[VERDICT` (excluding `.git`):

```
.claude/hooks/ollama-post-tool.py:55        <- the injector (ephemeral, runtime-only)
.claude/hooks/verdict-capture.py:4,83,89    <- the consumer
docs/plans/verdict-numeric-migration.md:41,75,80  <- draft plan + synthetic fixture
.claude/archive/deferred-completed.md:15    <- archived, descriptive
.claude/archive/session-log-2026-03-07-to-2026-03-07.md:36,66  <- archived, descriptive
```

**Not one is a durable, agent-facing instruction.** The injector and the consumer form a
closed loop that talks only to itself. Persistent instruction beats ephemeral injection.

### 3.5 The capstone: a document that is confidently wrong

`.claude/archive/handoff-session-66.md:136`

> - **Verdict scoring after `generate_code` calls:** record verdict 0/1/2 + reason +
>   `~N est. Claude tokens saved` per the `local-model-conventions` pattern.
>   **Hooks expect this format.**

The inline form asserted *as* the hook-expected form. This is worse than silence: someone
reasoned about the hooks and concluded wrongly, which stops the next reader from checking.

### 3.6 The migration plan contains both halves of the bug

`docs/plans/verdict-numeric-migration.md:38-41` — § **"Chat-text grammar (no change needed)"**

> The verdict is **not** free-floating prose. `ollama-post-tool.py` injects a fenced
> `[VERDICT prompt_hash=…]` block …

`docs/plans/verdict-numeric-migration.md:230` — Phase 5.1

> `2/1/0` scale + legend; inline example → `2 — ~300 est. tokens saved`.

The same document declares the block operative and then writes the competing form into
CLAUDE.md. Two orthogonal axes existed; the plan addressed only one:

- **Axis 1 — CAPS → digits.** The plan's whole subject. Applied.
- **Axis 2 — inline phrase vs `[VERDICT]` block.** The actual defect. Explicitly waved off
  in the section titled *"no change needed"*.

---

## 4. Why it went unseen for five months

### 4.1 PostToolUse is structurally incapable of enforcing

Official docs: *"PostToolUse hooks can't undo actions since the tool has already executed."*
The injection at `ollama-post-tool.py:62-67` is advisory by construction, and
`additionalContext` renders as a **system reminder** — visually identical to background
metadata. Docs further advise writing *factually, not imperatively*; the current payload
(`ollama-post-tool.py:54-60`) is an imperative fill-in-the-blank form.

### 4.2 Verification ran from the hook inward, never from the agent outward

- `docs/plans/verdict-numeric-migration.md:80` — the Phase 1 proof is a **synthetic** string:
  ```python
  sample = "[VERDICT prompt_hash=abc123def456]\nverdict: 2\nreason: clean\nest_claude_tokens: 300\n[/VERDICT]"
  ```
- Commit `15e5be1` verified SubagentStop *"after manually **simulating** the SubagentStop
  event"* (its own commit message).

Both test that the parser parses text handed to it. Neither tests that the agent **emits** it.

### 4.3 No automated test covers the harness

```
$ ls .claude/hooks/tests/*.py
test_oficina_runs_scan.py
test_oficina_watch_hook.py
$ grep -rl -i verdict .claude/hooks/tests/ | wc -l
0
```

Both oficina hooks are tested. The harness that silently lost ~90 % of its data is the
untested one.

### 4.4 The harness is and has been live

`~/.claude/settings.json:140` (PostToolUse `mcp__ollama-bridge__.*`), `:177` (Stop),
`:196` (SubagentStop) — all pointing at absolute paths in this repo. Never disabled;
`48f3d7e` moved wiring project→user level, `df89c21`/`3b9a7d0` untracked a `{}` file.

---

## 5. Defect register

| # | Defect | Evidence | Impact |
|---|---|---|---|
| D1 | Durable docs teach inline; regex accepts block only | §3.2–3.4 | **Root cause** — ~90 % loss |
| D2 | A doc asserts inline *is* hook-expected | `.claude/archive/handoff-session-66.md:136` | Misinforms future sessions |
| D3 | Migration plan holds both halves | plan `:41` vs `:230` | Wrong axis addressed |
| D4 | `prompt_hash` is not a call identity | §5.1 | Blocks safe back-fill |
| D5 | Hash provenance is a positional guess | `ollama-post-tool.py:43-47` | Can mislabel verdicts |
| D6 | PostToolUse cannot enforce | §4.1 | Gate must move to `Stop` |
| D7 | No test coverage | §4.3 | Why it went unseen |
| D8 | `run_result` absent from watched tools | `ollama-post-tool.py:26-34` | oficina never prompted |
| D9 | 30-day GC erodes evidence | §8 | Recoverable set decaying |
| D10 | `calls.jsonl` records no `tool` field | §5.3 | The judgeable denominator is **unmeasurable** |

### 5.3 D10 — the denominator is undefined and currently unmeasurable

`mcp-server/src/ollama_mcp/client.py:312-333` writes 18 fields; **`tool` is not among them**:

```
claude_tokens_est, eval_count, eval_duration_ms, had_format, model, prompt, prompt_chars,
prompt_eval_count, prompt_eval_duration_ms, prompt_hash, response, response_chars, run_id,
system, temperature, think, total_duration_ms, ts
```

Consequences:
1. **Coverage cannot be computed per tool.** `ollama-post-tool.py:26-34` deliberately prompts
   only for 7 generation tools, but the log cannot distinguish them — so the 9.9 % denominator
   silently includes calls the harness never intended to prompt for.
2. **"9.9 % coverage" conflates two populations**: *should-have-been-judged but wasn't*, and
   *needn't-be-judged at all* (the 24-call compare sweep, warm-ups, trivial transforms,
   `summarize`/`translate`/`classify_text`).
3. Any gate scoped to "every ollama call" would demand verdicts on calls that shouldn't have
   them — friction, plus filler judgments polluting the DPO corpus.

Measured proxy in the absence of the field: **86 calls share a `prompt_hash` with a sibling**
(sweep-like); 478 are singletons. **Defining the judgeable set is a prerequisite to both the
metric and the gate's scope.**

### 5.1 D4 — `prompt_hash` collides (critical for back-fill)

```
calls=564  distinct prompt_hash=499
hashes used by >1 call = 21 (covering 86 calls)
max collisions on one hash = 24
```

Worst case `8005c6852894`: **24 calls, 8 different models, all 2026-03-20** — a
`benchmarks/lib/run-compare-models.sh` sweep, documented at line 4 as *"Sends the same prompt
to multiple Ollama models side-by-side"* and indexed as *"same prompt → N models → verdict →
DPO pairs"* (`.claude/index.md`). **The workflow designed to produce DPO pairs is the one the
key cannot represent.**

Consequences:
1. `verdict-capture.py:104` (`if prompt_hash in existing_verdict_hashes: continue`) — once any
   call with that prompt is verdicted, no sibling can **ever** be. A 24-call sweep records one.
2. A verdict on a shared hash cannot say **which model's output** was judged → silently
   mislabeled DPO data.

Origin: `mcp-server/src/ollama_mcp/client.py:300` documents the field's actual purpose —
*"prompt_hash allows deduplication without storing sensitive text"*. A **content-addressing**
key was reused as an **identity** key.

### 5.2 D5 — provenance, and the cheap fix

`ollama-post-tool.py:43-47` reads the **last** record in `calls.jsonl`:

```python
for line in reversed(CALLS_LOG.read_text(encoding="utf-8").strip().splitlines()):
    ...
    prompt_hash = entry.get("prompt_hash", "unknown")
```

Measured effect: **217 injections carrying only 75 unique hashes**, one hash injected 16×.
With parallel tool calls every concurrent hook reads the same tail record.

`mcp-server/src/ollama_mcp/server.py:545` returns bare `content`, so `tool_response` carries
no hash. **But** the logged `response` field is 97.5 % unique (547/563 distinct) — matching on
returned content identifies the exact record with **no server change**.

---

## 6. Live experiment — the harness works

Two probe calls (`mcp__ollama-bridge__ask_ollama`), then proper blocks emitted in-turn:

| prompt_hash | model | captured |
|---|---|---|
| `e2eaab77f0e6` | my-python-q3 | ✅ `2026-07-21T13:17:25` |
| `ab5b9b47b188` | my-go-q3 | ✅ `2026-07-21T13:17:25` |

Verdict records went **54 → 56**. Chain verified: inject → emit → `Stop` → parse → append.
**The mechanism is sound; only its input contract was broken.**

---

## 7. Recoverable data — 49 verdicts

Prose judgments exist in transcripts, matched to logged calls, never recorded. Found in
assistant text:

- ``2 — ~440 est. Claude tokens saved`` (14 occurrences of this exact CLAUDE.md-prescribed shape)
- `**Verdict: 2 (accepted)** — clean, matches the spec exactly. ~1,100 est. Claude tokens saved`
- `**Verdict: IMPROVED**` (pre-migration string form)
- 52 total `verdict: N` prose expressions

**May 2026 recorded 0 verdicts, yet 2026-05-31 transcripts are dense with prose verdicts** —
the cleanest demonstration that judgment was happening and evaporating.

Candidate set with match context: `scratchpad/recoverable-verdicts.json` (49 entries;
`prompt_hash`, `model`, `call_ts`, `matched_phrase`, ±200 chars of context, source transcript).

**Back-fill must not run before D4 is fixed**, or ambiguous-hash records get baked in.

---

## 8. Evidence retention (time-sensitive)

- `cleanupPeriodDays` default **30**, deletion runs **at startup**; raising it (e.g. 365) is
  documented as supported. Explains the June-22 cliff in live transcripts.
- Recovery: cozempic `*.jsonl.bak` snapshots restore **14 sessions**, extending the verifiable
  window to **2026-04-15 → 2026-07-21** (65 files, 38 days).
- **Subagent transcripts are unrecoverable**: written under
  `/tmp/claude-1000/<project>/<session>/tasks/*.output`, wiped on reboot — only the current
  day's survive.

The 49-verdict recoverable set shrinks with each session start.

---

## 9. Corrections to claims made earlier in this investigation

Recorded because each was stated with more confidence than the evidence supported.

| Claim | Status | Correction |
|---|---|---|
| "Zero strict-format blocks were ever filled" | **Wrong** | Parser artifact — filtered on `role=assistant` + `content[].type=="text"`; real blocks sit in other entry shapes with `\n` JSON-escaped. Filled blocks exist (they produced the 56 records). Correct signal: **190 unfilled template injections** vs ~16 captures in the retained window. |
| "The oficina watch-hook never fired" | **Wrong** | Over-specific grep. It fires: 12 injections / 5 real `submit_run` calls. |
| "Most misses are subagent-originated" | **Wrong** | 37/255 (14.5 %). The bulk (218) are main-session. |
| Delegated claim: PostToolUse field is `tool_output`, "NOT `tool_response`" | **UNVERIFIED / contradicted** | `.claude/hooks/oficina-watch-hook.py:31` reads `tool_response` and demonstrably works. Do not migrate the field name without a live probe. |
| Delegated claim: "no verdict captured since 2026-07-12 / `tool: None` anomaly" | **Stale** | Probes captured today; `_log_call` never writes a `tool` field (`client.py:312-333`). |

---

## 10. Fix surface

**Documentation (the root cause)**
- `CLAUDE.md:108-111`
- `docs/scaffolding-template.md:158-161`
- `overlays/ollama-scaffolding/files/local-model-conventions.md:144-151` → `cp` to
  `.claude/overlays/local-model-conventions.md` (currently byte-identical) → reinstall overlay
  to the 3 downstream repos (`expenses`, `web-research`, `career-search`)
- `.claude/archive/handoff-session-66.md:136` — correct or mark historical
- `.claude/agents/impl-opus.md:17-19`, `impl-opus-med.md` — inherit the gap via the inline doc

**Code**
- `.claude/hooks/ollama-post-tool.py` — provenance (D5), add `run_result` to `GENERATION_TOOLS` (D8)
- `.claude/hooks/verdict-capture.py` — call-identity key (D4); `Stop` input already supplies
  `last_assistant_message`, making the whole-transcript re-parse at `:58` unnecessary
- New `Stop` gate — `decision:"block"` + `hookSpecificOutput.additionalContext`, guarded by
  `stop_hook_active` (8-block cap; `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` raises it)
- First tests under `.claude/hooks/tests/` — must assert the **producer→consumer seam**, not
  the parser alone

**Data**
- Back-fill the 49 (after D4)
- Consider `cleanupPeriodDays` increase

---

## 11. Explicitly out of scope

- **Benchmarks** — separate pipeline: `benchmarks/lib/compare-models.py` and
  `record-verdicts.py` write `results[].verdict` to `benchmarks/results/compare-runs.jsonl`
  and never touch `calls.jsonl`. Not to be evaluated for now (user directive). Note it is a
  second, uncounted verdict corpus.
- **Oficina output** *should* be verdicted by the calling session; `run_result` is missing from
  `GENERATION_TOOLS` (`ollama-post-tool.py:26-34`), so it has never once prompted. Tracked as D8.

---

## 12. Open decisions

Sharpened after advisor review (2026-07-21). Items 1–2 were **DECIDED by the user** (session 125).

1. **Judgeable set (D10) — DECIDED: `generate_code`, plus oficina run deliverables.**
   Not `summarize`/`translate`/`classify_text`, not warm-ups, not multi-model sweeps.
   **Correction to the stated assumption:** oficina does *not* route through the
   `generate_code` MCP tool. `oficina/loop.py:260` calls `self.coder(prompt, self.model,
   self.run_id)` — the `GenerateFn` seam (`oficina/worker.py:43,153`) goes straight to the
   client. 18 oficina calls are in the log (`run_id` present), 0 verdicted. So the two need
   **different granularity**:
   - `generate_code` → **per-call** verdict (existing block mechanism)
   - oficina → **per-run** verdict on the finished deliverable, triggered by `run_result`
     (D8). Judging internal loop iterations would be wrong — the calling session reviews the
     deliverable, not the N repair attempts.
2. **Gate shape (D6) — DECIDED: measure first, gate later.** No `Stop` gate in this pass.
   Rationale: PostToolUse *cannot* block (§4.1); a `Stop` block **forces turn continuation**,
   risking Goodhart (a forced verdict is not a considered one — the same "mislabeled is worse
   than missing" hazard as D4), and the 8-block cap makes it escapable regardless. Ship the
   docs fix + identity key + back-fill, observe coverage-among-judgeable, and only then decide
   whether a gate earns its friction.
3. **Key + join ownership (D4+D5 are ONE decision, not two bugs).** Both trace to using a
   *content hash* as an *identity* key. Clean fix: write a unique `call_id` in `_log_call`, then
   decide who carries it into the verdict — model-echo (breaks with multiple calls per turn) vs
   hook-side association via the 97.5 %-unique response match. Do not patch `prompt_hash`.
4. **Tolerant reader?** Should capture *also* accept the inline phrase? It cannot recover
   `prompt_hash` from prose, so it needs positional association — acceptable for a one-off
   back-fill, risky as a live path.
5. **Sequencing — prefer measure-then-gate.** Ship docs + key + back-fill first, observe whether
   coverage-among-judgeable recovers, and only then decide whether the gate earns its friction.
6. **Verify the harness schema before building on it.** The `Stop` block shape and
   `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` come from a delegated summary that got `tool_output` wrong
   (§9). Probe with a real hook first.
7. Raise `cleanupPeriodDays` now to stop evidence decay (§8)?
8. **Housekeeping:** this file trips CLAUDE.md's hard requirement *"New files of any kind — add
   to `.claude/index.md`"*. That edit is pending user approval.

---

## Reproduction

```bash
.claude/tools/ollama-stats.py                      # coverage summary
.claude/tools/ollama-verdicts.py                   # verdict detail
grep -rn --fixed-strings "[VERDICT" --include="*.md" --include="*.py" .   # who teaches the block
grep -n "Note it inline in one phrase" CLAUDE.md docs/scaffolding-template.md
```
