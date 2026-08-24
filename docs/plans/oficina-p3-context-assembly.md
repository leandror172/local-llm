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
## Decision register (P3-D) — **D1 FROZEN (s140)** · D6 FROZEN AND BUILT · D2–D5, D7–D10 OPEN

House rule: each entry states the fork, the constraints that bound it, and a recommendation.
Freeze on review with the user; reverse only with new evidence once frozen.

### P3-D1 — What the model EMITS when editing — **DECIDED 2026-08-20 (s140) — (B), on FOUR operations**

**DECISION — (B), model-emitted structured edit operations.** The model returns typed JSON
naming a unit and supplying its new body; the harness resolves the name to a span and splices.

**The "who chooses" half is NOT decided here.** It is lifted to **P3-D10** (s140). Criterion 5
settled what the model *emits* and says nothing about who *selects* the shape, and § "Vision-level
reconciliation" item 5 requires that half to be **re-argued** rather than carried — a fork left
inside a frozen entry reads as settled, which is the s135 failure this register already made once.

**What decided it** — all pre-registered before running, all on `my-python-q25c14-16k`:

| criterion | result |
|---|---|
| 1 — address fidelity | **12/12 resolve to exactly one unit.** No no-match, multi-match, kind-mismatch |
| 2 — degeneration to a coarse unit | **0/12** address >50% of the file; span median **0.047**. The criterion that could kill the design, and it did not occur |
| 4 — response shape | **0/12** defects — no fences, no prose, no neighbouring code |
| output cost | **43 tokens FLAT** at every size, against whole-file's 120 / 216 / 479 |
| 5a — behaviour at the bound | a **coverage** bound, not an addressing failure: 1/2/4 stayed clean, tokens stayed flat |
| 5b — how often the bound is hit | **23–48% of real edits** (487 measured). **Not a rare fallback** |

