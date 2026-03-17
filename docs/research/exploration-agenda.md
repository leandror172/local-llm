# Exploration Agenda: Web Research Tool

*Created session 44 (genesis). This tracks what to explore next, across forked sessions.*

---

## Priority 1: Examine Local Deep Research

Questions to answer by reading the repo and testing:
- What's the actual architecture? (code quality, modularity, extensibility)
- How does the SearXNG integration work? Is it cleanly separated?
- How does the Ollama pipeline work? Which models, what prompts, structured output?
- How is the knowledge library implemented? (SQLCipher schema, embedding model, indexing)
- Is it designed for extension/plugins, or is it monolithic?
- What are the real gaps vs what we identified from docs alone?
- Could we fork/extend it, or is it better to extract patterns and build new?
- License — can we build on it?

## Fork Angles (for separate sessions)

### Angle A: MVP Spike — PLANNED
**Plan:** `mvp-spike-plan.md` (`ref:mvp-spike-plan`). Simplified from original: uses `httpx` + `trafilatura` + direct Ollama HTTP (no SearXNG/Crawl4AI needed for spike). Python script, 5 test URLs, structured JSON extraction via `format` param. Tests Qwen2.5-Coder-14B first, then Qwen3-14B and Qwen3-8B. Estimated ~1-2 hours implementation + ~1 hour evaluation.

### Angle B: DDD Agent Modeling
Formalize the "domain driven design as agent/model modeling" pattern as a reusable design framework. Map bounded contexts → agents, ubiquitous language → system prompts, anti-corruption layers → data translation between tools. Novel enough to write up independently.

### Angle C: Mastra Deep-Dive
Examine Mastra's suspend/resume + workflow engine. Does it solve progressive autonomy off-the-shelf? What's the actual DX? Could it be the orchestration layer? (TypeScript — would pull language decision toward TS.)

### Angle D: Tool Calling Benchmarks
Retest tool calling with current models (Qwen3-8B, Qwen2.5-Coder-14B, Qwen3-14B). Has it improved? Can a 14B model reliably route between 3-5 tools? This determines whether Agent Tool needs to be code or can be an LLM.

### Angle E: SearXNG Setup
Deploy SearXNG in Docker. Test search quality. Understand configuration. This is a prerequisite for any research pipeline — independent of language/architecture decisions.

---

## Deferred Tasks

### ref-lookup.sh prefix search
The script currently does exact matching (`<!-- ref:KEY -->`). A prefix search mode would let `ref-lookup.sh quick-memory` return ALL blocks starting with `quick-memory-*`. Useful for the `*-MEMORY.md` pattern where multiple topic-scoped memory files share a prefix convention. Low priority — only matters once multiple memory files exist.

---

## Notes on Research Folder Organization

**`*-MEMORY.md` convention:** Each topic gets a QUICK-MEMORY (concise, at-size-limit, entry point) and potentially deeper `*-MEMORY.md` files for specific sub-topics. These serve as scaffolding for any model that accesses the folder — especially useful at the "probe knowledge layer" stage.

**Folder-per-topic (future):** As research topics multiply, organize into subfolders, each with a standard structure (INDEX/MEMORY/findings/raw) that serves as scaffolding for any model or agent accessing that folder.
