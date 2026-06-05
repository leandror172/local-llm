# Session-Handoff — Placer (Local-Model) Enhancement [FUTURE]

> Status: **deferred enhancement, not scheduled.** Captures everything discussed/found in
> session 83 about adding a local model to the handoff pipeline. The base pipeline (Scope A,
> deterministic spine) is specified in `session-handoff-pipeline-design.md`
> (`ref:handoff-pipeline-design`). Read that first — this doc only covers what the *model layer*
> adds on top.

<!-- ref:handoff-placer-enhancement -->
## Why this is a separate, deferred layer

The register pivot (reuse existing handoff `ref:` blocks for localization) **ate the model's
original job.** The Placer was first conceived to do *semantic localization* — "find the right
spot by meaning." Once a per-repo register supplies location deterministically, and **Claude
authors each full block**, every handoff operation reduces to `replace` / `prepend` / `append` /
`check-off` — all deterministic, no model. So the base pipeline needs **no Ollama call at all**.

The model re-earns its place for exactly **one** value proposition, different from the spine's:

> **Spine saves Claude's *read* tokens** (no reading files to find edit positions).
> **This enhancement saves Claude's *authoring* tokens** — Claude hands *terse intent*
> ("status: anchors.py TDD next; phase-3 frozen") and the **local model expands it** into the
> full formatted block, using the existing section as context.

That is an optimization on top of a working system, not a prerequisite — hence deferred.
<!-- /ref:handoff-placer-enhancement -->

## Model role — Placer (decided), not Author, not Reconciler

The model is the **writer, not the author**. Core capability: **semantic merge / expansion** —
turn Claude's terse intent + the section's current state into the new interior, faithfully.

| Altitude | Claude hands it… | Model decides… | Decision |
|----------|------------------|----------------|----------|
| Transcriber | exact text + exact anchor | nothing | — |
| **Placer** | terse intent (+ role/slot id) | how to expand/merge within the region | **chosen** |
| Reconciler | raw content | also dedup, supersede stale entries, keep file coherent | **out of scope** (park) |

Explicitly parked (Reconciler behaviors, do **not** let the Placer drift into them): dedup,
superseding stale decisions, cross-run idempotency *judgment*.

## The pipeline-internal constraint (key)

The Ollama call is made **inside** the pipeline, **not** by Claude. Consequence: the model's
chattiness — retries, long interiors, fallback re-prompts — is **free from Claude's
perspective**; only the final summary returns to Claude's context. A rejected interior triggers
a *pipeline-internal* retry, never a round-trip to Claude.

## Trust boundary — the Verifier (F4) is what lets a cheap model run

F4 (already built in the spine) hashes everything outside the register-defined region; an edit
that touches anything else is rejected pre-commit. This **decouples two questions**:

- *Is the model good enough?* → content quality (did it expand/merge well)
- *Is it safe to run?* → file integrity (did it corrupt anything)

A weak model that produces a bad interior is **rejected, never committed**; worst case is
retry / fall back to Claude authoring it. **This is what makes an untrusted local model usable**
for the handoff backbone. The model is sandboxed by construction: it can only ever propose a
region interior, and a deterministic gate decides if it lands.

## Frictions specific to the model layer

(The spine already handles localization, atomicity, and outside-region integrity. These are the
*additional* frictions the model introduces.)

1. **Content correctness ≠ integrity.** An interior can pass F4 (well-formed, nothing else
   touched) yet be *content-wrong* (expanded the wrong thing, dropped a bullet intent implied).
   F4 cannot catch this — needs the deferred verdict (below).
