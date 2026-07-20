# oficina P2 language widening — design notes (staging)

**Status:** Staging notes, session 124 (2026-07-18). Captured from the Axis-A (add Go) scoping
discussion. **ABSORB when the widening plan is written:** the varies-table belongs in the P2
widening plan doc (or a new `oficina-p2-language-widening.md`); the two warnings belong in
`docs/patterns/refactoring-conventions.md` as a second proof-point for
`ref:patterns-refactoring-characterize-first` (they are that pattern applied to a *new-language*
case, not a refactor). This file is a holding pen so the analysis is not lost between sessions.
**Task:** T-92 (P2 widening), Axis A. Seam map source: session-124 Explore agent over
`parser.py`/`evaluator.py`/`intake.py`/`prompt.py`/`workspace.py`/`loop.py`/`validate-code.py`.

<!-- ref:oficina-language-widening -->
## What actually varies across languages (the interface-sizing table)

The loop *flow* is invariant; only a handful of steps vary. This table is what sizes the
eventual `LanguagePack` interface — and is a **prediction**, to be corrected against two working
implementations, not built from directly (see Warning 2).

| Concern | Python | Go | Varies? | Kind |
|---|---|---|---|---|
| Stage order, delta-scoping, anti-cheat, signature, budget | — | — | **No** | invariant algorithm |
| Compile *output* → `ParsedFailure` | JSON contract | identical JSON contract | No | — |
| `scope_of`, `attributable_failures`, `diff_touches_test_files` | normpath | same | No | — |
| `test_cmd` | caller-supplied | caller-supplied | No | — |
| **Compile execution** | single-file, external script | repo-aware `go build ./...` in the worktree | **Yes** | mechanism |
| **Test output parse** | pytest summary-block scan | **`go test -json` event stream** (measured) | **Yes** | mechanism |
| **File attribution** | nodeid carries the path | **compile: path is in the string; test: via `Package` field** | **Yes (test only)** | mechanism |
| **Category rule** | ERROR→mechanical / FAILED→structural | **flat: compile→mechanical, test→structural** (measured) | **Yes** | rule |
| `error_key` prefix | `py-` | `go-` | Yes | value |
| System prompt / persona | "precise Python engineer" / `my-python-q25c14` | Go equivalent | Yes | value |

**Reading:** three mechanisms + one rule + two values ≈ a five/six-member interface. The *flow*
is not in it at all. That is why this is **Template Method** (fixed algorithm, varying steps),
not pure Strategy.

## The design shape (matches the codebase's existing idiom)

`EvaluatedLoop` already takes `coder`/`evaluate`/`workspace`/`ledger`/`is_cancelled` as injected
`Callable`s; `EvaluateFn`/`CoderFn` are type aliases; `test_loop.py` fakes them with zero
subclasses. The consistent move is Template Method with **the abstract class replaced by the
existing function and the abstract methods replaced by a frozen value object**:

```
evaluator.evaluate(...)               # the invariant algorithm — already exists
    receives a LanguagePack           # frozen dataclass: {parse_test, compile, attribute_file,
                                      #   category_rule, error_prefix, system_prompt, persona}
LANGUAGES: dict[str, LanguagePack]    # the registry the language param selects from
```

**Why a value-object pack over a Java-style ABC here** (the decision the user raised — 1 manager
+ interface vs. abstract-class-with-generics etc.):

- Matches the file's idiom — five `Callable` seams already; an inheritance hierarchy beside them
  would make the code speak two dialects.
- `dataclasses.replace(PYTHON, error_prefix="go-", parse_test=_parse_gotest)` gives
  inherit-and-override *ergonomics* (shared defaults, selective override) with **no inheritance
  chain** to reason about.
- Fakes stay literal — build a pack, don't subclass an ABC to stub two methods.
- An ABC would only win if the varying pieces needed **shared mutable state**, or with many
  languages carrying deep partial overrides. Two stateless-function languages: neither holds.
<!-- /ref:oficina-language-widening -->

<!-- ref:oficina-language-widening-warnings -->
## Two warnings (→ absorb into refactoring-conventions as a 2nd proof-point)

**Warning 1 — do NOT pull the compile stage into the pack yet.** Go's compile is not "same
mechanism, different parser" — it is a *different execution model* (repo-aware `go build ./...`
vs. Python's single-file snippet through an external script). If `compile(target) -> failures`
is defined now, the interface gets shaped by **Python's accident** (one file, external process,
JSON out). Let compile be a member each pack may implement *differently*, and accept the two
implementations won't look alike. That is the "keep the divergence explicit" half of
`ref:patterns-code-extract-keep-divergence`.

**Warning 2 — do NOT extract the pack before Go exists concretely.** The extract-divergence
pattern's Rule 1 is *"drift is both the trigger and the map"* — there is no drift yet, because
there is one language. Designing `LanguagePack` from the seam map would be the **speculative
generality Rule 3 forbids**, and is the same failure that produced the **dead
`acceptance.validators`/`acceptance.structural` fields** (`intake.py:49-50`, accepted by intake,
consumed nowhere): an extension point placed by *anticipation* rather than by a second
implementation, landing in a shape nothing needed. Sibling of the guessed-trigger corollary
(`ref:active-decisions`).

