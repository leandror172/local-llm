## 2026-08-18 - Session 137: P3-T0 benchmark half BUILT + MEASURED — symbol-addressed editing is 43 output tokens FLAT; PR #89 open

### Context

Resumed on P3-T0, which s136 had shrunk twice: the apply half was already built and measured (arm A, s124) and the resolver was decided (in-process AST), leaving only dotted `Class.method` resolution and a hardened corpus. Four design questions were settled with the user before any code — the failure channel, placement beside a frozen `locate_function`, `kind`-as-check, and the unit boundary — then an advisor pass added a fifth (`unknown_kind`) and sharpened the coverage-bound finding.

### What Was Done

- **P3-T0's deterministic half shipped, tests-first.** `find_units`/`resolve_unit` beside a **frozen** `locate_function`; `[]` means absent and unparseable RAISES, so no value carries two meanings. Five resolve reasons, each a different remedy. 50 tests.
- **`apply_unit` shipped** — the dotted applier that **owns indentation** (dedent → re-indent to the resolved span). 58 tests.
- **Class-bearing corpus + `Task.target_path`**, plus ground-truth tests nothing had: the generated original must FAIL its target test and PASS every filler. 67 tests total.
- **4th benchmark arm `symbol_addressed`** — the model NAMES the unit (`{path, kind, body}`) instead of being handed it; per-criterion metrics recorded BEFORE the apply so failures still report their mode.
- **The probe ran.** 24 generations, `my-python-q25c14-16k`, class corpus.
- **Docs propagated** — `.claude/index.md`, three folder memories, root QUICK; plus two cross-session memories.
- **`benchmarks/results/` unignored** (170 files, +1 MB) on the provenance argument.
- **PR #89 opened**; four delegated runs pinned under `refs/oficina/<run_id>`.

### Decisions Made

- **Locator built ALONGSIDE `locate_function`, not folded into it** — it produced arm A's published numbers, and a changed instrument invalidates them (`ref:patterns-refactoring-duplicate-first`).
- **`kind` is a CHECK, never a selector.** Using it to narrow a multi-match is first-match-wins with extra steps, which survey § 3 rejects. As a check it makes "said Method, named a Class" loud — narrowing criterion 2's silent region without closing it.
- **`unknown_kind` is its own reason** (advisor's catch). "Wrong vocabulary" and "wrong unit" have opposite remedies — a prompt fix vs. abandoning the design — so they must not share a bucket. Same shape as T-130's `applies_to` inversion.
- **The unit is whatever the language's parser ATTACHES** — decorators in Python, `decl.Doc` in Go, by construction rather than a hand-authored per-language list. A `#` comment above a `def` is therefore outside the unit.
- **`kind` is a FREE STRING in the arm's response schema, not an enum** — constraining it would make `unknown_kind` unobservable. A probe must not use a grammar to hide the failure it exists to measure.
- **Benchmark owns the controlled A/B; oficina owns real files.** The plan named one vehicle for two questions and that vehicle cannot run the stated target — making it do so would reimplement oficina inside it.
- **`benchmarks/results/` tracked whole** rather than filtered to `*.md`, on the provenance argument `refs/oficina` rests on. Growth cost accepted deliberately.

### Next

- **P3-T0's OFICINA half — criterion 3.** A real file from T-122's blocked set (`parser.py`/`intake.py`), which the benchmark structurally cannot run. This is the remaining gate evidence.
- **Criterion 5 is UNEXERCISED, not passed.** No corpus task needs a new top-level statement, so its `0/12` says the case never arose. The P3-D1 item 6 prediction — a function-local `import` as the tell — is still untested and needs a task that genuinely requires one.
- **Then D2 / D3-half-1 / D7**, all D1-independent; D3 half 1 is marked *ready to freeze*.
- Carried: **T-136** (67 benchmark tests run in no suite), **T-137** (new), T-131, T-132 (root QUICK now 145 lines against its stated 30), T-135, T-125/126/127/128.

### Gotchas

- **Two of my own claims were wrong and are retracted in place.** (1) Estimated ~2–3 tok/s from a 22% GPU-utilisation reading; the measurable floor was **≥5.1**. (2) Claimed **8 ref keys break on any clone** — **false**, they resolve via a tracked duplicate in `docs/findings/`. Both are the magnitude-vs-mechanism error the repo already records against itself.
- **`ref-lookup.sh --paths` emits one `KEY<TAB>path` line per key**, a shape that structurally cannot represent two definitions. It showed the untracked copy and hid the tracked one; the follow-up check ("is *that* file tracked?") was answered honestly and confirmed a false premise. **`check-ref-integrity.py` had it right the whole time**, inside a **39-error backlog nobody reads** — a signal that fires unconditionally into a backlog carries as little as one that never fires.
- **Delegation gave a clean natural experiment on brief construction.** Same file, same model, same session: a brief saying *"do not modify any existing function"* produced a deleted module docstring and `list[…]`→`List[…]` churn across four frozen functions; a brief that **enumerated the frozen names and gave the reason** produced 31 added / 0 removed. Enumerate-and-justify beats assert-a-principle — a datapoint for **P3-D4**.
- **Both delegated models failed the SAME way on the corpus generator** — qwen2.5-coder:14b put a class docstring at column 0, gemma3:12b emitted every method `def` at column 0 with 8-space bodies. Not logic errors: **assembling correctly-indented multi-level text**, with the levels spelled out. That independently justifies `apply_unit`'s harness-owned re-indentation, which was derived from first principle 1 *before* the evidence existed.
- **A negative constraint on a defensive reflex loses to the reflex.** The brief said, in capitals, *"Do NOT catch SyntaxError"*; the model wrote `try/except SyntaxError: return []`. Third instance of this shape here, and the negative-control test caught it all three times.
- **My smoke test found a defect in the instrument, not the model** — a fenced body failed to parse, taking the neighbouring-code count down with it, so one criterion-4 defect silently hid the other. Third time this session a newly-tightened check's first failure was in the harness.
- Process: `python3 -m pytest` run directly again — but **structurally this time**, since no wrapper exists for these tests (T-136), so the project's bash-wrapper rule is currently unfollowable here.
