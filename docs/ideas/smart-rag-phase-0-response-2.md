Good questions. Each of these deserves a real look. Let me go deep on all three.

`★ Insight ─────────────────────────────────────`
- Two of these tradeoffs (embeddings, storage) look like "simplicity vs. capability" at first glance, but the honest framing is "simplicity now vs. *forced* complexity later." If we don't actually hit the wall that forces the complexity, it was pure tax.
- The third (extractor testing) is genuinely empirical — the only wrong move is *deciding without testing*. Thoroughness costs ~1–2 hours of compute and buys a load-bearing foundation.
- A theme that ties all three: **reversibility**. Embedding model and storage both have migration paths if we pick wrong; the extractor *prompt* is much stickier because it shapes the whole extracted graph. That asymmetry should bias effort allocation.
`─────────────────────────────────────────────────`

## #2 — Embedding model, thorough accounting

### What `bge-m3` brings over `nomic-embed-text`

| Feature | bge-m3 | nomic-embed-text | Actually matters for LTG? |
|---|---|---|---|
| Dense MTEB (English) | ~66 | ~62.4 | Marginally — 3-4 points in a <1000-node corpus ≈ 1-2 rank shifts in top-10 |
| Dense dimension | 1024 | 768 (Matryoshka-truncatable) | No — higher isn't automatically better at small scale |
| Model size | ~2.3 GB | ~274 MB | Yes — VRAM and load time |
| Context window | 8192 | 8192 | Tie |
| Multilingual (100+ langs) | Yes | English-focused | No — single-language corpus |
| Sparse (lexical) vectors | Built-in | Not offered | **Yes — meaningful for technical content** (ref keys, model names, flags) |
| Multi-vector (ColBERT-style) | Built-in | Not offered | Partially — our spans-within-topics already do chunk-level precision |
| Ollama availability | Varies by version (check) | Native, widely used | Yes — deployment simplicity |
| License | MIT | Apache 2.0 | Tie |

### What we *actually* lose picking `nomic-embed-text`

1. **~3–4 MTEB points on English dense retrieval.** In a corpus of hundreds of topics, this typically moves a handful of borderline items within top-10 but rarely flips the winner. For `relate(a,b)` which compares two known files, embedding quality matters less than extraction quality.

2. **Free sparse signal.** This is the most underrated loss. Technical prose is full of exact tokens — `qwen3:14b`, `ref:thinking-mode`, `OLLAMA_FLASH_ATTENTION=1`. Dense embeddings are famously bad at exact-token matching; sparse vectors (or BM25) recover it. bge-m3 gives you sparse alongside dense for one inference call. With nomic-embed-text you'd either (a) live without sparse or (b) bolt on a separate BM25 index (one extra library, bm25s is light).

3. **Built-in hybrid fusion recipes.** bge-m3 ships published weights and formulas for dense+sparse+multi-vector fusion. With nomic you roll your own. Not hard but non-zero work.

4. **Multi-vector late interaction.** Each long passage gets multiple per-token vectors and you compute `MaxSim` at query time. It's very good at "this passage is mostly irrelevant but one paragraph is gold." Our topic-span extraction architecture already solves most of this problem structurally — we chunk by topic boundary before embedding. The marginal win from ColBERT-style on top of already-segmented spans is small.

5. **Multilingual headroom.** Zero value today. Would matter if we ever indexed Portuguese docs or a bilingual codebase. We can always re-embed later.

### What we *gain* picking `nomic-embed-text`

1. **Single runtime, single API, single VRAM budget.** This is not aesthetic — it's the difference between one Ollama process you already understand and two backends (Ollama + sentence-transformers via Python) sharing 12GB VRAM. Mental accounting gets harder. Failure modes multiply.

2. **VRAM headroom for extractor co-residence.** qwen3:14b ≈ 9GB; nomic-embed-text ≈ <1GB; ~2GB headroom for OS/app. With bge-m3 loaded via HF (~3–4GB VRAM), you'd likely have to unload the extractor to embed and vice versa — serialized, slower, more complex. This is a real daily friction.

3. **Cold-start speed for batch indexing.** Phase 2 embeds every extracted topic in sequence. A small embedder spins up in a couple of seconds; bge-m3 takes noticeably longer to load the first time.

4. **Zero dep growth.** bge-m3 pulls `sentence-transformers`, `transformers`, `torch`, tokenizers, a parade of transitive packages. ~1.5GB of disk if you don't already have torch. Ollama-only avoids this whole layer.

