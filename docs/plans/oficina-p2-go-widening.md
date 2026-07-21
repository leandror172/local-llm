# oficina P2 — Go language widening (Axis A) — build plan

**Status:** Plan, session 124 (2026-07-18). R1/R3/R4 SETTLED (see below); not built.
**Task:** T-92 (P2-D1 widening), Axis A = add a second language (Go).
**Branch:** `feature/oficina-p2-go` — fresh from **master** (the current `docs/t102-…` branch is a
clean docs PR; keep it separate).
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

**Exit:** one algorithm, two packs, no duplication, suite green as characterization.

## Phase 5 — live acceptance

- One real Go `function` deliverable through the actual loop against real Ollama (`my-go-q25c14`):
  seeded compile defect → repair → Delivered, zero Claude edits. Mirror the P2 first-slice
  acceptance (`ref:delegate-p2-acceptance`).
- Confirm prefix-cache reuse on **`prompt_eval_duration`**, never `prompt_eval_count`
  (`ref:oficina-p2-cache-measurement`).
- Confirm the anti-cheat/masking guards hold for Go (a Go test failure attributes to the right file
  via `-json`; a pre-existing wart in a context file is not blamed).

**Exit:** Go is a supported language; Axis A done. Feeds the Axis-B kinds reconsideration.

## Open sub-decisions to resolve in-flight (not blockers)

- **Go test command ownership.** Does the caller supply `test_cmd = "go test -json ./..."`, or does
  the Go test stage *impose* `-json`? Lean: impose (attribution depends on it; a caller's plain
  `go test` would silently lose file resolution). Decide in Phase 3.
- **Multi-file Go targets / package clause.** The first slice keeps one target file (as Python did).
  A Go target with its own real package (not `main`) is fine under `go build ./...` — no scaffolding,
  unlike `validate_go`. Confirm no `package main` assumption leaks in.
- **`extract-code.py:infer_language`** exists (benchmark harness) — reference for the extension map,
  do not couple to it (off the loop path).
