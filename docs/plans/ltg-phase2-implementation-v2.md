# LTG Phase 2 Implementation Plan — Embedding + Storage (v2, revised)

*Written 2026-05-20 (session 61, dynamic revision). Supersedes `docs/plans/ltg-phase2-implementation.md` (v1).*

**Status:** Ready to execute. Decisions locked. This revision incorporates the broader LTG conceptual context (`ref:concept-latent-topic-graph`), the smart-rag research synthesis (`docs/ideas/smart-rag.md` → `smart-rag4.md`), and forward-compatibility hooks for Phases 3–9 that v1 underspecified.

---

<!-- ref:ltg-phase2-plan-v2 -->
## What Changed From v1

This v2 is a *superset* of v1 — every v1 decision still holds. The revisions are:

| Area | v1 | v2 | Why |
|------|----|----|-----|
| **Schema** | 12 fields | 16 fields (4 forward-compat additions, all nullable) | Phase 3–9 need `node_kind`, `scope_tags`, `segment_*`, `embedding_timestamp`; adding now costs nothing, refactoring later is a chore |
| **Embed mode** | Description-only hardcoded | `--embed-mode {description, description_plus_spans}` flag, defaulting to description | Description-only is decided, but the A/B is *expected* and the code should make switching one CLI flag, not a refactor |
| **Batch embedding** | Lower-priority suggestion | Baseline (BATCH_SIZE=32, configurable) | bge-m3 batch is straightforward and the 4–10× speedup matters when Phase 2.5 expands the corpus to ~50–100 files |
| **Probe queries** | 4 recall queries | 4 recall + 2 negative + 1 relate-preview | Phase 5's `relate(a,b)` depends on Phase 2's index quality; smoke-testing it lightly here surfaces issues earlier |
| **Probe persistence** | Print-to-stdout | Write to `retrieval/probes/{timestamp}.md` | Acceptance evidence should be durable; future iteration A/Bs need a baseline |
| **Pre-flight check** | Implicit | `retrieval/preflight.sh` — bge-m3 installed, ollama up, Phase 1 JSONL valid, disk space | Fail-fast is cheaper than failing 80% through an embed run |
| **Logging** | Implicit | Structured log to `retrieval/runs/embed-{timestamp}.jsonl` and `retrieval/runs/store-{timestamp}.jsonl` | Phase 1 set the precedent; consistency aids debugging |
| **Pre-compile framing** | Implicit | Explicit (see Architectural Context) | The index *is* the pre-compiled wiki from smart-rag3.md; framing this connects Phase 2 to the chatbot/Claude Code consumer story |
| **Phase 2.5 sketch** | One-line deferred item | Brief design sketch | Reduces future-session ramp-up; clarifies what schema fields are *for* |
| **Idempotency safety** | overwrite-only (good) | overwrite-only + automatic backup of prior `retrieval/index/` to `retrieval/index.bak/` | Catches "oops I rebuilt before checking the old probe results" |
| **Connection to Phase 3** | Mentioned | Explicit: schema reserves `node_kind` and anchor-merge ID convention | Phase 3 can read this plan and know exactly what slots to fill |

If you only have time to absorb one change: **the schema gains four nullable fields so Phase 3–9 don't require a backfill migration.**
<!-- /ref:ltg-phase2-plan-v2 -->

---

## Architectural Context (read this once before touching code)

Phase 2 is not "build a vector index." Phase 2 is **build the *first concrete artifact* of the LTG substrate** — the layer that turns LLM-extracted topic structure into a queryable, derived view of the corpus.

Reframe through three lenses:

**Through the LTG concept paper (`ref:concept-latent-topic-graph`):**
The substrate has four entity kinds — topic nodes, anchor nodes, containers (files), and edges. Phase 2 implements the **embedded topic node** — one of the four primitives. Phase 3 adds anchor nodes. Phase 4 builds the edges. Phase 2 is the storage commitment that all later phases live on top of, so schema choices here have downstream cost if wrong.

**Through the smart-rag3 pre-compile framing:**
The Karpathy-style "pre-compile wiki, query the wiki" architecture says the LLM-authored intermediate artifact is what makes retrieval smart. Phase 1 produced that artifact (LLM-extracted topics + spans). Phase 2 *indexes* the pre-compiled artifact. Together, Phase 1+2 = "build the wiki." Phase 6 onward = "query the wiki from any consumer." This is the deploy-ready shape: for the HF-Space chatbot the wiki/index is a static asset, for Claude Code it's a live MCP endpoint, but the *substrate* is the same files.

**Through the smart-rag4 derived-structure principle:**
Embeddings are stable; rankings, salience, and communities are derived and rebalance as content arrives. Phase 2 stores the stable layer (embeddings). Phase 4 will compute the derived layer (communities). The schema must keep these honest: every embedded row records *which extractor produced it*, *which embedder embedded it*, and *when*, so when the derived layer is recomputed, you can audit what changed and why.

**Implication for design:** every schema field, every CLI flag, every output is justified by either Phase 1's outputs feeding in, or a later phase reading out. Anything that doesn't serve one of those two is scope creep.

---

## Goal and Scope (unchanged from v1)

