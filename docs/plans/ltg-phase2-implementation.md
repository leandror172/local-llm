# LTG Phase 2 Implementation Plan — Embedding + Storage

*Written 2026-05-20 (session 61). Decisions locked; ready to execute.*

---

<!-- ref:ltg-phase2-plan -->
## Goal and Scope

Build the embedding + storage layer for the Latent Topic Graph (LTG):
- **`retrieval/embed.py`** — reads Phase 1 extraction JSONL, filters to winning models, embeds topic descriptions via bge-m3, writes embedding JSONL
- **`retrieval/store.py`** — reads embedding JSONL, creates and populates a LanceDB table at `retrieval/index/`
- **`retrieval/inspect.py`** — opens the index, runs top-K nearest-neighbour queries, prints results (primary acceptance test runner)
- **Bash wrappers** for each script (`run-embed.sh`, `run-store.sh`, `run-inspect.sh`)

**Scope:** 8-file validation pass first (Phase 1 corpus), using existing Phase 1 JSONL output. Full corpus expansion is Phase 2.5 (deferred — see end of this document).
<!-- /ref:ltg-phase2-plan -->

---

## Required Reading (before starting implementation)

Read these in order. Each answers a specific question the implementer will face.

| File | Why |
|------|-----|
| `retrieval/.memories/QUICK.md` | Current status, sequential constraint, Phase 1 frozen decisions |
| `retrieval/.memories/KNOWLEDGE.md` (`ref:ltg-vram-probe`) | VRAM probe findings — why sequential, what the footprints are |
| `retrieval/.memories/KNOWLEDGE.md` (`ref:ltg-phase1-summary`) | Extractor model routing: which model for which file type |
| `retrieval/DECISIONS.md` (`ref:ltg-embedding`, `ref:ltg-vector-store`, `ref:ltg-storage-layout`) | Embedding model, vector store choice, schema conventions |
| `retrieval/extract_topics.py` | Source of truth for the extraction JSONL format; dependency pattern (`httpx`, standalone script, no pyproject.toml) |
| `retrieval/runs/20260416-181839.jsonl` | The actual Phase 1 data to be filtered and embedded (32 rows, 8 files × 4 models) |
| `docs/plans/2026-04-13-latent-topic-graph-implementation.md` (`ref:ltg-plan-phase-2`) | High-level Phase 2 plan with acceptance criteria |

---

## Decisions In Force (do not re-litigate)

| Decision | Value | Ref |
|----------|-------|-----|
| Embedding model | `bge-m3` via Ollama | `ref:ltg-embedding` |
| Embedding text | Description-only (not spans) | Session 61 decision; A/B deferred |
| Sequential constraint | embed and infer must NOT run in parallel | `ref:ltg-vram-probe` |
| Vector store | LanceDB, `retrieval/index/` | `ref:ltg-vector-store` |
| Schema | See below | `ref:ltg-storage-layout` |
| Input | Phase 1 JSONL filtered to winning models | Session 61 decision |
| Scripts | Separate files, bash wrappers, no pyproject.toml | Project convention |

---

## Input: Phase 1 JSONL Format

File: `retrieval/runs/20260416-181839.jsonl` (32 rows)

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

`raw_response` is a JSON string; parse it to extract `topics`. Skip rows where `status != "ok"`.

**File → model routing** (filter logic in embed.py):
```
*.py, *.go, *.ts, *.java  →  qwen2.5-coder:14b
everything else            →  qwen3:14b
```

Of the 8 Phase 1 files, `personas/build-persona.py` is the only code file.
All other 7 are prose → qwen3:14b.

---

## LanceDB Schema

```python
import pyarrow as pa

SCHEMA = pa.schema([
    pa.field("id",                   pa.string()),       # "{file_path}:{topic_name}"
    pa.field("file_path",            pa.string()),       # e.g. "docs/research/smart-rag-repowise.md"
    pa.field("topic_name",           pa.string()),       # snake_case name from extractor
    pa.field("description",          pa.string()),       # text that was embedded
    pa.field("spans",                pa.string()),       # JSON string: "[[10,16],[26,32]]"
    pa.field("vector",               pa.list_(pa.float32(), 1024)),
    pa.field("embed_model",          pa.string()),       # e.g. "bge-m3"
    pa.field("embed_dim",            pa.int32()),        # e.g. 1024 — belt-and-suspenders
    pa.field("extractor_model",      pa.string()),       # "qwen3:14b" or "qwen2.5-coder:14b"
    pa.field("extraction_run_id",    pa.string()),       # run_id from Phase 1 JSONL
    pa.field("extraction_timestamp", pa.string()),       # ISO timestamp from Phase 1 JSONL
    pa.field("file_role",            pa.string()),       # file_role from Phase 1 JSONL
])
```

