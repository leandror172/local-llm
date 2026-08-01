# Session Log

**Current Layer:** "Layer 5+ — oficina P1–P4 built; P3 (context & prompt assembly) planned, D1 re-evidenced and still open, register unwalked"
**Current Session:** 2026-07-31 — Session 135: "P3-D1 RE-OPENED — the option set was incomplete; symbol-addressed editing surveyed (4 arms) and measured on our own corpus; five confident claims corrected"

---
## 2026-07-31 - Session 135: "P3-D1 RE-OPENED — the option set was incomplete; symbol-addressed editing surveyed (4 arms) and measured on our own corpus; five confident claims corrected"

### Context

Opened as "discuss next steps" with the P3 register walk as the user's stated plan. The walk
never got past D1 — a user challenge on what `deliverable.unit` actually meant exposed that the
register's option set was **missing the intended design**, and the session became a full
prior-art survey plus an own-corpus measurement to price it. No code written; docs only.

### What Was Done

- **`docs(P3-D1): symbol-addressed editing — 4-arm survey, own-corpus census, register rewritten`** (b9aaf36, 11 files, +2019/−77).
- **P3-D1 rewritten TWICE.** First to a three-option fork correcting the s134 scoping error; then to a four-option fork with the evidence folded in and a concrete schema. Recorded as revisions, not silent fixes.
- **Two AST censuses of the actual targets** (`ref:unit-addressing-census`): 10 oficina Python modules, and 129 non-test Go files / 20,643 lines across `expenses/code` + `career-search` via `go/ast`. Scripts promoted to `.claude/tools/unit-census-*`.
- **Four-arm prior-art survey commissioned and preserved** (`ref:symbol-addressed-editing-survey`, `docs/research/symbol-addressed-editing/`) — address grammars, LLM edit vocabularies, Java/OpenRewrite, small-model reliability; ~690K subagent tokens rescued out of a session-scoped scratchpad.
- **T-133 trimmed 3,800→1,535 chars**, body moved to `ref:declared-unconsumed-spec-fields`, and **extended with a second declared-and-unconsumed field** (`acceptance.validators`, `intake.py:58`) found by the same grep.
- Branch renamed `docs/p3-plan-and-join-record` → `feature/oficina-p3-context-assembly` (local-only, no PR).
- **Cross-repo, `web-research` (2 commits):** field report on a new defect class + **T-09**; then discovered the **2026-07-11 field report had been UNTRACKED for three weeks** while cited from this repo as delivered, and **four of its five defects had no task** — committed it and backfilled **T-10..T-13**.

### Decisions Made

- **`deliverable.unit` (caller names one function) was NOT what the phase needs.** The T-122 blocked set is blocked by SIZE, not by having one identifiable bad unit, so a caller-scoped span does not reach it. The intended design — **the model emits structured edit operations** — had been dropped in s134 as a "duplicate axis", on a reason **S15 undercuts**: the branch IS the deliverable, so response shape is not a `kind`, and E-D8's Axis-B trigger therefore does not capture it.
- **Schema: symbol-addressed, structured tuple, NO `file` field** (user decision). `{"op":"replace_unit","path":["EvaluatedLoop","run"],"kind":"Method","body":"..."}`. Dropping `file` matches S1 rather than exceeding it, turns "cross-file moves are inexpressible" from a grammar gap into a **scope boundary** (which file is Claude's reasoning), and removes a failure mode outright — a model that can name a file can name the *wrong* file, and `patch_file` would apply the edit to it successfully and silently.
- **Dotted addressing is mandatory, not a refinement.** `loop.py`'s top-level ceiling is 438 lines (69% of file) vs 66 (10%) dotted; median edit 17 lines. Top-level-only addressing is worthless on exactly the files that motivated T-122.
- **Omit the overload slot entirely.** Every index system's disambiguator is a POSITIONAL counter (SCIP/SemanticDB `+1` = `methods.indexOf(sym)`, Serena `[n]`, Glean's `span`-in-key). Multi-match ⇒ hard resolve error. Java needs arity-first with type spelling as tiebreaker — not positional, and compatible.
- **A refusal region is mandatory** (anonymous/lambda/local classes, in-body spans) — arms 1 and 3 converged on it independently. Fallback is whole-file, i.e. **E-D1's existing mechanism**, so it costs nothing to build.
- **Only the NARROW ask is licensed.** E-D1 preserved code-anchored as *"the fallback mechanism"*; T-122 is a *feasibility* argument while E-D1 was decided on *quality + spec simplicity*. So a **size-gated fallback** is E-D1 operating as designed; making it the default would reverse E-D1 on three grounds T-122 does not rebut.
- **D1 still NOT frozen.** The mechanism argument gained a production precedent and a measured +20.8pp on the weakest-model case; the magnitude on *our* coder remains unmeasured, and the two published results bearing on format choice **disagree with each other**.
- **A fourth option recorded rather than left to be rediscovered:** the CASCADE (Claude emits an edit sketch, the local model applies it). Not recommended — it moves intellectual work back to Claude, which is the cost oficina exists to avoid.