Build the embedding + storage layer for the Latent Topic Graph:
- **`retrieval/embed.py`** — reads Phase 1 extraction JSONL, filters to winning models, embeds topic descriptions (or description+spans, switchable) via bge-m3, writes embedding JSONL
- **`retrieval/store.py`** — reads embedding JSONL, creates and populates a LanceDB table at `retrieval/index/`
- **`retrieval/inspect.py`** — opens the index, runs top-K nearest-neighbour queries (and a `--relate` mode for paired-file overlap), prints + persists results
- **`retrieval/preflight.sh`** — fail-fast environment check
- **Bash wrappers** for each script (`run-embed.sh`, `run-store.sh`, `run-inspect.sh`, `run-preflight.sh`)

**Corpus scope:** 8-file Phase 1 validation pass first. Phase 2.5 (corpus expansion) is deferred but sketched at the end.

---

## Required Reading (read in order before implementing)

| File | Why | Read priority |
|------|-----|---------------|
| `retrieval/.memories/QUICK.md` | Current status, sequential constraint | **Must** |
| `retrieval/.memories/KNOWLEDGE.md` (`ref:ltg-vram-probe`, `ref:ltg-phase1-summary`) | VRAM constraint mechanism; which extractor for which file type | **Must** |
| `retrieval/DECISIONS.md` (`ref:ltg-embedding`, `ref:ltg-vector-store`, `ref:ltg-storage-layout`) | Frozen Phase 0 decisions | **Must** |
| `retrieval/extract_topics.py` | Source of truth for Phase 1 JSONL format and the standalone-script + bash-wrapper convention | **Must** |
| `retrieval/runs/20260416-181839.jsonl` | The actual 32-row input (8 files × 4 models) | **Must** |
| `docs/research/latent-topic-graph.md` (`ref:concept-latent-topic-graph`) | Why files are containers, why topics are first-class, what edges mean | **Should** (skip only if read in a prior session) |
| `docs/ideas/smart-rag3.md` | The pre-compile-wiki framing this phase implements | **Should** |
| `docs/ideas/smart-rag4.md` | The "derived structure rebalances" principle the schema is built to track | **Should** |
| `docs/plans/2026-04-13-latent-topic-graph-implementation.md` (`ref:ltg-plan-phase-2`, `ref:ltg-plan-phase-3`, `ref:ltg-plan-phase-5`) | High-level plan; Phase 3 and Phase 5 contexts that justify the forward-compat fields | **Should** |
| `docs/plans/ltg-phase2-implementation.md` (v1) | Predecessor — the advisor review in v1 is preserved by reference; don't re-litigate | **Skim** |

---

## Decisions In Force (do not re-litigate)

| Decision | Value | Source |
|----------|-------|--------|
| Embedding model | `bge-m3` via Ollama (1024-dim dense) | `ref:ltg-embedding` |
| Embedding text (default) | Description-only | Session 61 |
| Embedding text (alt, switchable) | Description + concatenated span text | New in v2 — flag added now, A/B run when triggered |
| Sequential constraint | embed.py must NOT run alongside qwen3:14b inference | `ref:ltg-vram-probe` |
| Vector store | LanceDB at `retrieval/index/` | `ref:ltg-vector-store` |
| LanceDB pin | `lancedb>=0.20,<0.30` | v1 advisor #4 |
| Input | Phase 1 JSONL filtered to winning models per file role | Session 61 |
| File → extractor routing | `.py/.go/.ts/.java → qwen2.5-coder:14b`; else `qwen3:14b` | `ref:ltg-extractor` |
| Scripts | Separate files, bash wrappers, no `pyproject.toml` | Project convention |
| Store mode | Overwrite-only for MVP; append/dedupe deferred to Phase 2.5 | v1 advisor #1 |
| ID scheme | `f"{file_path}:{topic_name}"` | v1 |
| Vector field name | `"vector"` (LanceDB convention) | v1 advisor + LanceDB docs |
| Batch embed | Yes, `BATCH_SIZE=32`, configurable | v2 (promoted from "lower priority") |

---

## Input: Phase 1 JSONL Format (unchanged)

File: `retrieval/runs/20260416-181839.jsonl` (32 rows = 8 files × 4 models).

Each row:
```json
{
  "run_id": "uuid",
  "timestamp": "2026-04-16T21:19:16Z",
  "model": "qwen3:14b",
  "file": "docs/research/smart-rag-repowise.md",
  "file_role": "long_research_doc",
  "line_count": 54,
  "char_count": 4907,
  "prompt_tokens": 1761,
  "output_tokens": 591,
  "latency_s": 40.05,
  "status": "ok",
  "raw_response": "{\"topics\": [{\"name\": \"...\", \"description\": \"...\", \"spans\": [[10,16],[26,32]]}]}"
}
```

`raw_response` is a JSON string; parse to extract `topics`. Skip rows where `status != "ok"`.

**File-to-extractor routing** (filter logic in embed.py):
```
*.py, *.go, *.ts, *.java   → qwen2.5-coder:14b
everything else (incl. .md, .yaml, .toml) → qwen3:14b
```

Of the 8 Phase 1 files, `personas/build-persona.py` is the only code file. The other 7 are prose → qwen3:14b.

---

## Revised LanceDB Schema

