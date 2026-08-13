# Symbol-addressed editing — prior-art survey (P3-D1) — 2026-07-31, session 135

*Four-arm survey commissioned to answer: **should a local coder model emit structured edits
addressed by SYMBOL rather than by string anchor**, and if so, whose vocabulary do we adopt?
Feeds `docs/plans/oficina-p3-context-assembly.md` § P3-D1. Method follows the house pattern from
the 2026-07-11 vision session (parallel research arms, divergence recorded as a product,
`ref:delegate-cross-repo`).*

| Arm | Question | Where |
|---|---|---|
| 1 | Canonical symbol address grammars — SCIP, SemanticDB, LSP/LSIF, ctags, pytest, Javadoc, Doxygen, objectpath, JVM, Kythe, Glean, tree-sitter | § 1–3 below |
| 2 | LLM edit-operation vocabularies — `text_editor`, Codex V4A, Aider, SWE-agent, OpenHands, fast-apply, ast-grep/Comby/Semgrep/OpenRewrite | `arm2-edit-vocabularies-notes.md` + § 4 |
| 3 | Does the grammar survive **Java**? | `arm3-java-openrewrite.md` |
| 4 | Measured small-model edit reliability | § 5 below |

A fifth stream (the `web-research` MCP arm) **failed** and its failure is recorded in § 6.

<!-- ref:symbol-addressed-editing-survey -->
## 0. Corrections this survey produced — read this section first

**Five confident claims were wrong, and the pattern in how they were caught is the reusable
part.** Each was corrected by a primary source or a measurement, never by further reasoning. They
are recorded here rather than silently fixed, because the register entry as it stood before this
session would have committed the phase to a design none of them supports.

| Believed | True | Caught by |
|---|---|---|
| SCIP's `<method-disambiguator>` uniquely identifies overloads | It is a **source-order counter** — `methods.indexOf(sym)`, statics last. Renumbers on insert. | Reading scip-java's generator, after a summarizer paraphrased the spec vaguely |
| udiff-l scores best for small models; marker collision is the mechanism | udiff-l is the **worst** format at every size (7B **0.00**); marker collision is the paper's *hypothesis 2*, which it **rejects** | Reading the paper instead of a search summary |
| Java has the decorator *and* doc-comment span hazards at once | It has **neither** — annotations are grammatically modifiers; JDT's node range *starts at the `/**`* | Primary spec + JDT source |
| Top-level unit addressing is sufficient | `EvaluatedLoop` is **438 lines / 69%** of `loop.py`. Must be dotted. | AST census of our own modules |
| The fork is caller-declared `unit` vs `kind: patch` | Neither — the intended design (model-emitted structured edits) **was not in the register**, having been dropped as a "duplicate axis" on a reason S15 undercuts | User review |

**The through-line:** every error was a *magnitude or mechanism detail* that reading one layer
deeper falsified, and every one survived because a plausible summary was accepted in place of the
source. This is `feedback_measure_magnitude_not_estimate` recurring at design altitude, and the
sibling rule earned here is narrower: **a summarizer's paraphrase of a spec is not the spec.**
Two of the five came from search-result snippets that were *directionally* right and *specifically*
wrong — the most dangerous shape, because nothing looks incorrect.

### 0a. Two further corrections — added session 136, and they are about THIS survey's own corpus

| Believed | True | Caught by |
|---|---|---|
| The span problem is solved by SCIP's `enclosing_range` and would otherwise need hand-backfilling per language (§ 2, § 9) | **Solved in this repo since session 124.** `benchmarks/lib/writemodel_apply.py:36` `locate_function` spans from `decorator_list[0].lineno` when decorated. Local-model generated, **verdict 2, used as-is** | Reading our own benchmark harness |
| No production system addresses edits by symbol except Serena / Moderne / CODESTRUCT (§ 4) | **Arm A of `ref:oficina-write-model-report` is exactly this operation** — model returns only the rewritten unit, code locates the span via `ast` and reads `old_string` from disk. Built, measured s124: **apply-failure mode "none — 100% by construction"**, 25 output tokens flat across all size buckets | Reading `ref:oficina-write-model-report` |