**Caveats carried INTO the freeze, because a frozen entry is quoted without them otherwise
(s137's own list):** n is **12 per arm** over **two** defect kinds (`scale`, `clamp`) on generated
classes; **whole-file also scored 100%** on that corpus, so it still does not stress omission —
E-D1's *"best possible case for whole-file fidelity"* is only partly retired by adding classes;
and the token ratio is a **floor**, since the large bucket is ~100 lines and `loop.py` is 638.

#### The operation vocabulary, RECONCILED at freeze (s140)

This entry named `ensure_import` / `remove_import` / `replace_module_docstring` and said the
census shows they *"close the entire non-def/class residue in both languages."* **True of
STRUCTURE, false of EDITS** — and nothing caught it because the two measurements sit 400 lines
and three sessions apart. The census enumerated what **exists** in a file (the complement of
def/class is imports and the module docstring, ~10.9%). 5b measured what **edits do**, and an
edit can *add* a top-level unit the static census never saw. `replace_unit` replaces; it cannot
create. **Static coverage ≠ edit coverage.** Neither document is wrong; they answer different
questions, and only one of them is the coverage question.

| # | operation | population (oficina src ≤40) | status |
|---|---|---|---|
| 1 | **`replace_unit`** — dotted `path` + `kind` + `body` | the addressable majority | **built and measured** (criteria 1/2/4) |
| 2 | *no new operation* — index assignments, add a `Constant` kind | **17.4%** | a **resolver gap**, not a construction bound |
| 3 | **`insert_top_level`** — imports · module docstring · **added** constants | 17.4% + 4.3% + 13.0% | **the largest population** |
| 4 | **`insert_unit`** — a top-level unit that does not exist yet | 17.4% | a gap this plan had **never named** |

**The magnitude was corrected AT the freeze, and the correction is roughly half (s140).** The 5b
remedy table asserts *"No new operation"* against the whole **30.4%** constant slice, while 5b's
own caveat (c) records that the count includes statements *"added **or changed**"*. Only the
**changed** half is convertible by a `Constant` kind — an **added** constant has a name but
nothing to replace, so it needs `insert_top_level` exactly as an import does. Measured over 487
real edits (`run-census-report.sh`): on oficina's own source the 30.4% splits **CONVERT 17.4% /
ADDED 13.0%**, and across cuts CONVERT ranges **6.4%–17.4%**. The unbounded cut overstates the
convertible share about **fourfold**.

**Consequence, and it reverses this plan's stated ordering.** The claim *"cheapest first and
largest first are the same thing"* is **false**: the resolver extension (17.4%) **ties imports
alone** (17.4%), while `insert_top_level`'s real population — imports **+** added constants **+**
docstrings — is strictly larger. **Cheapest-first survives on its own merits** (no new operation,
no schema change, no prompt text, and criterion 1 already measured `find_units` at 12/12 unique)
— but it is no longer *also* largest-first, and **30.4% must never be quoted as the resolver's
share.**

*Reproduction check, stated so the correction is auditable:* all six of s139's published 5b rows
reproduce on the new instrument — four **exact**, two off only by the single commit added since.
The split is **additive**; the published 23–48% headline does not move.

#### Attached at freeze — conditions, not commentary

- **Harness-side detection is MANDATORY, not an alternative to the operations.** 5a: the model
  **never refuses** — 24 of 24 attempts emitted a confident, well-formed, correctly-addressed
  operation — so the fallback cannot be triggered by a model signal. **14 of 24 emitted a
  function-local import and 10 of those 14 PASS ALL TESTS**, i.e. the failure is silent to
  criteria 1–4 *and* to the suite. Detection is two AST checks on output the harness already
  parses (does `body` contain an import; does it reference a name the target never binds), and
  it is first principle 1 — *"harness code does all mechanics"* — not a new burden.
- **Separate the budgets.** *"Edit didn't apply"* must not consume the *"output didn't parse"*
  budget (SWE-agent, **+3.0 points** measured). Cheap now, expensive to retrofit.
- **Rename breaks symbol identity.** If `body` renames the unit, the address names the old and
  the body defines the new. Serena has a live bug in exactly this operation (oraios/serena#576).
- **Multi-target assignment must REFUSE, not guess.** `A, B = 1, 2` is one node binding two
  names, so `["A"]` and `["B"]` resolve to the **same span** and replacing one rewrites both.
  `apply_unit` already contracts *"Refuses rather than guesses"*; this is the case that tests it.
- **ACCEPTANCE CONDITION — criterion 3.** This freeze rests on the benchmark half plus 5a/5b.
  If criterion 3's build shows the operation list does not apply cleanly to a real file and pass
  that file's real suite, **D1 reopens with evidence — not before.** Same shape as P4-D2's
  attached condition, which is the register's precedent for freezing a measured *fit* whose
  *end-to-end* half has not run.

---

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
  **~~close the entire residue~~ — CORRECTED AT FREEZE (s140). True of STRUCTURE, false of
  EDITS.** The census enumerated what a file CONTAINS; 5b measured what edits DO, and an edit can
  **add** a top-level unit the static census never saw — `replace_unit` replaces, it cannot
  create. The frozen vocabulary is **four** operations (see the DECISION block at the top of this
  entry), and the missing one is `insert_unit`. Left in place rather than reworded, because this
  sentence is the one a reader would otherwise carry forward.
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

**Who chooses — MOVED to P3-D10 (s140).** This entry froze on what the model EMITS. The
selection question, its four sub-options and the s136 re-argument now live in **P3-D10**, in one
place, so a fork does not sit inside a frozen entry reading as settled.

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
   remaining ~10.9% is imports and the module docstring: statements with no name, therefore
   **unaddressable by a dotted path by construction**, not by omission. Item 5's list is about
   constructs whose *address is unstable*; this is a class with **no address at all**. The two
   were never connected, and it is the same number the census published.

   > **CORRECTED s139 — this entry had CORRUPTED the census it cites, and the corruption was
   > the load-bearing part.** It read *"imports, **module constants** and the module
   > docstring"*. The census says the opposite in two places: its table classifies
   > `assign 64 (124 lines)` as **`named`**, and its text reads *"89.1% … already sit under a
   > name, and **the entire remainder is imports and module docstrings**."* A module constant
   > binds a name; it was never in the complement. **The census was right and is unchanged.**
   > What is true about constants is narrower and fixable: `KINDS = ("Function", "Method",
   > "Class")` and `_UNIT_NODES` covers only `FunctionDef`/`AsyncFunctionDef`/`ClassDef`, so
   > **the resolver does not index assignments** — a gap in our code, not a property of Python.
   > This matters because criterion 5b measured the constant as the **largest** unaddressable
   > class (30.4% of oficina's own edits vs 17.4% for imports), so the mislabel had moved the
   > biggest slice of the problem into the category marked *unfixable by construction*.
   > Same shape as s136's finding, running the other way: there a falsified claim survived in
   > the body that consumed it; here a **correct** claim was corrupted by its consumer, which
   > then cited the original as its authority. Propagated to
   > `test_writemodel_apply.py`, also corrected.

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
### P3-D10 — WHO CHOOSES the response shape — **OPEN, re-argued, recommendation standing**

**Why this is its own entry (s140).** P3-D1 froze on measurement: criteria 1/2/4 and 5a/5b
settled what the model **emits**. None of them touch who **selects** whole-file versus
symbol-addressed for a given run — that is argument-bound, not measurement-bound. Freezing an
argued half alongside a measured one, inside one entry, is how s135's register got stuck at D1
while reading as though it had moved.

**Status correction, made while lifting this out.** s136's reconciliation item 5 ends *"Re-argue
it before freezing"*, and s140's first draft of this entry read that as outstanding work. **It is
not: the re-argument was done in s136**, in the material below, and it ends in a recommendation.
What is outstanding is the **freeze**, not the argument. Recorded because the same misreading
would otherwise recur every time someone follows the s136 pointer.

**Everything below is moved verbatim from P3-D1 (s140), not restated.** The criteria drifted once
in this plan by existing in two places (s136); this entry is the one place.

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

---

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

   **RECLASSIFIED s140 — this is a BUILD, not a probe, and P3-D1 is frozen without it.** The
   reclassification was made in s139 and recorded only in `.claude/session-log.md`; written here
   because that is where a future session looks. Two facts force it. **(a) It cannot gate what it
   depends on:** criterion 3 prototypes (B)'s emit+apply inside `loop.py`, which cannot be built
   without having decided (B) — reading it as a gate makes P3-D1 unfreezable by construction.
   **(b) A probe that costs what the build costs is not a probe:** criteria 1/2/4/5a/5b answered
   every question a cheap instrument could answer, and what remains — does an operation list
   apply to a real file and pass that file's real suite — is the build itself.

   It therefore survives as P3-D1's **acceptance condition** (the P4-D2 pattern), not as its
   gate: if the operation list does not apply cleanly on `parser.py`/`intake.py`, **D1 reopens
   with evidence.** Note s137's reading below predates this and states a two-condition bar
   (*"the unaddressable-statement bound … and the real-file half"*); the first was satisfied by
   5a/5b, and the second is this reclassification.
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

   **SPLIT s139 — this criterion asked ONE vehicle for TWO questions, the same defect s137
   found one level up** (criteria 1/2/4/5 → the benchmark, criterion 3 → oficina). The two
   halves need opposite corpora and only one of them is answerable here:

   - **5a — BEHAVIOUR (answered here).** *Given that the coder needs a top-level statement it
     cannot address, what does it emit?* Vehicle: a corpus task **designed** so the only
     correct repair requires a new `import` or module constant. n≈12, `my-python-q25c14-16k`.
     Outcomes to count: function-local import (the prediction) · refusal or partial edit ·
     silent wrong fix that avoids the import · anything unanticipated.
   - **5b — RATE (NOT answered here, and must not be reported as if it were).** *What share of
     real edits need a top-level statement at all?* **A designed task makes this 100% by
     construction**, so running 5a and quoting its share would be measuring the corpus I chose
     and reading it as a property of the world. This is the fraction P3-D1 item 6 names as
     bounding (B)'s coverage, and it needs a **natural** sample — real edits, not generated
     ones. Nearest honest instrument: mine repo history for commits that add an import to an
     existing file (`git log -p` over `mcp-server/src/`), or read it off criterion 3's real-file
     runs. **Until then (B)'s coverage bound stays UNMEASURED and should be stated that way.**

   **Design constraint on 5a's task, and it is the probe's negative control:** the task must
   admit **no addressable repair**. If the defect can be fixed without the new top-level
   statement, the coder will simply do that, and the criterion returns another unexercised
   zero wearing a different mask — the exact failure s137's `0/12` already is. Assert this in
   the corpus ground-truth tests (`test_writemodel_corpus.py`'s discipline), not in prose.

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

### RESULTS — benchmark half, run 2026-08-18 (s137)

`my-python-q25c14-16k`, class-bearing corpus, 6 tasks × 2 runs × 2 arms = 24 generations.
Raw: `benchmarks/results/p3t0-symbol-addressed.jsonl`.

**Token cost at equal correctness — both arms scored 100% combined in every bucket:**

| bucket | whole-file | symbol-addressed | ratio | whole-file wall | symbol wall |
|---|---|---|---|---|---|
| small | 120 tok | **43** | 2.8× | 8.8 s | 5.0 s |
| medium | 216 tok | **43** | 5.0× | 16.0 s | 4.6 s |
| large | 479 tok | **43** | **11.1×** | 36.9 s | 5.1 s |

**43 tokens, flat across every size**, against whole-file's linear growth. This reproduces arm
A's *"25 output tokens flat"* for the case arm A never covered — the address is now **emitted by
the model** rather than supplied by the harness, and it stayed size-invariant anyway.

**Criteria:**

1. **Address fidelity — 12/12 `ok`.** Every emitted `path`/`kind` resolved to exactly one unit.
   No `no_match`, no `multi_match`, no `kind_mismatch`, no `unknown_kind`.
2. **Degeneration — did NOT occur.** Span median **0.047**, max **0.091**; **0/12 addressed more
   than 50% of the file.** The model named the method, never the enclosing class. This is the
   criterion the entry calls *"the one that can kill the design, and still the silent one"*, and
   on this corpus it is silent because it did not happen.
4. **Response shape — 0/12 defects.** No fences, every body parsed, never more than one unit.

### What this does NOT establish — stated with the numbers, not after them

- **Criterion 5 was NOT EXERCISED, and its `0/12` is worthless.** No task in this corpus needs a
  new top-level statement — every defect is an arithmetic fix inside one method body — so
  "no function-local imports" reports that the case never arose, not that it is rare. Reading it
  as a result would be the *"a check that can only pass teaches nothing"* error in its purest
  form. **The prediction at P3-D1 item 6 remains untested.**
- **n is small and the corpus is easy.** 12 attempts per arm over **two** defect kinds
  (`scale`, `clamp`) on generated classes whose siblings are trivially correct. **Whole-file also
  scored 100%**, so this corpus still does not stress omission — E-D1's *"best possible case for
  whole-file fidelity"* caveat is only partly retired by adding classes.
- **The token ratio is a floor, not a ceiling.** The large bucket is ~100 lines; `loop.py` is
  638. Whole-file cost scales with the file and symbol cost does not, so the gap widens exactly
  where T-122 bites.
- **Criterion 3 is untouched here.** Applicability end-to-end on a file whole-file cannot reach
  is the oficina half, not the benchmark half.

**Reading for P3-D1.** The outcome table's first row is the one that matched — *resolves
uniquely, units stay fine-grained*. That **clears the gate the probe was built to test** and
removes the "magnitude unmeasured" objection for the naming half specifically. It does **not**
by itself justify freezing (B): the unaddressable-statement bound (item 6) is still unmeasured,
and the real-file half has not run. *(s140: both conditions are now discharged — the
bound was measured by 5a/5b, and the real-file half is **reclassified as a build** and attached
to the freeze as an acceptance condition. See criterion 3 above. This paragraph is left standing
as written, because the bar it set is the reason the discharge has to be explicit.)*

### RESULTS — criterion 5a, run 2026-08-19 (s139)

`my-python-q25c14-16k`, **import-requiring** corpus (`--corpus import`), 6 tasks × 2 arms × 2
runs = 24 generations. Raw: `benchmarks/results/criterion5a-import-20260819.jsonl`.
**Reported over TWO independent runs**, because the split between outcomes moves at n=12 and
one run would have read as more precise than it is.

| | run 2 | run 3 |
|---|---|---|
| symbol-addressed **combined** | **4/12 (33%)** | **6/12 (50%)** |
| whole-file **combined** (control) | **12/12 (100%)** | **12/12 (100%)** |
| `function_local_import` | 6 — 4 pass | 8 — 6 pass |
| `used_without_importing` | 6 — **0 pass** | 4 — **0 pass** |
| `avoided_the_module` | **0** | **0** |
| mean output tokens | 47 vs 171 | 47 vs 171 |

**Criteria 1, 2 and 4 are clean, so this is NOT an addressing failure.** Address fidelity
12/12 `ok`; degeneration 0/12; no fences, no prose, no neighbouring code. The token advantage
also holds — ~47 flat against whole-file's 171 mean. **What collapses is correctness, and only
on this task class.**

**What is robust across all 24 attempts, rather than across one run:**

1. **The coder never once added a correct top-level import** — it cannot; the schema has no
   operation that expresses one. Every attempt either put the import *inside* the unit or
   reached for the module without importing it anywhere.
2. **`used_without_importing` never passes: 0 of 10.** The body references `math`/`itertools`
   and nothing imports them, so the edit is dead on arrival.
3. **`avoided_the_module` never happened: 0 of 24.** The pre-registered worry that a designed
   task would simply be hand-rolled around did not materialise, so the corpus does exercise
   the criterion it was built for.
4. **The control passes every time: 24/24.** Whole-file adds the import correctly on every
   attempt at every size. The task is entirely solvable; the failure is specific to (B).

**The prediction (P3-D1 item 6) was HALF right, and the missing half is worse.** The
function-local import happened — 14 of 24 — and is the *benign* branch: **10 of those 14 pass
all tests**, which is precisely the silent degradation criterion 5 exists to catch, invisible
to criteria 1–4 *and* to the test suite. The unpredicted branch is the model **using the module
without importing it at all**, which never runs. That outcome was only visible because
`body_references_module` was added this session; under `body_has_import` alone it was
indistinguishable from hand-rolling — the opposite reading.

**The plan's assumed fallback does not exist.** Item 5 records *"Fallback = whole-file for that
iteration … so the refusal costs nothing to build."* **The model never refuses.** It emits a
confident, well-formed, correctly-addressed operation in every one of the 24 attempts. So the
fallback cannot be triggered by a model signal and must be **detected mechanically by the
harness** — which is cheap, and is first principle 1 (*"harness code does all mechanics"*)
rather than a new burden: an emitted `body` either contains an import, or references a name the
target file never binds. Both are AST checks on output the harness already parses.

**A second defect surfaced, and only by reproducing a raw output.** Two cells emitted the
import plus a bare `return list(...)` — **the body without its `def` line**. Spliced in, that
puts a `return` at module level, the module fails to import, and *every filler test dies with
it*, which reads as a catastrophic edit rather than a shape defect. The run had recorded
`body_parses: True` and *"body does not parse 0/12"*: both true and neither useful, because
`ast.parse` builds an AST for a module-level `return` quite happily — the `SyntaxError` comes
from `compile()`. The signal that *was* present is **`body_units == 0`**, a body declared
`kind: Function` containing no function; it had been recorded on every run and reported on
none, since the report only ever flagged `> 1` unit. Both are now reported, and a
`body_compiles` check added. **Diagnosing it cost two fresh generations, because the JSONL
records no model output** — a surprising cell cannot be explained after the fact. → **T-139.**

**The outcome table above has NO ROW for criterion 5**, so nothing here can be read as a
pre-registered consequence. Proposed row, authored AFTER seeing the result and flagged as such:

| Probe result | Consequence |
|---|---|
| **Coder needs a top-level statement it cannot address (criterion 5a)** | **(B) needs a second operation or a mechanical fallback — it cannot be shipped on `replace_unit` alone.** The coverage bound is real, the model does not degrade gracefully into it, and half its failures are silent. Decide between an `insert_top_level` op and harness-side detection + whole-file fallback; the latter is smaller and is already first principle 1. **Does NOT reverse the s137 result** — token cost and addressing quality are unaffected, and 5b (how *often* a real edit needs this) remains unmeasured, so the size of the bound is still unknown. |

**Two earlier runs were discarded, stated so the count of runs is not silently three:** run 1
used a `body_references_module` that missed the `from X import Y` form (fixed; every from-import
would have been miscounted as hand-rolling); run 2 predates `body_compiles` and the zero-unit
report, and its numbers are shown above rather than dropped, so it is checkable that the
instrument changed and the conclusion did not.


### RESULTS — criterion 5b, the real-edit rate, 2026-08-19 (s139)

**486 real edits** from this repo's non-merge history — one (commit, file) pair per edit, since
that is oficina's unit of work. Structural, not textual: both revisions are parsed and their
top-level sets compared, because a `+import math` diff line may be a *function-local* import
and a parenthesized multi-line import has its added lines indented. Cross-checked against a
grep: **8.4% textual vs 10.7% structural**, and the gap is the parenthesized form, so the
structural figure is the correct one. Instrument: `benchmarks/lib/run-unaddressable-census.sh`
(+ 13 tests; a `tree.body` → `ast.walk` mutation fails 5 of them). Raw:
`benchmarks/results/criterion5b-unaddressable-census-20260819.json`.

| population | n | **unaddressable** | import | constant | docstring | new unit |
|---|---|---|---|---|---|---|
| all edits | 486 | 51.2% | 27.2% | 26.1% | 9.3% | 47.5% |
| ≤10 lines | 131 | **34.4%** | 10.7% | 20.6% | 4.6% | 3.1% |
| ≤40 lines | 313 | 40.3% | 17.6% | 20.1% | 6.4% | 30.4% |
| `mcp-server/src/` ≤10 lines | 39 | **23.1%** | 5.1% | 15.4% | 2.6% | 2.6% |
| `mcp-server/src/` ≤40 lines | 97 | 42.3% | 17.5% | 24.7% | 3.1% | 15.5% |
| **`oficina/` ≤40 lines** | 69 | **47.8%** | 17.4% | 30.4% | 4.3% | 17.4% |

**The answer to 5b: between roughly a quarter and a half**, depending on the cut. Even the most
favourable one — the bridge's own source, edits of ten lines or fewer — is **23.1%**, about one
edit in four. **This is not a rare fallback**, which is what item 5's *"the refusal costs
nothing to build"* quietly assumed.

**AND THE DOMINANT CLASS IS NOT THE IMPORT.** P3-D1 item 6 names the case as *"most commonly a
new import"*. At every single cut the **module constant** outnumbers it — 30.4% against 17.4%
in oficina's own source. The prediction picked the second-largest class.

**That matters because the two need different remedies, and one of them is nearly free.**
*(First draft of this paragraph blamed `ref:unit-addressing-census` for the mislabel and was
**wrong** — corrected here rather than quietly reworded. The census classifies `assign` as
**`named`** in its own table and says *"the entire remainder is imports and module
docstrings"*. **The census was right.** P3-D1 item 6 corrupted it by adding "module constants"
to the complement, and `test_writemodel_apply.py` propagated that while citing the census as
authority. Both corrected; the census needed no change.)* **A module constant has a name.**
`DEFAULT_CODER_MODEL = …` binds one. What is true is narrower and fixable: `KINDS = ("Function", "Method", "Class")` and `_UNIT_NODES` covers
only `FunctionDef`/`AsyncFunctionDef`/`ClassDef`, so the resolver **does not index assignments**.
So the bound conflates two classes:

| class | share (oficina ≤40) | why unaddressable | remedy |
|---|---|---|---|
| **module constant / assignment** | **30.4%** | **named, but the resolver does not index it** | extend `_UNIT_NODES` + a `Constant` kind. **No new operation** — same multi-match discipline as any other unit |
| import | 17.4% | genuinely nameless | needs an `insert_top_level` op |
| module docstring | 4.3% | nameless, but singular per module | a reserved address, or fold into the import op |
| **new top-level unit** | **17.4%** | has a name, does not exist yet — `replace_unit` replaces, it cannot create | needs `insert_unit`; **a separate gap this plan had not named at all** |

**Consequence for P3-D1, and it is more favourable than criterion 5a alone implied.** The
largest slice is a **resolver gap, not a construction bound** — closing it is an extension to
`find_units`, which criterion 1 already measured at 12/12 unique. What genuinely needs new
operations is the import (~17%) and the new-unit case (~17%). **The earlier lean toward
"harness-side detection + whole-file fallback because it is smaller" is retracted on this
measurement:** falling back on a quarter to a half of edits means falling back precisely on the
files whole-file cannot reach, which is the entire feasibility argument for (B).

**Caveats, stated because the cut moves the answer by 2×.** (a) One repo's history, mostly
AI-assisted commits by one author — the mix may not generalise. (b) A commit is generally
*larger* than one delegate run, so the unsegmented figures overstate; the ≤10-line row is the
closest proxy and is the one to quote. (c) `unaddressable` counts statements **added or
changed**, which is correct for the decision (`replace_unit` addresses neither) but is not
"added a new statement". (d) It counts what a human chose to do in one commit, not what
oficina would be asked to do.

**One instrument defect found and fixed mid-measurement:** the first run reported
`docstring 0.0%` at every cut while the sample visibly contained module-docstring edits.
`ast.unparse` renders a docstring as an ordinary single-quoted literal, never a triple-quoted
one, so the prefix test matched nothing and the whole category drained into `constant`. The
headline rate was unaffected — a docstring is unaddressable either way — **which is exactly why
a measured zero could sit there looking like a result.**

### RESULTS — remedy 2 BUILT and its model-facing half MEASURED, 2026-08-20 (s140)

**The resolver extension shipped, and the coder can reach it.** 24 generations,
`my-python-q25c14-16k`, `--corpus constant`. Raw:
`benchmarks/results/p3t0-constant-addressing.jsonl`.

| criterion | result |
|---|---|
| 1 — address fidelity | **12/12 `ok`** — every emitted `["CONSTANT"]` / `kind: "Constant"` resolved to exactly one unit |
| 2 — degeneration | **0/12** addressed >50% of the file; span median **0.027** |
| 4 — response shape | **0/12** on every sub-check, including the fragment check |

| bucket | whole-file | symbol-addressed | ratio |
|---|---|---|---|
| small | 84 tok | **30** | 2.8× |
| medium | 176 tok | **30** | 5.9× |
| large | 352 tok | **30** | **11.7×** |

Both arms 100% combined at every bucket on the re-run, so this is cost at equal correctness —
and **30 tokens is below s137's 43**, because a constant's body is one line rather than a
function.

**Why a corpus was needed at all, and not just the resolver tests.** A capability the model
cannot NAME is the *"check that can only pass"* failure in its costliest form: the deterministic
tests would all be green while never exercising the thing they exist to test. The corpus
**forces** the constant — three functions read it and the target test asserts all three, so
repairing any one function body leaves two assertions failing — and that forcing property is
itself pinned by a test that fails when the corpus is reduced to one consumer.

**Two instrument defects, either of which would have published a confident wrong number.**

1. **The prompt hardcoded a vocabulary the code owns** — `"kind": "Function", "Method" or
   "Class"`. `KINDS` grew `Constant`/`ClassConstant` and the prompt did not, so the resolver
   could address a constant while the model had no way to name one. The arm would have reported
   a clean zero **for a case it never offered**. The list is now rendered from `KINDS`, pinned
   in both directions.
2. **`body_units` counted def/class node types**, inheriting the exact assumption the resolver
   had just shed. A `Constant` body is `NAME = value`, so run 1 reported *"0 units in body
   12/12 — a fragment, not a unit"* against twelve correct answers. It now uses
   `_addressable_names`. Diagnosing it cost a **full re-run**, because the JSONL records no
   model output — **T-139, biting exactly as filed.**

**The plan's predicted implementation was measured and dropped.** This section said *"extend
`_UNIT_NODES` + a `Constant` kind"*. `_UNIT_NODES` was written and then **deleted**: with the
name dispatch returning empty for anything it does not handle, a membership pre-filter blocks
nothing — and it made the rule **untestable**, because adding `ast.AugAssign` to the dispatch
and `ast.Import` to the tuple **both left the whole suite green**, each neutralised by the
other. One rule needs one enforcement point or no single-point mutation can reach it.

**Still open on remedy 2:** `insert_top_level` (imports 17.4% + docstring 4.3% + **added**
constants 13.0%) and `insert_unit` (17.4%) are unbuilt, and criterion 3 — D1's acceptance
condition — has not run.

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