```python
import pyarrow as pa

SCHEMA = pa.schema([
    # ---- Identity (required, immutable) ----
    pa.field("id",                   pa.string()),         # "{file_path}:{topic_name}" (deterministic)
    pa.field("file_path",            pa.string()),         # container reference (files are containers, not nodes)
    pa.field("topic_name",           pa.string()),         # snake_case slug from extractor
    pa.field("description",          pa.string()),         # extractor's natural-language description (text that was embedded if embed_mode=description)
    pa.field("spans",                pa.string()),         # JSON-encoded list of [start_line, end_line] pairs

    # ---- Embedding (required) ----
    pa.field("vector",               pa.list_(pa.float32(), 1024)),
    pa.field("embed_model",          pa.string()),         # "bge-m3"
    pa.field("embed_dim",            pa.int32()),          # 1024 (belt-and-suspenders; LanceDB also enforces)
    pa.field("embed_mode",           pa.string()),         # "description" | "description_plus_spans"
    pa.field("embedding_timestamp",  pa.string()),         # ISO timestamp when this embedding was computed

    # ---- Provenance (required) ----
    pa.field("extractor_model",      pa.string()),         # "qwen3:14b" | "qwen2.5-coder:14b" | ...
    pa.field("extraction_run_id",    pa.string()),         # run_id from Phase 1 JSONL
    pa.field("extraction_timestamp", pa.string()),         # ISO timestamp from Phase 1 JSONL
    pa.field("file_role",            pa.string()),         # file_role from Phase 1 JSONL ("long_research_doc", etc.)

    # ---- Forward-compatibility (nullable, Phase 2 writes defaults) ----
    pa.field("node_kind",            pa.string()),         # "extracted" (Phase 2) | "anchor" (Phase 3) | "merged" (Phase 3)
    pa.field("scope_tags",           pa.string()),         # JSON-encoded list, default "[]" — populated by Phase 8 configs
    pa.field("segment_id",           pa.string()),         # null for Phase 2; populated if Phase 2.5 chunks long files
    pa.field("segment_range",        pa.string()),         # null for Phase 2; JSON "[start_line, end_line]" if segmented
])
```

### Why these fields, justified by downstream phases

**Phase 2 writers:** `id`, `file_path`, `topic_name`, `description`, `spans`, `vector`, `embed_model`, `embed_dim`, `embed_mode`, `embedding_timestamp`, `extractor_model`, `extraction_run_id`, `extraction_timestamp`, `file_role`, `node_kind="extracted"`, `scope_tags="[]"`, `segment_id=None`, `segment_range=None`.

**Phase 3 (anchor integration) will need:**
- `node_kind` set to `"anchor"` for rows derived from `<!-- ref:KEY -->` blocks, and to `"merged"` for extracted topics that aliased to an anchor above the similarity threshold (suggest 0.85 per `ref:ltg-plan-phase-3`).
- A new column (added by Phase 3, optional now) `anchor_ref_key` to record the merged anchor's key. Adding columns later is supported by LanceDB; we don't include it in Phase 2 because no Phase 2 row will populate it.

**Phase 4 (graph + community detection) will need:**
- Community assignments at multiple resolutions. These belong in a *separate* table (`communities` or `node_metadata`) keyed by `id`, not in the topic table itself, because they recompute frequently. Phase 4 will add that table. Phase 2 does nothing here.

**Phase 6 (MCP) will need:**
- `node_kind` to format retrieval results differently for anchor-hit vs extracted-hit responses.
- `scope_tags` to filter by `scope` argument.

**Phase 8 (per-repo config) will need:**
- `scope_tags` populated from the corpus config at index-time. Phase 2 writes `"[]"` because no scope tags are in force yet.

**Phase 2.5 (corpus expansion) will need:**
- `segment_id` + `segment_range` for files long enough to require chunking before extraction. Phase 1 results (the 8-file corpus) had no chunked files, so `null` is correct. Phase 2.5 will repopulate.

### A non-obvious schema decision

`spans` and `scope_tags` are stored as **JSON-encoded strings**, not as PyArrow list-of-struct types. Reason: LanceDB's ANN index builder and filter pushdown work best on flat scalar/list-of-primitive columns. Nested struct fields work but add filter complexity (and the value of strict typing is low — these fields are read by Python code that already parses JSON elsewhere in the pipeline). If a future phase needs structured queries on spans (e.g., "give me all topics that touch line 50 of file X"), introduce a sidecar table; don't restructure this column.

---

## Forward-Compatibility Notes

Phase 2 commits to a schema. The fields above are designed so that **no Phase 3–9 work requires a destructive migration**. Specifically:

- **Adding columns** is supported by LanceDB without rewriting rows. Phase 3 can add `anchor_ref_key`; Phase 4 can add `community_coarse` / `community_fine`. Phase 2 just doesn't write them.
- **Backfilling values** for a previously-`None` field is one query. e.g., when Phase 8 ships, an index-config tool will write `scope_tags` for every row in the index.
- **Changing embed model** requires a full rebuild (different vector dim or different semantic space). The schema's `embed_model` + `embed_dim` + `embedding_timestamp` make it possible to audit: every row identifies which embedder produced it, so a partial rebuild is detectable.
- **Switching to description+spans embedding** requires a full re-embed but no schema change. `embed_mode` already records the choice.

