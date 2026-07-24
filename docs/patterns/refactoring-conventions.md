# Refactoring conventions

**Status:** stable — promoted (T-115, session 128). Two recorded proof-points: the
`_run_script` extraction (characterize-first) and the T-92 `LanguagePack` extraction
(duplicate-first, session 127 — see "Duplicate before you abstract" below), which met the
original two-proof-point criterion. This is a first-class pattern-doc family, indexed in
`ref:patterns-index` (`docs/patterns/technology-conventions.md`) alongside the code-design
and technology conventions. Promotion was *graduate-in-place*: the content stays here (the
process/shape/test-body split below is the reason it is its own file); only its index
standing changed.

These govern the **process** of changing code safely — the sequence of steps around a
refactor — as distinct from `code-design-conventions.md` (how code is *shaped*) and
`test-authoring-executable-spec.md` (how a test *body* is written).

---

<!-- ref:patterns-refactoring-characterize-first -->
## Characterize Before You Extract

**Decision:** Before refactoring code that lacks tests, write **characterization tests that
pass against the *current* code first**. Only then change the code and re-run them.

**Why:**

A "behavior-preserving" claim is only as strong as the observations that pin the behavior.
This session extracted a shared `_run_script` helper across five call sites; three of them
(`detect_persona`, `build_persona`, `create_persona`) had **zero** tests. Tests written
*after* the extraction would encode what the *new* code does — circular, and worthless as a
regression check. Written *first* and green against the old code, they encode "what it does
today," so re-passing after the change actually **proves** preservation.

The failure mode this guards against is subtle: a green suite feels like evidence. But for
untested code, "the tests still pass" can be nearly meaningless — passing tests that never
*exercise* the changed paths prove nothing about whether the extraction preserved them.

**Rules:**

1. **Green on the unmodified code first.** New characterization tests must pass *before* you
   touch the code. If you cannot make them pass first, you do not yet understand the behavior
   you are about to change — stop and study it.
2. **Pin observable behavior, not structure.** Assert the exact things a caller sees: error
   strings, return shapes, which side-effects fire. (The persona tools: the precise
   `Error: {tool} exited with code N: …` wording, the timeout message, stripped-stdout on
   success — including the `Unknown error` branch for empty `stderr`.)
3. **A passing suite that never exercises the code proves nothing.** Confirm the specific
   paths are covered — grep for callers, assert the mock was actually hit, count the tests
   before and after (`260 → 270`, not `260 → 260`).
4. **Mock at the boundary you are *not* changing.** For `_run_script` that was the subprocess
   boundary (`create_subprocess_exec` / `wait_for`), so the same tests survive the extraction
   unchanged and keep asserting the same observable behavior on both sides of the refactor.

**Relation to the other pattern docs:**

- `ref:test-executable-spec` governs the *shape* of a test body (DSL vocabulary); this rule
  governs the *sequence* of writing tests relative to a code change. Orthogonal — a
  characterization test can be written in the executable-spec style or plain imperative.
- `ref:patterns-code-extract-keep-divergence` names this as step 4 of a drift-fixing
  extraction: characterize each drifted caller's behavior before unifying them, so
  "preserve each caller's message" becomes verifiable.

**When this does NOT apply:**

- Existing tests already pin the *exact* behavior you are preserving. (Retention's Option C
  split and `_assemble_prompt` both had boundary tests that exercised the changed paths, so
  `14 → 14` and `260 → 260` were real evidence — no new characterization pass was needed.)

<!-- /ref:patterns-refactoring-characterize-first -->

---

<!-- ref:patterns-refactoring-duplicate-first -->
## Duplicate Before You Abstract (proof-point 2: the T-92 LanguagePack)

**Decision:** When adding a second implementation of a varying concern (a new language, a
new backend), **write it concretely and duplicated beside the first, then extract the
abstraction from the two working implementations** — never design the interface from a
seam-map prediction. The duplication is the measurement instrument; it is temporary by
design.

**Why (the measured prediction-vs-reality delta, T-92 Phase 3→4, session 127):**

The Go-widening seam map (session 124) predicted a 5–6 member `LanguagePack`:
`{compile, parse_test, attribute_file, category_rule, error_prefix, system_prompt,
persona}` — plus, in an earlier draft, `locate_unit`. The pack extracted from two
*working* implementations has **4 members**: `{compile_stage, test_stage, system_prompt,
coder_model}`. The delta:

- **Three predicted members proved unnecessary:** `error_prefix` (stayed parser-internal
  — a map keyed by the language id, no caller touches it), `category_rule` (folded into
  the error-key prefixes `category_for` already reads — zero new code), `locate_unit`
  (dissolved before Phase 3 by an unrelated decision — edit mode went whole-file).
- **One predicted invariant proved variant:** the table said `test_cmd` was
  "caller-supplied, no variation". Reality: Go's test stage **owns its command**
  (imposes `go test -json` for structural attribution) while Python honors the
  caller's — so the member is the *whole stage*, not a parse function.
- **Three unpredicted seams emerged, none as pack members:** a module-path reader
  (`go.mod`), binary resolution (`OFICINA_GO`/`which`), and a go<1.24 stderr fallback
  for build-failures-under-test (discovered *empirically* by a greenfield C0 twin) —
  all module-private inside Go's stage.

A pack designed from the prediction would have carried three dead members (the exact
failure that produced the dead `acceptance.validators` field), missed the command-
ownership asymmetry, and been blindsided by the fallback. The 329-test suite, green with
**zero test edits** across the extraction, is what "the duplication was the measurement
instrument" buys.

**Rules:**

1. The first implementation's shape is an *accident*, not a spec — do not let its
   signatures define the interface (Warning 1: Go's compile is a different execution
   model, not a different parser).
2. Extract only when the second implementation **works** — a green suite over both
   duplicated paths is the extraction's precondition and its characterization net.
3. Record the prediction-vs-reality delta at extraction time; it is the evidence that
   the discipline paid, and the calibration for the next prediction.

**When this does NOT apply:**

- The variation is a *value*, not a mechanism (a string, a constant) — parameterize
  directly; duplication buys no information.

<!-- /ref:patterns-refactoring-duplicate-first -->