**Note:** LanceDB uses `"vector"` as the conventional field name for the embedding column. Use this, not `"embedding"`, to match LanceDB's default ANN index builder conventions.

**ID scheme:** `f"{file_path}:{topic_name}"` — deterministic, human-readable, deduplication-safe on re-run.

---

## Script 1: `retrieval/embed.py`

**Purpose:** Filter Phase 1 JSONL to winning models → embed descriptions → write embedding JSONL.

**CLI:**
```bash
python3 retrieval/embed.py \
  --input retrieval/runs/20260416-181839.jsonl \
  --output retrieval/embeddings.jsonl \
  [--model bge-m3] \
  [--ollama-url http://localhost:11434]
```

**Logic (pseudocode):**
```
1. Load all rows from --input
2. For each unique file in the JSONL:
   a. Determine winning model: code files → qwen2.5-coder:14b, prose → qwen3:14b
   b. Find the row for that file with matching model and status=ok
   c. Parse raw_response → topics list
   d. For each topic:
      - text_to_embed = topic["description"]
      - call POST /api/embed with model=bge-m3, input=text_to_embed
      - extract embedding = response["embeddings"][0]  (list of 1024 floats)
      - write one output row (see below)
3. Print summary: N files, M topics, total time
```

**Embed API call:**
```python
response = httpx.post(
    f"{ollama_url}/api/embed",
    json={"model": embed_model, "input": text_to_embed},
    timeout=60.0
)
embedding = response.json()["embeddings"][0]  # list[float], len=1024
```

**Output row per topic (JSONL):**
```json
{
  "id": "docs/research/smart-rag-repowise.md:git_co_change_analysis",
  "file_path": "docs/research/smart-rag-repowise.md",
  "topic_name": "git_co_change_analysis",
  "description": "Focuses on analyzing co-change pairs in Git commits...",
  "spans": "[[12,14],[26,32],[44,45],[52,52]]",
  "vector": [0.021, -0.043, ...],
  "extractor_model": "qwen3:14b",
  "extraction_run_id": "8723950f-a0a8-45b4-949d-3af6e96021b0",
  "extraction_timestamp": "2026-04-16T21:19:16.892426+00:00",
  "file_role": "long_research_doc"
}
```

**Sequential constraint:** embed calls are all bge-m3 only — no qwen3:14b involved in embed.py. No parallelism concern here. The constraint applies when embed.py and an inference call (e.g. in inspect.py synthesis) run simultaneously in the future.

