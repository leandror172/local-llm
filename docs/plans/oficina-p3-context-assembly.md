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

**This entry has been revised three times. All three are recorded, because the second one
reinstates something the first removed, and the third finds that the mechanism had already been
BUILT AND MEASURED in this repo and the record was never consulted.**

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

**Revision 3 (s136) — the apply mechanism was never open, and two arguments on this page were
built on falsified claims.** Prompted by re-reading the primary records the reading guide names.
Four corrections, each from a primary source in this repo:

1. **`ref:oficina-write-model-report` arm A *is* (B)'s apply path, built and measured s124** —
   *"model returns only the rewritten function; code locates the span (`ast`), reads `old_string`
   from disk, exact-replace; apply-failure mode: none — 100% by construction."* This entry
   presented the anchor question as open. It was closed twenty sessions ago, on our own coder.
2. **The `old_string`-emission framing was a category error.** The harness constructs the anchor;
   the model never reproduces bytes. A model that emits its own anchors is **arm C**, a different
   arm, also already measured — see the corrected mechanism block below.
3. **The udiff-l argument was falsified by this session's own survey and left standing here.**
   `ref:symbol-addressed-editing-survey` § 0 records that udiff-l is *"the **worst** format at
   every size (7B **0.00**)"* and that marker collision is the paper's *hypothesis 2*, **which it
   rejects**. The "(b) our schema is structurally udiff-l" transfer argument below rested on both.
   *This is the § 0 lesson recurring one hop later: the correction landed in the survey's summary
   and not in the body that consumed it.*
4. **`locate_unit`'s resolver was decided before the survey proposed SCIP** — T-104's own
   future-work line names `ast` + `go/parser`, and the seed already handles the decorator span.
5. **The vision set had never been checked against THIS entry.** Doing so found the T-122 remedy's
   actual code path (E-D9 / `_context_overflow`), an uncited argument that lands on the flywheel
   (first principle 8 + token-level diff masking), a principle that cuts against this entry's own
   token-cost framing (principle 3), a stance whose *subject* disappears rather than its risk
   (E-D6), and a "who chooses" decider that is weaker than it reads (E-D2). See
   § "Vision-level reconciliation (s136)" below. **This is the fourth consecutive session in which
   re-grounding changed a P3 conclusion** — the guide's warning is now self-evidencing.

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

**Evidence FOR (B) — and the strongest citation is first principle 1, which was never quoted.**

*"Harness code does all mechanics (**locate**, fetch, splice, verify, log); models only decide
content."* **Locating is named, in the founding text, as harness work.** An emitted string anchor
makes the *model* locate — it reproduces bytes so the harness can find them again. A symbol name
makes the *harness* locate. That puts anchor-**emission** on the wrong side of the design's
founding line independently of any benchmark, and it is the cleanest argument on this page.

**First principle 2 supports (B) too, but only on one of its two clauses.** *"Structured output
only — no free-form tool use by local models"* applies directly: `format` is **100% reliable**
(`ref:structured-output`), and the whole-file status quo is the one place the loop does *not* use
structured output. The clause revision 2 elided into it — *"models request (typed JSON);
deterministic fetchers fulfill"* — is about **context requests**, not edit responses. Cite the
first clause; do not join them.

**Mechanism, within (B) — CORRECTED s136. This was built and measured in session 124.**
`ref:oficina-write-model-report` benchmarked three apply arms on `my-python-q25c14`, 108
generations, 0 errors — and **arm A is precisely (B)'s apply path**:

| Arm | Model returns | Applied by | Apply-failure mode | Output tokens (small/med/large) |
|---|---|---|---|---|
| **A. code-anchored** | **only the rewritten unit** | **code locates the span (`ast`), reads `old_string` from disk**, exact-replace | **none — 100% by construction** | **25 / 25 / 25 — size-invariant** |
| B. whole-file | the complete modified file | overwrite | silent: drops/paraphrases unchanged code | 40 / 134 / 310 |
| C. model-anchored | aider SEARCH/REPLACE blocks | exact-match apply | loud: `old_string` absent → fail | 46 / 48 / 49 |

