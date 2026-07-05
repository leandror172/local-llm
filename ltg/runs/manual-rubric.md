# Manual rubric — 20260416-181839

threshold: 2.2 · weights: d5=0.35 d6=0.35 d7=0.2 d8=0.1

| model | file | d5 | d6 | d7 | d8 | weighted_q | pass | notes |
|---|---|---|---|---|---|---|---|---|
| gemma3:12b | docs/research/smart-rag-repowise.md | 3 | 1 | 3 | 2 | 2.20 | ✓ |  |
| gemma3:12b | .memories/QUICK.md | 0 | 1 | 1 | 2 | 0.75 | ✗ | Tends to infer wrong ideas (memory_architecture  name/description from aggregated pieces that seen very tangent to that idea), strange decisions on spans (12-14 + 16-23, missing "llm/" root folder of structure) |
| gemma3:12b | docs/research/smart-rag-index.md | 3 | 1 | 2 | 2 | 2.00 | ✗ |  |
| gemma3:12b | .claude/plan-v2.md | 2 | 1 | 1 | 1 | 1.35 | ✗ | Many topics in the document were not identified |
| gemma3:12b | personas/persona-template.md | 3 | 1 | 3 | 2 | 2.20 | ✓ | Clearly missed topic about naming |
| gemma3:12b | .memories/KNOWLEDGE.md | 3 | 1 | 3 | 2 | 2.20 | ✓ |  |
| gemma3:12b | docs/ideas/smart-rag3.md | 2 | 2 | 3 | 2 | 2.20 | ✓ | Missed ideas on the rest of the file |
| gemma3:12b | personas/build-persona.py | 2 | 1 | 2 | 2 | 1.65 | ✗ |  |
| qwen3:14b | docs/research/smart-rag-repowise.md | 3 | 3 | 2 | 2 | 2.70 | ✓ |  |
| qwen3:14b | .memories/QUICK.md | 3 | 3 | 2 | 3 | 2.80 | ✓ | Description/boundary: cross_repo_architecture missed "overlays/      # Portable scaffolding packages for cross-repo consistency" evaluation_frameworks missed "benchmarks/    # Multi-language code validation suite" Boundary: ltg_implementation includes "## Repo Structure" for no reason |
| qwen3:14b | docs/research/smart-rag-index.md | 3 | 3 | 2 | 3 | 2.80 | ✓ |  |
| qwen3:14b | .claude/plan-v2.md | 3 | 3 | 2 | 2 | 2.70 | ✓ | Still left out topics, but better at identifying them than Gemma:12b |
| qwen3:14b | personas/persona-template.md | 3 | 3 | 3 | 3 | 3.00 | ✓ |  |
| qwen3:14b | .memories/KNOWLEDGE.md | 3 | 3 | 3 | 3 | 3.00 | ✓ |  |
| qwen3:14b | docs/ideas/smart-rag3.md | 3 | 3 | 3 | 3 | 3.00 | ✓ |  |
| qwen3:14b | personas/build-persona.py | 3 | 3 | 3 | 2 | 2.90 | ✓ | persona_specification boundary missed 116-133? user_interaction boundary missed the instructions 13-22 codebase_integration boundaries missed 'detect' import that gemma got |
| qwen2.5-coder:14b | docs/research/smart-rag-repowise.md | 3 | 2 | 1 | 3 | 2.25 | ✓ | Found topics that 14b didn't like relation_to_projects and takeaways, but serious off-by-one errors on some short spans |
| qwen2.5-coder:14b | .memories/QUICK.md | 2 | 1 | 2 | 3 | 1.75 | ✗ | Name/description: memory_architecture thought that those lines talk about how the memory works |
| qwen2.5-coder:14b | docs/research/smart-rag-index.md | 2 | 3 | 2 | 3 | 2.45 | ✓ |  |
| qwen2.5-coder:14b | .claude/plan-v2.md | 3 | 2 | 2 | 2 | 2.35 | ✓ | local_ai_infrastructure: sounds like it captured the general tone/objective of the doc, and the spans take most of the titles; this is a very interesting signal model_deployment spans almost fit the tasks of the plan; again, interesting dependency_graph I think no other model identified this |
| qwen2.5-coder:14b | personas/persona-template.md | 3 | 2 | 3 | 2 | 2.55 | ✓ | system_prompt missed Rules, even if it include topic title line |
| qwen2.5-coder:14b | .memories/KNOWLEDGE.md | 3 | 2 | 3 | 3 | 2.65 | ✓ |  |
| qwen2.5-coder:14b | docs/ideas/smart-rag3.md | 3 | 2 | 2 | 2 | 2.35 | ✓ | graph_based_retrieval got the titles in the span, keeping it a table;  interesting hybrid_search then got *only* the title, and not the table content behavioral_signals only has empty line in the span |
| qwen2.5-coder:14b | personas/build-persona.py | 3 | 3 | 3 | 2 | 2.90 | ✓ | Missed/overlap coverage similar to 3.14b |
| qwen3:8b | docs/research/smart-rag-repowise.md | 3 | 3 | 1 | 2 | 2.50 | ✓ | Added line 41 "## Existing Infrastructure Connections" to ALL topics |
| qwen3:8b | .memories/QUICK.md | 3 | 3 | 2 | 2 | 2.70 | ✓ |  |
| qwen3:8b | docs/research/smart-rag-index.md | 2 | 3 | 3 | 3 | 2.65 | ✓ |  |
| qwen3:8b | .claude/plan-v2.md | 2 | 2 | 2 | 1 | 1.90 | ✗ | Missed many topics, and missed content for the found topics |
| qwen3:8b | personas/persona-template.md | 3 | 3 | 3 | 2 | 2.90 | ✓ | Missed registration, Persona explanation Interesting effect on spans: on some cases that it could be contiguous, it still detected and separated into 2 spans of "subtopics" |
| qwen3:8b | .memories/KNOWLEDGE.md | 3 | 3 | 3 | 2 | 2.90 | ✓ | Missed Smart RAG Research |
| qwen3:8b | docs/ideas/smart-rag3.md | 3 | 3 | 3 | 2 | 2.90 | ✓ |  |
| qwen3:8b | personas/build-persona.py | 3 | 3 | 2 | 1 | 2.60 | ✓ | Left out topics |