### Next

- **P3-T0 is now the ONLY thing that can decide D1** — reframed with three pre-registered criteria: anchor fidelity, **no degeneration to whole-file** (the silent one that voids T-122's rationale), and applicability rather than exact match. Write the apply-side negative control FIRST. Target `parser.py`/`intake.py`, never `loop.py`.
- **UNPRICED PREREQUISITE, not yet a task:** the recommended resolution path (join the tuple to SCIP's `enclosing_range`) assumes `scip-python`/`scip-go` can actually be run in this estate. **Nobody has checked.** If they cannot, the fallback tier is LSP `documentSymbol` — and then the span must be backfilled per language by hand, which re-opens the decorator/doc-comment hazard the SCIP route closes for free.
- **T-133 remains the cheapest first move** — untouched by all of this, now two-membered, independent of D1 and of the probe. Its test must fail today or it encodes the bug, and it must be **behavioural**, not a symbol scan.
- **The register was never walked.** D2, D3, D6, D7, D8, D9 remain open and unfrozen; only D1 was worked.
- Carried: **T-131** (weigh with T-111), **T-132** (root QUICK, own session), **Axis B**, T-125/126/127/128.

### Gotchas

- **Five confident claims were WRONG this session**, recorded as a corrections table in the survey § 0 rather than silently fixed. Two came from search-result summaries that were *directionally right and specifically wrong* — SCIP's disambiguator "handles overloads" (it **counts** them, so it renumbers on insert) and udiff-l "helps small models" (it is the **worst** format at every size, and the paper **rejects** the marker-collision mechanism that was quoted for it). **A summarizer's paraphrase of a spec is not the spec** — the failure has no symptom, because a plausible summary reads exactly like a correct one.
- **Java was assumed to have both span hazards at once; it has NEITHER.** Annotations are grammatically modifiers (inside the declaration), and JDT's node range *begins at the opening `/**`* — the only tool surveyed whose natural span is the correct span. javac's Trees API *does* have the Python/Go bug.
- **`query_knowledge` returning `[]` is not evidence of an empty corpus** — it matches close-to-literally (a known, unfixed defect since 2026-07-11, now `web-research` T-13). This session read two empty results as "genuinely new ground for the estate" and commissioned a four-arm survey on that basis. The tool cannot distinguish "nothing stored" from "nothing matched", so its silence reads as a fact about the corpus when it is only a fact about the matcher.
- **Code-index systems fail as addresses for a structural reason:** they are built for **navigation** (resolve once, jump — position-dependence is free) not **addressing** (a name that must survive a mutation the index has not seen). Do not expect to adopt an index's symbol *format*; adopt its taxonomy of distinctions.
- **A cited cross-repo artefact had never been committed.** The 2026-07-11 `web-research` field report sat untracked for three weeks while `ref:delegate-cross-repo` pointed at it, and four of its five defects had no task — invisible to every session since. Worth a periodic check that cross-repo citations resolve to something in *history*, not just on a disk.
- **The T-09/T-11 pair wants one guard with two bounds:** a `clean_chars` **ceiling** (a 452K-char document is probably off-domain) and a **floor** (a 350-char document is probably a bot wall). Neither is measured today.
