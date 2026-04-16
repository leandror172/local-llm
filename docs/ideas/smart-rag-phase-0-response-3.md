All three points land. Let me address each.

`★ Insight ─────────────────────────────────────`
- `bge-m3` being Ollama-native collapses the main objection I had (runtime split). The decision shifts from "simplicity vs. capability" to a pure VRAM+speed vs. quality tradeoff — much cleaner.
- Testing a coder model on actual code surfaces a useful anti-pattern: coder models tend to emit function/class enumerations as "topics," which is not what LTG means by topic. The rubric needs to penalize this explicitly.
- A >1MB file in the test set isn't just a stress test — it's a potential *architectural* finding. If extraction can't fit a file atomically, "file = extraction unit" silently becomes "file-or-segment = extraction unit," and that's better learned in Phase 1 than Phase 4.
`─────────────────────────────────────────────────`

## 1. `bge-m3` via Ollama — yes, this changes the call

With the runtime-split objection gone, the remaining tradeoff is narrower:

| Factor | nomic-embed-text | bge-m3 (Ollama) |
|---|---|---|
| Dense MTEB | ~62.4 | ~66 |
| VRAM loaded | <1 GB | ~2.5–3 GB |
| Disk | 274 MB | ~2.3 GB |
| Embeddings/sec | Faster | Slower (non-dramatic) |
| Ollama API surface | Dense | Dense only (sparse/multi-vector stay internal) |
| Cross-repo consumer install | Zero | Zero (Ollama-native) |

**Revised recommendation: switch default to `bge-m3` via Ollama.** Reasoning:
- The 3–4 MTEB point lift compounds across every query for the substrate's lifetime.
- Switching embedding models *later* means re-embedding the whole corpus — painful enough to avoid.
- Cross-repo consumers get it for free without torch/HF.

**One Phase 2 check I'd add:** a VRAM co-residence probe. Load `qwen3:14b` (≈9 GB), then `bge-m3` (≈3 GB), query both in alternation, watch for evictions. Total is ~12 GB on a 12 GB card — we'll definitely see pressure. If Ollama evicts between extract/embed *during indexing*, fine (sequential anyway). If it evicts *during query-time* (`embed query → retrieve → maybe LLM synthesis`), that's a daily friction cost we'd need to fix — either by running `bge-m3` smaller via quantization if available, or falling back to `mxbai-embed-large` (≈700 MB).

**Fallback order if VRAM pressure is real:** `mxbai-embed-large` → `snowflake-arctic-embed-l` → `nomic-embed-text`. All Ollama-native; all swap in with a one-line config change.

Note: the "sparse signal" argument I made before still applies — bge-m3 via Ollama only exposes dense. If you ever want the hybrid advantage, the bolt-on `bm25s` index is still an option on top.

## 2. Coder model on code — yes, add one code file to the sweep

Good catch. The plan's curated corpus (`docs/research/`, `.claude/`, `.memories/`, `docs/ideas/`) is prose-dominant, and I'd biased the whole test toward that. But LTG will eventually index code files (Phase 8 per-repo configs), and we should learn the extraction behavior on code *now*, not after we're committed.

**Add one representative Python file** — I'd pick something with enough structure to be interesting but not huge: `personas/create-persona.py` or one of the ollama-bridge tool modules. ~300–500 lines, multiple logical sections.

**Run both `qwen3:14b` and `qwen2.5-coder:14b` on it** — two extra runs total. This is the head-to-head that answers "does coder specialization help on code specifically?" for our specific extraction task.

**Add one rubric dimension specifically for code files:** *semantic vs. syntactic topics*. Score 0–3:
- 0: model emits one topic per function/class (syntactic enumeration — wrong)
- 1: mostly functions, some grouping
- 2: mixed — some semantic clusters, some function-level
- 3: true semantic topics (e.g., "argument parsing and validation," "YAML registry manipulation," "Modelfile generation") that may span multiple functions

This is the anti-pattern watch. Coder models are notorious for collapsing to function enumeration when asked for "topics."

**Corollary finding we might get:** if *neither* model does semantic extraction cleanly on code, that's a Phase 1 signal that code needs a different extraction prompt — or a pre-pass that groups functions by semantic role before extraction. Valuable to learn now.

## 3. gemma3:27b and the >1MB document

