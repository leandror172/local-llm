## 2026-08-11 - Session 136: P3-D1 re-grounded — the apply mechanism was already BUILT AND MEASURED in s124; T-133 shipped; PR #88 open

### Context

Opened as a "discuss next steps" session against the s135 handoff, whose Next named P3-T0 as the only thing that could decide P3-D1 and flagged an unpriced SCIP prerequisite. A user instruction to read the research we already had — and then the reading guide's own top entry, which had been skipped — turned it into a correction session: four claims in P3-D1 were falsified from primary sources inside this repo, and the phase's cheapest task then shipped.

### What Was Done

- **P3-D1 revision 3 (`1a35235`)** — recorded four corrections, each from a primary source in this repo rather than from further reasoning.
- **Vision-level reconciliation (`3f43806`)** — the first pass of `docs/vision/coding-delegate/` against THIS entry; five results, including T-122's actual code path.
- **"Who chooses" re-argued (`6ba0e09`)** — its stated decider does not hold, and the two-way framing hid the option the code already implements twice.
- **T-133 shipped (`7bd9191`)** — `context.callers` wired as its own stable prompt segment, `acceptance.validators` deleted; suite **408 → 416**, `make accept-p4` green.
- **Doc propagation (`4c10d15`)** — swept every record the schema change made stale; three real hits, one of them a recorded deferral this session had contradicted without saying so.
- **PR #88 opened** (`MERGEABLE`, merge state `CLEAN`, 12 commits) — the branch's first code after 7 docs-only commits.
- Checked the s135 handoff's flagged prerequisite empirically: **no `scip*` binary and no LSP server is installed** in this estate.
- *(`f78d0c4`, the payload-scalar quote-stripping fix, was already at HEAD when the session opened — s135's tail, covered by no session log.)*

### Decisions Made

- **P3-D1's apply mechanism was never open.** `ref:oficina-write-model-report` **arm A** is exactly it — *"model returns only the rewritten function; code locates the span (`ast`), reads `old_string` from disk, exact-replace; apply-failure mode: none — 100% by construction"*, 25 output tokens flat across every size bucket. The harness constructs the anchor; the model never reproduces bytes. A model emitting its own anchors is **arm C**, a different arm, also already measured.
- **Resolver: in-process AST per language, NOT SCIP** (supersedes survey § 9). Three grounds: the seed exists and already spans decorators (`writemodel_apply.py:36`, verdict 2); T-104 already chose `ast` + `go/parser`; and **a precomputed index is stale inside a batch** — op 1 invalidates it for ops 2..N, the same objection already made against line numbers. `locate_unit` stays a per-language `LanguagePack` member (verified as-built: the pack has exactly 4).
- **First principle 1 is the decisive citation and had never been made** — *"harness code does all mechanics (**locate**, fetch, splice, verify, log)"*. An emitted anchor makes the MODEL locate; a symbol name makes the HARNESS locate. Principle 2's ellipsis un-joined: the request/fulfill clause is about *context* requests, not edit responses.
- **T-133's two fields got opposite remedies for a recorded reason.** `callers` WIRED (measured evidence, no derivable substitute) as its **own** segment — folding it under `CONTEXT:` would make that header a false claim (P3-D3 half 1). `validators` DELETED (selection derives from the language; E-D2 refuses a spec field for a derivable fact).
- **"Who chooses" recommendation revised to DERIVE WITH OVERRIDE** — `_resolve_output_shape(assembly)` following E-D9/T-114's shape exactly. Recorded as **re-argued, not frozen**; the probe still gates the entry. User settled both open sub-questions: an *optional* override does not violate E-D2's spirit; recording shape for reproducibility is *"might be a good idea"* and stays open.
- **P3-D6 FROZEN AND BUILT**; the P3-vs-Axis-B routing conflict resolved in P3's favour **by mechanism** — `validators` is not a *kind*, so E-D8's trigger never covered it.

### Next

- **P3-T0 is materially smaller than it was.** The apply half is closed and the resolver is decided, so the probe measures only what arm A never covered: **dotted `Class.method` resolution** (`locate_function` is top-level-only) and **a hardened corpus** (arm A's filler was 20 identical `op_k` functions — *"the synthetic corpus accidentally optimized for whole-file"*). **Vehicle: the EXISTING benchmark** (`benchmarks/lib/writemodel_{apply,corpus,bench}.py`, `run-write-model-bench.sh`) plus E-D1's own prescribed corpus hardening — not a probe built from scratch. Criterion 1 is half deterministic and belongs in the 408→416 suite, not on the GPU.
- **D2 / D3-half-1 / D7 remain unwalked** and are D1-independent; the plan marks **D3 half 1 "ready to freeze"**. Walking them turns P3 from one blocked entry into a frozen register.
- **PR #88 is open and MERGEABLE** — note `checks: 0`, this repo has no CI, so the suite + `make accept-p4` results in the PR body are the only verification record.
- Carried: **T-131** (weigh with T-111), **T-132** (root QUICK, own session — now **three** sessions behind), **Axis B**, T-125/126/127/128, new **T-135**.

### Gotchas

- **The survey enumerated external prior art exhaustively and never enumerated our own.** 13-agent source survey, four indexer SHAs, five fast-apply vendors — and the operation was already built and measured in `benchmarks/lib/`. Nothing in it is false; the set it searched was not the set that mattered. **`ref:corpus-divergence-pattern` at document altitude** — recorded as § 0a in the survey itself.
- **The decorator span hazard was solved here in s124, in code, by a local model, verdict 2.** The s135 census re-derived it "by inspection" and the survey credited SCIP with solving it.
- **P3-T0's criteria existed in TWO copies in one document and drifted within a single revision pass.** The probe copy was rewritten in s135; D1's summary copy still asked for *"the emitted `old_string`"*. Collapsed to one source (T-130's pattern) — the duplication survived a full re-grounding **inside one file**.
- **A claim this branch's own survey falsified was left standing in the body that consumed it** — the udiff-l argument. § 0 corrected it; P3-D1 still argued from it in two places.
- **The "who chooses" decider rested on a code path that does not execute.** All three oficina personas declare `PARAMETER num_ctx 16384`, so `_context_limit is None` only when `/api/show` fails — i.e. Ollama is down and the run dies anyway.
- **The memory that OUTRANKS the plan docs was itself two sessions stale.** `coding-delegate/.memories/KNOWLEDGE.md`'s assembly paragraph listed neither `current_file` nor `mode`, both added by T-110 in s126 → **T-135**.
- **A recorded deferral was contradicted without noticing.** `oficina-p2-go-widening.md` said deleting `validators` *"would flip accepted-and-ignored into unknown-key REJECTION"* and queued it for Axis B. The flip **is** the fix and the blast radius was measured (one occurrence, its own declaration) — but nothing in T-133's evidence chain pointed at that plan. **It surfaced only because the user asked for a doc sweep.**
- Process: ran `python3 -m pytest` directly (project rule is `make test` / bash wrappers) and grepped files that then had to be `Read` anyway to edit.
