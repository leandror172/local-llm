# oficina P2 — Go language widening (Axis A) — build plan

**Status:** Plan, session 124 (2026-07-18). R1/R3/R4 SETTLED (see below). **Phase 1 BUILT
session 124** (intake `language` plumbing; suite 279 then); Phases 2–5 open. **Amended session 127
(2026-07-23) — see § Amendments:** post-T-110 deltas (A1), `-json` imposed (A2), `_parse_gotest`
dogfood via oficina edit run (A3), ABSORB deferred to Phase 4 exit (A4). Suite baseline at
amendment: 298.
**Task:** T-92 (P2-D1 widening), Axis A = add a second language (Go).
**Branch:** `feature/oficina-p2-go` — fresh from **master** (the s124 remark about keeping a live
`docs/t102-…` branch separate is obsolete — branch estate is master-only since session 126).
**Design notes + measured Go output shapes:** `docs/plans/oficina-language-widening-notes.md`
(`ref:oficina-language-widening`, `ref:oficina-language-widening-warnings`).
**Why Go, why first:** Axis A's result reshapes how we think about Axis B kinds (user, session
124), so it goes first. Go because `my-go-q25c14` is the recorded Layer-5 codegen persona and the
toolchain is present (go1.23.6).

## Settled decisions

- **R1 — language is DECLARED** (`deliverable.language`), inferred-from-extension as the default
  when absent. Override, not a required field. Revisit trigger: a non-authoring client submits specs.
- **R3 — Go compiles via in-worktree `go build ./...`** (experiment-confirmed: worktree `.git` is a
  pointer file, Go resolves `go.mod` by filesystem walk). Genuinely different mechanism from
  Python's external-script compile — the pack exposes the divergence.
- **R4 — file attribution: compile is self-attributing** (path in the string); **test uses
  `go test -json`** and resolves file via the `Package` field. Scoped to the test stage only.
- **Category rule for Go is flat:** compile→mechanical, test→structural (no ERROR/FAILED split).

## Governing discipline (from the two warnings)

This is `ref:patterns-refactoring-characterize-first` applied to a new-language case. **Write Go
concretely and duplicated beside Python FIRST; extract `LanguagePack` only after two working
implementations reveal the real divergence.** Do not design the abstraction from the seam-map
prediction — that is the speculative generality `ref:patterns-code-extract-keep-divergence` Rule 3
forbids, and the failure that produced the dead `acceptance.validators` field. The duplication is
the measurement instrument; it is temporary by design. **Phase 4 (extract) never precedes Phase 3
(duplicate).**

TDD throughout; tests first (repo workflow). Local-model-generate test bodies + impl where the
conventions allow (`my-python-q25c14` for the Python-side plumbing, `my-go-q25c14` for Go fixtures),
verdict-logged. Parser/evaluator test files stay **hand-written fixture style**, matching their
recorded DSL opt-out; `test_loop.py`/`test_intake.py` keep the executable-spec DSL.

---

## Phase 1 — R1 plumbing (pure Python, no Go yet)

Pin the language seam before Go touches anything.

- `intake.py`: add `Deliverable.language: Optional[str] = None`. `DELIVERABLE_KEYS` derives
  automatically (`:78`) → unknown-key check extends for free.
- Resolution helper: `resolve_language(deliverable) -> str` — return `language` if declared, else
  infer from `os.path.splitext(target)[1]` via an extension map `{".py":"python", ".go":"go"}`.
- New intake rule `unsupported_language` (where/whose/what triad, like every rejection) — reject a
  declared language not in the supported set; reject an *inferrable-but-unsupported* extension only
  for loop kinds (a `file`/`answer` kind has no language contract).
- **Tests** (`test_intake.py`, DSL): declared `python` accepted; absent+`.py` infers python;
  declared `go` accepted (even before Go works — intake is language-list-gated, not
  implementation-gated); unsupported rejected with triad; `file` kind unaffected.

**Exit:** language is a first-class, pinned intake fact. Suite green, Python behavior unchanged.

## Phase 2 — the `py-` prefix fix (folded in, user decision)

- `parser.py:109`: `error_key = (f"py-{...}")` → prefix derived from the resolved language. Thread
  `language` into `_parse_compile` / `parse_validator_output`.
- `PYTHON` behavior stays **byte-identical** — the existing 24 `test_parser.py` cases pin it.
- **Test:** a compile failure under `language="go"` keys `go-…`, not `py-…` (the bug, now
  regression-pinned). This is the seam Phase 3's Go parser plugs into.