### What *would* require a migration (avoid these)

- Renaming `vector` → anything else (LanceDB indexes are named).
- Changing vector dim (would require a new table).
- Making any "required" field nullable retroactively (forward-only).

---

## Script 1: `retrieval/embed.py`

**Purpose:** Filter Phase 1 JSONL to winning extractor per file → embed (batched) → write embedding JSONL.

### CLI

```bash
python3 retrieval/embed.py \
  --input retrieval/runs/20260416-181839.jsonl \
  --output retrieval/embeddings.jsonl \
  [--embed-model bge-m3] \
  [--embed-mode description] \
  [--batch-size 32] \
  [--ollama-url http://localhost:11434] \
  [--log-dir retrieval/runs] \
  [--max-failures 5]
```

### Pseudocode

```
1. Pre-flight: ping {ollama_url}/api/tags, confirm embed_model present.
   If absent, print one-line install hint and exit 2.

2. Read --input lines into memory. Validate JSONL parses.

3. Group rows by file. For each file:
   a. Determine winning extractor by file extension (routing table above).
   b. Find the row matching {file, model=winning, status="ok"}. If none, log warning, skip file.
   c. Parse raw_response → topics list.
   d. Validate each topic has {name, description, spans}; coerce spans to JSON string.
   e. Build "text to embed" per topic:
      - embed_mode=description: text = topic["description"]
      - embed_mode=description_plus_spans: text = topic["description"] + "\n\n" + concat(spans_text from file)
        (spans_text requires re-reading the source file at the indicated line ranges)
   f. Normalize topic_name → slugify_snake(topic_name); if collision within file, append "-2", "-3", ...

4. Batch embed all (file, topic, text) triples in chunks of BATCH_SIZE via POST /api/embed with input=list[str].
   - For each batch, on error, retry once after 2s; on second failure, log + count toward max_failures, skip those topics.
   - If max_failures exceeded, abort with non-zero exit.

5. For each successful embedding, write one output JSONL row per topic (see schema below).

6. Write run log to {log_dir}/embed-{timestamp}.jsonl with:
   - one row per file processed (file, topics_emitted, topics_failed, latency_s)
   - one final row with totals

7. Print summary to stdout: N files processed, M topics emitted, K failed, total latency, output path.
```

### Embedding API call (batched)

```python
import httpx

def embed_batch(texts: list[str], model: str, url: str) -> list[list[float]]:
    response = httpx.post(
        f"{url}/api/embed",
        json={"model": model, "input": texts},
        timeout=120.0,
    )
    response.raise_for_status()
    return response.json()["embeddings"]  # list[list[float]], len matches texts
```

### Output row (JSONL, written to `--output`)

```json
{
  "id": "docs/research/smart-rag-repowise.md:git_co_change_analysis",
  "file_path": "docs/research/smart-rag-repowise.md",
  "topic_name": "git_co_change_analysis",
  "description": "Focuses on analyzing co-change pairs in Git commits...",
  "spans": "[[12,14],[26,32],[44,45],[52,52]]",
  "vector": [0.021, -0.043, ...],
  "embed_model": "bge-m3",
  "embed_dim": 1024,
  "embed_mode": "description",
  "embedding_timestamp": "2026-05-20T14:32:17.482910+00:00",
  "extractor_model": "qwen3:14b",
  "extraction_run_id": "8723950f-a0a8-45b4-949d-3af6e96021b0",
  "extraction_timestamp": "2026-04-16T21:19:16.892426+00:00",
  "file_role": "long_research_doc",
  "node_kind": "extracted",
  "scope_tags": "[]",
  "segment_id": null,
  "segment_range": null
}
```

### Edge cases and defenses

| Case | Behavior |
|------|----------|
| Topic with empty/whitespace description | Skip, log warning. (Defensive — extractor should not emit these, but Phase 1 stability is not 100%.) |
| Duplicate topic_name within a single file | Append `-2`, `-3` suffix to the slug; record original in description if needed. |
| File has 0 valid topics | Log warning; skip file (do not write empty rows). |
| Phase 1 row has `status != "ok"` | Skip silently (already not a winning row). |
| File missing from Phase 1 JSONL entirely | Log warning; skip. |
| `--embed-mode description_plus_spans` and span text can't be read (file moved/deleted) | Fall back to description-only for that topic; tag in log. |
| `httpx` connection refused | Print "Is Ollama running? Try `systemctl --user start ollama` or `ollama serve`" and exit 3. |
| Ollama returns 404 for the model | Print "Model not pulled. Run `ollama pull bge-m3`" and exit 4. |
| Vector length != `embed_dim` | Print error, abort. (Catches accidental model-name typos that resolve to a different dim.) |

### Sequential constraint (comment, not enforced)

Add a header comment to `embed.py`:

```python
# Sequential constraint: do not run alongside qwen3:14b or qwen2.5-coder:14b inference.
# bge-m3 (~700MB VRAM) + qwen3:14b (~9GB VRAM) co-fit, but a concurrent extraction +
# embedding pass on the 12GB GPU has been observed to thrash. See `ref:ltg-vram-probe`.
# In Phase 2's pipeline, embed.py runs after extraction is complete, so this is policy
# (don't manually launch extraction in another shell while embed.py runs), not a lock.
```

