<!-- ref:ldr-assessment -->
# Local Deep Research — Deep Assessment

*Session 44, 2026-03-17. Research agent (Sonnet) examined the GitHub repo.*

**Repository:** github.com/LearningCircuit/local-deep-research
**License:** MIT — no restrictions on forking, extending, or commercial use
**Activity:** Extremely active. ~4,539 commits, pushed today. 4,149 stars, 389 forks, 145 open issues.
**Python:** >=3.11,<3.15

---

## Architecture

**Structure:** ~35 sub-packages under `src/local_deep_research/`:
- `advanced_search_system/` — core research engine (~10 sub-packages: strategies, questions, candidates, constraints, filters, evidence, findings, knowledge)
- `web_search_engines/engines/` — 20+ search engine plugins
- `database/` — SQLCipher ORM (SQLAlchemy 2.0)
- `embeddings/` — pluggable providers (Ollama, OpenAI, sentence-transformers)
- `llm/` — pluggable provider registry with auto-discovery
- `api/` — Flask REST API
- `web/` — Flask + Flask-SocketIO frontend (Vite JS)
- `mcp/` — MCP server/client (4 files)
- `benchmarks/` — SimpleQA, BrowseComp harness
- `exporters/` — PDF, LaTeX, Quarto, RIS, ODT
- `metrics/`, `news/`, `notifications/`, `library/`, `research_scheduler/`

**Modular:** Yes, genuinely. Abstract base classes for search engines, strategies, embedding providers, LLM providers. Documented extension points in `EXTENDING.md`.

---

## Main Research Loop

```
for iteration in range(max_iterations):  # default: 3
    questions = generate_questions(query, current_knowledge, prev_questions)
    for question in questions:
        results = search_engine.run(question)
        findings.append(results)
        current_knowledge = accumulate(findings)
    if context_limit_exceeded:
        current_knowledge = compress(current_knowledge)
synthesized = synthesize_findings(query, findings)
return formatted_report
```

**Stopping:** Standard strategy is purely count-based (runs exactly `max_iterations`). Specialized strategies (`early_stop_constrained`, `dual_confidence`) have confidence-threshold stopping, but opt-in.

**20+ named strategies:** standard, source-based, focused-iteration (96.51% SimpleQA), iterative-refinement, parallel, recursive, adaptive, browsecomp, mcp (ReAct), news, etc. Strategy explosion is technical debt — 30+ files, some experimental.

---

## SearXNG Integration

**Loosely coupled.** One of ~20 search engines, implements `BaseSearchEngine`. Default URL: `http://localhost:8080`. Swapping is trivial — change one config key (`search.tool`). Other engines: DuckDuckGo, Brave, Tavily, Google PSE, arXiv, PubMed, Wikipedia, GitHub, Wayback, Elasticsearch, Semantic Scholar, OpenAlex, NASA ADS, Wikinews.

---

## Ollama Pipeline

- **Calls Ollama via:** `langchain-ollama`'s `ChatOllama` (LangChain abstraction), not direct HTTP
- **Default model:** `gemma3:12b`
- **Default context:** 4096 tokens (conservative; configurable up to 131K)
- **Structured output:** NOT used. Free-text prompting + regex parsing for question generation, synthesis, citations
- **Multi-model:** No. One global LLM for all stages
- **Thinking mode:** `llm.ollama.enable_thinking` setting (default: true), uses LangChain `reasoning` parameter

---

## Knowledge Library

- **SQLCipher:** AES-256 encrypted per-user DB. Tables: research_tasks, search_queries, search_results, reports, library/documents, rag_indices, metrics, logs, cache
- **Embeddings:** Default `nomic-embed-text` via Ollama. FAISS vector index (cpu-only)
- **Cross-session:** Library stores documents from research. New research CAN include library as search source, but it's opt-in, not automatic
- **UX pain point:** Open issue #2809 — encrypted DB requires password after restart

---

## Extensibility

- No formal plugin system, but well-documented extension patterns:
  1. `BaseSearchEngine` subclass + factory registration
  2. `BaseSearchStrategy` subclass + strategy list registration
  3. LLM provider auto-discovery
  4. `BaseEmbeddingProvider` subclass
  5. LangChain retriever integration
- **Configuration:** SQLCipher-backed settings DB, ~180KB default_settings.json, env var overrides, web UI

---

## Dependencies (Weight Concerns)

All unconditional — no optional groups:
- LangChain full stack (~1.2)
- sentence-transformers (~5.2) + faiss-cpu (~1.13)
- playwright (~1.58)
- weasyprint (~68.1) — PDF gen
- unstructured (~0.18) — document parsing
- datasets (~4.5) + pyarrow (~23.0) — HuggingFace
- optuna (~4.7) — hyperparameter optimization
- elasticsearch (~9.3)
- matplotlib, pandas, plotly, kaleido
- pypandoc-binary (~1.16)

**Total install: ~2-3GB.** Not suitable as an embedded library.

---

## Code Quality

- **Tests:** 1,608 test files. Extensive, actively growing. pytest with 60s timeout, coverage reporting (but `fail_under = 0`)
- **Patterns:** Clean — abstract base classes, DI, factory pattern, proper separation
- **Debt:** Strategies directory excluded from coverage, 30+ strategy files with duplication
- **CI:** CodeQL, Semgrep, Dependabot, OSSF Scorecard, custom pre-commit hooks
- **Docs:** EXTENDING.md, FAQ, troubleshooting, MCP docs, inline docstrings

---

## Gaps vs Our Vision

| Gap | Impact |
|-----|--------|
| LangChain deep coupling | Can't easily extract pieces or use direct Ollama HTTP |
| No structured output (JSON schema) | Regex parsing fails on 7-8B models; our `format` param is 100% reliable |
| No multi-model pipeline | One LLM for all stages; we want 7B extraction + 14B synthesis |
| No progressive autonomy | Fully automated or manually interrupted; no pause/steer/resume |
| 4096 default context | Too conservative for our 8K-10K models |
| ~2-3GB install | Unconditional heavy deps |
| Multi-user web app design | Encrypted per-user DB, Flask frontend — overhead for local CLI |
| No focus-directed extraction | Can't say "extract specifically about X" |
| No Claude Code integration | MCP exists but one-way |

---

## Patterns Worth Borrowing (Independent Implementation)

1. **`BaseSearchEngine` + factory** — clean plugin architecture for search backends
2. **Two-phase retrieval** — metadata preview → full content on demand
3. **Strategy registry** — named strategies with configurable params
4. **ReAct loop** (MCP strategy) — search/read/reason cycle
5. **Library as search source** — past research queryable alongside live web

---

## Verdict: Build New, Informed by LDR

The patterns are more valuable than the code. A fresh implementation can:
- Use direct Ollama HTTP (existing client) instead of LangChain
- Use `format` param for structured output (100% reliable)
- Support multi-model pipelines from day one
- Be lightweight (no 2-3GB dep chain)
- Build progressive autonomy as first-class
- Target CLI + MCP, not web app
- Reopens language question — not inheriting Python from LDR
<!-- /ref:ldr-assessment -->
