# Session Log

**Current Layer:** Layer 5+ — oficina P3 (context & prompt assembly); P3-D1 open, criterion 5 measured, criterion 3 outstanding
**Current Session:** 2026-08-19 — Session 139: T-137 closed on a FALSE premise; P3-T0 criterion 5 MEASURED in both halves — (B) needs three operations, not one; PRs #91 + #92 open

---
## 2026-08-19 - Session 139: T-137 closed on a FALSE premise; P3-T0 criterion 5 MEASURED in both halves — (B) needs three operations, not one; PRs #91 + #92 open

### Context

Started from a merged PR #90 and a clean master, choosing between the declared next step (P3-T0 criterion 5) and three carried infra tasks. T-137 was picked first on the argument that its `eval_duration` field would make criterion 5's GPU run self-measuring. That premise turned out to be false, which redirected the session's first half.

### What Was Done

- **T-137 closed, and its filed premise falsified.** `eval_duration_ms` is present in **738/738** `calls.jsonl` records, added session 32 (`8666c0ea`) — `mcp-server/.memories/KNOWLEDGE.md` had listed it all along. The real gap was a **second Ollama client**: `benchmarks/lib/` imports `ollama_chat` from `personas/lib/ollama_client.py`, which dropped every timing but `total_duration` and logs nothing, so s137's 24 generations never reached the log. Enumerating by the defining property found **seven** call sites, not two.
- Shipped `eval_duration_ms`/`prompt_eval_duration_ms`/`load_duration_ms` on `ollama_chat`; `call_model` returns `(content, stats)` and `run_cell` spreads it, error rows keeping every key at 0 so `summarize()`'s row-sum cannot `KeyError`.
- **Criterion 5 split into 5a (behaviour) and 5b (rate)** — one vehicle had been asked two questions, and a designed corpus makes the rate 100% by construction.
- **5a built and measured:** import-requiring corpus, `--corpus import`, three-way outcome classification, warm-up before the sweep. 24 generations over two runs.
- **5b measured:** a durable census instrument (`run-unaddressable-census.sh`, 13 tests, `100755`) over **486 real edits**.
- Docs propagated to the plan, `evidence.md`, `oficina-p2-edit-mode.md`, survey **§ 0b**, the census finding, `.claude/index.md`, the reading guide and four `.memories/` files.
- PRs **#91** (T-137) and **#92** (criteria 5a+5b, stacked on #91) opened. Suite **894 → 954**.

### Decisions Made

- **(B) needs THREE operations, not one** — address an existing unit, insert a top-level statement, create a new unit. Build order is resolver-extension first, because the largest class is also the cheapest.
- **Earlier lean RETRACTED on measurement:** "harness-side detection + whole-file fallback because it is smaller" fails, since falling back on 23–48% of edits means falling back on exactly the files whole-file cannot reach.
- **`active-decisions` deliberately NOT updated.** Reproducing its 17.8 KB interior verbatim for one added principle risked silent drift that the pipeline's verifier cannot catch. The 5a principle is recorded in the plan, `evidence.md`, § 0b and the reading guide, and belongs on the resume surface next session.
- **No new tasks filed** for the resolver extension or the insert operations — user's call; the plan's 5b table is the register, and duplicating it is how two copies of one decision drift.

### Next

- **P3-D1's remedy set:** extend the resolver to index assignments (largest class, cheapest fix), then `insert_top_level`, then `insert_unit`. Pair whatever is built with harness-side detection — the model never signals that it needs the fallback.
- **Then criterion 3 — a BUILD, not a probe.** Prototype (B)'s emit+apply inside `loop.py` against `parser.py`/`intake.py`, not `loop.py`.
- Review/merge **#91** and **#92** (#92 is stacked on #91).
- Put the 5a principle into `active-decisions`. Converge the stale **LTG index**.

### Gotchas

- **The task's premise was the defect.** Implementing T-137 as filed would have shipped, verified green against `calls.jsonl`, and changed nothing about the number it existed to obtain. An open task's "still broken" is as unverified as a closed one's "done".
- **A delegated edit silently corrupted a frozen symbol** — `clamp(value, lo, hi)` → `hhi` — and the **entire suite stayed green**, because the target test calls positionally. The ground-truth tests check the corpus's *behaviour*; the model reads its *text*.
- **Every real defect this session came from a negative control or a mutation, never a green run.** Reverting T-137 turned 5 of 6 new tests red — and the 6th passed both ways, because it asserted an unreachable line.
- **`ast.parse` accepts a module-level `return`** (the `SyntaxError` is `compile()`'s), so `body_parses: True` was reported for a body that cannot be imported. The real signal, `body_units == 0`, had been recorded for months and reported never.
- **A measured zero can look like a result.** The census first reported `docstring 0.0%` at every cut because `ast.unparse` renders a docstring single-quoted; the headline was unaffected, which is precisely why it sat there unnoticed.
- **The `cd`-persistence gotcha fired a third time** — an inspection `cd` into `benchmarks/lib` made the next heredoc write to a path that did not exist. It failed loudly again.