### gemma3:27b

Session 50 ruled it out for code gen at 3.2 tok/s (timeouts on everything). Topic extraction is a different shape:
- Mostly *reading* rather than *generating* — the output is maybe 500–800 tokens, not thousands
- At 3.2 tok/s, 500 output tokens ≈ 2.5 minutes per file; 7 files ≈ 18 minutes
- Slow but *possible* for a one-time sweep

**Include it as an optional 6th config, single-stage only.** If the quality gap over `gemma3:12b` is large, it's a real finding — we might commit final indexing to 27b even though iteration stays on 12b. If the gap is small, we drop it forever with data behind the decision.

Do *not* run it through the two-stage variant. That'd be ~35 minutes per file; not worth it.

### The >1MB MCP wiki file

This is a great addition. It tests two things at once:

**1. The degenerate case for extraction-as-atomic.** At >1MB, the file is ~250K tokens — beyond *every* model in our lineup. Context limits:
- gemma3:12b: 128K (nominal, maybe less effective)
- qwen3:14b: 32K (configured)
- qwen2.5-coder:14b: 10K (configured)
- qwen3:8b: 32K
- gemma3:27b: 128K

None fit the file atomically. This means one of:
- Truncation (we send the first N tokens; model extracts topics from the prefix only; result is provably incomplete)
- Chunking + merging (we split into sections, extract per section, merge overlapping topics) — this is *new code* the MVP didn't plan for

**2. The architectural finding.** Running this test in Phase 1 surfaces the question: **is the extraction unit "a file" or "a segment"?** The plan's mental model is file-level. If any real-world corpus file blows past context, the unit has to be segment-level with a file-level aggregator.

### Proposed handling for the long file in Phase 1

Don't try to solve chunking yet. Instead, **treat this one file as a bounded experiment** with three runs:

1. **Prefix truncation run:** feed first ~30K tokens of the file, extract. Record "topics covered" vs. what a human would expect from the whole file. Expected result: we get the first third's worth of topics, missing the rest.

2. **Naive chunking run:** split the file into ~20K-token chunks, extract each independently, concatenate results (no merging). Look for duplicated topics across chunks (= merge logic is needed later) and missed cross-chunk topics (= chunking strategy matters).

3. **Structure-aware chunking run** (if markdown with headings): split on H2/H3 boundaries, extract each section, tag with section path. This is likely the production answer; testing early validates it.

Use one model for these runs — probably `qwen3:14b` (32K context fits a 20K chunk comfortably). ~3 extra runs.

**Artifact:** a Phase 1 appendix — `retrieval/phase1-long-file-findings.md` — documenting:
- Whether chunking was needed at all
- Which chunking strategy (naive vs. structure-aware) produced cleaner topics
- Whether duplicated-topic merging is trivial or requires its own prompt
- Whether this changes the Phase 2 schema (do we need `chunk_id` on nodes?)

This feeds directly into a potentially revised Phase 2 plan.

## Updated Phase 1 sweep total

| Item | Count |
|---|---|
| Models × prose files | 5 models × 7 files = 35 runs |
| Optional gemma3:27b × prose files | +7 runs |
| Code file × (qwen3:14b + qwen2.5-coder:14b) | +2 runs |
| Top-2 models × two-stage variant × 7 files | +28 runs |
| Determinism re-runs (top model × 3 files × 2) | +6 runs |
| Long file × 3 strategies | +3 runs |
| **Total** | **~81 runs** |

At ~30 tok/s for 12B/14B and ~3 tok/s for 27B, roughly 5–6 hours of compute with warm models. Meaningful investment but still a single session's worth.

## Where we are on decisions

| # | Decision | Current state |
|---|---|---|
| 2 | Embedding | **`bge-m3` via Ollama** (flipped from nomic), with fallback chain if VRAM doesn't cooperate; Phase 2 VRAM co-residence probe required |
| 5 | Extractor | 5–6 models, 8 files (7 prose + 1 code), 1 long-file appendix, two-stage variant for top 2, 11-dimension rubric + semantic-vs-syntactic for code |
| 7 | Storage | Pure LanceDB + sidecars + `inspect.py` (unchanged from last round) |

Ready to lock these in? Or want to also talk about #1/#3/#4/#6/#8 before writing a `DECISIONS.md` scaffold?