**The disciplined order** (this IS `ref:patterns-refactoring-characterize-first` applied to a
new-language case): write Go's parser + category rule + compile path as **plain concrete
functions beside Python's, duplicated on purpose** → let the real divergence surface → *then*
extract `LanguagePack` from two working implementations, with `PYTHON` reproducing today's
behavior verbatim so the existing ~99 oficina tests pin it. The duplication is the measurement
instrument; it is temporary by design. Expect one predicted seam to prove unnecessary and one
unpredicted seam to prove required.
<!-- /ref:oficina-language-widening-warnings -->

## Known live bugs to fold into the widening (session 124)

- **`parser.py:109`** hardcodes `error_key = (f"py-{...}", …)` on **every** compile error
  regardless of validator → a Go compile failure keys as `py-syntax_error`; silently corrupts the
  P2-D7 repetition signature. The `py-`→language-derived prefix fix stops being a special case
  the moment there are two languages. **Fold into the widening** (user decision, session 124).
- **`category_for` (`parser.py:214-232`) raises `ValueError`** on unrecognized keys, and Go has no
  ERROR/FAILED split → without a Go rule the loop **crashes** at `loop.py:156`. Mandatory, not
  optional.
- **`_run_test_stage`'s nonzero-rc-with-no-parseable-failures guard** (`evaluator.py:173-178`)
  **fails loud rather than falsely passing** — a half-migrated Go run errors instead of silently
  declaring success. Safety net to lean on during the build.

## Decisions — SETTLED (session 124, after the R3 experiment)

- **R1 — how language is decided: DECLARED.** Add `deliverable.language: Optional[str]` to intake;
  **infer from target extension as the default when absent** (override, not a required field — keeps
  every existing Python spec valid without migration). Rationale: intake's derived-key machinery
  (`DELIVERABLE_KEYS` at `intake.py:78`) makes the field nearly free, and — decisive — R4 is a
  *silent* hazard, so its trigger must be a **declared input you can pin in one intake test**, not a
  fact computed three layers deep from a filename. **Revisit trigger:** a *non-authoring* client
  submits specs (the T-86 boundary world) — then inference-with-declared-override is the shape.
  Record what would *force* the change, not what feels redundant.
- **R3 — Go compile execution model: IN-WORKTREE `go build ./...`. CONFIRMED by experiment.**
  A `git worktree add` checkout carries `.git` as a *pointer file*; Go resolves `go.mod` by
  filesystem walk and is indifferent to it — sibling imports resolve, worktrees are isolated
  (base build unaffected by the worktree's broken edits). This is the exact repo-context that
  `validate-code.py`'s single-file `validate_go` snippet-scaffolder throws away. So Go's `compile`
  is a genuinely *different mechanism* from Python's external-script path — the divergence the pack
  should expose, not hide (Warning 1). *(Latent finding: Python's own compile stage is also
  single-file-through-a-script and has the same blind spot; the worktree is the right compile
  context for BOTH, and Python may eventually want to converge toward Go's, not vice-versa. Not
  acting on it now — noted.)*

## Measured Go output shapes (from the session-124 experiment; write parsers against THESE)

**Compile failure** — `go build ./...`, exit 1, stderr:
```
# example.com/probe
./area.go:10:23: undefined: mathutil.Volume
./area.go:5:1: syntax error: unexpected }, expected expression
```
→ **real worktree-relative path + line:col**. Compile-stage attribution needs **no stamp** — the
path is already in the string. (`# pkg` banner lines are non-failures; skip them.)

**Test failure** — `go test -json ./...`, exit 1, event stream:
```
{"Action":"output","Package":"example.com/probe","Test":"TestArea","Output":"    area_test.go:11: Area(3,4) = 7, want 12\n"}
{"Action":"output","Package":"example.com/probe","Test":"TestArea","Output":"--- FAIL: TestArea (0.00s)\n"}
{"Action":"fail","Package":"example.com/probe","Test":"TestArea"}
```
→ the authoritative failure set is the **`Action:"fail"` events with a non-empty `Test`** — NOT a
text scrape of `--- FAIL:`. This closes the phantom-failure hole `_summary_section` exists for,
**for free** (no scraping to fool). File path: read `file:line` from that test's `Output` events;
resolve to a worktree-relative path via the `Package` field + the `_test.go` basename. Cleaner
than pytest's summary-block scan, not a hack around a weaker signal.

- **R4 — Go test → file attribution: SCOPED TO THE TEST STAGE ONLY** (compile is self-attributing,
  above). Plain `go test` gives a *bare* `area_test.go:11:` (no package dir) which would risk a
  `scope_of` mismatch → `SCOPE_OUT` → wrongful subtraction (the **P2-D12 masking hole**). `-json`'s
  `Package` field resolves it structurally. Use `-json`; do not text-scrape.
- **Category rule — FLAT for Go.** `go build` catches undefined-name/import defects that Python
  only sees at test-time, so the pytest ERROR-vs-FAILED split **has no Go analog and needs none**:
  compile→mechanical, test→structural. Simpler than Python's; kills the `category_for` `ValueError`
  crash path (`parser.py:232`) with one branch.