5. **Upgrade path is free.** Ollama's embedding story is actively improving. When they add `bge-m3` (if they haven't already — **worth a quick `ollama list` / `ollama pull bge-m3` check**) or arctic-embed or whatever's next, it's a one-line switch.

6. **Shared cache.** Every future consumer that embeds a query hits the same loaded model. With a separate HF backend, we'd be running two inference systems forever.

### The alternatives you should know about

The binary "nomic vs. bge-m3" actually hides more interesting options, all available via Ollama:

| Model | Size | MTEB dense | Notes |
|---|---|---|---|
| `nomic-embed-text` | 274 MB | ~62.4 | Baseline, Matryoshka-truncatable |
| `mxbai-embed-large` | 670 MB | ~64.7 | Better than nomic, still small, Ollama-native |
| `snowflake-arctic-embed-l` | 335 MB | ~66.0 | Very competitive with bge-m3 dense, Ollama-native |
| `bge-large-en-v1.5` | 1.3 GB | ~64.2 | Ollama-native, slightly worse than arctic |
| `bge-m3` | 2.3 GB | ~66 | If available in your Ollama version, ideal — but only dense exposed through Ollama's API |

The honest middle path: **`snowflake-arctic-embed-l` or `mxbai-embed-large` via Ollama**. Gets you within a point of bge-m3 dense quality, keeps everything in one runtime, zero dep growth, and costs <1GB VRAM.

### Recommendation (revised, more honest)

1. **Default: `nomic-embed-text` via Ollama.** Cheapest to start, verifiable on your actual probe queries in Phase 2.
2. **If Phase 2 probe queries underperform:** swap to `snowflake-arctic-embed-l` or `mxbai-embed-large`, both Ollama-native, no runtime change.
3. **Only escalate to bge-m3 via sentence-transformers if:** (a) probe quality is still bad *and* (b) you determine the gap is specifically in sparse/lexical matching that hybrid would solve.
4. **Orthogonal option:** add a tiny BM25 index with `bm25s` (pure Python, fast) alongside dense. This recovers the sparse signal without touching embeddings. Cheap, reversible.

**Net: agreeing with Ollama-only loses you almost nothing measurable for MVP, but reduces your daily operational surface meaningfully.**

---

## #7 — Pure LanceDB, what are we losing?

### Concrete losses vs. SQLite+LanceDB split

| Capability | SQLite + LanceDB | Pure LanceDB | Real impact |
|---|---|---|---|
| Foreign key enforcement | Native `REFERENCES` | Not enforced | Silent bugs possible — mitigate with one-shot integrity scan at rebuild end |
| Multi-table transactions | Yes (BEGIN/COMMIT) | Per-table versioning only | Low — rebuild is offline and idempotent; "rerun it" is the recovery |
| Ad-hoc SQL from shell | `sqlite3 db.sqlite "SELECT ..."` | Requires Python (or DuckDB-on-Lance) | Small daily friction for debugging |
| M:N relationships | Join tables | Array columns only | Fine for coarse/fine community resolution; awkward for deeper taxonomies |
| CTE-style graph traversal | SQL recursive CTEs | Load edges into networkx, traverse there | Wash — networkx is where you'd go anyway |
| Schema migrations | Familiar (ALTER TABLE, etc.) | Lance supports add/drop columns, less familiar tooling | Small learning curve |
| Backup/diff of a single file | Trivial — one `.db` file | Lance is a directory tree with versioned fragments | Slightly less convenient, still tractable |
| Cross-process concurrent readers | WAL mode | Single-writer, multi-reader | Tie for our use case |
| Tooling ecosystem | Enormous (DB Browser, sqldiff, every language binding) | Growing (Arrow ecosystem, DuckDB integration) | SQLite wins on universality |

### Concrete gains going pure LanceDB

1. **One store, one ingest path, one query path.** Cannot overstate how much this simplifies the `store.py` module and the rebuild pipeline. Fewer files = fewer sync bugs = fewer 3am "wait, which one is authoritative" moments.

2. **Atomic filter-after-search.** A single Lance query does `table.search(embedding).where("file_path LIKE '%smart-rag%'").limit(10)`. In the split, that's two round trips and a manual join. Not just slower — more code to get right.

3. **Arrow/Parquet underneath.** Lance writes Parquet-compatible files. Any data-science tool (polars, DuckDB, pyarrow) reads them for free. SQLite's `.db` format requires its own drivers everywhere.

4. **Versioned time travel.** Lance tracks table versions automatically. You can query "what did the graph look like 3 rebuilds ago" with no extra machinery. SQLite would need explicit snapshotting.

