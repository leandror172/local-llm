# Session Log

**Current Layer:** Layer 5+ — oficina P3 (context & prompt assembly); P3-D1 FROZEN, P3-D10 open, criterion 3 outstanding as D1's acceptance condition
**Current Session:** 2026-08-20 — Session 140: P3-D1 FROZEN on (B) — four operations, the magnitude corrected AT the freeze, and remedy 2 built + measured live

---
## 2026-08-20 - Session 140: P3-D1 FROZEN on (B) — four operations, the magnitude corrected AT the freeze, and remedy 2 built + measured live

### Context

Opened as a "discuss next steps" session against the s139 handoff, whose Next named P3-D1's remedy set. Orientation found the decision itself still formally OPEN, so the session became: measure what the remedy is actually worth, freeze the entry, then build the cheapest operation and check the model can reach it.

### What Was Done

- **Split 5b's constant slice — the resolver extension converts 17.4%, not 30.4%.** `bound_names`/`_names_in` added to the census; `classify` gained `before_bound` and two keys; cuts made durable in a new `census_report.py` + `run-census-report.sh`. 487 real edits re-measured.
- **P3-D1 FROZEN on (B), four operations** — with s137's caveats carried INSIDE the entry, the reconciled vocabulary, the corrected magnitude, and criterion 3 attached as an acceptance condition.
- **P3-D10 created** and s136's 89-line "who chooses" re-argument MOVED into it verbatim; the residue claim in D1's own body struck in place rather than reworded.
- **Remedy 2 built** — module constants addressable, `Constant`/`ClassConstant`, `shared_binding` refusal, `SharedBinding` raised from `find_units`.
- **Remedy 2 measured live** — a forcing `--corpus constant`, 24 generations: 12/12 fidelity, 0/12 degeneration, 0/12 shape defects, 30 output tokens flat.
- **Two instrument fixes**: the prompt's kind list now RENDERED from `KINDS`; `body_units` now uses `_addressable_names`.
- **Memory + index propagation**: the unit-addressing contract written to vision KNOWLEDGE; four index rows corrected; a stale ⚠️ in `benchmarks/.memories/QUICK.md` claiming its tests run in no suite (closed s138) removed.
- Suite **954 → 1009**; benchmarks 116 → 170. **PR #94 open**, 8 commits.

### Decisions Made

- **(B) over (A)/(C)/(D)**, on criteria 1 (12/12), 2 (0/12 — the design-killing case), 4 (0/12), 43 tokens flat, and 5a/5b. Provisional by its own terms until criterion 3 runs.
- **The operation vocabulary is FOUR, not three** — the entry's "closes the entire residue" is true of STRUCTURE and false of EDITS. Static coverage ≠ edit coverage.
- **"Who chooses" is NOT decided here.** Lifted to P3-D10 rather than frozen alongside a measured half — a fork inside a frozen entry reads as settled, which is the s135 failure.
- **Criterion 3 is a BUILD, not a gate.** It cannot gate what it depends on, and a probe costing what the build costs is not a probe. Attached as an acceptance condition (P4-D2 pattern) and written into the plan, where it had lived only in `session-log.md`.
- **`_UNIT_NODES` deleted** — the plan predicted it; measurement showed a pre-filter blocks nothing the dispatch does and makes the rule untestable. One rule, one enforcement point.
- **Cheapest-first kept, its justification replaced.** The resolver extension is no longer "also largest" — it ties imports alone.

### Next

- **Freeze P3-D10** (recommendation standing from s136), then **criterion 3 as the production BUILD**: graduate the locator to `LanguagePack` #5, emit+apply in `loop.py`, harness-side detection. `replace_unit`-only is a legitimate first increment because detection makes it safe.
- **Verify the derived feasibility number**: (B) frees ~6144 tokens of prompt budget (~1.75×, not 3× — the 8192 cap already bounds today's damage). Re-run T-122's sweep and report N/27 against 21/27.
- Review/merge **PR #94**. Converge the **stale LTG index**. Fold **T-139** into the criterion 3 session — it will produce surprising cells.

### Gotchas

- **A measurement taken under today's assumptions cannot price a change to those assumptions.** The census's own docstring argued the added/changed conflation was sound — "a module constant has no path whether you are adding it or editing it" — true, until you give it a path. Three load-bearing numbers were wrong the same way this session.
- **EVERY defect came from a mutation or a reproduction check; none from a green run.** 10/10 mutations caught only after three survived and became tests.
- **Two mutations both left the suite green, each neutralised by the other** — a rule enforced twice is a rule no single-point mutation can reach.
- **A definition owned by code must be RENDERED from it, never restated.** The prompt's kind list and `body_units` were each a second copy of "what counts as a unit"; both went stale the moment `KINDS` grew — one making the new capability unreachable by the model, the other reporting twelve correct answers as fragments.
- **My own cut definition would have "corrected" a CORRECT published number** — `"oficina/"` also matches `tests/oficina/`. Caught only by checking the new table against s139's.
- **I wrote "PR #93" into a memory file before the PR existed.** It is #94.
- The reading guide already recorded the backgrounded-call verdict gap (T-128), so a "new finding" was dropped before filing — reading beat assuming.
