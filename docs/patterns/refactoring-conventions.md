# Refactoring conventions

**Status:** seeded this session (single origin — the `_run_script` extraction across the
previously-untested persona tools). Candidate for promotion into
`docs/patterns/code-design-conventions.md` once it proves out across a second refactor,
mirroring the staging arrangement of `docs/patterns/test-authoring-executable-spec.md`.

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