**Exit:** `error_key` prefix is language-derived; `go-` is expressible; no behavior change for Python.

## Phase 3 — Go, written concretely BESIDE Python (the duplication phase)

Each piece is a plain function next to its Python sibling. **No `LanguagePack` yet.**

1. **Go compile** — new `_run_go_compile_stage` (or a branch that runs `go build ./...` in the
   worktree, captures stderr, parses). Parser: `# pkg` banner lines skipped; `./path:line:col: msg`
   → `ParsedFailure{stage=compile, file=<relpath from the string>, error_key=("go-"+classify, …)}`.
   Classify from the message tail (`undefined:` → undefined_reference, `syntax error` →
   syntax_error) — mirror `classify_go_error` in `validate-code.py:115` but against real build
   output, not the snippet validator.
2. **Go test parse** — `_parse_gotest(json_lines) -> list[ParsedFailure]`: authoritative set =
   `Action:"fail"` events with non-empty `Test`; `file:line` from that test's `Output` events;
   resolve to worktree-relative via `Package` + `_test.go` basename. `error_key=("go-test-failed:"+…)`.
   Test stage invokes `go test -json ./...` (or the caller's `test_cmd` if it already emits json —
   decide: **mandate `-json` in the Go test path**, since attribution depends on it).
3. **Go category rule** — extend `category_for`: `go-` compile keys → mechanical, `go-test-…` →
   structural. Remove the `ValueError` crash for the Go branch.
4. **Go persona/prompt** — `loop.py`: language-select `DEFAULT_CODER_MODEL` (`my-go-q25c14`) and
   `_SYSTEM` ("precise Go engineer"). Both are **stable** prompt segments → per-language is correct
   and cache-cheap. `_CONSTRAINTS` reused as-is (language-neutral).
5. **Dispatch** — the minimal `(stage, language) → parser` branch in `parse_validator_output`
   (still an `if`, not yet a registry — the registry is Phase 4).
- **Tests** — new Go fixtures in `test_parser.py` (hand-written, against the measured strings in the
  notes doc); Go twins for the `evaluate` tests in `test_evaluator.py` (real `go build`/`go test`
  subprocess, mirroring the Python integration tests). ~30 new tests estimated.

**Exit:** a Go `function` deliverable evaluates end-to-end through two parallel, duplicated code
paths. Ugly on purpose. Suite green.

## Phase 4 — extract `LanguagePack` from the two working implementations

Only now, with real divergence in hand.

- `LanguagePack` = frozen dataclass: `{compile_stage, parse_test, category_rule, error_prefix,
  system_prompt, coder_persona}` — **membership determined by what actually diverged in Phase 3**,
  not by the prediction table. Expect one predicted seam to prove unnecessary and one unpredicted to
  be required (Warning 2).
- `LANGUAGES: dict[str, LanguagePack]` = `{"python": PYTHON, "go": GO}`. `PYTHON` reproduces current
  behavior **verbatim** → the full ~99-test suite is the characterization net; it must stay green
  with zero edits.
- `evaluate`/loop select the pack via `resolve_language`. The `if stage==/language==` branches from
  Phase 3 collapse into pack-member calls.
- Reconsider the dead `acceptance.validators` field: is it the right registry key, or is
  `deliverable.language` sufficient? Decide from the concrete shape, do not inherit it.

