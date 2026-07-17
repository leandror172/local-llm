# Test authoring — the executable-spec (DSL) style

**Status:** piloted in `mcp-server/tests/oficina/test_loop.py` (session 121, from the PR #76 review).
Candidate for promotion into `docs/patterns/code-design-conventions.md` once it proves out across a
second test file (task T-100). Origin: the user's review comment that a test body should read as *"an
English-written, coding-language-compiler-grammar-constrained executable specification of the scenario
and expected behavior, with the called functions (and constants too) working as a form of DSL."*

<!-- ref:test-executable-spec -->

## The idea

A test body states **the scenario and the expected behavior in English**; all imperative wiring hides
behind named helpers and constants that form a small domain vocabulary. The reader sees *what* is being
specified, never *how* it is set up.

```python
def test_iteration_editing_tests_is_rejected(tmp_path):
    run = given_a_function_run_whose_target_is_a_test_file(tmp_path)
    when_the_coder_iterates(on=run, writing=[A_TAMPERED_TEST], and_evaluation_yields=EVALUATION_NEVER_REACHED)
    then_the_iteration_was_rejected_as_a_cheat(run)
```

## The styles considered (why the hybrid)

Five flavors were prototyped on the same `test_loop.py` anti-cheat test:

- **A — Given/When/Then free functions.** `given_… / when_… / then_…` module functions. Smallest
  machinery; each test keeps its own narrative; the three phases are explicit.
- **B — Fluent builder.** `a_run(...).whose_target_is_a_test_file().where_the_coder_generates(X).run()`.
  Reads most like one sentence; heaviest machinery; clumsy for multi-assertion tests (chaining pain).
- **C — Scenario object, prose methods.** A stateful object whose methods mutate then read. Handles
  multi-assertion cleanly; reads as a script of named steps rather than prose.
- **D — Declarative scenario as data + one runner.** The scenario *is* data; every constant is
  vocabulary. Purest "constants as DSL"; compresses a homogeneous family into a scannable matrix but
  hides each test's narrative.
- **E — pytest `parametrize` over D.** The table endpoint of D: the whole family becomes rows.

**Chosen: the A+D hybrid** — Style A's narrated `given/when/then` bodies, with Style D's named
combinators (`CLEAN`, `FAILS(...)`, content constants) passed *into* them. Each test keeps its own
story (unlike D's table), while the loop's behavior is still read off data (`and_evaluation_yields=
[FAILS("a"), FAILS("b")]`). Multi-assertion claims get **one English-named `then_`** that holds the
several `assert`s together (the case Style B handles worst).

## Design rules the pilot surfaced

### 1. Value-identical, intent-distinct constants earn their names
`CLEAN = []` and `EVALUATION_NEVER_REACHED = []` are the same value but different *meaning* (an
evaluation that found nothing vs. per-iteration evaluations the anti-cheat check short-circuits before
consuming). Naming them separately is the DSL earning its keep — the test says what it means, not what
it evaluates to. Same pattern for baselines: `with_baseline=CLEAN` vs `with_baseline=A_PREEXISTING_WART`.

### 2. Hide structural conventions inside the verbs, with an escape hatch
The fakes carry a positional convention that is pure implementation detail: `FakeEvaluate`'s **first**
result is consumed by `workspace.assemble()` as the **C0 baseline** (tests present, deliverable absent),
and the **rest** are per-iteration. So `FakeEvaluate([[], [fail_a], [fail_b]])` means "baseline clean,
iter1 fails a, iter2 fails b" — an off-by-one in that leading `[]` silently shifts every iteration.
The `when_` verb takes **only the per-iteration evaluations** and prepends the baseline itself
(`FakeEvaluate([with_baseline, *and_evaluation_yields])`). The escape hatch `with_baseline=` keeps the
delta-scope family (which must specify a non-clean C0) inside the same vocabulary instead of dropping
back to raw fakes. **General rule:** when a fixture carries a positional/ordering convention, absorb it
into the verb and expose a named parameter for the cases that must override it.

### 3. The accretion stopping rule (when to STOP DSL-ing)
Each new *kind* of assertion adds a field to the run object and a new `then_` family:
- outcome assertions read `run.result`;
- event assertions read `run.ledger`;
- prompt assertions read `run.coder.prompts` — which forced `when_` to expose the coder.

One run object carrying three assertion targets and three verb families is healthy. If a **fourth**
kind appears (e.g. worktree filesystem state), the DSL is spanning too many property types and is
re-growing pytest; let those odd tests stay imperative rather than bending the vocabulary to fit. The
DSL earns its keep only while the family shares **one shape** and a **small set of assertion kinds**.

**Boundary nuance (third-file finding).** A *single* test whose claim is a 4th assertion kind can
still get **one** dedicated, well-named verb — e.g. `test_worker_loop.py`'s
`then_the_worktree_was_torn_down_leaving_the_branch` reads filesystem + git state in one cohesive
predicate — provided you mark it as the boundary in a comment. It is a *family* of such verbs that
signals the DSL is over-reaching, not a lone boundary verb. One is a named exception; several is a
new (unwanted) verb-family.

### 4. The `given`-constant / `when`-varies taxonomy tells you where the seam is
Across the behavioral family, `given` is the same and only `when` varies. That is not incidental — it
is the **deterministic-spine + injected-seam** design reflected in the tests: the loop's behavior is a
pure function of the injected `(coder outputs × evaluation results)` sequence against a fixed world, so
every test is implicitly a determinism assertion, and the essential complexity (signatures, budgets,
fresh-start, repair threading) is all `when`-driven.

The tests that instead vary `given` are testing a *different kind of property*:
- **anti-cheat** varies the world (target *is* a test file) — a structural precondition;
- **refs injection** varies what the world feeds the model;
- **cancel** varies a control signal (an injected `is_cancelled`).

So the split is a real taxonomy: **behavioral tests vary `when`** (share the vocabulary; a `pytest`
fixture for `given` + parametrized `when` is their structural endpoint), while **structural/wiring tests
vary `given`** (keep bespoke setup, though they can still reuse the `when_`/`then_` verbs). The
`given`/`when` boundary *is* the boundary of how far to spread the DSL — it maps onto the two kinds of
property the system under test actually has.

### 5. Corollary (second-file finding): the DSL *shape* adapts to the SUT's nature
Proven by converting `test_intake.py` as the second file. The given/when/then scaffold is not the
pattern — it is the *temporal* form of it. What varies is whether the system under test consumes an
input **over time**:

- **Temporal SUT** (`loop`: consumes a coder/evaluator *sequence* across iterations) → the full
  `given_ … when_the_coder_iterates(…) … then_ …`, because there is a "when" to narrate.
- **Pure-function SUT** (`intake`: `spec → verdict`, no sequence, no state) → the scaffold
  **collapses**: no `when_` survives, and the vocabulary reduces to **builder-nouns**
  (`a_function_spec`, `a_file_spec`, `an_answer_spec`) + **verdict-verbs** (`accepts`,
  `rejects(with_rule=…)`, `rejects_with_triad`). A test is one line: `rejects(spec, with_rule=RULE_X)`.

Two things this pins down. **First**, the *portable* parts of the pattern are the noun-vocabulary
(rule 1) and the convention-hiding verbs (rule 2/3) — NOT the `given/when/then` skeleton, which is
present only when the SUT is temporal. **Second**, it sharpens rule 3's stopping rule from the other
side: a pure-function family has exactly one verb-family (verdict predicates), so the earned
vocabulary is small by construction — resist adding a mutation mini-language (`without(spec, key)`,
`with_workspace(…)`); the exotic malformations (a deleted key, a bogus nested key) read fine as one
inline line of data-prep. Over-DSLing a pure-function test is the most common way to violate rule 3.

**Diagnostic:** before writing the DSL, ask "does the SUT consume a sequence?" Sequence → `when_`
verbs; no sequence → builders + a verdict predicate and nothing more.

### 6. Third-file finding: the taxonomy is a *triage function* for mixed files
The first two files were each internally uniform (temporal-clean, pure-function-clean). The third,
`test_worker_loop.py`, was **mixed**, and that is the common real-world case — so it tested whether the
`given`/`when` split is merely descriptive or is a usable decision rule. It is a decision rule: asking
"does this test vary the input *sequence*?" sorted all five tests correctly on the first pass —
3 behavioral (routing→delivered, exhaustion, branch-in-payload) → the DSL vocabulary; 1 with a lone
filesystem/git assertion (teardown) → one boundary verb (the rule-3 nuance); 1 that varies the `given`
*and* the injected seam (answer kind + single-shot `generate`) → left fully imperative. **The payoff of
the pattern on a mixed file is not the converted tests — it is a principled answer to *which* tests to
convert and which to leave.** Apply the diagnostic per test, not per file.

## When to use / not use
- **Use** when a test file has a homogeneous behavioral family (same shape, small set of assertion
  kinds) whose variation is an input sequence — the `when`-varying case.
- **Do not force** it onto structural/wiring tests with bespoke worlds, or onto heterogeneous files; a
  too-narrow DSL leaks (rule 3). Keep those imperative or give them their own `given_` variant.
- The vocabulary constants (rule 1) and the convention-hiding verbs (rule 2) are the portable parts;
  the specific verbs are per-domain.

<!-- /ref:test-executable-spec -->