**The pattern, and it is a named one here.** This survey enumerated *external* prior art
exhaustively — 13-agent source survey, four indexer SHAs, five fast-apply vendors, three
structural engines — and **never enumerated our own**. Nothing in §§ 1–11 is false; the set it
searched simply was not the set that mattered. That is `ref:corpus-divergence-pattern` at document
altitude rather than in a health-reporting tool: *"name the set it enumerates and the set its
consumers use; if they come from different definitions they will drift."* The consumer here is
P3-D1, whose own decision history includes the benchmark this survey did not read.

**Consequence for § 9's resolution recommendation: SUPERSEDED — see P3-D1 § "The resolver".** The
in-process AST route wins on three grounds, one of which no external survey could have surfaced:
a precomputed index is **stale inside a batch** (operation 1 invalidates it for operations 2..N),
which is the same objection this survey's own consumers already make against line numbers.

## 1. The headline: adopt nothing whole — JOIN two things

> *"No surveyed grammar is adoptable whole, because the emittable address and the correct span
> come from different systems."*

- **SCIP** defines and emits the span we need, but its symbol string
  (`` scip-go gomod sg/initial 0.1.test `sg/initial`/MyStruct#RecvFunction(). ``) is not
  something a 14B model will produce.
- **Serena / pytest** give the emittable address (`Class/method`, `path::Class::method`) but have
  no span of their own — Serena takes the LSP `DocumentSymbol.range` **verbatim**, and gopls'
  range **excludes the doc comment**, reintroducing the exact orphaning bug that motivated the
  question.

**Recommendation: emit a Serena-shaped tuple; resolve it against SCIP's `enclosing_range`.**

## 2. `enclosing_range` — the span problem is already solved

`scip.proto` L758-776, verbatim:

> *"For definition occurrences, the enclosing range should indicate the start/end bounds of the
> entire definition AST node, **including documentation**."*
> *"Any **attributes/decorators/attached macros** should also be part of the enclosing range."*

The spec's own example is the Python decorator case exactly:

```
@cache
^ enclosing_range start---------------------|
def factorial(n):                           |
    return n * factorial(n-1) if n else 1   |
< enclosing_range end-----------------------|
```

**Emission verified per-indexer (SHA-pinned):** scip-typescript (deprecated flat field 7),
scip-python (functions + classes only, flat), scip-java (`typed_enclosing_range` oneof 10/11),
scip-go (typed; a test asserts field 7 stays empty). **A resolver must read BOTH encodings.**
The field lives on `Occurrence` only — there is no `SymbolInformation.enclosing_range`.

Everything else excludes attached docs: gopls' `DocumentSymbol.range` never references
`decl.Doc`; `go/ast` `FuncDecl.Pos()` is the `func` keyword and `TypeSpec.Pos()` is the *name*;
ctags `end:` starts at `line:`; Doxygen `bodystart` is the declaration line; tree-sitter-python
puts decorators in `decorated_definition`, a **sibling** of `function_definition`.
**Counter-example:** pyright *does* extend the range over decorators
(`extendRange(functionNode, decorators[0])`), which is why scip-python inherits it.

## 3. Every index system's overload disambiguator is a POSITIONAL COUNTER

This is the survey's most decision-relevant negative result, and it recurs everywhere:

- **SCIP / SemanticDB** — *"the tag is computed from the order of appearance of overloads in the
  source code: empty string for the definition that appears first, `+1` for the second."*
  scip-java's generator is literally `methods.indexOf(sym)` with statics sorted last.
- **Serena** — `NamePathComponent.__str__` → `f"{name}[{overload_idx}]"`. Same scheme.
- **Glean** — `span` is **in the key** of declaration predicates (incl. `MethodDeclaration`), so
  entity identity is position-dependent; Glass's `SymbolId` is a lossy projection whose reverse
  lookup implements only the `cxx` case.

**Unusable for a model:** it must *count* the overloads before it can name the second one, and
any reorder silently retargets the edit. **Omit the overload slot; treat multi-match as a hard
resolve error.** (Java needs *arity*, per arm 3 — arity-first with type spelling as tiebreaker,
which is not positional and is compatible with this.)

**The structural reason these systems fail as addresses:** they are built for **navigation**
(resolve once, jump — position-dependence is free because the answer is consumed immediately),
not for **addressing** (a name that must still mean the same thing *after* a mutation the index
has not seen). Do not expect to adopt an index's symbol format; adopt its *taxonomy of
distinctions* instead.

**Also not honoured uniformly:** scip-java emits method parameters as `local N`, not `(param)`;
scip-go emits type parameters as `local N`, not `[T]`; scip-typescript and scip-python never set
the disambiguator at all, so **TypeScript overloads collide onto one symbol**. The proto itself
says `Descriptor.Suffix` is *not* the kind and to use `SymbolInformation.Kind`.

## 4. Does any production harness address edits by symbol? Qualified yes

- **No standalone harness does.** A 13-agent source survey ([arXiv 2604.03515]) covering
  OpenCode, Codex CLI, OpenHands, Cline, Aider, SWE-agent, Agentless and others has **no
  symbol/AST category** in its edit-mechanism table.
- **Two production MCP tools do** — bolted onto harnesses lacking it natively.
  **Serena** (`replace_symbol_body(name_path, relative_path, body)`) is our proposed schema,
  shipped, used with Claude Code. **Moderne MCP** does it type-aware over OpenRewrite's LST.
- **One research system does, with the decisive number** — CODESTRUCT ([arXiv 2604.05407], AWS
  AI Labs), `editCode(path, op, selector, code)`, selector `file.py::Class::method`:

| Model | `str_replace` | CODESTRUCT | Δ |
|---|---|---|---|
| GPT-5 | 66.0 | 67.2 | +1.2 |
| GPT-5-mini | 60.4 | 62.0 | +1.6 |
| **GPT-5-nano** | **19.6** | **40.4** | **+20.8** |
| Qwen3-Coder | 61.2 | 66.2 | +5.0 |

> *"Models that frequently fail to produce valid patches under text-based interfaces benefit
> most: GPT-5-nano improves by 20.8% as empty-patch failures drop from 46.6% to 7.2%."*

**The weakest model gains the most.** That is our case.

**`ensure_import` is unprecedented as a model-emitted primitive.** It appears in **zero** LLM edit
vocabularies. It exists only in the structural lineage — OpenRewrite's
`AddImport(type, member, onlyIfReferenced)`, libcst's `AddImportsVisitor` — and in both it is an
**invariant the framework maintains**, never an opcode an author requests. Validated as a
concept, unprecedented as an op. **Say so; do not claim precedent.**

### 4a. Load-bearing operations across all surveyed systems

Present in **every** system: **replace-a-region** and **create-file**. Common: **insert-at-a-position**
(absent from aider `diff` and Codex V4A, which express insertion as a hunk with zero `-` lines —
it earns its place only when the address is not a byte range). Rare: **delete-region** is almost
always *replace-with-empty*, not its own op (only CODESTRUCT has explicit `removal`);
**rename-symbol** exists only in Serena and Moderne; **move/rename file** only in Codex V4A.

### 4b. Vendor findings that correct common assumptions

- **Cursor's apply model does NOT consume a lazy sketch.** *"By default, we have language models
  generate the fully rewritten file conditioned on the current file…"* — its three stated reasons
  for rejecting diff output are *"Thinking in Fewer Tokens"*, *"Diffs are Out of Distribution"*,
  and *"models are notoriously bad at counting line numbers."* The ~1000 tok/s comes from
  **speculative edits** — a decoding-fidelity guarantee, **not** a merge-correctness one.
- **Morph's lazy format is not fail-safe.** *"ALWAYS use `// ... existing code ...` for unchanged
  sections (**omitting this marker will cause deletions**)"* — omission and deletion are the same
  signal, and the call returns HTTP 200. Relace deliberately does **not** fix the marker string,
  relying on *"a less intelligent model [using] the context clues you provide."*
- **A wrong merge is silent in every fast-apply product.** No syntax check at inference, no
  applied/not-applied flag, no per-hunk report. Relace makes infidelity a *feature* —
  "Smoothing", where the model auto-adds an import the sketch omitted, is scored **correct**. A
  third-party plugin exists purely to add the guards vendors don't ship (marker-leakage abort,
  catastrophic-truncation abort at >60% chars lost, dropped-imports abort).
  **No independent accuracy benchmark of any apply model exists** — every published number is
  vendor-produced on a vendor-defined metric.
