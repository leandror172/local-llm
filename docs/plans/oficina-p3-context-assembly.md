# oficina P3 — Context & prompt assembly (plan)

**Status:** DRAFT — decision register OPEN (P3-D1…P3-D9), no build steps yet. Authored session
134 (2026-07-30) immediately after PR #87 merged, so P4's carried constraints are recorded
before they decay into folklore.

**Phase source:** `ref:delegate-phasing` § P3. **Vision decision this plan must NOT answer:**
V-D2 — in H1 the "planner" is Claude plus this deterministic compiler; a planner *model* is not
introduced here and stays gated behind P6. **plan-v2 positioning:** this phase realizes Layer
7.10 (context pre-processor), per `ref:delegate-estate-map`.

**What this plan inherits, and it is unusual:** P4 shipped first (session 131, by the phasing
doc's own licence), so P3 arrives *after* two of its consumers exist and after three constraints
on it were discovered empirically rather than designed. Most of the register below is therefore
not "invent something" but **"make an existing local invariant structural"** or **"wire a seam
that was specified and never connected."** That is the phase's actual character.

**First revision (same session):** the register was drafted, then re-grounded against the
inception docs (`vision.md`, `decisions.md`, `evidence.md`, `integration.md`, `architecture.md`)
and the as-built code. That pass changed the plan materially and the changes are recorded in
place — see P3-D1 (the shape is not a new spec field), P3-D6 (a specified seam that was never
wired), and § "Founding evidence" (P3's own evidence predates P4 by four months). Recorded
because the *reversal* is the plan's most useful content, per the P4 precedent.

---

<!-- ref:delegate-p3-goal -->
## Goal & scope

P1 made a run survivable, P2 made it converge, P4 made it legible. **What a run is *asked* is
still assembled ad hoc.** Today's prompt comes from `oficina/prompt.py`'s `SEGMENTS` fold plus
`loop.py`'s `_stable_prompt_parts`, the judge's comes from `judge.py` independently, and the
conventions the two encode agree only by hand.

P3 is the layer that makes the *ask* a compiled artifact with declared properties, rather than a
string two modules happen to build similarly.

### Founding evidence — P3's own, and it predates P4 by four months

`ref:delegate-conventions-mapping` is described in `integration.md` as **"the design's core
justification"**, and it routes three convention rules to this phase:

| Convention (manual today) | Becomes |
|---|---|
| "Describe behavior, not implementation" prompt style | Prompt compiler template (**P3**) |
| CONSTRAINTS block (single responsibility, ≤15-line bodies, naming) | Loop gate (P2) + prompt compiler (**P3**) |
| **Callers included in context (0-verdict prevention)** | **Intake/fetcher rule (P3)** |

And `ref:delegate-evidence-verdicts` records the measurement that makes the third row the
strongest single argument this phase exists:

> *"Context quality already fixed a defect class: the March re-declaration cluster (models
> re-declaring types instead of importing) disappeared after the conventions started requiring
> protocol files + callers in context."*

**A context-assembly change killed a whole defect class.** That is P3's founding evidence.

**Three further constraints arrive as P4 side effects** — carried, not founding:

1. **Prompt ORDER is worth 79–85% of a call's prefix evaluation** (T-129) — and the coder
   already knew this (P2-D2) while the judge did not.
2. **A payload must name the artifact it carries** (T-130) — measured, not stylistic.
3. **The delegate's envelope has two walls, and one has no live source** (T-122 + s133).

### In scope (from `ref:delegate-phasing` § P3)

- **Deterministic prompt compiler** encoding the conventions, with **order and stability as
  declared, checkable properties** rather than caller conventions (P3-D2).
- **Typed context requests fulfilled by deterministic fetchers** — files + refs (existing
  ollama-bridge features), LTG `retrieve_context` / `relate_files`, signature extractor when
  T-77 exists.
- **Wiring `context.callers`**, which is declared in the spec model and consumed by nothing
  (P3-D6). Cheapest deliverable in the phase and the best-evidenced.
- **Bounded re-request round** — one round, deterministic, distinct from P5's model-initiated
  `blocked` union.
- **`steps:` support** — decomposed generation, mechanizing `benchmarks/lib/decomposed-run.py`.
- **The code-anchored output question** (P3-D1) — not in the phasing doc, and after re-grounding
  it may not be a P3 entry at all. See § "Relationship to T-122".

### Explicitly out of scope

- **A planner model.** V-D2 stays open; H1's planner is Claude.
- **P5's question channel.** The bounded re-request round is one deterministic round at a known
  point, not a model-initiated escape hatch at arbitrary stages — the line P4 drew for S14, and
  first principle 4's *"most 'the model should ask' cases are really 'the harness should
  refuse'"* (S13).
- **Re-judging.** P3 changes what the coder and judge are *sent*; P4 owns what is done with the
  answer. Any P3 change to the judge's payload re-runs `make accept-p4` (P3-D2).
- **Making large files editable by widening windows.** Dead on measurement — see P3-D1.
- **A general agent framework** (`ref:delegate-non-goals`). The compiler is deterministic
  assembly; it does not acquire agency because it acquired a budget.
<!-- /ref:delegate-p3-goal -->

---

## Relationship to T-122 and P4's recorded rejection

P4's plan records, under § "Why P4 before P3":

> *"Rejected argument, recorded so it is not re-raised: that P3 owns a remedy for T-122's
> feasibility band via `steps:` (decomposed generation). It does not. … Decomposing the
> generation task does not stop each step emitting a whole file; only span-confined **output**
> removes the multiplier … None of P3's deliverables … shrink the target's double cost."*

**That rejection stands and is not being reversed.** `steps:` is not a band remedy; re-reading
it is what kept this plan from making the same claim (see P3-D9).

Two things changed since it was written, neither touching its argument:

1. **Remedy (b) — bigger-ctx personas — died on measurement (session 133).** Recorded as
   "blocked on T-113"; now blocked on evidence. `loop.py` cleared the 32K window and produced
   **nothing in 7,066 s** at 9.4 GiB resident of a 14.2 GiB config, ~49% utilisation — partial
   offload at ~2 tok/s. A window you cannot drive is not a remedy, and T-113's re-probe cannot
   revive it because the throughput measurement is downstream of the footprint number. T-122 is
   therefore a **two-way** choice: (a) code-anchored output, or (c) route large edits to Claude.
2. **(a) was chosen (session 134) — subject to P3-T0. RE-OPENED and narrowed (session 135).**
   Two changes. **Its mechanism was mis-specified:** (a) was written as caller-declared
   `deliverable.unit` ("modify this function"); the intended and better-fitting design is
   **model-emitted structured edit operations** — P3-D1(B) — which the T-122 blocked set actually
   needs, since those files are blocked by *size*, not by having one identifiable bad unit. **And
   its scope is narrower than "chosen" implies:** E-D1 preserved code-anchored as *"the fallback
   mechanism"*, so T-122 licenses (a) only as a **size-gated fallback**, not as the default edit
   mechanism — the default would reverse E-D1 on three grounds T-122 does not rebut.
   **Counter-evidence now on file (s135, verified):** Diff-XYZ measures *diff generation* on our
   own coder family at **0.03 (7B) / 0.24 (32B)** exact match, and Aider recorded a weak model
   degenerating to whole-file-inside-the-diff. Neither is our configuration — `format` enforces
   the schema and our criterion is applicability, not reference equality — but both mean **(a) is
   now the option with measurements against it and mechanism for it.** See P3-D1.

**What P3 owns is narrower than "the remedy":** the **surface on which the shape is expressed**
— the constraints block, the output-contract framing, and the segment headers naming the
artifacts carried. It does not own the apply path (that is `patch_file`, already built), and it
does not claim `steps:` shrinks anything.

**One argument in (a)'s favour nobody has recorded:** anchored output attacks **both** walls.
Throughput cost is dominated by *output* tokens at ~2 tok/s, and anchored output emits a span
instead of a whole file — where remedy (b) widened the window while making throughput strictly
worse. It also **structurally eliminates** the failure class `_EDIT_CONSTRAINTS` currently begs
the model to avoid: you cannot corrupt code you never emit. T-119's leak and E-D6's family are
*whole-file* failure modes.

**And one argument against treating (c) as defeat:** `ref:delegate-non-goals` states *"not a
replacement for Claude's judgment"*, and H1 is Claude-gated by design. Routing the largest
edits to Claude is consistent with the design's own stated boundary, not a concession forced by
hardware. The tasks.md framing ("conceding a fifth to a quarter of the estate *including the
spine*") is the honest cost; the vision framing is that Claude was always the gate.

---

<!-- ref:delegate-p3-decisions -->
## Decision register (P3-D) — OPEN

House rule: each entry states the fork, the constraints that bound it, and a recommendation.
Freeze on review with the user; reverse only with new evidence once frozen.

### P3-D1 — What the model EMITS when editing, and who chooses — **BLOCKS**

**This entry has been revised twice. Both revisions are recorded, because the second one
reinstates something the first removed.**

**Revision 1 (s134).** The first draft proposed `deliverable.output_shape: whole_file |
code_anchored` and it was rejected as a duplicate axis, on three findings that remain true as
statements of fact:

1. **The draft run spec already contained a related concept.** `ref:delegate-run-spec` lists
   `kind: test_file | function | class | file | patch` — **`patch` was specified and dropped at
   build.** As-built: `VALID_KINDS = {"file", "answer", "function"}`, `LOOP_KINDS = {"function"}`.
2. **The kind taxonomy has a declared owner and trigger.** E-D8 (`ref:oficina-edit-mode-decisions`):
   *"Kind taxonomy unchanged. `function` stays … Rename deferred; **trigger: the Axis-B
   kind-widening pass, which must touch the taxonomy anyway**."* Axis B has been carried since
   s128 and never started.
3. **The recorded fallback names `unit`.** `ref:oficina-write-model-report` § AMENDMENT prices
   code-anchored as *"a **`unit` spec field**, response-shape validation, deterministic import
   merging, a constants boundary."*

**Revision 2 (s135) — the option set was INCOMPLETE, and finding 3 was read too narrowly.**
Surfaced by the user in review: the intended design was never "name one unit," it was **the model
emits a structured description of the changes it wants** (operations — replace / insert /
imports — in a schema-enforced JSON response), and the harness applies them. That option was
absent from revision 1's fork.

Two corrections follow:

- **Finding 3 quotes a FOUR-item list and revision 1 treated the first item as the mechanism.**
  The AMENDMENT's list is `unit` field · **response-shape validation** · import merging ·
  constants boundary. The `unit` field is the *input* half (which span); response-shape
  validation is the *output* half. The recorded fallback contains **both**, so it does not
  adjudicate between them.
- **Finding 1's "duplicate axis" objection does not survive S15.** The as-built deliverable is
  *"a branch + diff report"* — **the branch IS the deliverable**. So whether the model emits a
  whole file or a set of operations changes **nothing about what is delivered**; Claude reviews a
  diff either way. A `kind` names what the deliverable **is**; this names how the model
  *communicates*. They are different axes, not two spellings of one — which also means **E-D8's
  Axis-B trigger does not capture option (B)**. *(This is reasoning, not measurement.)*

**The fork, corrected — three options:**

- **(A) `deliverable.unit` — caller-scoped span.** The caller says *"modify this function"*;
  `locate_unit` finds the span; the model returns replacement text for it; `patch_file` splices.
  **Cost:** the caller must already know which single unit is wrong — which the T-122 blocked set
  does not satisfy, since `loop.py`/`parser.py`/`intake.py`/`evaluator.py` are blocked by *size*,
  not by having one identifiable bad function.
- **(B) Model-emitted structured edit operations — PRIMARY, and now concrete.** The model returns
  typed JSON naming the unit and supplying its new body; the harness resolves the name to a span
  and splices. Permits N scattered changes in a large file while emitting only what changed.
  **This is the option the phase actually needs for T-122** — the blocked set
  (`loop.py`/`parser.py`/`intake.py`/`evaluator.py`) is blocked by *size*, not by having one
  identifiable bad unit, so (A)'s caller-names-the-unit shape does not reach it.

  ```json
  {"op": "replace_unit", "path": ["EvaluatedLoop", "run"], "kind": "Method", "body": "..."}
  ```

  Plus `ensure_import` / `remove_import` and `replace_module_docstring`, which the census shows
  close the entire non-def/class residue in both languages (`ref:unit-addressing-census`).
- **(C) revive `kind: patch`.** Routes to Axis B by E-D8's trigger; P3 becomes a consumer. Note
  this is now the *weakest* fit: per the S15 argument above, response shape is not a kind.
- **(D) The CASCADE — added s135, previously unconsidered.** Claude emits an edit *sketch*
  (locations + contents); the local model performs the mechanical *application*
  (`ref:symbol-addressed-editing-survey` § 4c, arXiv 2604.19201). Untuned QC-14B applying
  DeepSeek-R1 sketches reached Pass@2 **66.7 vs 67.6** for R1 editing directly — on small files.
  It fits H1's *"Claude holds the plan; the system holds the grind"* while **inverting who decides
  the change**, and its headline result needs fine-tuning. Recorded so it is not discovered later;
  not recommended, because it moves intellectual work back to Claude, which is the cost oficina
  exists to avoid.

**Evidence FOR (B) that revision 1 never cited.** **First principle 2** is a direct endorsement —
*"Structured output only — no free-form tool use by local models … models **request** (typed
JSON); deterministic fetchers **fulfill**"* — and `ref:structured-output` records Ollama's
`format` param as **100% reliable, no speed penalty**. (B) is that principle applied to the
response; the whole-file status quo is the one place the loop does *not* use structured output.

**Mechanism, within (B): anchor-based, NOT line numbers.** Line numbers shift after the first
operation, so a batch is expressed against a moving target. An `{old_string, new_string}`
operation list composes **`patch_file`**, which already exists in the same server with exactly
the needed semantics (exact match, uniqueness check, `replace_all`). T-104's principle —
*"oficina composes the ollama-bridge tools, it does not reimplement them"* — lands in (B)'s
favour: **the apply path is free and already hardened.** Import merging and the constants
boundary remain genuinely unpriced.

**Evidence AGAINST (B), measured, on our own model family — verified s135.** Diff-XYZ
([arXiv 2510.12487](https://arxiv.org/html/2510.12487v1)) benchmarks **Qwen2.5-Coder**, our coder
base. *Diff Generation*, exact match: **0.5B 0.00 · 3B 0.00 · 7B 0.03 · 32B 0.24** —
*"None of the open-source models achieve comparable performance on Diff Generation."* **Our 14B
coder sits inside that gap.** Two further results bear on the design:

- *"search-replace is a strong default for most larger models, while **udiff-l achieves the best
  scores for smaller models**"* — and the stated mechanism is **marker collision**: *"Small models
  may confuse single-character udiff markers (+, −, leading space) with ordinary code characters.
  Replacing them with explicit tags (ADD/DEL/CON) makes the control tokens unambiguous and rare."*
- Aider's own benchmark records GPT-3.5, when it emitted diffs at all, *"often uses it in a
  pathological manner, placing the entire original source file in the ORIGINAL block and the
  entire updated file in the UPDATED block — strictly worse than just using the whole edit
  format."*

**How much of that transfers, and how much does not.** The mechanism transfers; the magnitude is
NOT derivable from these numbers (`feedback_measure_magnitude_not_estimate`). Three reasons the
benchmark is not our configuration: (a) its formats are **text parsed from free output**, while
(B) is **schema-enforced via `format`** — marker collision, the paper's own first mechanism, is
exactly the class `format` eliminates; (b) a JSON schema with named fields (`operation`,
`old_string`, `new_string`) is structurally **udiff-l** — explicit, unambiguous, rare control
tokens — i.e. the variant the paper found *best* for small models, not the search-replace variant
it found worst; (c) its metric is **exact match against a reference diff**, while our success
criterion is an **applicable** edit. `0.03` is therefore not "3% success at our task."

**The pathological failure mode is the one that must be pre-registered.** If the coder emits the
whole file as `old_string`, the design pays for the target **twice** again — the exact bound (B)
exists to escape — while adding an edit language, and the run still *looks* successful. Aider
measured this on a weak model; nothing rules it out at 14B. **P3-T0 must measure it directly.**

**Corroborating scaffolding costs, from our own evidence base:** SWE-agent carries a
*"model-error requery ladder for recovering from malformed actions"* and an *"edit+lint tool with
rollback"* (`coding-subagent-prior-art-webresearch.md:71-78`); Aider's `max_reflections = 3`
budgets re-prompts for *"lint/test failures **or malformed edits**"*
(`coding-subagent-prior-art.md:15`). Both built recovery machinery around this exact failure
class. That machinery is part of (B)'s unpriced cost.

**Who chooses.** Three sub-options, and one constraint decides it:

- **auto-select at assembly** — a `_resolve_output_shape(assembly)` beside `_resolve_num_predict`
  (E-D9) and `_resolve_max_iterations` (T-114). Attractive because **T-112's guard is a refusal
  assembled from exactly the numbers a selector needs**: `_context_overflow` compares
  `ceil(len(prompt)/4) + _num_predict` against the live ceiling, and `_resolve_num_predict`'s
  edit branch computes `max(NUM_PREDICT, ceil(chars/4) * 2)` — *which is* the "pays for its
  target twice" arithmetic of the band.
- **caller declares** — validated at intake, with today's guard refusing loudly on a mismatch.
- **refuse-and-suggest** — no new runtime behaviour; `ContextBudgetError` names the remedy.

**The deciding constraint.** Under auto-select, when `_context_limit is None` the selector *must*
still emit something — and `transport.model_context_limit`'s docstring is a written record of
this project refusing that exact guess:

> *"Absence is NOT 'the architectural maximum' … an absent or unreadable value yields None rather
> than a guess: guessing high silently disables the caller's fit check, guessing low aborts valid
> work."*

Auto-select would place a guessing selector directly beside a resolver documented as refusing to
guess. **Caller-declares does not answer that question — it removes it:** with the choice
declared, an undeterminable ceiling simply disables the backstop, as today.

**The precedent that must be addressed out loud: E-D2.** Edit-vs-greenfield mode was
**deliberately not a spec field** — *"Mode = target committed at HEAD (E-D2, no spec field)"* —
a recorded stance against spec fields for derivable facts. Caller-declares survives it because
shape depends on a **budget**, not an unambiguous repository fact; but the entry must say so
rather than appear ignorant of the precedent.

### Prior art and measurement — commissioned s135, four arms

Full survey: **`ref:symbol-addressed-editing-survey`** (`docs/research/symbol-addressed-editing/`).
Own-corpus measurement: **`ref:unit-addressing-census`**. The load-bearing results:

1. **Precedent exists, narrowly.** No standalone harness addresses edits by symbol (13-agent
   source survey, arXiv 2604.03515). But **Serena** ships `replace_symbol_body(name_path, …)` —
   this operation, in production, used with Claude Code — and **Moderne MCP** does it type-aware.
   **CODESTRUCT** (arXiv 2604.05407) measures it: **GPT-5-nano +20.8 pts**, empty-patch failures
   **46.6% → 7.2%**. *The weakest model gains the most*, which is our case.
2. **The variable is ANCHOR BURDEN.** ~50pp of structured-edit failures are anchoring, and that
   number is **flat from 7B to 32B** (Diff-XYZ on Qwen2.5-Coder). Scale fixes syntax, not
   anchoring. There are exactly two escapes from exact-anchor reproduction — whole-file (what we
   do; aider routes every Qwen2.5-Coder ≤14B to it) and symbol selectors. **The second bounds
   output to one unit; the first does not.** This reconciles the apparently contrary evidence:
   the measurements against structured edits are all measurements against *anchor-based* ones.
3. **The span problem is already solved.** SCIP's `enclosing_range` is specified to include
   documentation and *"attributes/decorators/attached macros"* — its own worked example is the
   `@cache`/`def factorial` case — and **every shipped indexer emits it**. So `locate_unit` need
   not be hand-written per language: **emit a Serena-shaped tuple, resolve against SCIP.** ~30-line
   matcher. (Fallback tier LSP `documentSymbol`, but then backfill the span yourself — gopls'
   range excludes the doc comment.)
4. **Omit the overload slot.** SCIP's `(+N)`, SemanticDB's `+1` and Serena's `[n]` are the *same
   positional counter* over source order. A model must **count** to name the second overload, and
   any reorder silently retargets the edit. Multi-match ⇒ hard resolve error. Java (arm 3) needs
   **arity-first with type spelling as tiebreaker** — not positional, and compatible.
5. **A REFUSAL region is mandatory** — anonymous classes, lambdas, local classes, in-body spans.
   Arms 1 and 3 converged on this independently; no grammar addresses them stably.
   **Fallback = whole-file for that iteration, which is E-D1's existing mechanism**, so the
   refusal costs nothing to build.

***Recommendation:* (B), symbol-addressed, size-gated — and now evidenced rather than reasoned,
but STILL not freezable today.** What changed: the mechanism argument acquired a production
precedent and a measured +20.8pp on the weakest-model case, and the span hazard I found by
inspection turned out to be solved in a spec. What did **not** change: the magnitude on *our*
coder is still unmeasured, and the two published results that bear on format choice
**disagree with each other** (`survey` § 10) — which means any choice made on published numbers
inherits someone else's configuration. Freezing on mechanism alone would still repeat the error
s132 recorded five times over: **right about the mechanism, wrong about the size.**

**Relationship to E-D1 — the distinction that decides whether this is a reversal.** E-D1
(s126, T-110) reversed T-104's code-anchored choice for the loop's edit mode, on four grounds of
which three still stand undiminished (spec simplicity, product intent, the ≤5-point tie branch).
But its wording is precise: ***"Code-anchored stays on file as the fallback mechanism."*** So:

| Ask | Relation to E-D1 |
|---|---|
| (B) as the **default** edit mechanism | **Reverses E-D1** on evidence it already weighed. T-122 rebuts none of its three surviving grounds. |
| (B) as a **size-gated fallback** for targets the band blocks | **Uses** the fallback E-D1 preserved — on a second trigger E-D1 never priced. `KNOWLEDGE.md`: window feasibility is *"a third leg the M2 decision never weighed."* |

**Only the first is a reversal, and this entry should not attempt it.** T-122 is a *feasibility*
argument (files that cannot be edited at all, including oficina's own spine); E-D1 was decided on
*quality and spec simplicity*. Different questions — which is why T-122 counts as new evidence
rather than re-litigation, and equally why it licenses only the narrow ask.

**E-D1 prescribes a cheaper step that has never been taken.** `ref:oficina-write-model-report`:
*"If it fires: **harden the corpus** (heterogeneous filler, 500+ lines), re-run, revisit."*
The original benchmark returned **null on correctness** because the uniform-filler corpus was
whole-file's best case — the finding calls this *"a coverage failure, NOT 'whole-file is safe'."*
**So the comparison that would settle default-vs-fallback has never been run on a fair corpus**,
and it costs GPU time and no design surface. It belongs before any edit-language build.

**GATED on P3-T0, which is now the only thing that can decide this entry.** Revision 1 gated on
*"can the coder emit a well-formed anchor"*; `format` largely answers that for free, so the probe
must measure what `format` cannot guarantee. **Pre-registered criteria, all on the real 16K
coder:**

1. **Anchor fidelity** — does the emitted `old_string` occur in the target **exactly and
   uniquely**? This is precisely what `patch_file` already checks, so the negative control is
   obvious: a case whose anchor cannot match, asserting a **loud** failure rather than a silent
   no-op. *(Write the negative control FIRST — s133's delegated model inverted `applies_to` with
   the case spelled out in its brief.)*
2. **No degeneration to whole-file.** Measure `len(old_string) / len(file)` per operation. Aider
   measured a weak model placing the entire file in the ORIGINAL block; if that happens here, (B)
   pays for the target twice and **T-122's entire rationale evaporates** while the run still
   reports success.
3. **Applicability, not exact match** — the criterion is that the operation list applies cleanly
   and the result passes the run's own acceptance, never equality with a reference diff.

**If the probe reports poorly, T-122 collapses to remedy (c) — route large edits to Claude — by
measurement rather than by concession.** Do not freeze before the probe reports. Target
`parser.py` / `intake.py`, **never `loop.py`** (it measures throughput: nothing in 7,066 s at
32K).

### P3-D2 — Prompt order and stability as structural properties, not conventions

**There are THREE prompt builders, not two.** Corrected after reading
`mcp-server/.memories/KNOWLEDGE.md`:

| Builder | Its ordering rule | Where the rule is written |
|---|---|---|
| `server.py` (the bridge, 2026-05) | `<refs>` → `<context_files>` → `[Language hint]` → user prompt; *"each layer wraps outward: context_files first, refs outermost"* | KNOWLEDGE § "Refs Param Design" |
| `oficina/prompt.py` (P2) | `SEGMENTS` fold, stable segments first (P2-D2) | the function's own docstring |
| `oficina/judge.py` (P4) | criterion-invariant system message, criterion block LAST (T-129) | KNOWLEDGE § "The judge's payload" |

Three implementations, three independently-authored ordering rules, **no shared definition**.
The bridge's predates both oficina builders and is the one P3's fetchers will sit next to —
`loop.py` already calls `server._build_refs_block` for `context.refs`, then prepends the result
into its own `context` segment, so the two orderings agree today **by two people making the same
call, not by construction.**

**The rule already exists — for one of the three.** `oficina/prompt.py` folds parts in
`SEGMENTS` order, stable segments first, and says so:

> *"Because stable segments come first, the stable prefix is byte-identical whenever the stable
> parts are unchanged — the P2-D2 cache win."*

**The judge violated it anyway,** because `judge.py` builds its own prompt and never touches
`prompt.py`. Measured cost before T-129: ms/token was **flat** across a run's two calls
(1.393→1.392, 1.352→1.355), so prefix reuse was **zero, not weak**; after, the second criterion's
prompt eval fell **2398→513 ms** and **3105→459 ms** (79–85% cold, ~88% session-warm), with
**verdicts unchanged**.

**This is the corpus-divergence shape** (`ref:corpus-divergence-pattern`, T-126) in a new
subsystem — the first instance in prompt construction rather than in a health-reporting tool.
P2-D2 was a property of **one implementation**, not of the system, so nothing was wrong *inside*
`prompt.py` and no check could fire. Worth reporting to T-126's audit as a widening of scope.

**The cache the invariant buys has a 15-minute lifetime, and that bounds the claim.**
`ref:mcp-keep-alive`: `chat()` passes `keep_alive="15m"` on every payload, and *"llama.cpp
automatically reuses KV states for any leading prefix that matches the cached slot; `keep_alive`
controls how long that slot stays alive."* So prefix stability buys nothing across a gap longer
than the slot's life — the compiler cannot treat order as a free win, only as a win **within a
run** (or within 15 minutes of one). It also does **not** protect against sliding-window
eviction inside a single long call (that is `num_keep`), which is the regime an anchored-output
run is least likely to enter and a whole-file run most.

**Fork.** (i) Do all three builders go through one compiler, or do they remain separate with
the invariant enforced some other way? (ii) Is **stability** a declared, checkable property
of a segment, or does it stay a `loop.py` convention (`_stable_prompt_parts` vs the `variable`
dict) where nothing verifies that a part named stable is actually run-constant?

**Why (ii) matters independently of (i):** a "stable" part that silently varies destroys the
prefix with no error, no signal, and no visible cost except a latency number nobody reads —
failure-silent-by-construction, the direction T-126 flags as dangerous.

***Recommendation:* one compiler for the two oficina builders; the bridge's ordering becomes a
*declared* rule the compiler is checked against, not a fourth implementation.** The bridge
serves interactive `generate_code`/`ask_ollama` callers outside oficina entirely, so folding it
in wholesale exceeds P3's scope — but its rule and oficina's must be stated in one place, since
today they agree only by coincidence. **Stability declared per segment.** The testing constraint
comes with it: **the honest metric is `prompt_eval_duration_ms`, never `prompt_eval_count`** —
the latter reports full tokens regardless of reuse, which is how T-129's pre-change measurement
was first misread as weak reuse instead of none.

**Blast radius:** any change here alters what the judge is sent, so it re-runs `make accept-p4`.
The suite fakes `chat` and is structurally blind to prompt layout.

### P3-D3 — A segment names its artifact truthfully, and derives that name from one source

**Measured basis** (`ref:judge-sees-the-change`, row 2): the drift metrics were **in the prompt**
(`lines_added: 114`, `max_verbatim_run_vs_tests: 78`), the criterion description explained what a
large value means, the scale reserved `1` for exactly that case — and the judge scored **5**,
writing *"contains only the requested change."* This tier resolves a conflict between what it is
told and what it can see **by trusting what it can see**. A header is a *claim*, and a false
claim is silently overruled by the payload.

T-130's fix is the pattern to copy: `LoopResult.mode` derives from `_edit_baseline is None` —
**one source, no second field to drift** — and `_change_heading(mode)` labels from that source.

**This entry has TWO halves with different dependencies — do not freeze them together.**

**Half 1 — headings derive from the fetcher that produced the segment (D1-INDEPENDENT, ready to
freeze).** No heading is authored at a call site; each is emitted by the fetcher that produced
the artifact, from one source, on T-130's `LoopResult.mode` → `_change_heading(mode)` pattern.
This is true regardless of what the model emits, and it is already the measured rule.

**Half 2 — a vocabulary for PARTIAL artifacts (D1-DEPENDENT, park with D4/D5).** This exists only
because a design that produces fragments needs it. **Corrected s135:** the falsification table
below was written for P3-D1 **(A)** (caller-scoped span). Under **(B)** — model-emitted structured
edits — the prompt still carries the **whole** file, because the model must see it to choose
anchors; what becomes partial is the *response*, not the context.

| Segment | The claim it makes | Falsified under (A) | Falsified under (B) |
|---|---|---|---|
| `current_file` | "this is the file" | it is a span | **not falsified** — still the whole file |
| `context` | "these are the callers" | dropped for budget | dropped for budget |
| `tests` | "these are the acceptance tests" | truncated to fit | truncated to fit |
| `previous_attempt` | "your last output" | a diff of a fragment | **an operation list, not code** — a different artifact class, and T-120 made this a diff for a reason that must be re-derived, not assumed to carry over |

So (B) *narrows* this half rather than widening it: two of four rows are budget-truncation
concerns that exist today independently of D1. **If D1 lands on (B), half 2 may reduce to naming
`previous_attempt` honestly** — which is exactly the T-130 lesson, not a new vocabulary.

***Recommendation:* freeze half 1 now; park half 2 behind P3-T0** with D4 and D5, for their
reason: write the vocabulary from what the probe actually needed, not from what it might need.

### P3-D4 — Constraints selection becomes two-dimensional

`_stable_prompt_parts` selects the constraints variant on `assembly.mode == "edit"` (E-D4).
`_EDIT_CONSTRAINTS` states the preservation contract — *"Keep every existing function, constant,
import and comment byte for byte"* — which is **meaningless under anchored output**, because the
model never emits the siblings at all.

Open: a 2×2 table of authored blocks, or a composable preservation fragment the compiler
includes only when the output can violate it? The second is smaller but introduces
prompt-fragment composition, a compiler feature with its own ordering question (P3-D2).

***Recommendation:* deferred to the probe.** If P3-T0 shows anchoring works, the constraints
text must be authored from what the probe actually needed, not predicted.

### P3-D5 — `scope_adherence`'s ladder has no rung for anchoring's characteristic defect

**Checked, and narrower than it first appeared.** `drift.measure()` compares baseline lines
against **delivered** lines, and anchored output still reconstructs a delivered file — so
`hunks` / `lines_added` / `lines_removed` / `max_verbatim_run_vs_tests` stay computable and mean
the same thing. The metrics are shape-independent, and `max_verbatim_run_vs_tests` survives
fully: a model can still paste tests *inside* a span, so the T-119 signal is intact.

**The ladder is not.** Every rung of `oficina-edit.yaml`'s `scope_adherence` describes a defect
*of rewriting*:

```
5: "Only the requested change is present; everything else is byte-for-byte intact"
4: "The requested change plus a trivial incidental edit (whitespace, an import ordering)"
3: "The requested change plus a small unrequested edit a reviewer would ask to remove"
```

Under anchored output an incidental whitespace edit is structurally impossible, so rungs 4 and 3
go dead — while anchoring's *characteristic* defect, **an anchor matching the wrong location**,
has **no rung at all**.

**This is T-130's lesson a third time, in its precise form:** *"a ladder written for one run
shape has no vocabulary for the other's characteristic failure"* — structurally identical to
`code-python`'s `completeness` criterion scoring the T-119 leak **5** and calling the pasted
acceptance tests *"a usage example."*

**And it fails in the dangerous direction.** The dead rungs make it a check that can only pass —
which is **first principle 6** at vision level: *"a signal that fires unconditionally carries
zero bits … every warning/verdict/status in this system must discriminate."* The same principle
already caused `files_touched` to be **dropped at build** (the loop writes exactly one file, so
it would fire unconditionally). A rubric rung is subject to it too.

**Fork.** Does anchored output get its own rubric (the `applies_to` precedent — T-130 chose
rubric-level over per-criterion deliberately, because filtering criteria out of the reductions
is structurally the same operation as the filtered-subset bug P4-D8 removes), or does
`scope_adherence` gain shape-neutral rungs?

**Note this may widen `applies_to` from a mode to a `(mode, shape)` pair**, touching P4's frozen
T-130 design — record it as such rather than editing that decision in place.

***Recommendation:* deferred to the probe**, for P3-D4's reason: write the ladder from an
observed anchoring failure, not a predicted one.

### P3-D6 — `context.callers` is declared and consumed by nothing — **cheapest, best-evidenced**

`intake.py:44` declares `callers: List[str]` on the `Context` model. Nothing reads it:
`_check_context_files` validates only `context.files`, and no consumer exists in `loop.py`,
`prompt.py` or `workspace.py`. **A caller can set `context.callers` and it is silently ignored.**
Verified by grep over all of `mcp-server/src` and `mcp-server/tests`: `callers` appears exactly
once as a symbol — the declaration — and every other hit is the English word in a docstring.
No test names it either.

**The declaration is what makes the silence possible.** `Context` sets `extra="forbid"` and
`CONTEXT_KEYS = set(Context.model_fields)`, so an *undeclared* key would be **rejected at
intake**. `callers` is accepted precisely because it is declared and only because it is
declared — the schema converts what would have been a loud rejection into a silent swallow.
That is the inverse of first principle 4 (*"the harness should refuse"*): here the harness
declines to refuse, and says nothing instead.

This is the one row of `ref:delegate-conventions-mapping` labelled **0-verdict prevention**, and
the one whose effect was *measured*: the March re-declaration cluster disappeared once the
conventions required protocol files + callers in context (`ref:delegate-evidence-verdicts`).

**It is also a `ref:corpus-divergence-pattern` sibling by a different mechanism:** the spec
field exists, so a caller reading the schema concludes the rule is enforced. Silence is read as
compliance. Unlike T-125/T-126's checkers, nothing here reports anything at all — which is why
no audit found it.

**Fork.** Is `callers` (i) a fetcher input the compiler resolves and injects as its own segment,
(ii) an intake *requirement* for edit runs (refuse a spec that names no callers for a target
with importers — first principle 4's harness-should-refuse), or (iii) both? Note (ii) needs a
caller-discovery mechanism the harness does not have; T-77's signature extractor is the natural
supplier and `ref:delegate-estate-map` says explicitly **do not block on it**.

***Recommendation:* (i) now, (ii) recorded with T-77 as its named trigger.** Wiring the declared
field is small, testable, and closes a live silent-ignore; making it mandatory needs a
discovery primitive that does not exist yet.

### P3-D7 — Typed context fetchers: what is actually open

**Mostly settled at vision level — this entry records what is left.**

Settled, do not re-litigate: **models *request* (typed JSON), deterministic fetchers *fulfill***
(first principle 2 / S5 — structured output only, no free-form tool use). **T-77 does not gate
anything** — `ref:delegate-estate-map`: *"this system is its second consumer … do not block on
it."* **LTG's dependency direction is delegate→LTG** (products depend on primitives, never
product↔product).

Genuinely open: (i) what a run does when the LTG MCP server is unavailable — the `RefsDropped`
fail-open-by-record precedent (T-96) is the obvious model, on the run ledger rather than the
worker ledger for `ContextLimitUnknown`'s reason (the absence must be visible to whoever reads
the run); (ii) whether a fetcher may consult a *sibling repo's* index at all from a run
submitted elsewhere — note the carried unverified assumption that `OFICINA_RUBRICS`/`repo_root()`
resolution has never been checked from a foreign working directory (T-109(4) is a recorded
instance of that path-surprise class).

### P3-D8 — The bounded re-request round: what bounds it

**Architecture settled** by first principle 2 (typed request, deterministic fulfilment) and S13
(intake rejection over model questioning). Open: what the model may request; whether a
re-request resets the iteration budget; and what refuses an unbounded request. Distinct from
P5's `blocked` union by the line P4 drew for S14 — one deterministic pause at a known point.

### P3-D9 — `steps:` decomposed generation

Mechanizes `benchmarks/lib/decomposed-run.py` and the Layer-0 3-stage finding.
**Carries P4's rejection forward explicitly:** `steps:` is **not** a T-122 remedy and must not be
planned as one — each step still emits a whole file unless P3-D1 says otherwise.
<!-- /ref:delegate-p3-decisions -->

---

<!-- ref:delegate-p3-probe -->
## P3-T0 — The gating probe: can the 16K coder emit APPLICABLE structured edits?

**Why this exists.** Every argument for P3-D1(B) on this page is **mechanism** reasoning — both
walls, the eliminated sibling-drop class, first principle 2, the free apply path. Session 132
recorded five findings that got the mechanism right and the **magnitude** wrong, and session 133
continued it in both directions. Mechanism is derivable by reading; magnitude and reachability
are not (`feedback_measure_magnitude_not_estimate`). Freezing P3-D1 on mechanism alone repeats
that error at design scale — **and here the only measurements that exist point the other way**
(Diff-XYZ on Qwen2.5-Coder: 7B 0.03 / 32B 0.24 on diff generation; see P3-D1).

**The question REFRAMED (s135).** The earlier framing — *"can it emit a well-formed anchor"* — is
largely answered for free: `format` enforces schema conformance, and `ref:structured-output`
records it as 100% reliable. **So the probe must measure exactly what `format` cannot
guarantee**, which is three things, none of them syntactic.

**Pre-registered criteria** (all on the real 16K coder, all decided before running — a criterion
chosen after seeing output is not a measurement):

1. **Anchor fidelity.** Does the emitted `old_string` occur in the target **exactly and
   uniquely**? `patch_file` already checks precisely this, so the harness is free and the
   negative control is obvious.
2. **No degeneration to whole-file.** Record `len(old_string) / len(file)` per operation.
   **This is the criterion that can kill the design**: Aider measured a weak model placing the
   entire source file in the ORIGINAL block and the entire updated file in the UPDATED block. If
   that happens at 14B, (B) pays for the target **twice** — the exact bound it exists to escape —
   T-122's rationale evaporates, **and the run still reports success.** A pass on criteria 1 and
   3 with a failure here is the dangerous outcome, because nothing else surfaces it.
3. **Applicability, never exact match.** Success = the operation list applies cleanly *and* the
   result passes the run's own acceptance. Diff-XYZ scores equality with a reference diff, which
   is a strictly harder question than ours and is why its numbers bound the mechanism but not the
   magnitude.

**Method:**

- **Target:** one file from T-122's blocked set that fails on the **window** only —
  `parser.py` or `intake.py`.
- **NOT `loop.py`.** It produced nothing in 7,066 s at 32K, so it measures throughput and would
  say nothing about output language. (It is also the file whose refusal at 16K took 0.48 s — the
  contrast worth keeping: T-112 refuses what cannot fit before spending anything, while nothing
  refuses what cannot finish, T-131.)
- **Change:** small, real, on a file the whole-file path cannot reach at all today.
- **N attempts**, reporting the distribution and the failure modes — not a single run.

**Write the apply-side negative control BEFORE the probe.** Session 133 recorded a delegated
model inverting `applies_to` (`rubric.get("applies_to") != mode`, which refuses when the key is
ABSENT) with the case spelled out in its brief; the negative-control test is what caught it. A
structured edit language is strictly harder to emit correctly than a boolean check. The control:
a case whose anchor **cannot** match, asserting a loud failure rather than a silent no-op.

**A cheap variant worth pricing in the same pass.** Diff-XYZ found *udiff-l* — explicit
`ADD`/`DEL`/`CON` tags rather than terse markers — best for small models, attributing it to
control tokens being *"unambiguous and rare."* A JSON schema with named fields is already that
shape, but if criterion 1 or 2 fails, **verbosity of the operation vocabulary is the first knob
to turn**, before abandoning (B).

**What each outcome decides:**

| Probe result | Consequence |
|---|---|
| Applies reliably, no degeneration | Freeze P3-D1 on **(B)**, size-gated per the E-D1 split; author P3-D4's constraints text and P3-D5's ladder rungs **from what the probe needed** |
| Degenerates to whole-file (criterion 2) | **(B) buys nothing** — it is the status quo with an edit language on top. T-122 → (c). |
| Anchors unreliable (criterion 1) | The field has no implementation; **T-122 collapses to (c)** — route large edits to Claude — by measurement, consistent with `ref:delegate-non-goals` |
| Mixed / fixable with prompt or vocabulary work | The cost s126 left unpriced now has a number; re-weigh against (c) with it, and run E-D1's prescribed corpus-hardening re-run before any default-mode change |
<!-- /ref:delegate-p3-probe -->

---

## Acceptance (from `ref:delegate-phasing` § P3, made concrete)

**To be written once P3-D1 freezes.** Recorded now so the shape is not forgotten:

- Assertions must be **capable of failing for the reason they exist** (first principle 6; s133's
  A5). An assertion that a prompt "contains the objective" passes on any layout and teaches
  nothing; the property under test is **order and prefix stability**, in
  `prompt_eval_duration_ms`.
- **`context.callers` needs a test that fails today** — the field is currently accepted and
  ignored, so any test written against present behaviour would encode the bug
  (`feedback_review_rederive_invariants`).
- The suite fakes `chat` and is structurally blind to what a model is *asked*. Anything P3
  changes about the judge's payload re-runs **`make accept-p4`** (~35 s, real Ollama).
- Expect the first failure of any newly-tightened check to be **in the fixture** (s133, A5).

---

## Build steps

**Not yet ordered.** P3-T0 runs first and gates P3-D1; build steps are authored after the
register freezes. P3-D6 (`context.callers`) is independent of the probe and could lead.