2. **Intent-tagging burden.** For the model to expand correctly, Claude's payload must carry
   intent + target per chunk. Too loose → it guesses; too rigid → Claude is back to authoring
   full prose (defeating the enhancement's purpose). The contract must hit the middle.
3. **Per-file conventions.** Newest-first vs newest-last, tone, bullet style — the model must
   honor them. Encode in the register/prompt, not in Claude's intent.

## Verdict model — layered; L1 = deferred labeling (decision (a))

F4 verifies **integrity**, not **content correctness**. So the verdict is layered:

| Layer | Question | Source | Maps to |
|-------|----------|--------|---------|
| **L0 — structural** | well-formed & safe? | F4, automatic inline | fail-after-retries → `0`; pass → "usable, unscored" |
| **L1 — content** | placed/expanded the right thing? | **deferred labeling (a)** | the real `2 / 1 / 0`, backfilled later |

F4's accept/reject is a genuine *free* label — but for **format adherence**, a *different* DPO
objective than **content correctness** (L1). Keep them separate so a model that reliably emits
*well-formed-but-wrong* interiors is catchable, not hidden behind a structural pass.

### Deferred verification — two distinct deltas

| Delta | Question | Verdicts… | Availability |
|-------|----------|-----------|--------------|
| **input ↔ report** | Did the *pipeline/model* faithfully render the request? | the **Placer** (L1) | when input.md + report.md are logged |
| **report ↔ reality** | Was Claude's *claim itself* correct? | **Claude's authoring** | later — path **(b)**, next-session behavioral |

Logging Claude's `input.md` (the spine already does this for audit/recovery) turns L1 from
"judge an interior in isolation" into "**diff intent against outcome**" — far more tractable, and
itself a stepping-stone toward an automatic **(b)** signal (detecting whether the *next* session
had to correct the handoff). The two deltas verdict different things and don't compete.

## DPO / call logging (added by this layer)

The spine logs `input.md` + `report.md` per run. This layer adds **`calls.jsonl`** — one row per
Ollama call — because a **pipeline-internal** call bypasses the MCP bridge's auto-log
(`~/.local/share/ollama-bridge/calls.jsonl`). Row fields:

```
prompt, slot/role context (id, mode, current interior), model,
produced interior, structural_ok (L0, auto), retries, latency, verdict=UNSCORED (L1 slot)
```

The verifier's accept/reject is the *free, automatic* `structural_ok` label (format adherence).
`verdict` (content) is backfilled by the deferred input↔report labeling pass. This feeds the
project's Layer-7 distillation corpus per the verdict convention.

## Contract change Claude must make (vs Scope A)

- **Scope A:** Claude authors the *full* block for each role (verbatim insert/replace).
- **This layer:** Claude may instead hand *terse intent* per role; the register/payload marks a
  region as `authored` (verbatim, no model) vs `intent` (model expands). Mixed per run.
  → The `session-handoff/SKILL.md` output schema (F7) grows an `intent` mode alongside
  `authored`. Start every role as `authored`; opt individual roles into `intent` as the model
  proves out on them.

## Model pick

At Placer/expansion altitude on a single region interior, an **8B** (or even **4B-q8**) is
plenty; all candidates already pulled. Pick + benchmark when this layer is scheduled. Structured
output via the `format` param (project convention: 100% reliable). Sequential-VRAM constraint
applies only if a handoff runs concurrently with an embed job — unlikely.

## Build steps (when scheduled)

- **E1.** Add `intent` mode to the register + F7 payload schema; SKILL.md emits it.
- **E2.** Build F2 (Placer): in-pipeline Ollama call (reuse `retrieval/model_client.py` pattern),
  prompt template encoding role + mode + current interior + intent, `format` structured output,
  bounded to "return the new interior only."
- **E3.** Wire L0 `structural_ok` from F4 into `calls.jsonl`; add the row writer.
- **E4.** Pipeline-internal retry-on-reject loop (K retries → fall back to Claude-authored).
- **E5.** Deferred-labeling tool: open run N, show input↔report per role, write L1 `verdict`.
- **E6.** (later) Path (b): next-session corrective-edit detector reusing the per-run keying.

## Open questions (model layer)

- Model pick + retry count K before fallback.
- One `calls.jsonl` per run vs one appended global corpus file.
- Whether `intent`-expanded output is shown to Claude for an *inline* spot-check on
  low-confidence (high-retry) regions — trades some context cost for content safety; default no.
- Reconciler altitude (dedup/supersede) — revisit only after Placer is trusted.