- **Serena has a live bug in exactly our operation** — [oraios/serena#576](https://github.com/oraios/serena/issues/576),
  `replace_symbol_body` duplicating code. The precedent is real but not flawless; whatever we
  build needs its own verification rather than inheriting confidence from Serena's existence.

### 4c. A fourth architecture nobody in the register proposed — the cascade

**Cascaded Code Editing** ([arXiv 2604.19201], FSE 2026): a large model emits a concise **edit
sketch** (deciding locations and contents); a small model performs **sketch application** (the
mechanical merge). Untuned Qwen2.5-Coder-14B as the applier scores **73.3 EM synthesized /
40.2 EM on real commit data**; in their Table 7, untuned QC-14B applying DeepSeek-R1 sketches
reached Pass@2 **66.7 vs 67.6** for R1 editing directly — near-zero quality loss, **on small
files**.

This fits oficina's stated shape uncomfortably well (*"Claude holds the plan; the system holds
the grind"*) while **inverting who decides the change** — today the local model decides. It is a
genuine fourth option beside whole-file / anchor-edits / symbol-edits and should be recorded as
such rather than discovered later. Caveats: the headline result requires **fine-tuning**
(commit EM 40.2 → 67.0), and the 40.2-vs-66.7 gap is plausibly file-size-driven but the corpora
and metrics also differ, so that attribution is **not established**.

## 5. Reliability — and why arms 2 and 4 only *appear* to disagree

Arm 4's corpus is entirely **anchor-based** formats. Its load-bearing finding, from Diff-XYZ
([arXiv 2510.12487v2], which benchmarks **Qwen2.5-Coder** — our coder base):

| failure mode (pp of 1000) | 3B | 7B | **14B** | 32B |
|---|---|---|---|---|
| Malformed — won't parse | 16 | 30 | **8** | 1 |
| **Parses but won't apply (anchoring)** | 78 | 51 | **54** | **50** |
| Applies but wrong | 6 | 16 | **24** | 26 |
| Exactly right | 0 | 3 | **14** | 23 |

**Scale fixes syntax and does not fix anchoring** — the anchoring bucket is flat at ~50pp from 7B
to 32B. Aider's own same-model ablation agrees: Qwen2.5-Coder-**32B** on polyglot scored pass@2
**16.4 whole** vs **8.0 diff**, with 1 vs 148 malformed responses; aider assigns `whole` to every
Qwen2.5-Coder **through 14B**, `diff` only at 32B.

**The reconciliation:** the variable is **anchor burden — what the model must reproduce.**

| format | what the model must produce |
|---|---|
| line numbers | *count* — universally rejected |
| whole file | every byte |
| SEARCH/REPLACE | region bytes + enough for uniqueness |
| V4A / udiff | 3 lines above + below, verbatim |
| **symbol selector** | **the unit's name + the new body** |

There are exactly **two** escape hatches from exact-anchor reproduction, and both are established
practice: aider routes weak models to `whole`; CODESTRUCT gives GPT-5-nano selectors. Whole-file
removes the burden but pays output proportional to file size. **A symbol selector removes it
*and* bounds output to one unit.**

**Corrections to earlier readings, recorded because both were acted on before being checked:**
- **udiff-l is the WORST format, not the best.** Marker collision is Diff-XYZ's *hypothesis 2*,
  which the authors **reject**: *"this verbosity increases complexity rather than actually helping
  the models"*; *"smaller open models benefit little from any formatting choice."* Diff-generation
  EM: udiff-l 1.5B 0.00 / 3B 0.00 / 7B 0.00 / 32B 0.01 vs search-replace 0.20 / 0.14 / 0.28 /
  0.68. **Do not ship ADD/DEL/CON tagging.**
- **SCIP's disambiguator does not solve overloads** — see § 3.

**Unmeasured anywhere, stated loudly:** Qwen2.5-Coder-14B on search-replace (the format×size cell
that matters most); any Qwen3 ≤14B on any edit-format benchmark; constrained decoding on a
code-edit task at any size; **code inside JSON string escaping**; the regime above ~4K tokens of
source. And critically — **every number above comes from a regime where whole-file was still an
option, so none of them price the doesn't-fit case.** There, the comparison is edits-vs-nothing.

**Format Tax** ([arXiv 2604.03616], 3B–32B band) attributes accuracy loss under format
constraints: **prompt 33%, grammar-constrained decoding only 4%** — *"the decoder is not the
problem — asking for format in the prompt is."* Implied mitigation: **decouple** (free-text
generation, second-pass reformat). *"Let Me Speak Freely"* (2408.02442) is **contested** by the
dottxt rebuttal — do not cite as settled.