**Exit:** one algorithm, two packs, no duplication, suite green as characterization. **Added
session 127 (A4):** record the prediction-vs-reality delta (which predicted seam proved
unnecessary, which unpredicted seam was forced — Warning 2's claim, now measurable), then execute
the notes doc's deferred ABSORB: promote the two warnings into
`docs/patterns/refactoring-conventions.md` as the second proof-point for
`ref:patterns-refactoring-characterize-first`, with that measured delta as the evidence.

## Phase 5 — live acceptance

- One real Go `function` deliverable through the actual loop against real Ollama (`my-go-q25c14`):
  seeded compile defect → repair → Delivered, zero Claude edits. Mirror the P2 first-slice
  acceptance (`ref:delegate-p2-acceptance`).
- Confirm prefix-cache reuse on **`prompt_eval_duration`**, never `prompt_eval_count`
  (`ref:oficina-p2-cache-measurement`).
- Confirm the anti-cheat/masking guards hold for Go (a Go test failure attributes to the right file
  via `-json`; a pre-existing wart in a context file is not blamed).

- **Stretch goal (added session 127, runs only after the frozen greenfield gate passes):** one Go
  **edit run** — an existing committed `.go` target with a seeded defect — exercising the T-110
  edit machinery (`current_file`, `_EDIT_CONSTRAINTS`, derived `num_predict`) on the second
  language. Not part of the acceptance gate; contributes evidence to E-D6's
  production-runs-as-corpus stance.

**Exit:** Go is a supported language; Axis A done. Feeds the Axis-B kinds reconsideration.

## Open sub-decisions to resolve in-flight (not blockers)

- ~~**Go test command ownership.** Does the caller supply `test_cmd = "go test -json ./..."`, or does
  the Go test stage *impose* `-json`? Lean: impose (attribution depends on it; a caller's plain
  `go test` would silently lose file resolution). Decide in Phase 3.~~ **SETTLED session 127:
  the Go test stage IMPOSES `-json` (A2, § Amendments).**
- **Multi-file Go targets / package clause.** The first slice keeps one target file (as Python did).
  A Go target with its own real package (not `main`) is fine under `go build ./...` — no scaffolding,
  unlike `validate_go`. Confirm no `package main` assumption leaks in.
- **`extract-code.py:infer_language`** exists (benchmark harness) — reference for the extension map,
  do not couple to it (off the loop path).

---

## Amendments (session 127, 2026-07-23)

Additive, per the repo's amendment idiom (T-104 § AMENDMENT precedent). The frozen text above is
untouched except the status header, the settled sub-decision strike, and the two exit-line
additions marked "session 127". R1/R3/R4 and the governing discipline stand as frozen.

### A1 — The plan predates edit mode (T-110, session 126); what Go inherits for free

Edit mode (`docs/plans/oficina-p2-edit-mode.md`, E-D1–E-D9) shipped after this plan froze and is
**language-agnostic by construction** — none of it needs a Go variant:

- The `current_file` stable segment (E-D3), fence-strip composing `server._strip_code_fences`
  (E-D5), and the chars-based edit `num_predict` derivation (E-D9) all operate on file content,
  not syntax. A Go **edit** run works the moment Go compile/test stages exist.
- `locate_unit` is **out of the predicted pack** — the code-anchored locator survives only as the
  on-file fallback (T-104 § AMENDMENT, omission trigger), so no per-language span-location member
  exists. This is the "simpler now" fact recorded in the s126 register, now recorded where the
  build reads.
- **Phase 3 item 4 correction: prompt selection is now two-axis (mode × language).** `loop.py`
  already selects constraints by `Assembly.mode` (`_CONSTRAINTS` / `_EDIT_CONSTRAINTS`, both
  language-neutral); the Go work adds a language axis (`DEFAULT_CODER_MODEL`, `_SYSTEM`) that
  **composes with — does not replace — the mode axis**. All combinations remain stable prompt
  segments, so the P2-D2 cache contract holds unchanged.

### A2 — SETTLED: the Go test stage imposes `go test -json ./...`

The stage owns the command; a caller-supplied `test_cmd` does not opt Go out of `-json`.
Rationale: R4's file attribution depends **structurally** on the `Package` field, so a plain
`go test` would *silently* degrade attribution — the P2-D12 masking hole reintroduced as a caller
default. Same family as "a signal that fires unconditionally carries zero bits": a silent
degradation path is not accepted as configuration.

### A3 — SETTLED: `_parse_gotest` is dogfooded via an oficina EDIT RUN

The frozen dogfood note predates edit mode and imagined `generate_code`-style delegation.
Revised shape: hand-write the fixture tests first (unchanged — hand-written fixtures against the
measured shapes), then `submit_run` with `kind: function` targeting `parser.py` at HEAD — a real
edit run on a load-bearing module, async per the revised T-89 routing default, judged per-run via
`run_result`. The 24 existing parser tests + the new fixtures are the regression net. Fallback
per the recorded retry protocol: improve prompt + retry before any hand-write; a rejected run is
itself wanted signal (the first production edit run after T6 acceptance). Session scope
(settled this session): **Phases 2+3 in one session; Phases 4–5 the next.**

### A4 — DEFERRED: the notes doc's ABSORB (warnings → refactoring-conventions)

Deliberately not executed at amendment time: the warnings' central claim ("expect one predicted
seam to prove unnecessary and one unpredicted to prove required") is a **prediction**, and its
evidence only exists after Phase 4 extracts the pack from two working implementations. Promoting
the staging pattern on an unverified prediction would be the anticipation-over-evidence failure
the warnings themselves describe. Execution point: the Phase 4 exit item added above.
