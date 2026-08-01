# Unit-addressing census: is symbol-addressed editing viable? — 2026-07-31, session 135

*Measured input to **P3-D1**, which asks what a coder model should EMIT when editing a file that
is too large to re-emit whole (T-122). The candidate — schema S3 — has the model name a code unit
and supply its new body, with the harness resolving the name to a span and splicing. Two
questions decide whether that vocabulary is expressive enough: **what granularity is needed**,
and **what does it fail to address**. Both are measured here rather than reasoned about
(`feedback_measure_magnitude_not_estimate`).*

<!-- ref:unit-addressing-census -->
## Method

Two AST censuses, no heuristics.

- **Python:** `ast` over 10 `mcp-server/src/ollama_mcp/oficina/*.py` modules — deliberately the
  T-122 blocked set plus its siblings, i.e. the exact files the decision is about.
- **Go:** `go/ast` (go1.23.6) over `~/workspaces/expenses/code` + `~/workspaces/career-search`,
  **129 non-test files / 20,643 lines**, excluding `vendor/` and `_test.go`.

Scripts: `toplevel-census.py`, `nested-census.py`, `gocensus.go` (session scratchpad — promote to
`.claude/tools/` if this becomes a repeated measurement, cf. `judge-window-sweep.py`).

## Finding 1 — granularity must be DOTTED, and in Python that is the whole decision

Top-level-only addressing is not merely coarse; on the files that motivated T-122 it is useless.

| file | lines | top-level ceiling | dotted ceiling | median unit |
|---|---|---|---|---|
| `loop.py` | 637 | **438 (69%)** | **66 (10%)** | 17 |
| `workspace.py` | 328 | **231 (70%)** | **36 (11%)** | 14 |
| `parser.py` | 378 | 48 (13%) | 48 | — |
| `intake.py` | 444 | 26 (6%) | 26 | — |
| `judge.py` | 357 | 50 (14%) | 50 | — |

`loop.py` is one 438-line class inside a 637-line file. Under top-level addressing, changing one
method costs **69% of the file** and T-122's saving evaporates for the file that defines the
problem. `Class.method` addressing drops the ceiling to **10–11%** and the median edit to
**14–17 lines**.

**In Go the same grammar is needed for a different reason, and buys less.** Go has no nesting —
`func (r *T) M()` is already a top-level declaration — so the two ceilings are *identical*
(median 26%, p90 56%, max 87%). Go's ceiling is set by how long people write functions, not by
containers. The receiver is a naming convention; the address grammar is the same shape
(`Owner.Member`) arrived at from the opposite direction.

**The ratio is the wrong metric for Go.** What T-122 cares about is the absolute size of the
emitted unit:

```
median addressable unit:   7 lines   (n=1240)
largest in corpus:       159 lines   (runBatch)
                         119 lines   (MarkdownStore.Stage)
```

159 lines ≈ 2,000 output tokens — comfortably inside `num_predict`. Go's tail looks alarming as a
percentage and is harmless in absolute terms.

## Finding 2 — the "module-level code that isn't a def/class" problem barely exists

**Python**, 237 top-level statements across 10 modules:

```
function     82   (1348 lines)   named
class        17   ( 853 lines)   named
assign       64   ( 124 lines)   named   ← NUM_PREDICT, VALID_KINDS, …
import       64   (  78 lines)   unnamed
docstring    10   ( 206 lines)   unnamed
if_block / try_block / bare_expr:  0
```

**89.1% of top-level lines already sit under a name**, and the entire remainder is imports and
module docstrings. No top-level control flow, no `if TYPE_CHECKING:` blocks, no bare expressions.

**Go**, 1,260 top-level declarations:

```
func (plain)   690     func (method)  152     type  174
var             79     const           46     import 119
OTHER (unnamed)  0     ← nothing else exists in the language's top level
```

**90.6% of declarations carry a name**; the remainder is imports. Go is *cleaner* than Python
here — there is no docstring statement and no unnamed construct at all.

**So three typed operations close the entire gap in both languages:**

| Residue | Op | Why typed beats an anchor |
|---|---|---|
| imports (64 Py / 119 Go) | `ensure_import` / `remove_import` | harness merges deterministically — first principle 1; and imports are *"~1/3 of improved reasons"* in our own verdict data (`ref:delegate-evidence-verdicts`) |
| module docstrings (10 Py) | `replace_module_docstring` | exactly one per module, so the module IS the address |
| named constants (64 Py) | already `replace_unit` | they carry names |

**Struct/type bodies are a non-issue in Go:** 158 structs, only **4** with bodies over 30 lines,
largest 41. Replacing a whole type is cheap, so no field-level addressing is required.

## Finding 3 — two span hazards, one per language, same shape

A span of `(node start, node end)` **excludes attached material that belongs to the unit**:

- **Python:** `ast.FunctionDef.lineno` points at the `def` line; decorators live in
  `decorator_list` with *earlier* linenos. Replacing a `@property` would splice a new body under
  an orphaned `@property`.
- **Go:** `FuncDecl.Pos()` points at the `func` keyword; the doc comment is separate in
  `decl.Doc`. Replacing an exported function would orphan its `// Foo does…`. Go convention puts
  a doc comment on essentially every exported symbol, so this fires **constantly**, not rarely.

Both are silent corruptions of exactly the class symbol-addressing exists to prevent, and both
are invisible to a test that only uses undecorated / undocumented functions. **The locator must
span from the earliest attachment, and the test corpus must include a decorated and a documented
symbol.**

**Third hazard, Go-specific:** building `Receiver.Method` requires resolving receiver types in
`T`, `*T`, `T[P]` and `*T[P]` forms. The census needed all four to avoid unresolved entries —
that is real `locate_unit` complexity, not a detail.

## What this does NOT establish — corpus limits, stated out loud

Applying `ref:corpus-divergence-pattern` to this measurement rather than waiting for someone else
to:

1. **The two percentages are not comparable.** Python's 89.1% is named-lines over *summed
   declaration spans*; Go's 78.5% is over *total file lines* (including blanks, comments and the
   package clause). Different denominators. Do not read Go as worse.
2. **The Go corpus mostly isn't the problem case.** 20,643 lines over 129 files averages **160
   lines per file** — most would never be blocked by the window at all, so the ceiling
   percentages are measured largely on files that were never T-122's concern. What the corpus
   establishes reliably is the *declaration taxonomy* (exhaustive, clean) and the *absolute unit
   sizes* (small). It does not establish the ceiling for large Go files.
3. **Both corpora are our own code**, library-shaped. Script-shaped or config-shaped Python (top
   level control flow, `if __name__ == "__main__"`) and framework code would look different. If
   oficina is meant to edit arbitrary user code, the measured corpus is narrower than the
   consumer set — the exact silent-and-narrow direction `ref:corpus-divergence-pattern` flags.
4. **Java is unmeasured here** and is the language most likely to break the grammar (overloading,
   inner/anonymous classes, annotations, generics). Under research at time of writing.

## Consequence for P3-D1

The two objections that would have killed S3 — *"unit granularity is too coarse"* and *"module
level code has no address"* — **do not survive measurement**, provided addressing is dotted. What
survives unresolved is orthogonal: whether a 14B model can reliably *produce* a correct address
and body (the Diff-XYZ evidence, P3-T0's job), and whether the grammar survives Java.

`locate_unit` is confirmed as a per-language `LanguagePack` member — the seam already exists
(`compile_stage`, `test_stage`, `system_prompt`, `coder_model`) and this is its fifth member. It
cannot be one implementation: Python resolves by nesting, Go by receiver.
<!-- /ref:unit-addressing-census -->