### Dependencies

```
pip install httpx
```

(Already required by `extract_topics.py` — check the existing venv before installing.)

---

## Script 2: `retrieval/store.py`

**Purpose:** Read embedding JSONL → create/overwrite LanceDB table at `retrieval/index/`.

### CLI

```bash
python3 retrieval/store.py \
  --input retrieval/embeddings.jsonl \
  --index retrieval/index \
  [--table topics] \
  [--backup-dir retrieval/index.bak] \
  [--no-backup] \
  [--log-dir retrieval/runs]
```

### Pseudocode

```
1. Validate --input exists and is non-empty.

2. If --index directory exists and --no-backup is not set:
   a. Move {--index} → {--backup-dir} (replacing any prior backup).
   b. Print "Prior index backed up to {--backup-dir}".

3. Load JSONL → list[dict]. Convert "vector" list[float] → pa.array(float32, 1024).
   Convert "segment_id"/"segment_range" None → null in the Arrow column.

4. Connect to LanceDB at --index.

5. Create table with mode="overwrite", schema=SCHEMA, data=rows.

6. Validate: SELECT COUNT(*) == len(rows); SELECT vector dim of one row == 1024.

7. Write run log to {log_dir}/store-{timestamp}.jsonl:
   - one row per file (file, n_topics, n_extracted_kind, n_anchor_kind, n_merged_kind)
   - one final row with totals + table size + index path

8. Print summary: rows written, table size on disk, index path.
```

### Why always overwrite (no append)

Per v1's advisor #1: for the 8-file MVP, every re-run is a full rebuild. Append-with-dedupe is a real design problem (LanceDB does not enforce ID uniqueness — append would silently create dupes), and the *right* time to solve it is Phase 2.5 when incremental indexing actually matters. For now, the overwrite + auto-backup pattern lets you compare a new index against the prior one (e.g., for the description vs description+spans A/B) without losing the previous build.

### Dependencies

```
pip install 'lancedb>=0.20,<0.30' pyarrow
```

---

## Script 3: `retrieval/inspect.py`

**Purpose:** Run probe queries against the index. Primary acceptance-test runner. Also previews Phase 5's `relate(a,b)` with a lightweight `--relate` mode.

### CLI

```bash
# Single query
python3 retrieval/inspect.py \
  --query "what's special about Repowise's git co-change analysis" \
  --k 5 \
  [--index retrieval/index] \
  [--table topics] \
  [--ollama-url http://localhost:11434] \
  [--embed-model bge-m3] \
  [--output-md retrieval/probes/{timestamp}.md]

# List all rows (no query)
python3 retrieval/inspect.py --list [--index retrieval/index]

# Stats (counts, embed model breakdown)
python3 retrieval/inspect.py --stats [--index retrieval/index]

# Pairwise relate preview (Phase 5 stub)
python3 retrieval/inspect.py \
  --relate \
  --file-a docs/research/smart-rag-repowise.md \
  --file-b docs/research/smart-rag-claude-mem.md \
  [--top-pairs 10]

# Batch probe (runs all acceptance queries, persists results)
python3 retrieval/inspect.py --acceptance [--output-md retrieval/probes/{timestamp}.md]
```

### Query-mode logic

```
1. Embed the query string via bge-m3 (same API call as embed.py).
2. table.search(query_vector).limit(k).to_list()
3. For each result, print:
   #rank  score  file_path  [file_role]  [node_kind]
       topic_name
       description[:120]...
       spans
4. If --output-md provided: append a markdown block with query + results to that file.
```

### Relate-mode logic (Phase 5 preview, not the full implementation)

```
1. SELECT all rows WHERE file_path = file_a OR file_path = file_b.
2. For each pair (topic_a, topic_b): cosine = dot(va, vb) (vectors are L2-normalized post-extraction; bge-m3 outputs unit-normed when used via /api/embed... verify).
3. Print top-N pairs by cosine, with each side's file/topic/description preview.
4. Print divergences: topics in A whose best match in B is < 0.5, and vice versa.
5. Print summary: mean cosine of top-N pairs as a crude "overall_similarity" estimate.
6. NOTE: this is a preview, not the Phase 5 deliverable. Phase 5 adds the natural-language synthesis step.
```

### Stats-mode output

```
Index: retrieval/index
Table: topics
Rows: 47
Files: 8 (5 research docs, 2 memory files, 1 python)
embed_model breakdown: bge-m3 (47)
embed_mode breakdown: description (47)
extractor_model breakdown: qwen3:14b (40), qwen2.5-coder:14b (7)
node_kind breakdown: extracted (47)
```

This is useful when you re-run with different settings — diff `--stats` output before/after to confirm the right rows changed.

### Acceptance-mode output

Runs all probe queries (see Expanded Acceptance Tests below) and writes a single markdown file with each query, expected behavior, and observed results.

---

## Bash Wrappers

Three wrappers in `retrieval/`, plus pre-flight. Same pattern as `extract_topics.sh`:

```bash
# retrieval/run-embed.sh
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/embed.py" "$@"
```

Repeat for `run-store.sh`, `run-inspect.sh`, `run-preflight.sh`.