## 6. The failed arm — an acronym-collision defect worth reporting cross-repo

The `web-research` MCP arm resolved **"SCIP" to the mixed-integer-programming solver**
(`gams.com/latest/docs/S_SCIP.html`), spending 146 s on solver branching parameters and 205 s on
the full ECMAScript spec (777K chars). Its auditor correctly self-reported
`sufficient: false, confidence: low` — an improvement on the D2 defect recorded 2026-07-11
(non-discriminating auditor). **The failure moved upstream into query resolution.**

Two lessons: the tool is strong on *"research this URL"* and weak on *"find the thing called X"*
when X is ambiguous; and `search_topic` uses **open** extraction, which returns README summaries
rather than answers — `research_url(focus=...)` is the shape that would have worked.
Worth a cross-repo note to `web-research` alongside the 2026-07-11 field report.

## 7. What a symbol address CANNOT express

Converged on independently by arms 1 and 3:

1. **Anonymous classes, lambdas, closures, local classes.** SCIP forces `local N`, a per-document
   counter the proto says *"MUST only be used for entities local to a Document."* JDT's
   `SourceType.isAnonymous()` is literally `name.length() == 0`. OpenRewrite's matcher takes a
   `J.ClassDeclaration`, and an anonymous body is a `J.Block` — **not hard, impossible.** ctags
   synthesizes `__anon<hash>` hashed over the *filename*, so it breaks on rename.
