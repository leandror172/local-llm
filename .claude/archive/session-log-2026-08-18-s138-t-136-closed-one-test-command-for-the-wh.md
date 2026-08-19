## 2026-08-18 - Session 138: T-136 CLOSED — one test command for the whole repo: 894 tests across six suites, not 416; T-138 filed; PR #90 open

### Context

Opened on "PR merged, local master updated — let's discuss next steps" after PR #89 landed. Orientation confirmed master at `4cd0589` (a real merge commit, not a squash) with `HEAD == origin/master`. The discussion surfaced that P3-T0's remaining gate evidence is a build rather than a probe, and that criterion 5 is schema-shaping and should precede criterion 3 — after which the user chose the T-136 debt item first, then criterion 5. No P3 code was written; criterion 5 was not started.

### What Was Done

- **feat(T-136): one test command for the whole repo — 894 tests, six suites.** Root `Makefile` + `scripts/run-all-tests.sh`, plus new runners `benchmarks/lib/run-tests.sh`, `mcp-server/scripts/run-tests.sh`, `docs/portfolio/hf-space/run-tests.sh`; `mcp-server/Makefile`'s `test` delegates instead of inlining `uv run pytest`; `overlays/Makefile` lost its hardcoded counts; `.claude/hooks/tests/run-tests.sh` gained a summary line. All five new scripts recorded `100755` in the index.
- **docs(T-136): reconciled every quoted test count** across `.claude/index.md` (new **Test Runners** section + a completeness recipe), `.claude/session-context.md`, `mcp-server/.memories/QUICK.md`, `docs/vision/coding-delegate/.memories/QUICK.md`. T-136 closed, **T-138 filed**.
- **PR #90 opened** (`chore/t136-repo-test-command`, 2 commits).
- **Measured, not assumed, throughout:** the three suite counts independently (416 / 296 / 67) before writing anything, then hooks 26, personas 21, hf-space 68. Verified the aggregator in **both** directions with a deliberate failing test (exit 1, `FAIL` row, failure count surfaced) and arg pass-through with a check that could fail (`-k` → 8 selected / 59 deselected). `check-ref-integrity.py` held at **39 errors** — the known backlog, none added.
- **New memory** `feedback_enumerate_before_asserting_a_set`, indexed in `MEMORY.md`.
- Propagated the PR #89 merge into the coding-delegate folder memory, which still described the branch as in flight (the T-135 staleness class).

### Decisions Made

- **Fold nothing into `mcp-server`'s pytest; give each area a runner and aggregate.** The alternative — `testpaths = ["tests", "../benchmarks/lib"]` — would have merged two of six corpora and called the result one number, leaving `overlays`, `hooks`, `personas` and `hf-space` outside. That relocates the boundary rather than removing it, which is the failure T-136 is filed against.
- **Delete asserted counts from help text rather than correcting them.** `overlays/Makefile` claimed "196 tests total" against an actual 296. Editing it to 296 re-arms the identical trap; a count in help text is a claim with no checker. The run reports the number.
- **Include `docs/portfolio/hf-space/tests` (68) in `make test`** — user decision. `app.py` is this repo's code and the suite is hermetic by design (conftest mocks gradio / huggingface_hub / anthropic before import). `benchmarks/test-fixtures/ollama-client/` stays out as fixture data, and the exclusion is stated in the script rather than left accidental.
- **Fix the producer, not the parser.** The hooks runner printed no total; teaching the aggregator that one runner's format would have left the next one to fail the same way, so the runner now emits `N passed, M failed`.
- **T-138 filed rather than swept.** A `.sh` meant to be *sourced* should stay non-executable, so the 53 files need a real pass, not a bulk `--chmod=+x`.
- **Branched rather than committing to master**, since every recent change lands via PR and `master` is the default branch.

### Next

- **P3-T0 criterion 5 — the unaddressable-statement rate — BEFORE criterion 3.** A `writemodel_corpus.py` task that genuinely requires a new top-level statement (an `import`, a module constant). No existing corpus task does, so s137's `0/12` reports that the case never arose. It is schema-shaping: the answer decides whether the edit schema needs an insert-top-level op.
- **Then criterion 3 — which is a BUILD, not a probe.** `mcp-server/src/` has **zero** hits for `find_units`/`resolve_unit`/`apply_unit`; they exist only in `benchmarks/lib/`. Obtaining the last gate evidence requires prototyping P3-D1(B)'s emit+apply inside `loop.py` against a real file from T-122's blocked set (`parser.py`/`intake.py`, **not** `loop.py`).
- Then **D2 / D3-half-1 / D7**, all D1-independent; D3 half 1 is marked *ready to freeze*.
- **PR #90 needs review/merge.** Carried: **T-138** (new), T-137, T-131, T-132 (root QUICK 145 lines against its stated 30), T-135, T-125/126/127/128.
- LTG index is stale — the post-commit hook reported `11 changed, 10 added, 0 removed`.

### Gotchas

- **The fix committed the bug it was fixing.** The aggregator's first draft listed THREE suites because it enumerated **Makefiles** rather than **test runners**; `.claude/hooks/tests/` and `personas/` have runners and no Makefile. `.claude/index.md` caught it — the index earned its keep against my own search. A correlate for membership always has a complement nobody looks at.
- **The same error one step earlier, and the user caught that one.** I recommended *against* a root Makefile arguing "the repo has exactly one Makefile" — never run, and false: `overlays/Makefile` existed and already implemented the exact delegation pattern I called unnecessary. Two instances, one cause: asserting a set's size without enumerating it.
- **Both defects in my own instrument were found by the negative control, not by the green run.** The hooks runner reporting no total would have shown 26 passing tests as `0 passed`; the summary totalled only passes, printing `779 passed` next to a `FAIL` flag. Expect a newly-written check's first real failure to be in the check.
- **`overlays/Makefile`'s help was 100 tests stale** and nothing could have reported it — a hardcoded count has no checker. Found by running the suite instead of reading its header.
- **53 of 62 tracked `.sh` files are non-executable in git** (T-138), invisible here because `core.filemode=false` and drvfs forces 777. `ls -l` cannot see this; `git ls-files -s` is the only instrument.
- **The `cd`-persistence gotcha fired again** (s136 recorded it): a `cd docs/portfolio/hf-space` to run one check left the shell there, and the next heredoc write failed outright. It failed loudly this time — the dangerous version is a repo-root script silently resolving against the wrong directory.
