# RAG & AI/ML Claims Verification Report
**Date:** 2026-06-09
**Purpose:** Verify what can honestly be claimed in a recruiter message targeting a Java+AI role
that lists RAG and vector databases as explicit requirements.

---

## 1. RAG / Vector DB / Embeddings — Status by Item

### 1.1 LanceDB Vector Store
- **Files:** `retrieval/store.py`, `retrieval/ltg_inspect.py`, `retrieval/index/topics.lance`
- **Status: Committed and pushed to GitHub (master)**
- Commits on master: `58af787` (store.py), `d2d5bbf` (inspect rename fix), `4134b0e` (task 9 docs)
- `store.py` creates/overwrites a LanceDB table, uses Apache Arrow (`pa.Table`), performs
  backup rotation, and writes a 16-field schema with vector column.
- `ltg_inspect.py` provides 5-mode CLI: `--list`, `--stats`, `--query TEXT`, `--relate`,
  `--acceptance`. The `--query` mode calls `table.search(vector)` with ANN.
- A real index (`retrieval/index/topics.lance`) with 69 rows was generated and is gitignored
  (runtime artifact), but the code that built it is on master.
- **Claimable:** Yes — "built a vector index pipeline with LanceDB, 69 topics, 5-mode query CLI."

### 1.2 Dense Embeddings (qwen3-embedding:8b, 4096-dim)
- **Files:** `retrieval/embed.py`, `retrieval/config.yaml`
- **Status: Committed and pushed to GitHub (master)**
- Commits on master: `7ecd148` (embed.py), `a0f1e92` (embedding upgrade bge-m3 → qwen3-embedding:8b)
- `embed.py` reads Phase 1 extraction JSONL, routes by file extension (prose vs code),
  batches `qwen3-embedding:8b` via Ollama API, writes 16-field embedding JSONL.
- The 4096-dim embedding model was selected over bge-m3 (1024-dim) after a VRAM co-residence
  probe — that decision rationale is documented in `retrieval/DECISIONS.md` (on master).
- **Claimable:** Yes — "built a batched embedding pipeline using a 4096-dim local embedding
  model (qwen3-embedding:8b), with empirically validated VRAM co-residence constraints."

### 1.3 Topic Extractor (Latent Topic Graph Phase 1 + Phase 2)
- **Files:** `retrieval/extract_topics.py`, `retrieval/model_client.py`, `retrieval/embed.py`
- **Status (Phase 2 base pipeline): Committed and pushed to GitHub (master)**
- `model_client.py` is the Ollama isolation layer; it provides `extract_prose()`,
  `extract_code()`, `embed_texts()` with VRAM-aware routing.
- The 2-arm production runner routing logic (qwen3:14b for prose, qwen2.5-coder:14b for code)
  is in `extract_topics.py` on master — but the clean refactor (`routing.py`, `schemas.py`,
  sweep_extractors.py) is **NOT on master** (see §1.4 below).
- **Claimable:** Yes — "built a topic extraction pipeline with empirically validated model
  routing; scored 8/8 files with a hand-designed 11-dimension rubric across 32 A/B runs."

### 1.4 Extractor Retrofit (routing.py, schemas.py, sweep_extractors.py)
- **Files:** `retrieval/routing.py`, `retrieval/schemas.py`, `retrieval/sweep_extractors.py`
- **Status: Pushed to GitHub on feature branch ONLY — not merged to master**
- Branch: `feature/ltg-extractor-retrofit` (pushed to origin: commit `ce885df`)
- Also present on `feature/ltg-phase3-anchors` (25+ commits ahead of master) and on the
  current working branch `feature/session-handoff-pipeline`.
- 148 tests green; parity verified vs Phase 2 output. PR was noted as ready but the branch
  was never merged to master (the session-handoff branch was stacked on top of it instead).
- **Claimable as "on GitHub":** Yes (branch is public). **Claimable as "shipped/merged":** No.
  Say: "implemented and tested; on a public feature branch, pending merge."

### 1.5 RAG Query / Retrieval (ANN search + semantic relate)
- **Files:** `retrieval/ltg_inspect.py` (`--query`, `--relate` modes)
- **Status: Committed and pushed to GitHub (master)**
- `--query TEXT` embeds the query, runs ANN search against LanceDB, returns top-k topics.
- `--relate` uses cosine similarity between topic vectors to find nearest neighbors.
  Acceptance probe result: cosine similarity improved 0.663 → 0.697 after embedding upgrade.
- **Claimable:** Yes — "implemented end-to-end RAG retrieval: embed query → ANN search in
  LanceDB vector store → ranked topic results."

### 1.6 LTG Phase 3 Anchor Integration (ref-key dual-path RAG)
- **Status: Decisions frozen, zero implementation code written**
- `docs/plans/ltg-phase3-anchor-discovery.md` and `retrieval/DECISIONS.md` contain the
  full spec (D1–D7 decisions frozen, session 82).
- No `anchors.py` has been written yet. This is planned work.
- **Claimable:** No. Do not reference Phase 3 in a recruiter message.

---

## 2. What Is Implemented and Publicly Visible on GitHub Right Now

All items below are on `master` (pushed to `origin/master`, commit `25ffdf7`).

