<!-- ref:rag-hera -->
# HERA: Multi-Agent RAG with Evolving Orchestration

**Source:** https://arxiv.org/abs/2604.00901 ("Experience as a Compass: Multi-agent RAG with Evolving Orchestration and Agent Prompts")
**Philosophy:** Adapt orchestration and agent prompts dynamically based on accumulated experience; use reward-guided sampling to optimize query-specific agent topologies.
**Relevance:** **Low** — tangential to the content-linking question, but on the roadmap for Auditor self-improvement.

## Summary

HERA is a hierarchical framework for multi-agent RAG that addresses two limitations of traditional RAG pipelines: *static orchestration* (fixed agent topology) and *fixed agent behaviors* (unchanging prompts). Key mechanisms:

- **Reward-guided sampling** + experience accumulation — the system builds up "experience" across queries and uses it to bias future agent selection
- **Role-Aware Prompt Evolution** — refines agent behaviors via credit assignment and dual-axes adaptation
- **Global-level topology optimization** + **local-level prompt evolution** — hierarchical adaptation
- Evaluated on knowledge-intensive benchmarks; explicit knowledge-graph / content-linking is *not* discussed

**Accessed via:** `web-research` MCP tool (`research_url`) — first live test of the tool in this session. Extraction ran qwen3:14b in 46s, result cached in the knowledge store for future queries.

## Relation to Our Projects

### web-research
Most direct alignment. The Auditor agent's current role ("is research sufficient, should we explore more?") is exactly the place where HERA's reward-guided adaptation would plug in: track which research topologies produced high-quality outputs and bias future research toward those shapes. Also aligns with the *DDD-as-agent-modeling* patterns in `ddd-agent-modeling.md` — HERA gives a technique for *evolving* the agent topology dynamically, which is the missing piece in the current static DDD decomposition.

### Local LLMs (llm repo)
Tangentially relevant. The verdict protocol (ACCEPTED/IMPROVED/REJECTED) is already a reward signal. HERA's pattern of using accumulated experience to bias agent selection maps onto: "which persona worked best for Python refactoring last month?" — a meta-query over calls.jsonl that we currently answer manually. A lightweight version could be "automatically pick persona based on recent verdict history for similar prompts," which is a modest layer on top of existing infrastructure.

### Augmenting Claude Code
Minimal direct applicability in the near term. Claude Code doesn't currently run multi-agent research topologies; when it does (e.g., via the feature-dev plugin), HERA's evolving-orchestration angle becomes relevant.

### Career chat (HF Space)
Not applicable. The chatbot is a single-agent system with a static prompt.

## Existing Infrastructure Connections

- **web-research Auditor agent** — the closest architectural match; HERA would inform its self-improvement story.
- **`~/.local/share/ollama-bridge/calls.jsonl` + verdict data** — already a reward signal log; HERA-style credit assignment could run on top.
- **`evaluator/` framework** — complements HERA's reward mechanism (evaluator provides scores, HERA decides what to do with them).
- **DDD agent modeling docs** (`ddd-agent-modeling.md`, `ddd-agent-decisions.md`) — HERA is the "make the DDD decomposition dynamic" extension; defer until the static version is stable.

## Takeaway

Not on the near-term path. Archive for when web-research hits the "we have lots of Auditor data and want to improve it automatically" stage. The interesting metadata is that this counts as a **live validation of the web-research MCP tool** — cached extraction, qwen3:14b ran in 46s, relevance assessment automatic. The pipeline works.
<!-- /ref:rag-hera -->
