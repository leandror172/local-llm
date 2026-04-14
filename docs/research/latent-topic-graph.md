<!-- ref:concept-latent-topic-graph -->
# Latent Topic Graph: A Content-Relation Retrieval Substrate

*Draft concept note. Model-agnostic. Authored 2026-04-13 (session 51). Status: exploratory — intended to be refined into something publishable if the direction holds up under implementation.*

---

## Abstract

A **Latent Topic Graph (LTG)** is a retrieval substrate where the primary nodes are topics extracted by a language model from a corpus, files (or documents) are mere containers for those topics, and edges are weighted by embedding-space distance between topics. Hand-curated anchor structures (cross-references, tags, manual links) are first-class but stratified: anchor edges carry human-verified confidence, while LLM-inferred edges carry model-derived confidence that can be retraced. The graph surfaces *content relationships* rather than *structural connections*, enabling queries that answer "how do these things relate" across documents that share no citations, imports, or explicit links.

LTG occupies a gap between existing approaches: more abstract than Microsoft GraphRAG (which extracts entities, not topics), more structural than vector RAG (which treats documents as atomic), and less rigid than hand-authored knowledge graphs (which don't scale). Its distinguishing property is that it models knowledge the way cognition apparently does — as a dense, multi-scale relational fabric — while files remain only the physical-world storage containers that humans happen to use.

---

## Motivation: Files Are a Crude Container

Outside the mind, humans store knowledge in documents, chapters, notes, or code files because the physical and digital worlds force a serialization: ink on paper, bytes in a file, pixels in a rendered page. These containers are *arbitrary with respect to content*. Two ideas stored in the same file may have nothing conceptually in common; two ideas stored in different files, different repositories, even different media, may be the same idea approached from two sides. The file boundary is a storage convenience, not a semantic structure.

Retrieval systems that treat files as first-class objects inherit this arbitrariness. Vector RAG over chunked files retrieves *fragments* of containers, not *concepts*. Keyword search matches surface form, not meaning. Hand-authored knowledge graphs capture only the relationships their author remembered to write down. Graph-based methods that lean on hyperlinks, imports, or citation edges capture only the structural signals humans were willing to encode — the relationships they could notice or were motivated to record.

What all of these miss is the **dense, latent, content-driven relational structure** that exists between ideas themselves, independent of which file they happen to live in. That structure is what readers reconstruct when they say "oh, this connects to that other thing I read." It is not usually written down anywhere.

**LTG's core claim:** if a language model can identify what a piece of content is *about* — not just where its paragraphs begin and end — then a retrieval substrate built on topics rather than files reveals the relationships that matter, and demotes the ones that don't.

## Core Construct

An LTG consists of four kinds of entities:

1. **Topic nodes.** Each topic is a semantically coherent concept identifiable within a corpus. Topics are extracted by a language model that reads a source and returns a list of the distinct ideas it contains, along with the locations in the source that discuss each idea. Crucially, a topic may be discussed in **non-contiguous locations within a single source** — its spans are not required to be adjacent. A file addressing four topics in interleaved paragraphs yields four topic nodes, each pointing at its own disjoint set of spans.

2. **Anchor nodes.** When a corpus already contains hand-curated structural markers — reference tags, cross-reference keys, typed links, schema entries — each such marker becomes an anchor node. Anchors are first-class nodes with the same retrieval properties as extracted topics, but their provenance and confidence differ.

3. **Containers.** Files, documents, notebooks, web pages, and other storage units. Containers hold topic nodes and anchor nodes but are not themselves retrieval-primary. File-to-file similarity is a *derived* quantity, computed from the aggregate overlap of the topics each file contains, rather than a direct edge in the graph.

4. **Edges.** Weighted, typed, and stratified by confidence. Three edge classes:
   - **Anchor edges** (confidence 1.0): human-verified cross-references, already declared in the source material.
   - **Extracted edges** (confidence < 1.0): inferred from embedding-space proximity between topic nodes, filtered by a threshold that varies with use case.
   - **Membership edges**: topics belong to containers; containers belong to higher-level scopes (folders, repos, domains). These are not retrieval edges but are used for scoping and permission boundaries.

The graph is weighted, nearly dense (every topic pair has *some* similarity), and queryable via standard graph operations: top-K nearest neighbor, shortest path, community detection at multiple resolutions, subgraph extraction, and so on.

## Key Properties

### 1. Topic-Level Abstraction

Topic nodes sit between two existing granularities. **Below** them, propositional indexing (Chen et al., "Dense X Retrieval", 2023) extracts atomic factual claims and embeds each as a retrieval unit — finer-grained, but prone to missing thematic structure above the claim level. **Above** them, document or section embeddings capture overall gist but blur distinct ideas that happen to co-locate. Topics are the level at which humans say "this part is about X" — the unit at which conceptual reasoning naturally operates.

### 2. Non-Contiguous Topic Recognition

A topic may exist in a file without being confined to a contiguous span. A file may open with a framing of topic A, develop an aside on topic B, return to topic A, and close with a synthesis that draws on both. A chunking-based retriever would split this into three or four chunks, none of which captures the full treatment of topic A. An LLM-driven topic extractor can identify that "the discussion of A spans paragraphs 1–2 and 5–7" and emit a single topic node covering both spans. This is closer to how a careful reader would summarize the file.

### 3. Files as Containers, Not Nodes

This is the framing move that distinguishes LTG from most related work. In LTG, *files do not participate as first-class retrieval nodes*. A query does not return files; it returns topic nodes, and those topic nodes indicate which files they were extracted from. File-to-file relationships exist only as derived aggregates: `relate(A, B) = f(topic_similarities_for_topics_in_A × topics_in_B)`.

The implication for cognitive modeling is explicit: files are a physical-world artifact. A topic graph more closely resembles how ideas are actually held in relation — as a dense web, not as a filing system.

### 4. Anchor Stratification

Many domains already contain partial hand-curated graphs: hyperlinks, citation networks, cross-reference tags, schema entries, typed wiki-links. LTG does not discard these. It ingests them as anchor nodes, merges them with semantically matching extracted topics (via embedding similarity above a threshold), and marks every edge with its provenance.

This has two benefits:
- **The LLM-inferred layer is kept honest.** Whenever a human-verified anchor disagrees with an extracted edge, the anchor wins and the disagreement is logged as a debugging signal.
- **Human-curated structure is never overwritten.** If someone already declared `X supersedes Y`, no amount of embedding similarity will weaken that edge.

### 5. Derived Structure Rebalances as Content Arrives

A common intuition is that "adding a document changes how existing documents relate to each other." This is almost — but not quite — literally true. Fixed embedding models produce fixed embeddings; the pairwise similarity of two topics is unchanged by the arrival of a third. But three *derived* quantities shift every time new content is indexed:

- **Relative ranking.** The nearest neighbor of a topic can change when a closer neighbor arrives, even though the original similarity is unchanged.
- **Topic salience.** Topic extraction is context-sensitive. An idea that appears only once may not cross the threshold to become a named topic; once it reappears in a second source, it is promoted, and the graph grows a new node from content it always contained.
- **Community structure.** Clustering algorithms (e.g., Leiden) reshuffle memberships near cluster boundaries whenever the node set changes.

The graph therefore has a steady-state raw layer (embeddings) and a fluid derived layer (rankings, salience, communities). Only the derived layer needs to be recomputed when content changes. This distinction matters operationally: incremental updates recompute cheap things, not expensive ones.

### 6. Multi-Scale Structure

Because topic extraction can be run at multiple granularities, and because community detection can be applied at multiple resolutions, an LTG naturally supports multi-scale views of the same corpus. Coarse resolution surfaces broad themes; fine resolution surfaces specific claims. Queries can target the scale that matches the user's intent. This is closely related to RAPTOR's hierarchical summarization tree, but expressed through the graph's community structure rather than through a distinct tree data structure.

## Novel Contributions

LTG does not invent embedding-based retrieval, knowledge-graph construction from text, hierarchical clustering, or confidence-weighted edges. Each of these exists in the literature. LTG's contribution is the specific *combination*, which does not appear assembled in the systems surveyed at time of writing:

1. **Topic-level nodes (not entity-level, not document-level)** as the primary retrieval abstraction.
2. **Non-contiguous topic recognition** as a supported extraction pattern rather than a corner case.
3. **Files as containers, not nodes**, making file-to-file similarity a derived aggregate.
4. **Explicit anchor stratification** with mandatory provenance and confidence on every edge.
5. **Cognitive framing** that treats files as a physical-world limitation and the graph as a closer model of how knowledge is actually held.

Individually, each contribution is incremental. Together, they shift the retrieval surface from "find documents that look like my query" to "find the set of ideas that surround my query, regardless of where they are stored."

## Relationship to Existing Work

- **Microsoft GraphRAG** (2024): closest structural neighbor. Extracts entities and relationships from text, clusters with Leiden, generates hierarchical summaries. LTG differs in the level of abstraction (topics vs entities), the container framing (GraphRAG retrieves documents; LTG retrieves topics), and the explicit anchor stratification.
- **RAPTOR** (2024): hierarchical summarization tree. LTG's multi-scale structure is conceptually adjacent but is expressed through graph communities rather than a tree, which admits cycles and cross-branch relationships.
- **Propositional indexing / Dense X Retrieval** (Chen et al., 2023): atomic factual claims as retrieval units. LTG's topic nodes are a coarser granularity; propositional embeddings can be used *inside* a topic node to support fine-grained recall within a known topic.
- **ColBERT and multi-vector retrieval**: finer granularity again, at the token level. LTG can incorporate ColBERT-style vectors within topic nodes for phrase-level matching but does not require it.
- **Knowledge-graph-from-text** tradition (decades of NLP work): classical NER-and-RE pipelines produce entity graphs; LTG's topic extraction is its LLM-era generalization to less-rigidly-defined conceptual units.
- **Obsidian / wiki-link knowledge management**: hand-authored graphs as the *primary* retrieval structure. LTG ingests these as anchors but does not depend on them — the graph continues to function without any hand authoring, and becomes richer where authoring exists.

## Applications

LTG is model-agnostic with respect to the extractor and the embedder. It can be powered by frontier models, local models, or a mix. The substrate is the same; the model is a tool. Specific applications that motivate the design:

- **Personal knowledge management.** A researcher's notes, papers, and drafts become queryable as a topic graph rather than as a file tree.
- **Code assistant augmentation.** An IDE agent can ask "what concepts in this codebase touch this change" and receive topic-scoped results, not just static-analysis neighbors.
- **Multi-agent research workbenches.** Agents can write into the graph as they extract findings, and subsequent queries can discover cross-agent connections that no single agent observed.
- **Conversational interfaces over static corpora.** A chatbot answering questions about a body of work can use LTG to retrieve the relevant topics rather than chunking documents.
- **Cross-repository reasoning.** Multiple corpora can be indexed separately and federated at query time, with per-corpus permission scopes.

## Open Questions

These are unresolved and motivate the first implementation round:

1. **Topic extraction quality at scale.** How stable are the topic boundaries an LLM produces across runs and across models? If the graph shifts every time the extractor is re-run, community detection will be unstable.
2. **Incremental update strategy.** When new content arrives, does the graph update incrementally, or is a full rebuild cheaper? At what scale does this trade-off shift?
3. **Evaluation methodology.** How does one measure "relational retrieval quality"? Standard IR metrics (precision, recall, nDCG) assume a fixed set of relevant documents per query. LTG returns topic sets, and the relevance of a topic to a query is itself a graded judgment.
4. **Clustering stability.** Leiden is known to be more stable than Louvain but still depends on resolution parameters. How sensitive are the community-level retrieval operations to these parameters?
5. **Topic identity over time.** If the same idea is extracted on two different runs with slightly different phrasings, are they the same topic node? Topic identity is a non-trivial problem in incremental graphs.
6. **Embedding model choice.** General-purpose embedders may not preserve the distinctions that matter for a given domain. When is fine-tuning worth it? When does a larger off-the-shelf embedder suffice?

## Testing and Demonstration

A useful acceptance test, distinct from benchmark IR metrics: the **pairwise relation query**. Given two documents (or two files, or two corpora regions), the system should return a structured answer of the form:

```
relate(A, B) → {
  overall_similarity: float,
  topic_overlap: [{topic, a_weight, b_weight, shared_strength}],
  path_via_intermediates: [A → X → Y → B],
  divergences: [topics in A but not in B, and vice versa],
  explanation: natural-language synthesis
}
```

This query format reveals the quality of the topic extraction directly: an LTG that produces a vague or generic answer is one whose topics are too coarse or whose extractor is hallucinating. An LTG that produces a specific, verifiable answer with named topics and traceable spans is one that has learned the structure of the corpus.

The pairwise relation query is also the **user-visible interface** most likely to demonstrate the system's value. It answers a question that is hard for a human — "how do these two things relate?" — and that neither keyword search nor flat vector retrieval can answer directly.

## Status and Scope of This Note

This is a concept paper, not an implementation description. An accompanying implementation plan (see `ref:plan-latent-topic-graph`) describes a concrete route to a prototype within a single codebase, using local language models, and with specific phases and acceptance criteria. The plan is tactical and scoped to one setup; the concept here is intended to be independent of that setup and potentially publishable if the implementation validates the direction.

Naming note: "Latent Topic Graph" is a working name. Alternatives considered: *semantic content graph*, *emergent topic network*, *topic-container graph*. The final name may shift once the construct is implemented and its distinctive behavior is observable in practice.

<!-- /ref:concept-latent-topic-graph -->
