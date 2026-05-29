# Adjacent Projects

Loose tracking of repos that consume or inform this one. Internal task tracking stays in each repo.
This file tracks: current status, what they use from llm repo, findings that affect decisions here, and cross-repo deferred work.

---

## expense-reporter

**Repo:** `~/workspaces/expenses/code/`
**Purpose:** Local model classifies expenses, auto-inserts into Excel workbook.
**Last synced:** 2026-05-29 (session 75)

### Status
Layer 5 complete — 439 tests passing, on master.

| Feature | Status |
|---|---|
| Training data (`feature_dictionary_enhanced.json` + `training_data_complete.json`) | ✅ |
| `classify` command (3-field → Ollama → top-N with confidence) | ✅ |
| `auto` command (HIGH ≥ 0.85 → insert, else candidates) | ✅ |
| `batch-auto` command (CSV → classified.csv + review.csv) | ✅ |
| Feedback/correction logging (`classifications.jsonl`, `correct` command) | ✅ |
| Expense persistence (`expenses_log.jsonl`, sha256[:12] ID) | ✅ |
| Few-shot injection (keyword top-K from training + feedback pool) | ✅ |
| MCP wrapper (`classify_expense` + `add_expense`) | ✅ lives in expense-reporter's own `mcp-server/`, not llm repo |
| `review` command (classified CSV + taxonomy → self-contained HTML) | ✅ RUI-1 |

### What it uses from llm repo
- Ollama models (qwen3:8b / qwen2.5-coder:14b for classification)
- MCP server conventions and personas (my-go-q25c14 for Go codegen)
- `local-model-conventions.md` from ollama-scaffolding overlay

### Deferred work (tracked in expense-reporter)
- **5.R1** TF-IDF retrieval — trigger: keyword miss rate > 10% (not yet measured)
- **5.R2** Embedding/RAG retrieval — trigger: semantic gap cases > 5% after TF-IDF
- **RUI-3** `apply` command — ingest `reviewed.json` → workbook + feedback logs
- **RUI-4** Full 3-level path (sheet/category/subcategory) in classified CSV

### Cross-repo implications for llm repo
- **MCP wrapper location changed:** 5.8 ended up in expense-reporter's own `mcp-server/`, not here. Original plan (thin wrapper calling Go binary) was superseded.
- **`auto_add` dropped:** caller decides; tools are `classify_expense` + `add_expense` only.
- **Tiny model benchmark (M-P1b):** relevant when 5.R1/5.R2 work starts — need to answer "faster/smaller model at same classify quality?" before retrieval upgrade locks in the approach.

---

## web-research

**Repo:** `~/workspaces/web-research/` (or similar — confirm path)
**Purpose:** Agent-driven web research with Dispatcher routing and structured output.
**Last synced:** session 60 (2026-05-16, ollama-scaffolding overlay propagation)

### Status
Active development. Long-document handling is an open question.

### What it uses from llm repo
- Ollama models via MCP bridge
- `local-model-conventions.md` from ollama-scaffolding overlay (propagated session 60)
- LTG substrate planned as downstream consumer (Phase 6+)

### Cross-repo implications for llm repo
- **Llama 4 Scout (M-P1a):** long-context retrieval is already a question here — concrete use case for Scout's 200K–1M effective context window.
- **LTG Phase 6 (MCP exposure):** `retrieve_context` tool planned as a web-research Dispatcher input once LTG Phase 5 (`relate()`) is working.