### RAG/ML Pipeline (retrieval/)
| File | What it does |
|------|-------------|
| `retrieval/embed.py` | Batch embedding pipeline (qwen3-embedding:8b, 4096-dim, JSONL I/O) |
| `retrieval/store.py` | LanceDB table creation, Apache Arrow schema, backup rotation |
| `retrieval/ltg_inspect.py` | 5-mode query CLI: list / stats / ANN query / cosine relate / acceptance |
| `retrieval/model_client.py` | Ollama isolation layer: `embed_texts()`, `extract_prose()`, `extract_code()` |
| `retrieval/extract_topics.py` | 2-arm topic extractor runner (qwen3:14b prose / qwen2.5-coder:14b code) |
| `retrieval/config.yaml` | Two-level config: `models:` + `roles:` sections |
| `retrieval/DECISIONS.md` | 8 frozen architecture decisions with full rationale |
| `retrieval/tests/` | 148 tests (8 test files) — currently on feature branch; ~61 on master |

### MCP Server (mcp-server/)
| Aspect | State |
|--------|-------|
| Transport | stdio (JSON-RPC via FastMCP) |
| Tools on master | 15 tools: `ask_ollama`, `generate_code`, `summarize`, `classify_text`, `translate`, `list_models`, `warm_model`, `query_personas`, `detect_persona`, `build_persona`, `create_persona`, `copy_persona`, `ref_lookup`, `patch_file` + 1 more |
| Notable additions (vs April 2026 portfolio) | `patch_file` (surgical file editing via LLM), `ref_lookup` (index-aware retrieval), `create_persona`/`copy_persona`, structured `debug_log.py` per-call JSONL logging, `keep_alive` for KV prefix cache reuse |
| Test count | 29 green tests on master (Plans 1+2+3 complete) |
| Calls log | `~/.local/share/ollama-bridge/calls.jsonl` — all inference calls with latency, passive DPO training data |

### Persona Registry (personas/)
| Aspect | State |
|--------|-------|
| Total in registry | 58 entries |
| Active | 50 personas |
| Base models covered | qwen2.5-coder:7b, qwen3:8b, qwen3:8b-q8_0, qwen3:14b, qwen2.5-coder:14b, qwen3:30b-a3b, qwen3.5:9b, qwen3.5:27b, qwen3-coder:30b, gemma3:12b, deepseek-r1:14b, deepseek-coder-v2:16b |
| Notable additions (vs April 2026) | `my-python-q3-14b`, `my-java-q25c14`, `my-go-q25c14`, `my-classifier-qcoder`, `my-go-qcoder`, `my-python-q3c30`, `my-go-q35`, `my-go-q35-27b`, `my-python-q35`, `my-classifier-q35`, `my-go-q3-30b` |
| State of portfolio docs | `docs/portfolio/portfolio.md` and `engineer-profile.md` were last substantively updated April 2026 — they say "28 active personas" which is now stale (50 active). |

### Benchmark Framework (benchmarks/)
| Aspect | State |
|--------|-------|
| Wrapper scripts | 7 bash wrappers in `benchmarks/lib/` |
| Python libs | 9 Python tools (ollama-probe.py, compare-models.py, record-verdicts.py, etc.) |
| Notable recent use | DeepCoder-14B benchmark (session 74): 5/6 timeout at 500s — documented in `docs/findings/` on master. Outcome: qwen2.5-coder:14b confirmed as primary coder, DeepCoder rejected. |
| DPO pipeline | All local model calls logged; `run-compare-models.sh` + `run-record-verdicts.sh` produce verdict-labeled pairs for future fine-tuning |

---

## 3. Summary: What Can and Cannot Be Claimed

| Claim | Honest one-liner |
|-------|-----------------|
| "Built a RAG pipeline with LanceDB vector database" | ✅ Claimable. `embed.py` + `store.py` + `ltg_inspect.py` all on master with ANN search working. |
| "Implemented dense vector embeddings (4096-dim)" | ✅ Claimable. qwen3-embedding:8b, empirically benchmarked against bge-m3, upgrade committed. |
| "End-to-end topic extraction → embedding → vector search" | ✅ Claimable. All three stages on master, acceptance probe documented. |
| "Multi-model routing for RAG extraction (prose vs code)" | ✅ Claimable (base version on master). Clean refactor on public feature branch, pending merge. |
| "LLM-as-judge evaluation framework" | ✅ Claimable. `evaluator/` + `benchmarks/` framework with rubric scoring, automated + LLM judge phases, on master. |
| "MCP server integrating Claude Code with local LLMs" | ✅ Claimable. 15 tools, 29 tests, shipped on master, used daily as active tooling. |
| "50+ specialized LLM personas across 12 base models" | ✅ Claimable, but portfolio docs say 28 — update those docs before sharing. |
| "Graph-based RAG with community detection (Phase 4)" | ❌ Not implemented. Design only. Do not claim. |
| "Anchor-based dual-path retrieval (Phase 3)" | ❌ Not implemented. Decisions frozen but zero code. Do not claim. |
| "Fine-tuned local models / DPO" | ❌ Infrastructure built (calls.jsonl, verdict labeling), training not executed. Claimable as "DPO data pipeline built"; not claimable as "fine-tuned a model." |

---

## 4. Action Items Before Sending a Recruiter Message

1. **Update portfolio docs** — `docs/portfolio/portfolio.md` and `engineer-profile.md` say
   "28 active personas." Real count is 50. Update before sharing.
2. **Merge the extractor retrofit PR** — `feature/ltg-extractor-retrofit` contains routing.py/
   schemas.py (148 tests). It's on a public branch but unmerged. If citing "clean modular
   architecture," either merge it or add the PR link.
3. **The RAG work is genuinely strong for a local-infra project.** LanceDB + embeddings +
   ANN query + empirical model selection + 148 tests is a real, verifiable implementation —
   not a tutorial clone. Lead with it.