5. **Schema evolution without pain.** Add a column to a Lance table — new rows have it, old don't get corrupted. Works like Parquet+Delta. SQLite ALTER TABLE is fine but less flexible on type changes.

6. **One mental model.** Claude Code sessions debugging this later don't need to remember "nodes live here, vectors live there." Everything is Lance-shaped.

### The honest risk I'd flag

The single real risk I'd flag is **item 3 in the loss column** — debuggability from a shell. When something looks wrong in the graph, the fastest debug loop is often "open the table, eyeball the rows." With SQLite that's `sqlite3 nodes.db`. With Lance it's `python -c "import lance; print(lance.dataset('nodes').to_table().to_pandas().head())"`. The Python path is fine in a long-lived session but friction in one-off shell pokes.

**Mitigation that makes this a non-issue:** write a tiny `retrieval/inspect.py` CLI — 30 lines, takes table name + optional filter, prints rows as a rich-formatted table. You get `./retrieval/inspect.py nodes --where "file_path LIKE '%smart-rag%'"` which is actually nicer than raw sqlite3. Cost: 30 minutes once.

### Pragmatic sidecars

Some things don't belong in any store anyway:
- **Run logs:** `retrieval/extraction_runs.jsonl` (append-only) — lives outside Lance.
- **Decisions:** `retrieval/DECISIONS.md` — flat markdown.
- **Configs:** `retrieval/configs/*.yaml` — per Phase 8 plan.

These don't benefit from transactions or SQL; they're documents. Keep them as plain files.

### Recommendation (hardened)

**Pure LanceDB for `nodes`, `edges`, `communities`.** JSON/JSONL/YAML sidecars for logs, decisions, configs. Add `retrieval/inspect.py` as the debug UX patch. Revisit only if Phase 4 surfaces a specific query we can't express — **and at that point, adding SQLite as a metadata overlay is a 2-hour project, not a rewrite.**

**Net: you're losing shell-level ergonomic debugging, which is patchable; everything else is wash or net gain.**

---

## #5 — More thorough extractor testing protocol

Since you want more rigor, here's a hardened Phase 1 protocol. The plan currently says "5 files, 2-3 models, 70% agreement threshold." That's thin. Here's what I'd actually do.

### Models to test (4–5 configurations)

| Config | Why include |
|---|---|
| `gemma3:12b` | Speed-tier incumbent, IMPROVED verdict in session 50 |
| `qwen3:14b` | Your current quality workhorse |
| `qwen2.5-coder:14b` | Code-focused base — is code-trained extraction better or worse on prose-heavy research docs? |
| `qwen3:8b` (think:false) | Budget tier — can it surprise? If yes, massive cost/iteration savings |
| `qwen3:30b-a3b` *(optional)* | See if "larger" buys anything. Expect slow per session 34–35 findings; might skip if token budget tight |

### Corpus — stress-test each failure mode

Not just "5 files at random." Pick files that exercise different extraction challenges:

