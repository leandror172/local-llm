<!-- ref:rag-dify -->
# Dify: Off-the-Shelf LLM App Platform

**Source:** https://github.com/langgenius/dify
**Philosophy:** Visual workflow platform for LLM apps. Generic RAG included, no specialized content-linking or graph features.
**Relevance:** **Baseline only** — what *not* to build.

## Summary

Dify is an open-source LLM application development platform (not a library) centered on visual workflow design, model integration, prompt optimization, and LLMOps monitoring. It includes generic RAG capabilities ("extensive RAG from document ingestion to retrieval") covering common formats (PDF, PPT, etc.) but **no mention of graph-based features, content-linking, or cross-document relationship modeling** in the README.

## Why It's Here (And Why We Won't Adopt It)

Dify is the canonical "off-the-shelf" option for teams that need a standard RAG chatbot in a hurry. Its inclusion in this research cluster is to establish the baseline: this is what you get by installing an existing platform. The gap between "standard RAG" (what Dify offers) and "content-linking, relationship-aware retrieval" (what we're after) is exactly what the other six files in this cluster characterize.

## Relation to Our Projects

### All four (web-research, local LLMs, Claude Code augmentation, career chat)
Dify solves none of the specific problems we've surfaced:
- No graph / content-linking (the whole point of this research)
- Platform lock-in conflicts with the "pluggable everything" principle from `docs/research/web-research-tool-vision.md`
- Runs as a separate service, not as a library or set of primitives
- Generic chunking, no contextual or propositional indexing
- No way to reuse existing `ref:KEY` graph structure as seed edges

It is conceivable that the career chatbot could be *hosted on* Dify for the UI layer, but the retrieval layer underneath would still need to be ours.

## Existing Infrastructure Connections

None worth building on. Dify's architecture is a separate deployment target, not something to integrate with our `.memories/` + `ref:` + ollama-bridge stack.

## Takeaway

Confirms that off-the-shelf RAG platforms don't solve the content-linking problem — and therefore validates the build-minimum-from-primitives decision in `docs/ideas/smart-rag2.md`.
<!-- /ref:rag-dify -->