2. **Anything inside a function body** — a statement, a nested branch. Go objectpath rejects it
   outright (*"no path for local %v"*).
3. **Portable overload selection** (§ 3).
4. **Parameters and type parameters, in our languages** — the SCIP suffix vocabulary looks like it
   covers these; the indexers we would actually run emit `local N`.
5. **Two same-named module-level Python functions** — Python shadows one before any tool sees it.
6. **Cross-file moves** — the address is file-anchored by design.

**⇒ The schema needs an explicit REFUSAL region with whole-file fallback** — which is E-D1's
existing mechanism, so it costs nothing to implement.

## 8. Mechanisms to copy, and debts owed

**Copy:**
- **Separate the "edit didn't apply" budget from the "output didn't parse" budget.** SWE-agent's
  `_RetryWithOutput` deliberately does **not** increment `n_format_fails` — the only reason a
  trajectory survives 33 failed edits when the format budget is 3. Its edit tool was worth
  **+3.0 points** (18.0 vs 15.0 with linting removed; 10.3 with no edit tool at all).
- **On failure return the nearby candidates, not "not found."** Aider's `find_similar_lines`
  "Did you mean" and SWE-agent's whole-file fallback search. For symbol addressing the analogue is
  returning the file's actual symbol list.

**Owe:**
- **A replacement for the "did the model read the file?" check** a string anchor gives for free.
  Serena settles for a prompt norm (*"Only replace symbol bodies if you have previously made a
  retrieval with `include_body=True`"*) — a norm, not an invariant. Our loop carries the file as a
  stable C0 segment, so a content-hash check is available to us and is not available to a
  stateless MCP tool.
- **An ambiguity contract scoped from day one** (`Class.method`), not as a v2 fix.

**Independent corroboration of E-D6** (validate at the iteration boundary, not per edit): Serena
ships `ENABLE_DIAGNOSTICS = False` — *"per-edit diagnostics are a questionable feature, since
individual edits often intentionally introduce diagnostics … that are then resolved in subsequent
edits."* Our loop is Serena's shape, not CODESTRUCT's (which applies one edit per turn).

**Bearing on our own history:** the session-127 drift class — the module docstring deleted in
**4 of 4 runs**, including runs whose objective said not to touch it — is structurally impossible
under a symbol-body replace, because a span excluding the docstring never grants authority over
it. (Not a claim E-D1's trigger fired; that needs sibling *code*.)

## 9. The resulting schema

```json
{"op": "replace_unit",
 "path": ["EvaluatedLoop", "run"],
 "kind": "Method",
 "body": "..."}
```

- **No `file` field — deliberate (user decision, s135).** One call edits one file, and that file
  is already named by `deliverable.target`. Three consequences, all good: it matches **S1**
  (one call, one deliverable) instead of exceeding it; it turns *"cross-file moves are not
  expressible"* from a limitation of the grammar into a **scope boundary** — which file is the
  caller's reasoning, i.e. Claude's; and it **removes a failure mode entirely**, since a model
  that can name a file can name the *wrong* file and `patch_file` would apply the edit to it
  successfully, silently, outside the run's declared target. A schema that cannot express the
  file cannot make that mistake.
- **Tuple, not string.** Concrete hazards avoided: SCIP backtick-escapes identifiers; pytest node
  IDs are **not splittable on `::`** (`test_special[with::colon]` is a real collectible ID); gopls
  spells Go methods `(*T).method` and places them at **top level, not nested under the type** —
  so `EvaluatedLoop.run` is not what gopls calls it.
- **`kind` = an LSP `SymbolKind` name** — a closed 26-value vocabulary showable in the prompt.
  Not SCIP descriptor suffixes (§ 3).
- **Resolution — SUPERSEDED session 136 (see § 0a).** ~~Run `scip-python`/`scip-go`, parse each
  `SymbolInformation.symbol`, discard the `scheme manager package version` prefix, match the
  `path` array against the descriptor tail ignoring suffix characters, take the
  `Definition`-role `Occurrence`'s enclosing range. ~30 lines. Fallback tier: LSP
  `documentSymbol`.~~ **Decided instead: in-process AST per language**, a fifth `LanguagePack`
  member, seeded by `benchmarks/lib/writemodel_apply.py`'s `locate_function` (which already
  spans decorators) and extended to dotted `Class.method`. Three grounds, in P3-D1 §
  "The resolver": the seed exists, T-104 already chose `ast` + `go/parser`, and **a precomputed
  index is stale inside a batch**. The SCIP research below stands as the correct account of what
  SCIP specifies — it is simply not the tool we need. Verified session 136: no `scip*` binary and
  no LSP server is installed in this estate, so the route also carried an unmet prerequisite.

**Verification note:** Kythe and Glean claims were relayed between agents rather than
primary-verified, and are flagged lower-confidence in the arm reports.

## 10. An unresolved tension, recorded rather than smoothed over

**Aider's own blog measures the opposite of Diff-XYZ on format preference.** Aider reports
gpt-4-1106 scoring **20% with SEARCH/REPLACE vs 61% with udiff** (and gpt-4-0613, 26% vs 59%),
attributing it to udiff making the model *"act more like it's writing textual data intended to be
read by a program"*. Diff-XYZ, on the Qwen2.5-Coder family, measures **search-replace beating
udiff at every size** (7B 0.28 vs 0.06; 32B 0.68 vs 0.23).

These are not directly comparable — different model families, different tasks, different metrics,
two years apart — and neither is wrong. But the disagreement is itself informative: **format
preference is not a property of "small models" in general, it is a property of a
model-family × task pairing.** Which means any format choice we make on the strength of published
numbers is inherited from someone else's configuration, and **P3-T0 must measure our own**. It
also means neither result should be cited as settled guidance in a decision record.

## 11. Companion measurement

Our own AST census of the target corpora — what granularity is required, what a symbol address
fails to cover in Python and Go, and the two span hazards found by inspection — is
`ref:unit-addressing-census` (`docs/findings/unit-addressing-census-2026-07-31.md`). The two
documents answer different halves: this one is *what has been built and measured elsewhere*, that
one is *what our own code actually looks like*. Read together they are P3-D1's evidence base.
<!-- /ref:symbol-addressed-editing-survey -->