### Standard pipeline invocation

```bash
# Step 0: confirm environment is ready
retrieval/run-preflight.sh

# Step 1: embed Phase 1 topics
retrieval/run-embed.sh \
  --input retrieval/runs/20260416-181839.jsonl \
  --output retrieval/embeddings.jsonl

# Step 2: populate LanceDB index
retrieval/run-store.sh \
  --input retrieval/embeddings.jsonl \
  --index retrieval/index

# Step 3: run acceptance tests (writes to retrieval/probes/{timestamp}.md)
retrieval/run-inspect.sh --acceptance

# Optional: ad-hoc query
retrieval/run-inspect.sh --query "how does Repowise analyze code repositories" --k 5

# Optional: peek at the table
retrieval/run-inspect.sh --stats
retrieval/run-inspect.sh --list
```

---

## Pre-flight Check Script

**`retrieval/preflight.sh`** — fail-fast on environment issues before a long embed run.

```bash
#!/usr/bin/env bash
set -euo pipefail

PY=python3
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
PHASE1_JSONL="retrieval/runs/20260416-181839.jsonl"
EMBED_MODEL="${EMBED_MODEL:-bge-m3}"

echo "== LTG Phase 2 pre-flight =="

# 1. Python deps
echo -n "[1/5] Python deps... "
$PY -c "import httpx, lancedb, pyarrow" 2>/dev/null \
  && echo "ok" \
  || { echo "MISSING — run: pip install httpx 'lancedb>=0.20,<0.30' pyarrow"; exit 2; }

# 2. Ollama reachable
echo -n "[2/5] Ollama reachable at $OLLAMA_URL... "
curl -fsS "$OLLAMA_URL/api/tags" >/dev/null \
  && echo "ok" \
  || { echo "FAIL — start Ollama or set OLLAMA_URL"; exit 3; }

# 3. Embed model installed
echo -n "[3/5] Embed model '$EMBED_MODEL' pulled... "
curl -fsS "$OLLAMA_URL/api/tags" | grep -q "\"$EMBED_MODEL" \
  && echo "ok" \
  || { echo "MISSING — run: ollama pull $EMBED_MODEL"; exit 4; }

# 4. Phase 1 JSONL exists and is non-empty
echo -n "[4/5] Phase 1 input ($PHASE1_JSONL)... "
[ -s "$PHASE1_JSONL" ] \
  && echo "ok ($(wc -l <"$PHASE1_JSONL") rows)" \
  || { echo "MISSING — re-run Phase 1 or check path"; exit 5; }

# 5. Disk space (rough — 1024-dim * 4 bytes * ~50 topics ≈ 200KB, but LanceDB adds index overhead)
echo -n "[5/5] Disk space in retrieval/... "
AVAIL_KB=$(df -k retrieval/ | awk 'NR==2 {print $4}')
[ "$AVAIL_KB" -gt 102400 ] \
  && echo "ok ($((AVAIL_KB/1024)) MB free)" \
  || { echo "LOW (<100MB); not a blocker, but consider cleaning"; }

echo "== Pre-flight OK =="
```

Run before any embed pass.

---

## Expanded Acceptance Tests

### Recall queries (must return relevant topic from named file)

| # | Query | Expected top result file | Pass criterion |
|---|-------|--------------------------|----------------|
| R1 | "what's special about Repowise's git co-change analysis" | `docs/research/smart-rag-repowise.md` | Top-1 from this file; topic name contains "co_change" or "git" |
| R2 | "how do we handle memory across sessions" | `.memories/QUICK.md` OR `.memories/KNOWLEDGE.md` | Top-3 includes a memory file |
| R3 | "which models are good at topic extraction" | `.memories/KNOWLEDGE.md` (Phase 1 summary) OR `retrieval/spike-results.md` if indexed | Top-3 references extractors/models |
| R4 | "how does Repowise analyze code repositories" | `docs/research/smart-rag-repowise.md` | Top-3 from this file |

### Negative / specificity queries (added in v2)

| # | Query | Expected behavior | Pass criterion |
|---|-------|-------------------|----------------|
| N1 | "expense report classification accuracy" | Low overall scores (corpus has no expense-classifier file in the 8-file subset) | Top-1 score < 0.55 OR top-1 from an unrelated file |
| N2 | "Kubernetes deployment YAML" | Low overall scores (not in corpus) | Top-1 score < 0.55 |

Negative queries catch the failure mode where the index returns *something* for *anything*. A healthy embed model should produce visibly lower scores when no good answer exists.

### Relate-preview query

| # | Query | Expected | Pass criterion |
|---|-------|----------|----------------|
| P1 | `--relate --file-a docs/research/smart-rag-repowise.md --file-b docs/research/smart-rag-claude-mem.md` | Some topic overlap on retrieval/codebase analysis; clear divergences (repowise's git focus, claude-mem's observation hooks) | At least 2 cross-file pairs with cosine > 0.55; visible asymmetry in divergences |

### Latency target

- Single `--query` (1 embed + 1 ANN search on 8-file corpus): **< 500ms wall time**
- `--acceptance` (7 queries total): **< 5s wall time**

### Overall pass condition