| File type | Example | What it stresses |
|---|---|---|
| Long, dense research prose | `docs/research/smart-rag-llm-wiki.md` | Long-range topic coherence, 5+ topic detection |
| Structured memory file | A `.memories/QUICK.md` | Tight short content, risk of over-segmentation |
| Mixed markup + code | `CLAUDE.md` (this repo's) | Code blocks shouldn't become their own topic; headings shouldn't leak into topic names |
| Multi-topic long-form | `.claude/plan-v2.md` or `session-context.md` | Non-contiguous span detection (Layer 5 topics scattered through the doc) |
| Short, tight | A persona `Modelfile` | Does the model gracefully emit <3 topics or hallucinate filler? |
| Heavy cross-reference | `docs/research/smart-rag-obsidian-mind.md` | Does extraction preserve the refs structure or flatten it? |
| Extremely long | Concatenate 2 research docs if nothing single qualifies | Context budget pressure, truncation handling |

That's **7 files × 4–5 models = 28–35 extraction runs**. At typical extractor throughput, ~1.5–2.5 hours of compute. With `warm_model` to avoid cold starts, tight.

### Dimensions to score (rubric-driven, not vibes)

For each (file, model) run, record:

1. **Structural compliance** — JSON valid? Fields present? PASS/FAIL. A fail is automatic disqualification for that run.
2. **Topic count** — in [3, 10]? Flag out-of-range.
3. **Span coverage** — `sum(span lengths) / file length`. Target ~0.6–0.9. Below 0.3 → missing most content; above 0.95 → topics are too broad.
4. **Non-contiguity rate** — fraction of topics with >1 span. Plan requires ≥1 non-contiguous topic per file; I'd prefer "at least 30% of topics are non-contiguous" on multi-topic files.
5. **Topic name quality** — human score 0–3 (nonsense / vague / adequate / crisp). Worth 35% of weighted quality.
6. **Description quality** — human score 0–3. Worth 35% of weighted quality.
7. **Boundary sanity** — do span boundaries fall on paragraph breaks, heading starts, sentence terminals? 0–3. Worth 20%.
8. **Mutual coverage** — do topics *collectively* cover the file without huge gaps, or do they cluster on the first half? Subjective 0–3. Worth 10%.
9. **Determinism / stability** — run the same (file, model) **twice** with temp 0.1, measure Jaccard similarity of topic names. Target ≥0.8. Do this on a 3-file subset to keep cost down.
10. **Latency** — tokens/sec and wall time.
11. **Token economy** — output tokens / input tokens. Lower is better (more compression).

### Weighted aggregate

Per-model score = `0.35*name + 0.35*desc + 0.20*boundary + 0.10*coverage + stability_bonus − speed_penalty`

Stability bonus: +0.5 if Jaccard ≥0.85, +0.25 if ≥0.80, 0 otherwise.
Speed penalty: none unless tok/s < 15 (a hard floor).

### One variant I want to include: **single-stage vs. two-stage extraction**

Topic extraction often fails because the model tries to do *boundary detection* and *naming* in one pass, splitting attention. A known-better pattern:
- **Stage A:** "List 3–10 distinct concepts in this file with a one-line rationale."
- **Stage B:** "For each concept, provide the span ranges that support it."

Two calls per file, roughly doubles latency, often meaningfully improves quality. Worth testing as a variant of the top 2 models from the single-stage sweep. Adds ~2 × 7 × 2 = 28 more runs if you fork to a second phase.

**Total with variants: ~56–63 runs.** Still finite, ~3–4 hours wall time with warm models.

### Iteration budget and exit criteria

- **Round 1:** all models, all files, single-stage. Score everything.
- **If no model scores ≥ 2.0 weighted average:** iterate the *prompt* (not the model). Most common improvements: explicit "do not emit code blocks as topics," explicit "topics can be non-contiguous," explicit example output.
- **Max 3 prompt iterations** before escalating to decomposed (two-stage) approach.
- **Round 2:** top 2 models × two-stage variant.
- **Pick winner:** highest weighted score, with a tiebreaker toward higher stability.
- **Exit threshold:** winner must have average quality score (name+desc+boundary weighted) ≥ 2.2 across all 7 test files. Below that, Phase 2 is premature.

### Artifacts produced

- `retrieval/phase1-prompt-v1.txt`, `-v2.txt`, etc. — every prompt version you tried
- `retrieval/phase1-raw/{model}/{file}.json` — every raw extraction
- `retrieval/phase1-scores.csv` — the rubric scores
- `retrieval/phase1-results.md` — narrative summary with:
  - Winner + runner-up
  - Evidence table
  - Failure modes observed (with quotes)
  - Estimated cost to index the planned corpus with the winner
  - Recommendation for Phase 2
- `retrieval/DECISIONS.md` — amended with the chosen extractor config

### What this protocol actually gets you

- Confidence that Phase 2 isn't built on a flaky foundation
- Quantitative comparison instead of "felt better"
- A rubric you can reuse in Phase 4 (extraction quality re-evaluation as corpus grows)
- Clear iteration pattern: prompt → not model, until you've exhausted prompt space

---

## Summary — where we land

| # | Decision | Recommendation |
|---|---|---|
| 2 | Embedding | `nomic-embed-text` via Ollama as default; keep `mxbai-embed-large` / `arctic-embed-l` in back pocket; bge-m3 only if Phase 2 probes demand hybrid and the Ollama build lacks it. Optional tiny BM25 index if exact-token recall is needed. |
| 5 | Extractor testing | 4–5 models × 7 stress-test files × single-stage sweep → top 2 re-run with two-stage variant. 11-dimension rubric. Exit threshold on weighted quality. |
| 7 | Storage | Pure LanceDB for nodes/edges/communities + JSON/YAML sidecars for run logs/decisions/configs. Build `retrieval/inspect.py` (30-min task) to patch shell debuggability. |

Want me to commit these as the Phase 0 decisions in a `retrieval/DECISIONS.md` scaffold — or keep discussing? There are still #1, #3, #4, #6, #8 on the "you said agree" list that I could formalize at the same time, but I won't write anything until you say go.