**Error handling:** On httpx error or non-200 response, print a warning and skip the topic (don't abort). Log skipped topics at the end.

**Dependency:** `pip install httpx` (already required by extract_topics.py — check before installing).

---

## Script 2: `retrieval/store.py`

**Purpose:** Read embedding JSONL → create/populate LanceDB table.

**CLI:**
```bash
python3 retrieval/store.py \
  --input retrieval/embeddings.jsonl \
  --index retrieval/index \
  [--table topics]
```

**Logic:**
```
1. Load all rows from --input as list of dicts
2. Convert "vector" field from list[float] to pa.array (float32, len=1024)
3. Open (or create) LanceDB at --index path
4. Always use mode="overwrite" (drop and recreate on each run for MVP)
5. Write all rows using schema defined above
6. Print: N rows written, table size, index path
```

**LanceDB setup:**
```python
import lancedb
import pyarrow as pa

db = lancedb.connect("retrieval/index")
# create_table auto-builds ANN index on first write if vector field present
table = db.create_table("topics", data=rows, schema=SCHEMA, mode="overwrite")
```

**Dependency:** `pip install 'lancedb>=0.20,<0.30' pyarrow`

**Note on `retrieval/index/`:** This directory is binary LanceDB data. Add to `.gitignore` if not already present.

---

## Script 3: `retrieval/inspect.py`

**Purpose:** Run top-K nearest-neighbour queries against the index. Primary acceptance test runner.

**CLI:**
```bash
# Top-K query
python3 retrieval/inspect.py \
  --query "what do we know about thinking mode" \
  --k 5 \
  [--index retrieval/index] \
  [--table topics] \
  [--ollama-url http://localhost:11434]

# List all rows (no query)
python3 retrieval/inspect.py --list [--index retrieval/index]
```

**Query logic:**
```
1. Embed the query string via bge-m3 (same /api/embed call as embed.py)
2. Run table.search(query_vector).limit(k).to_list()
3. Print results: rank, score, file_path, topic_name, description[:120], spans
```

**Output format (one result per block):**
```
#1  score=0.923  docs/research/smart-rag-repowise.md  [long_research_doc]
    topic: git_co_change_analysis
    desc:  Focuses on analyzing co-change pairs in Git commits to identify files...
    spans: [[12,14],[26,32],[44,45],[52,52]]
```

**Dependency:** `pip install 'lancedb>=0.20,<0.30' pyarrow httpx`

---

## Bash Wrappers

Three wrappers in `retrieval/`. Follow the same pattern as `extract_topics.py` (shebang, `set -euo pipefail`, pass-through args).

```bash
# retrieval/run-embed.sh
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/embed.py" "$@"
```

Same pattern for `run-store.sh` and `run-inspect.sh`.

**Standard pipeline invocation:**
```bash
# Step 1: embed Phase 1 topics
retrieval/run-embed.sh \
  --input retrieval/runs/20260416-181839.jsonl \
  --output retrieval/embeddings.jsonl

# Step 2: populate LanceDB index
retrieval/run-store.sh \
  --input retrieval/embeddings.jsonl \
  --index retrieval/index \
  --overwrite

# Step 3: run acceptance queries
retrieval/run-inspect.sh --query "what's special about Repowise's git co-change analysis" --k 5
retrieval/run-inspect.sh --query "how do we handle memory across sessions" --k 5
retrieval/run-inspect.sh --query "which models are good at topic extraction" --k 5
retrieval/run-inspect.sh --query "how does Repowise analyze code repositories" --k 5
```

---

## Acceptance Test

Phase 2 passes when all four probe queries return sensible results.

| Query | Expected top result | Pass criterion |
|-------|--------------------|----|
| "what's special about Repowise's git co-change analysis" | `docs/research/smart-rag-repowise.md` topic | Top result from the repowise file (confirmed in Phase 1 JSONL) |
| "how do we handle memory across sessions" | `.memories/QUICK.md` or `.memories/KNOWLEDGE.md` topic | Top result from a memory file |
| "which models are good at topic extraction" | `.memories/KNOWLEDGE.md` Phase 1 summary topic or `spike-results` | Top result references extractors/models |
| "how does Repowise analyze code repositories" | `docs/research/smart-rag-repowise.md` topic | Top result from the repowise file |

**Latency:** sub-second for each query (embed + ANN search on 8-file corpus).

**If a query underperforms:** Note which topic was expected and what was returned. This is input for the deferred A/B test (description+spans may recover recall on technical queries).

---

## `.gitignore` additions

Add to repo root `.gitignore` if not present:
```
retrieval/index/
retrieval/embeddings.jsonl
```

`retrieval/index/` is binary LanceDB data — large, re-generatable, not version-controlled.
`retrieval/embeddings.jsonl` is a transient intermediate — re-generatable from Phase 1 JSONL + bge-m3.

---

## Index and Memory Updates (after completion)

When Phase 2 passes acceptance:

1. **`retrieval/DECISIONS.md`** — mark Phase 2 complete in `ref:ltg-embedding`, add note about schema field choices (why `"vector"` not `"embedding"`)
2. **`retrieval/.memories/QUICK.md`** — update status: "Phase 2 complete: index at retrieval/index/, M topics from N files"
3. **`retrieval/.memories/KNOWLEDGE.md`** — add `ref:ltg-phase2-findings` section: probe query results, actual topic counts, any surprises
4. **`.claude/session-context.md`** (`ref:current-status`) — add session entry, update Next pointer to Phase 3 (anchor integration)
5. **`.claude/index.md`** (`ref:bash-wrappers`) — add `run-embed.sh`, `run-store.sh`, `run-inspect.sh` to the Retrieval / LTG Tools table

---

## Deferred Items (do not implement in this phase)

| Item | Why deferred | Trigger to revisit |
|------|-------------|-------------------|
| **A/B: description vs description+spans** | Description-only is simpler; may be sufficient | Any probe query underperforms — `ref:ltg-embedding` "sparse signal option" |
| **Full corpus expansion (Phase 2.5)** | Validation on 8 files first | After 8-file acceptance test passes |
| **BM25 sidecar index** | Dense-only may be sufficient for MVP | Probe queries miss exact technical terms (model names, ref keys, flags) |
| **Synthesis with qwen3:14b** | inspect.py is retrieval-only for now | Phase 5 `relate(a,b)` adds synthesis |
| **Chunking for long files** | No long files in Phase 1 corpus | Phase 2.5 corpus expansion |
| **Incremental append / dedupe in store.py** | MVP is a single 8-file pass; LanceDB does not enforce ID uniqueness | Phase 2.5 needs proper dedupe design before append is safe |

---

## Advisor Review — Session 61

**Plan review — solid overall, four concrete fixes worth incorporating:**

### 1. Re-run idempotency is underspecified (blocker for clean iteration)

The plan says: *"If table exists and not --overwrite: append (allows incremental adds later)"*. But append mode with no dedupe creates duplicate rows on every re-run, even though IDs (`{file_path}:{topic_name}`) are designed to be unique. LanceDB does NOT enforce uniqueness on any field — `id` is just metadata.

**Fix:** Pick one of:
- **(a)** Default behavior is always overwrite for MVP; remove the append branch. Document that incremental adds are a Phase 2.5 concern when full-corpus mode arrives. *(Recommended for the 8-file pass.)*
- **(b)** Before append, run `table.delete(f"id = '{row['id']}'")` for each incoming row's id. Explicit dedupe, costs a small per-row query.

Pick (a) — it matches the actual Phase 2 scope (single 8-file pass). The append story can be designed properly when Phase 2.5 actually needs it.

### 2. Schema missing `embed_model` field (foresight gap)

The schema records `extractor_model` (which extractor produced the topic) but not which embedder produced the vector. Today this is uniformly `bge-m3`, but the fallback chain (`mxbai-embed-large`, `nomic-embed-text`) is documented in `ref:ltg-embedding`. If you ever switch — or run a comparison — you'll have a mixed index with no way to tell which row came from which embedder.

**Fix:** Add `pa.field("embed_model", pa.string())` and `pa.field("embed_dim", pa.int32())` to the schema. embed.py writes both. ~2 lines of code, removes a future foot-gun. The `embed_dim` field is belt-and-suspenders — LanceDB enforces vector dimension at the schema level, but having it queryable means `inspect.py` can warn if the index doesn't match the expected dim.

### 3. Probe query #1 is weakly grounded in the 8-file corpus

*"What do we know about thinking mode"* — none of the 8 files have a dedicated topic on thinking mode. The closest is `.memories/KNOWLEDGE.md`, which discusses model tier findings and prompt decomposition. The extractor names topics semantically, so there's no guarantee a topic literally named or described around "thinking mode" exists. If the test fails on this query, it's ambiguous whether the pipeline is broken or the corpus just doesn't carry that signal.

**Fix:** Replace with a query that's clearly grounded:
- *"What's special about Repowise's git co-change analysis"* (you already have this exact topic confirmed in the sample JSONL)
- Or: *"What memory architecture does this repo use"* — hits `.memories/KNOWLEDGE.md` or `.memories/QUICK.md` topics

Keep the other three — they're well-grounded.

### 4. LanceDB version is unpinned (instability risk)

`pip install lancedb` will pull the latest release, which has had API changes (e.g., the table-creation surface shifted between 0.4 → 0.10 → 0.20). The plan's `create_table(data=rows, schema=SCHEMA, mode="overwrite")` syntax is current as of recent versions but could break on a fresh install months later.

**Fix:** Pin to a known-working version in the plan: `pip install 'lancedb>=0.20,<0.30' pyarrow`. If the implementing session finds the pin is wrong, they update it then; the explicit range is documentation that "this was tested against 0.2x".

### Lower-priority suggestions

**5. Batch embed calls.** bge-m3's `/api/embed` accepts `input: [str, str, ...]` and returns `embeddings: [[...], [...], ...]`. ~128 topics in one batch is much faster than 128 sequential calls. Drop into embed.py's loop with a `BATCH_SIZE = 32` constant. Not a blocker, but a 4-10x speedup essentially for free.

**6. Sequential constraint is policy, not mechanism.** The plan states the rule but doesn't enforce it. For MVP this is fine — the pipeline naturally runs sequentially (embed.py → store.py → inspect.py, each a separate process). Worth a comment in embed.py: `# Sequential constraint: do not run alongside qwen3:14b inference (ref:ltg-vram-probe)`.

### What's good and shouldn't change

- Required Reading section is exemplary — exactly what a future session needs.
- Decisions In Force prevents re-litigation cleanly.
- Per-script CLI specs with concrete pseudocode = no design ambiguity left.
- The 4-probe acceptance test with explicit expected-result column is the right level of detail.
- Index/memory update checklist for post-completion is the kind of thing that gets forgotten without an explicit list.
- The deferred-items table with explicit triggers is exactly right.