All four recall queries pass, both negative queries return scores below the threshold, the relate-preview shows believable overlap and divergence, and total acceptance run is under the latency target. Probe markdown is written to `retrieval/probes/`.

### If a recall query underperforms

Note the expected vs observed topic in the probe markdown. This is direct input to the deferred description-vs-description+spans A/B (`ref:ltg-embedding` "sparse signal option"). Decision point: if **two or more** recall queries underperform, run the A/B before declaring Phase 2 done. If only **one** does and the divergence is small, document and proceed.

---

## Probe Result Persistence

Every `--acceptance` run writes a markdown file to `retrieval/probes/{YYYYMMDD-HHMMSS}.md`:

```markdown
# LTG Phase 2 Acceptance Probe — 2026-05-20T15:42:10Z

- Index: `retrieval/index/`
- Embed model: bge-m3
- Embed mode: description
- Rows: 47
- Files: 8

## R1: what's special about Repowise's git co-change analysis

**Expected:** top result from `smart-rag-repowise.md`, topic about co-change

**Top 5:**
1. score=0.913 — smart-rag-repowise.md — `git_co_change_analysis` — "Focuses on analyzing..."
2. score=0.671 — smart-rag-claude-mem.md — `observation_capture` — "..."
3. ...

**Verdict:** ✓ PASS

## R2: ...
```

Probe files are committed to git (small, valuable for cross-session comparison). `retrieval/index/` and `retrieval/embeddings.jsonl` are not.

---

## Logging Strategy

Two log files written per pipeline run, both JSONL, in `retrieval/runs/`:

- **`embed-{timestamp}.jsonl`** — one row per file processed (`file, topics_emitted, topics_failed, latency_s, errors`) + one final totals row (`event: "summary", n_files, n_topics, n_failed, total_latency_s, peak_batch_latency_s`).
- **`store-{timestamp}.jsonl`** — one row per file (`file, n_topics, n_extracted, n_anchor, n_merged`) + one totals row (`event: "summary", n_rows, table_path, table_bytes`).

These mirror `extract_topics.py`'s convention so the runs directory is a single audit trail.

---

## Performance Targets (revised in v2)

Rough estimates for the 8-file Phase 1 corpus, ~50 topics total:

| Stage | Target | Notes |
|-------|--------|-------|
| `preflight.sh` | < 2s | mostly curl + py imports |
| `embed.py` (batched, 32) | 5–15s total | bge-m3 ~50–150ms per batch of 32; 2 batches = ~1s of model time + 1–2s startup |
| `store.py` | 1–3s | LanceDB writes + ANN index build are fast at this scale |
| `inspect.py --acceptance` | < 5s | 7 queries × (1 embed + 1 search) — embed is ~100ms, search is ms |

If `embed.py` takes substantially longer than 30s on 50 topics, something is wrong (probably bge-m3 not warm, or running concurrent with extraction).

---

## `.gitignore` Additions

Add to repo-root `.gitignore`:

```
retrieval/index/
retrieval/index.bak/
retrieval/embeddings.jsonl
```

Keep tracked (commit these):

```
retrieval/probes/*.md
retrieval/runs/embed-*.jsonl
retrieval/runs/store-*.jsonl
```

Reason: probes and run logs are small, valuable as cross-session evidence, and the index/embeddings are large + re-generatable.

---

## Index and Memory Updates (post-completion)

When Phase 2 passes acceptance:

1. **`retrieval/DECISIONS.md`** — mark Phase 2 complete in `ref:ltg-embedding`. Add note: "`embed_mode=description` validated as default; A/B with `description_plus_spans` deferred unless a recall query fails." Add new ref block `ref:ltg-phase2-schema` recording the final 16-field schema and rationale.
2. **`retrieval/.memories/QUICK.md`** — status block: "Phase 2 complete: index at `retrieval/index/`, M topics from N files, X probe queries pass."
3. **`retrieval/.memories/KNOWLEDGE.md`** — new section `ref:ltg-phase2-findings`: probe query results table, actual latencies, batch-embed effective batch size, anything surprising.
4. **`.claude/session-context.md`** (`ref:current-status`) — session entry; advance Next pointer to "Phase 3 — anchor integration."
5. **`.claude/index.md`** (`ref:bash-wrappers`) — add `run-embed.sh`, `run-store.sh`, `run-inspect.sh`, `run-preflight.sh` to the Retrieval / LTG Tools table.
6. **`docs/plans/2026-04-13-latent-topic-graph-implementation.md`** — append a "Session N expansion" note under `ref:ltg-plan-phase-2` linking to this plan and noting v2 schema additions.

---

## Phase 2.5 Sketch (Corpus Expansion)

Out of scope for Phase 2. Sketched here so a future session has direction.

**Trigger to start Phase 2.5:** Phase 2 acceptance passes on 8 files, and at least one consumer (Phase 6 MCP or chatbot use case) has tried the index and asked "why isn't X in here?"

**Scope expansion targets** (in priority order):
1. All of `docs/research/` (likely ~20–40 files).
2. All of `.claude/` and `.memories/` across the repo.
3. `personas/` directory.
4. Long files: re-extract with chunked input (1500–2500 tokens per chunk with 200-token overlap), populating `segment_id` and `segment_range`.