**The harness constructs the anchor; the model never reproduces bytes.** So `{old_string,
new_string}` is the *internal* representation that reaches `patch_file`, **not what the model
emits**. The model emits `path` / `kind` / `body`; `locate_unit` resolves the path to a span; the
harness reads the current text at that span as `old_string`. Line numbers are rejected for the
reason already stated — a batch is expressed against a moving target — but so is
anchor-*emission*, and for a stronger reason: **arm C is the model-emits-anchors variant, it was
measured in the same run, and the benchmark's own meta-finding argues against it.** The 14B
*"mis-generated the SEARCH/REPLACE parser … and fenced its own block contents at runtime — the
exact-format fragility arm C exists to measure … a cheap independent prior in favour of removing
exact-format reproduction from the model's plate (i.e. code-anchoring)."*

T-104's principle — *"oficina composes the ollama-bridge tools, it does not reimplement them"* —
therefore lands exactly: **the apply path is free, already hardened, and already measured at 100%
by construction.** What remains genuinely unpriced is what E-D1 actually named: the **spec
surface** — response-shape validation, deterministic import merging, the constants boundary.
Not the locator, and not the apply.

**Two riders on that principle, both s137.**

*(a) The benchmark's purity is correct THERE and would be a defect if carried forward.*
`writemodel_apply.py` opens with *"Pure functions, no model calls, no I/O"*, so
`apply_code_anchored` splicing a string in memory is right for a measurement instrument. But
`patch_file` is where the same operation acquires its atomic tmp+rename write and its uniqueness
check, and this entry's own § above records the original design as **`locate_unit` → `patch_file`**.
So: **the locator is the piece that graduates to production; the benchmark's applier is not.**
Writing that down here because the pure applier is the thing a future session will find first,
and nothing in the module says "do not ship this shape."

*(b) "Deterministic import merging" now has a size.* Item 6 above converts that line-item from a
named cost into a measured boundary — ~10.9% of Python top-level lines are unaddressable by
construction — and criterion 5 of P3-T0 goes looking for the failure it produces. It is still
unpriced as *work*; it is no longer unbounded as a *risk*.

**The resolver — in-process AST, NOT SCIP (decided s136; supersedes survey § 9).** The survey
recommends emitting a Serena-shaped tuple and resolving it against SCIP's `enclosing_range`
(*"~30 lines"*). Three facts already on file decide against it:

1. **The seed exists and already solves the span hazard.**
   `benchmarks/lib/writemodel_apply.py:36` `locate_function` returns a span whose *"start = the
   first decorator's line if decorated, else the `def` line"* — the exact hazard the s135 census
   re-derived by inspection and credited SCIP with solving. Local-model generated,
   `my-python-q25c14`, **verdict 2, used as-is.**
2. **T-104 already chose this route:** *"`locate_unit` for Python (`ast` — the benchmark's
   `locate_function` is a working seed) + Go (`go/parser`)."*
3. **A precomputed index is stale inside a batch.** Operation 1 of an N-operation batch
   invalidates the index for operations 2..N — structurally the same objection this entry already
   makes against line numbers, and N-scattered-changes-in-one-large-file is the entire reason (B)
   exists over (A). `ast.parse` of the current buffer has no such problem.

Corollary: `locate_unit` stays a **per-language `LanguagePack` member** (`ref:unit-addressing-census`
§ Consequence — the fifth member, on a seam T-92 Phase 4 validated with measured evidence), which
a single protobuf reader could not be. **The gap is real and named:** `locate_function` handles
*"only top-level functions (not methods)"*, and the census measured top-level addressing at
**69% of `loop.py`** versus **10%** dotted. **Extending the seed to dotted `Class.method` is the
build** — not a new architecture.

**Limits to carry into the schema so they are not rediscovered:**