**What changes in scripts:**
- `embed.py` gains a `--corpus-config` arg pointing to a YAML that lists include/exclude globs, scope tags per path, chunking thresholds.
- `extract_topics.py` (Phase 1 tool) gains a `--chunked` mode; its JSONL output gets `segment_id`/`segment_range` fields populated.
- `store.py` gains a `--append` mode with dedupe-by-id (delete-then-insert) for incremental updates.
- A new `retrieval/reindex.sh` orchestrates a full rebuild.

**What stays the same:**
- Schema (the forward-compat fields are why).
- bge-m3 as embedder.
- LanceDB as store.
- Probe-query acceptance pattern (with more queries added to cover newly indexed regions).

---

## Connection to Subsequent Phases

| Phase | What it reads from Phase 2 | What it adds |
|-------|----------------------------|--------------|
| **Phase 3 (anchors)** | All rows; walks `<!-- ref:KEY -->` blocks in the repo; computes embedding sim between extracted topic and anchor block; for sim > 0.85, updates `node_kind` to `"merged"` and adds an optional `anchor_ref_key` column. Pure anchor nodes get inserted with `node_kind="anchor"`. | New rows + column |
| **Phase 4 (graph + community)** | Reads all vectors; builds ANN-pruned all-pairs edge set; loads to networkx; Leiden at 2 resolutions. Stores community assignments in a *new* `communities` table keyed by `id`. | New table |
| **Phase 5 (`relate(a,b)`)** | Reuses `inspect.py --relate` skeleton; adds natural-language synthesis via qwen3:14b. The Phase 2 relate-preview is the smoke test that the data shape works. | Synthesis step |
| **Phase 6 (MCP)** | Wraps `inspect.py` query logic as `retrieve_context(query, scope, mode, limit)`. Filters by `scope_tags` (populated by Phase 8 before Phase 6 is useful for the chatbot, but works untagged for repo-local Claude Code immediately). | MCP wrapping |
| **Phase 7 (reranker)** | Inserts a cross-encoder between ANN top-K and final return inside `inspect.py`/MCP tool. | Rerank step |
| **Phase 8 (per-repo configs)** | Adds a tool that writes `scope_tags` on existing rows per a YAML config. | Backfill tool |
| **Phase 9 (federation)** | Multiple indexes, one federator. Each repo's `retrieval/index/` follows this schema. | Federator service |

---

## Risks (revised)

- **bge-m3 vector normalization assumption.** The relate-preview's cosine math assumes vectors are unit-normalized. Verify on first run: pick two random vectors, compute `np.linalg.norm` — should be ~1.0. If not, normalize in `embed.py` before writing.
- **Topic name collisions across extraction runs.** If a future run produces the same `file:topic_name` ID with different content, overwrite mode handles it cleanly. If we ever ship append-mode (Phase 2.5), this is a real problem.
- **Description-only may under-recall on technical-term queries.** Known risk. Mitigation: `embed-mode` flag is already in place; A/B is one command away.
- **LanceDB API drift.** Pinned to `>=0.20,<0.30`. If installer picks a version where `create_table(schema=...)` signature changed, fail fast and update the pin.
- **JSON-encoded spans field readability in inspect/query output.** Cosmetic only; query results parse and pretty-print.
- **Embed batch size too aggressive.** Default 32. If `/api/embed` returns 413 or timeouts, drop to 16 or 8. Configurable.
- **Forward-compat fields cause confusion.** A reader of the schema may wonder why `segment_id` exists in Phase 2 rows where it's always null. Mitigation: schema comments in code; `ref:ltg-phase2-schema` documents intent.

---

## Why This Plan Is Worth Following (closing rationale)

Phase 2 is the single phase where wrong commitments are expensive. Phase 1 is throwaway (extraction prompt can be re-tuned). Phase 3+ are additive. Phase 2 *commits to a schema and a storage layout that every later phase reads*.

v1 of this plan was correct on every decision it made but underspecified the future-proofing. v2's main contribution is: the schema's four forward-compat fields turn Phases 3, 6, and 8 from "open a migration" into "fill in a column." That's the difference between a sturdy substrate and a slow drag on every downstream session.

The other v2 additions (batch embed, pre-flight, probe persistence, negative queries, relate preview) are smaller wins, but each one removes a category of friction that would otherwise eat 30–90 minutes of a future session.

If only one v2 idea makes it through to implementation, make it the schema additions. The rest can be retrofitted; the schema cannot be retrofitted cleanly.

---

## Handoff Notes for the Executing Session

- Start with `Required Reading`. The `Architectural Context` section is the part most often skipped that most often causes confusion two phases later.
- `Decisions In Force` are frozen. If you find yourself wanting to revisit one, write a paragraph in the session log first explaining why, get a sanity check, then decide.
- Run `run-preflight.sh` before the first `run-embed.sh`. It's cheap and catches the failure modes that waste sessions.
- The acceptance probe markdown is your evidence. Commit it before moving on.
- If you find a real bug in this v2 plan, edit it in-place (don't write a v3 unless decisions are changing).
- Phase 3 starts the moment Phase 2 acceptance passes — `node_kind`, `scope_tags`, and the merged-node ID convention are already laid out above.

<!-- end ltg-phase2-implementation-v2.md -->