- **Rename breaks symbol identity.** If `body` renames the unit, the address names the old and the
  body defines the new. Serena has a live bug in exactly this operation
  ([oraios/serena#576](https://github.com/oraios/serena/issues/576)).
- **CODESTRUCT's +20.8pp includes FUZZY selector matching** (`FuzzyMatch`; *"guf can match
  get_user_file"*), while § 3's recommendation is fail-loud on ambiguity. Do not quote the number
  as though it transfers to an exact-match resolver.
- **The binding output constraint is the ~800-token 14B reliability ceiling**
  (`.memories/KNOWLEDGE.md:55`), not `num_predict`. Python's 17-line median unit sits well inside
  it; **Go's largest measured unit is 159 lines ≈ 2,000 tokens and does not.** The census called
  that *"comfortably inside `num_predict`"* — true, and the wrong constraint. Same class as E-D9's
  own lesson one level up.
- **Separate the budgets** (SWE-agent, **+3.0 points** measured): *"edit didn't apply"* must not
  consume the *"output didn't parse"* budget. That single choice is why a trajectory survives 33
  failed edits on a format budget of 3. Cheap now, expensive to retrofit.

**Vision-level reconciliation (s136).** The reading guide requires re-grounding against
`docs/vision/coding-delegate/` before amending a phase plan, *and* checking the as-built facts.
Both passes were done here for the first time on this entry. Five results:

1. **E-D9 IS the code path by which (B) fixes T-122, and this entry never named it.** Verified
   as-built at `loop.py:263` — `_resolve_num_predict` returns
   `min(EDIT_NUM_PREDICT_CAP, max(NUM_PREDICT, ceil(len(current_file) / 4) * 2))`. **That `* 2` is
   the feasibility band**, and T-112's `_context_overflow` adds the result to the input estimate
   before comparing against the live `/api/show` ceiling. So under (B) the resolver sizes to the
   **unit**, not the file — which shrinks the guard's own arithmetic and thereby changes *which
   files are feasible at all*. The remedy is two named functions, not a new subsystem. **Any
   build step for (B) starts here**, and E-D9's rule needs a third branch rather than an edit.
2. **First principle 8 + the DPO evidence give (B) an argument nobody has made — and it lands on a
   founding fact.** `ref:delegate-evidence-dpo`: *"whole-block pairs teach style collapse;
   **token-level diff masking** (credit only the changed tokens) is the documented correction."*
   **Symbol-addressed output is token-level diff masking, structurally** — the model only ever
   emits the changed unit, so a (chosen, rejected) pair is already scoped to it. Under whole-file,
   every DPO pair is a whole-block pair, i.e. the documented pitfall. Fact 3 of five
   (`ref:delegate-vision`) is the flywheel; this is the only argument on this page that touches it.
3. **First principle 3 cuts AGAINST this entry's token-cost framing, and T-122 survives it
   anyway.** *"Async exists to buy quality, not speed … latency is spent where it buys verdict-2
   outputs."* So arm A's **25 vs 310 output tokens is not the argument** — the design has already
   decided it does not optimize for cost, and that is exactly why E-D1 discounted the same number
   in s126. What survives is **feasibility**: a file that cannot be edited *at all* is not a cost
   complaint. State the band; stop citing the token count as though it persuades.
4. **E-D6's subject disappears rather than its risk shrinking.** *"No omission heuristic in v1 …
   omission detection is behavioral."* Under (B), code outside the addressed span is **structurally
   impossible to omit** — the model never emits it, so there is nothing for a heuristic to detect.
   The s127 drift class (module docstring deleted in **4 of 4** runs, including runs that forbade
   it) cannot occur. **Inside** the span it is unchanged: a model can still paste tests into a unit,
   so `max_verbatim_run_vs_tests` stays live and P3-D5's reading holds.
5. **E-D2's precedent may not bind "who chooses" the way this entry argues.** The recommendation
   is caller-declares, on the ground that shape depends on *"a **budget**, not an unambiguous
   repository fact"*, with the deciding constraint that auto-select must emit something when
   `_context_limit is None`. **Under the size-gated-fallback framing this entry itself adopts, that
   constraint dissolves:** an unknown ceiling means *do not fall back*, i.e. keep today's whole-file
   default — the same fail-safe direction `transport.model_context_limit` already documents. This
   does not decide the sub-fork, but the stated decider is weaker than it reads. **Re-argue it
   before freezing.**

*Also verified as-built: `LanguagePack` has exactly four members (`compile_stage`, `test_stage`,
`system_prompt`, `coder_model`, `evaluator.py:322`), so `ref:unit-addressing-census`'s "fifth
member" claim is correct as of this commit.*

**Evidence AGAINST (B), measured, on our own model family — verified s135.** Diff-XYZ
([arXiv 2510.12487](https://arxiv.org/html/2510.12487v1)) benchmarks **Qwen2.5-Coder**, our coder
base. *Diff Generation*, exact match: **0.5B 0.00 · 3B 0.00 · 7B 0.03 · 32B 0.24** —
*"None of the open-source models achieve comparable performance on Diff Generation."* **Our 14B
coder sits inside that gap.** Two further results bear on the design:

- ~~*"search-replace is a strong default for most larger models, while udiff-l achieves the best
  scores for smaller models"* — mechanism: marker collision.~~ **STRUCK s136 — falsified by this
  session's own survey and left standing here.** `ref:symbol-addressed-editing-survey` § 0 and § 5:
  udiff-l is **the worst format at every size** (diff-generation EM — udiff-l 1.5B 0.00 / 3B 0.00 /
  7B 0.00 / 32B 0.01 vs search-replace 0.20 / 0.14 / 0.28 / 0.68), and marker collision is the
  paper's *hypothesis 2*, **which the authors reject**: *"this verbosity increases complexity
  rather than actually helping the models"*; *"smaller open models benefit little from any
  formatting choice."* The survey's instruction is **"do not ship ADD/DEL/CON tagging."**
- Aider's own benchmark records GPT-3.5, when it emitted diffs at all, *"often uses it in a
  pathological manner, placing the entire original source file in the ORIGINAL block and the
  entire updated file in the UPDATED block — strictly worse than just using the whole edit
  format."*

**How much of that transfers, and how much does not — CORRECTED s136.** The magnitude is NOT
derivable from these numbers (`feedback_measure_magnitude_not_estimate`). But the deeper point is
that **this evidence is about arm C and (B) is arm A**: every format Diff-XYZ scores is one where
the model reproduces existing bytes. Under (B) it reproduces none. Three further reasons the
benchmark is not our configuration: (a) its formats are **text parsed from free output**, while
(B) is **schema-enforced via `format`**; (b) ~~a JSON schema with named fields is structurally
udiff-l, the variant the paper found best for small models~~ — **STRUCK s136. Both halves are
false.** `ref:symbol-addressed-editing-survey` § 0: udiff-l is *"the **worst** format at every
size (7B **0.00**)"*, and marker collision is the paper's *hypothesis 2*, **which it rejects**
(*"this verbosity increases complexity rather than actually helping the models"*). The claim
entered from a search-result summary, was falsified by this survey, and was left standing in the
body that consumed it; (c) its metric is **exact match against a reference diff**, while our
criterion is an **applicable** edit. `0.03` is not "3% success at our task."

**The pathological failure mode, re-aimed s136.** Aider's mode — the whole file inside the
ORIGINAL block — **cannot occur under (B)**, because the model emits no anchor to put it in. The
surviving failure of the same shape is **naming too coarse a unit**: the census measured
`EvaluatedLoop` at **438 lines, 69% of `loop.py`**, so a model that names the class instead of
the method pays for the target twice by a different route, and the run still *looks* successful.
**That is what P3-T0 must measure directly**, and it is still the silent one.

**Corroborating scaffolding costs, from our own evidence base:** SWE-agent carries a
*"model-error requery ladder for recovering from malformed actions"* and an *"edit+lint tool with
rollback"* (`coding-subagent-prior-art-webresearch.md:71-78`); Aider's `max_reflections = 3`
budgets re-prompts for *"lint/test failures **or malformed edits**"*
(`coding-subagent-prior-art.md:15`). Both built recovery machinery around this exact failure
class. That machinery is part of (B)'s unpriced cost.

**Who chooses.** Three sub-options were recorded, and one constraint was said to decide it. **The
constraint did not survive s136 and a fourth option — the one the code already implements twice —
was hidden by the two-way framing.** The sub-options as recorded:

- **auto-select at assembly** — a `_resolve_output_shape(assembly)` beside `_resolve_num_predict`
  (E-D9) and `_resolve_max_iterations` (T-114). Attractive because **T-112's guard is a refusal
  assembled from exactly the numbers a selector needs**: `_context_overflow` compares
  `ceil(len(prompt)/4) + _num_predict` against the live ceiling, and `_resolve_num_predict`'s
  edit branch computes `max(NUM_PREDICT, ceil(chars/4) * 2)` — *which is* the "pays for its
  target twice" arithmetic of the band.
- **caller declares** — validated at intake, with today's guard refusing loudly on a mismatch.
- **refuse-and-suggest** — no new runtime behaviour; `ContextBudgetError` names the remedy.

**~~The deciding constraint.~~ RE-ARGUED s136 — the decider does not hold, and it hid the option
the code already implements twice. Still NOT frozen: the probe gates the whole entry.**

The constraint as written: *under auto-select, when `_context_limit is None` the selector must
still emit something*, and `transport.model_context_limit` is a written record of this project
refusing that guess — *"an absent or unreadable value yields None rather than a guess: guessing
high silently disables the caller's fit check, guessing low aborts valid work."* Auto-select would
place a guessing selector beside a resolver documented as refusing to guess; caller-declares
removes the question rather than answering it.

**It fails on two counts, one logical and one measured.**

1. **It conflates guessing a ceiling VALUE with choosing a DEFAULT under absence** — and the
   consumer of that same `None` already demonstrates the correct move, one function away
   (`loop.py:536`): `if self._context_limit is None: return None` — *"an unresolvable ceiling
   disables the guard; the caller was already told once, at resolve time."* `_context_overflow`
   does not guess; it **declines to act**. A `_resolve_output_shape` returning `"whole_file"` on
   `None` is the identical move: keep today's behaviour, change nothing. **The precedent cited as
   forbidding auto-select is in fact the template for handling absence.**
2. **The case is close to hypothetical for oficina's own models — measured, not assumed.** All
   three personas the system uses declare the window explicitly:
   `modelfiles/python-q25c14-16k-qwen25c14.Modelfile:4`, `go-…:4`, `judge-…:5` — all
   `PARAMETER num_ctx 16384`. `None` therefore arises only when `/api/show` itself fails, i.e.
   Ollama is unreachable or wedged, in which case the run dies at the first generate regardless.
   *(Boundary: the Modelfiles were read; live `/api/show` output was not re-confirmed.)* **A
   design fork was closed on a code path that does not execute** — s132's calibration lesson at
   design altitude.

**The option the two-way framing hid: DERIVE WITH OVERRIDE.** E-D9 and T-114 are both
*derive-from-mode, explicit-wins* (`if self._explicit_num_predict is not None: return …`;
`if self._explicit_iterations is not None: return …`). That is neither "auto-select" nor "caller
declares" — it is the **house pattern for exactly this class of question**, established twice, and
recording the fork as two-way made the synthesis invisible.

**E-D2 now points the other way, and the entry had it backwards.** The stance is *"no new spec
fields"* for derivable facts. The previous text argued caller-declares survives it because shape
depends on *"a budget, not an unambiguous repository fact"* — but the budget is `num_ctx` +
`num_predict`, and **`_context_overflow` computes that comparison today**. Shape is as derivable
as mode is. The s134 `output_shape` field was rejected for the wrong reason (duplicate axis);
**the E-D2 objection is a separate, still-live one, and it tells against caller-declares.**

**First principle 1 seconds it.** *"Harness code does all mechanics … models only decide
content."* Choosing an output encoding from a budget is mechanics. Pushing it to the caller
reproduces the objection this entry already makes against option (D): *"it moves intellectual work
back to Claude, which is the cost oficina exists to avoid."* Today Claude must know which 6 of 27
files are blocked; a derived shape is what makes T-122 disappear for the caller.

***Recommendation (re-argued, NOT frozen):* `_resolve_output_shape(assembly)`, third in the
sequence at `loop.py:550-552`, following E-D9's shape exactly** — an explicit
`deliverable.output_shape` wins if present; otherwise derive from the numbers `_context_overflow`
already compares; return `"whole_file"` when the ceiling is unknown. Emit the choice as an event
(first principle 5) so a run's shape is never inferred after the fact.

**Two costs, both real:**

- **P3-D5's widening becomes live** — if both shapes occur in edit mode, `applies_to` may need to
  key on `(mode, shape)` rather than `mode`, touching P4's frozen T-130 design. **This does not
  discriminate between the sub-options**: the shape varies under caller-declares too.
- **A third resolver is a third thing that can be wrong.** Mitigated by the pattern being
  twice-established, and by the negative control being cheap.

**Both open questions answered by the user, s136:**

1. **An *optional* `output_shape` override does NOT violate E-D2's spirit.** E-D2 refuses a
   *required* field for a derivable fact; an override is the E-D9/T-114 shape, where the derived
   value is the contract and the field only pre-empts it. **Derive-with-override is clear to
   build.**
2. **Recording the shape for reproducibility: leaning yes, not decided.** Noted as *"might be a
   good idea"*, so it stays open. **Synthesis offered, not user-stated:** first principle 5
   (*everything is an event*) already supplies most of what reproducibility wants — emitting the
   **chosen** shape on the run ledger makes a completed run's encoding recoverable without making
   the field required, and it is the same move `AssemblyDone`'s additive `mode` key made for E-D2.
   The residual question the ledger does *not* answer is **forward** reproducibility: a re-run on a
   different persona derives a different ceiling and could silently pick a different encoding. If
   that matters, the answer is a spec field; if only forensics matter, the event suffices.
   **Decide with the probe's results, not before.**

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
6. **The refusal region is LARGER than item 5 states, and the census already measured it
   (s137).** `ref:unit-addressing-census` reports *"89.1% of Python top-level lines already sit
   under a name"* — and **the complement is the answer to a question nobody asked it.** The
   remaining ~10.9% is imports, module constants and the module docstring: statements with no
   name, therefore **unaddressable by a dotted path by construction**, not by omission. Item 5's
   list is about constructs whose *address is unstable*; this is a class with **no address at
   all**. The two were never connected, and it is the same number the census published.

   **Consequence for (B), stated as a bound rather than discovered later:** an edit that must
   add a top-level statement — most commonly **a new import** — cannot be expressed as
   `replace_unit`. `ref:oficina-write-model-report` § AMENDMENT already named *"import merging"*
   among the edit-language costs *"never priced"*; it is still unpriced, and this is where the
   bill lands. **(B)'s coverage is therefore bounded by the fraction of real edits needing no
   new top-level statement, and that fraction is UNMEASURED** — the census counted *lines*, not
   *edits*, so it does not answer this and must not be read as if it did.

   The mechanical fallback costs nothing (whole-file for that iteration, per item 5). What it
   costs is the **feasibility win**: an edit needing an import falls back to the path that
   cannot reach the file, so `loop.py` stays unreachable for exactly that class of change.

   **Recorded as executable spec, not prose** (`benchmarks/lib/test_writemodel_apply.py`):
   `test_find_module_constant_is_not_addressable` and `test_find_import_is_not_addressable`
   assert `[]`. A test cannot go stale silently, which is the failure mode this document has
   now recorded four times against itself.

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

**GATED on P3-T0, which is now the only thing that can decide this entry.**

**The criteria live in ONE place — § P3-T0 — and are not restated here (s136).** This section
previously carried a second copy, and the two drifted: the P3-T0 copy was rewritten while this one
still asked for *"the emitted `old_string`"*, a mechanism the corrected entry does not propose.
That is precisely the defect T-130 fixed by deriving `_change_heading` from `LoopResult.mode` —
**one source, no second field to drift** — and it is worth noting that the duplication survived a
full revision pass **within the same document**, unread.

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

### P3-D6 — `context.callers` is declared and consumed by nothing — **FROZEN AND BUILT (T-133, s136)**

**Resolution: recommendation (i) shipped; (ii) stays deferred with T-77 as its named trigger.**
`callers` is now a stable prompt segment of its own between `context` and `current_file`; it and
`context.files` render through one `workspace._rendered_file_block`. Intake rejects a missing
caller path on the existing `RULE_CONTEXT_FILE_MISSING` — **the fetch is what makes an unreadable
path a silent empty block**, the same failure one layer down. Sibling `acceptance.validators`
**deleted**, and the **P3-vs-Axis-B routing conflict resolved in P3's favour by mechanism**:
`validators` is not a *kind*, so E-D8's trigger never covered it. Suite **408→416**,
`make accept-p4` green (the prompt layout changed, and the suite fakes `chat`). 5 of 8 new tests
were RED first, verified by running them.

*The original entry follows, unedited — the evidence is what made the remedy obvious.*

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

**Why this exists.** The remaining arguments for P3-D1(B) are **mechanism** reasoning — both
walls, the eliminated sibling-drop class, first principle 1's *locate*, the apply path. Session
132 recorded five findings that got the mechanism right and the **magnitude** wrong, and session
133 continued it in both directions. Mechanism is derivable by reading; magnitude and reachability
are not (`feedback_measure_magnitude_not_estimate`).

**What s136 removed from this probe's job, and what it added.** The apply half is **not open** —
arm A of `ref:oficina-write-model-report` measured it at *"100% by construction"*, 25 output
tokens flat across all three size buckets. And the Diff-XYZ counter-evidence scores **arm C**
(model-emitted anchors), not arm A. So the probe no longer asks *"can the coder produce a working
anchor"*. It asks the two questions arm A never covered:

- **arm A resolved only top-level functions** (`locate_function`: *"Only top-level functions (not
  methods)"*), and the census says dotted addressing **is** the decision (`loop.py` 69% → 10%);
- **arm A's corpus was 20 structurally-identical `op_k` fillers** — the report's own words,
  *"the best possible case for whole-file fidelity … the synthetic corpus accidentally optimized
  for whole-file"*, and *"you cannot conclude 'whole-file is safe' from a test that did not
  stress it."*

**Pre-registered criteria — REWRITTEN s136** (all on the real 16K coder, all fixed before running;
amending them *before* a run is plan maintenance — the rule forbids only choosing them *after*
seeing output). The previous set asked whether *"the emitted `old_string`"* matched and recorded
`len(old_string)/len(file)`: under (B) the model emits no `old_string`, so those criteria measured
arm C, a mechanism this entry does not propose.

1. **Address fidelity.** Does the emitted `path`/`kind` resolve to **exactly one** unit in the
   target? Multi-match and no-match are both hard failures (§ 3 — never "first match wins").
   **Half of this is deterministic and belongs in the 408-suite, not on the GPU:** given a path,
   `locate_unit` either resolves uniquely or fails loud, and *that* is the negative control. What
   needs the live coder is only whether it **names a unit that exists**.
2. **No degeneration to a coarse unit.** Record `len(resolved span)/len(file)` **and**
   `len(body)/len(file)` per operation. The failure mode is **not** Aider's — the model cannot
   paste the file into an anchor it does not emit — it is **naming the class instead of the
   method** (`EvaluatedLoop` = 438 lines, 69% of `loop.py`). **Still the criterion that can kill
   the design, and still the silent one.**
3. **Applicability, never exact match.** Unchanged. Success = the operation list applies cleanly
   *and* the result passes the run's own acceptance — never equality with a reference diff.
4. **Response-shape discipline** (added s136). Does `body` contain **only** the unit — no fences,
   no prose, no neighbouring code? The same 14B *"fenced its own block contents at runtime"* in
   the s124 benchmark, and E-D5 already strips fences at the write step for exactly this reason.
   This is the *"response-shape validation"* item E-D1 priced and nobody has built.
5. **What the coder does when it needs a unit it CANNOT address** (added s137, from the
   coverage bound recorded at P3-D1 item 6). The predicted behaviour — **prediction, to be
   confirmed or falsified, not assumed** — is that a model needing `import itertools` emits it
   as the first line of `body`, producing a **function-local import**.

   That is the reason this criterion exists rather than being folded into criterion 4: a
   function-local import is legal Python, it passes the tests, and it **slips past all four of
   the criteria above**. It is not a coarse unit (2), it applies cleanly (3), and it is not a
   fence or prose or *neighbouring* code (4) — because it is *inside* the addressed unit. A
   silent failure with no criterion pointing at it is exactly what this probe exists to
   prevent, so it gets its own count.

   Record the rate, not just the occurrence: **what share of attempts needed a top-level
   statement at all** is the unmeasured fraction P3-D1 item 6 names, and this probe is the
   cheapest place to get a first read on it.

**The method below names ONE vehicle for TWO questions, and the vehicle cannot run the
target — corrected s137.** `run_tests` writes the edited module to `module_under_test.py` in a
tmp dir and runs generated tests that `import *` from it. A real `parser.py`, with its real
imports and the repo's real test suite, does not fit that harness at all. **But oficina already
does exactly this** — s137 drove four runs against real files with real committed tests in a git
worktree. So the split is:

| Question | Vehicle | Why |
|---|---|---|
| Criteria 1/2/4/5 — can the coder NAME a unit, and how coarsely? | **the benchmark** (arm D, `--corpus class`) | needs a controlled A/B against whole-file on one corpus, many runs, cheap |
| Criterion 3 — does it work end-to-end on a file whole-file cannot reach? | **oficina** | already runs real files against real tests; the benchmark would have to rebuild it |

Making the benchmark run real files would be reimplementing oficina inside it — the exact
inversion of the T-104 principle this entry cites elsewhere (*"oficina composes the
ollama-bridge tools, it does not reimplement them"*).

**Method:**

- **Target:** one file from T-122's blocked set that fails on the **window** only —
  `parser.py` or `intake.py`. **Via oficina, not the benchmark** (see above).
- **NOT `loop.py`.** It produced nothing in 7,066 s at 32K, so it measures throughput and would
  say nothing about output language. (It is also the file whose refusal at 16K took 0.48 s — the
  contrast worth keeping: T-112 refuses what cannot fit before spending anything, while nothing
  refuses what cannot finish, T-131.)
- **Change:** small, real, on a file the whole-file path cannot reach at all today.
- **N attempts**, reporting the distribution and the failure modes — not a single run.

**Two corpora, and only one of them is gated — do not conflate them (s137).** The hardening
below refers to `writemodel_corpus.py`, the *generated benchmark* corpus that GPU runs consume.
That work is governed by an E-D1 trigger which `coding-delegate/.memories/QUICK.md` records as
**not fired** (*"harden write-model corpus IF a real edit run drops sibling code … docstring
deletions are DOC omissions, not code"*). This plan asks for the same hardening on a **different
rationale** — a fair comparison, since the existing filler was *"the best possible case for
whole-file fidelity"* — which is not the trigger's rationale and does not fire it. **Two live
rationales for one piece of work, one of them gated: recorded rather than silently resolved**
(the "grep the plans, not just the code" lesson from T-133). The *unit-test* fixture in
`test_writemodel_apply.py` is a third thing entirely and is gated by nothing; it was hardened in
s137 for the span hazards of `ref:unit-addressing-census` Finding 3.

**Vehicle — do not build a new probe (s136).** All three apply arms already exist in
`benchmarks/lib/writemodel_{apply,corpus,bench}.py`, driven by `run-write-model-bench.sh`. The
unbuilt halves are (i) dotted `Class.method` resolution in `locate_function` and (ii) **E-D1's own
prescribed corpus hardening** — *"heterogeneous filler, 500+ lines, re-run, revisit"* — which is
the comparison this plan elsewhere notes *"has never been run on a fair corpus."* Hardening the
corpus answers the whole-file omission question **and** criterion 2 in one run, and it costs GPU
time and no design surface.

**Write the resolve-side negative control BEFORE the probe.** Session 133 recorded a delegated
model inverting `applies_to` (`rubric.get("applies_to") != mode`, which refuses when the key is
ABSENT) with the case spelled out in its brief; the negative-control test is what caught it. The
control is now **deterministic and free**: a `path` that resolves to **nothing**, and a `path`
that resolves to **two** units, each asserting a loud failure rather than a silent no-op or a
first-match win. Both belong in the suite. **The test corpus must include a decorated symbol and
a documented symbol** (`ref:unit-addressing-census` Finding 3) — the span hazards are invisible to
a corpus of plain functions, and in Go a doc comment is on essentially every exported symbol, so
it fires constantly rather than rarely.

*(STRUCK s136 — a "cheap variant" recommending `ADD`/`DEL`/`CON` udiff-l tagging as the first knob
to turn. `ref:symbol-addressed-editing-survey` § 0 falsifies both its premise and its mechanism:
udiff-l is the worst format at every size and the paper rejects marker collision. The survey's own
instruction is **"do not ship ADD/DEL/CON tagging."**)*

**What each outcome decides:**

| Probe result | Consequence |
|---|---|
| Resolves uniquely, units stay fine-grained | Freeze P3-D1 on **(B)**, size-gated per the E-D1 split; author P3-D4's constraints text and P3-D5's ladder rungs **from what the probe needed** |
| Names coarse units (criterion 2) | **(B) buys little** — the target is still paid for twice, by a different route. Re-weigh against (c); a prompt/vocabulary fix is tried before abandoning |
| Names units that do not exist (criterion 1) | **T-122 collapses to (c)** — route large edits to Claude — by measurement, consistent with `ref:delegate-non-goals` |
| `body` carries fences/prose/neighbours (criterion 4) | Not fatal — this is the response-shape validation E-D1 priced; it becomes a build item with a measured need rather than a predicted one |
| **Hardened corpus shows whole-file dropping code** | **E-D1's own fallback trigger fires on its own prescribed evidence.** The narrow ask stops being narrow — revisit default-vs-fallback, which E-D1 explicitly reserved for this |
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
