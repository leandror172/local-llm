# llm/ — Knowledge (Semantic Memory)

*Repo-wide accumulated decisions. Read on demand by agents and chatbot.*

## VRAM Budget Constraints (2026-02, updated 2026-06-30)

All architecture decisions are shaped by 12GB VRAM on an RTX 3060.
7-8B models fit fully in VRAM with generous context (32K tokens).
14B models fit at 32K context with `OLLAMA_KV_CACHE_TYPE=q8_0` (probed 2026-05-30; exception: deepseek-coder-v2:16b at 24K — tight at 32K).
30B MoE models (Qwen3-30B-A3B) run hybrid VRAM+RAM at ~10-20 tok/s.
Dense partial offload: a 27B dense model spilling 5GB to RAM runs at ~3.2 tok/s —
slower than 30B MoE because dense models pay PCIe bandwidth on every layer; MoE
only activates ~3B params per token so fewer layers cross the bus.

**Rationale:** Consumer GPU is the constraint, not a limitation — it forces
discipline in prompt design, model selection, and context management that
would be invisible with unlimited compute.
**Implication:** Every feature must answer "does this fit in 12GB?" before
architecture discussion begins. Hybrid VRAM+RAM is viable only for MoE
architectures; dense models must fit fully in VRAM to be practical.

**Host-RAM budget — the second constraint (2026-06-30, diagnosed in llm repo):**
For models that partially offload, host RAM is a *separate* ceiling from VRAM.
The Ollama model store lives on `/mnt/i` (a `9p`/drvfs Windows mount), where
Ollama cannot mmap blobs → it sets `UseMmap:false` → it reads the **entire**
model blob into host RAM rather than paging from disk. `my-go-qcoder`
(qwen3-coder:30b, 19.3 GiB footprint, ~29/49 layers offloaded to CPU) therefore
needs ~12 GiB of *host* RAM at load. WSL2 defaulted to 15.5 GiB total (~11 GiB
free) → ENOMEM → `panic: cannot allocate memory` → runner `exit status 2` →
**HTTP 500 on load**. This was repeatedly mis-logged as "VRAM contention" across
~6 expense-repo sessions; the real signature is `cannot allocate memory` in the
Ollama server log, not a CUDA OOM.
- **Mitigation (2026-06-30):** raised WSL `.wslconfig` `memory=24GB` (host has
  31.7 GiB physical). Apply via `wsl --shutdown`.
- **Why the 14B fallback always works:** `my-go-q25c14` (~9 GB) fits almost
  entirely in VRAM, so even with mmap off the host read is small.

**CORRECTION (T-67 executed, session 98):** moving the store to a dedicated ext4
vhdx (on I:, attached via `wsl --mount --vhd`) did **NOT** re-enable mmap. Ollama
forces `UseMmap:false` whenever a model is **partially offloaded** (some layers
GPU, some CPU) — it's a loader constraint, independent of filesystem. So 9p was
*a* cause of no-mmap but not *the* cause; ext4 keeps mmap off too, and the
~10–15 GiB host-RAM read remains. **The `.wslconfig memory=24GB` cap stays
load-bearing.** What ext4 *did* buy: cold load **33 s → ~15 s** (and ~10 s
cache-warm) from removing the 9p read tax + page-cache reuse, plus a clean store
free of 9p quirks. Net: the move is a latency/robustness win, NOT a RAM fix.
Store now at `/mnt/ollama-store/models` (ext4); old `/mnt/i/ollama-models` kept
as rollback. NB: under WSL2+systemd the mount lives in PID 1's namespace —
invisible to interactive shells (`findmnt` shows nothing); verify via
`make -C ~/workspaces ollama-store-check` (systemd+API based).

## Model Tier Findings (2026-02 through 2026-04)

8B models: 63-67 tok/s, reliable up to ~400 output tokens, good for boilerplate.
14B models: 32 tok/s, reliable up to ~800 output tokens, better reasoning.
Key insight: prompt complexity has a hard ceiling per model tier. Beyond that,
both timeout and logic errors co-occur. The fix is prompt decomposition, not
retries or larger context windows.

**gemma3:12b (2026-04-09):** ~31 tok/s, 1 (improved) tier on Go + Python — 3-4× faster than
qwen2.5-coder:14b (8 tok/s) with comparable quality. Same 1 (improved) verdict on all 3
benchmark prompts. Best use: iterative tasks where speed matters more than one-shot accuracy.
**gemma3:27b (2026-04-09):** 3.2 tok/s, timeouts on all coding tasks (even warm, even
on shorter prompts). Dense 27B at 5GB RAM spillover is slower than 30B-A3B MoE — dense
partial offload costs more PCIe bandwidth per forward pass than MoE sparse routing.

**Rationale:** Discovered empirically through benchmark runs, not from documentation.
**Implication:** Model selection is task-driven (8B for boilerplate, gemma3:12b for speed,
14B for reasoning, frontier for judgment), not "always use the biggest."

## Prompt Decomposition (2026-02)

Multi-stage prompts where each stage's output feeds the next work better than
single large prompts. Empirically validated sweet spot: 3 stages.
Example: Stage 1 generates HTML structure, Stage 2 adds animation, Stage 3 refines.

**Rationale:** Keeps each prompt within the model's reliable output budget.
**Implication:** Complex tasks should be decomposed before attempting, not retried
with bigger context.

## Cross-Repo Architecture (2026-02 through present)

Three interconnected repositories share one hardware platform:
1. **llm** (this repo) — AI platform: MCP server, personas, benchmarks, evaluator, overlays
2. **expenses** — Go CLI for expense classification using local LLM inference
3. **web-research** — Python extraction + search pipeline with DDD agent architecture

The MCP bridge server (this repo) is the integration layer — Claude Code in any repo
can delegate to local models through the same interface. Overlays provide cross-repo
consistency (ref-indexing, session tracking, local model conventions).

**Rationale:** Separation by domain (platform vs. application vs. research tool),
not by technology.
**Implication:** Changes to the MCP server affect all downstream repos. Overlays
must be backward-compatible.

## DPO Data Collection Strategy (2026-03)

Every local model call is logged to JSONL (prompt, response, model, latency, token counts;
plus `call_id` + `tool` since 2026-07-21). Human verdicts (0/1/2) are recorded **for the
judgeable subset** — `generate_code`/`ask_ollama` per-call and oficina per-RUN — as separate
typed records joined on `call_id`. The evaluator framework adds automated quality scores
(Phase 1) and LLM judge scores (Phase 2). Together these form DPO training triples:
(prompt, response, quality_signal).

**Rationale:** Fine-tuning requires labeled preference data. Collecting it passively
during normal work avoids the cost of dedicated annotation.

**MEASURED REALITY, not the design intent (T-105, 2026-07-21 — do not restate the
aspiration as fact):** coverage is **18.7% (106 verdicts / 566 calls)**, not 100%.
For five months the capture parser accepted only a `[VERDICT …]` block that no durable
doc taught, so judgments written in the documented prose form were silently discarded —
repaired in PR #80, which recovered 48 of them (9.6% → 18.7%). The format defect explains
the *minority* of the gap: **~81% of calls carry no judgment in any form**, which is
behavioural, and the enforcement gate is deliberately deferred (Phase 6). Coverage
*among judgeable calls only* is not yet computable — the `tool` field that would make it
so is prospective (1 of 566 records carried it at repair time).
**Corpus today: 106 labeled triples. No fine-tuning has been run.**
Findings: `docs/findings/verdict-coverage-collapse-2026-07-21.md`.

**Implication:** Coding tasks that use local models produce training data as a byproduct
**only when the session actually records the verdict block** — the pipeline is opt-in per
call, and its historical yield is roughly one in five.

## Local-First with Frontier Escalation (2026-02)

Default to local models for code generation, classification, summarization.
Escalate to Claude (frontier) for architectural decisions, multi-file reasoning,
security-sensitive code, and evaluation judgment.

**Rationale:** Local inference is free after hardware cost. Frontier inference
costs per token. But frontier quality is needed for tasks where errors compound.
**Implication:** The MCP server exists to make this delegation seamless — Claude Code
calls a tool, local model responds, Claude evaluates the result.

## Claude Code Source + Related Repos (2026-04)

Three repos cloned to `~/workspaces/clones/` after Claude Code source leaked via npm sourcemap:
- **claude-code/** — full TS source (785KB main.tsx, 40+ tools, coordinator/, services/)
- **claude-code-sourcemap/** — raw v0.2.8 with maps; community fork → dnakov/anon-kode
- **open-multi-agent/** — MIT TypeScript multi-agent framework (3 runtime deps)

**Key files to read before MCP server refactor:**
- `claude-code/src/services/mcp/normalization.ts` — how Claude Code normalizes MCP tool
  responses before they reach the prompt; informs optimal MCP response format
- `claude-code/src/services/autoDream/consolidationPrompt.ts` — the exact prompt driving
  automated memory consolidation (autoDream = our session-handoff, automated)

**open-multi-agent integration pattern:**
```typescript
const localAgent = { provider: 'openai', baseURL: 'http://localhost:11434/v1', apiKey: 'ollama' }
```
Verified tool-calling: Gemma 4, Llama 3.1, Qwen 3. Falls back to text extraction if model
returns tool calls as text (handles thinking-mode models). Relevant for web-research multi-agent phase.

**Full notes:** `docs/ideas/claude-code-python-port.md`

**Rationale:** Understanding Claude Code internals lets us align MCP tool response formats
with how the host actually consumes them, rather than guessing from observed behavior.
**Implication:** Read `normalization.ts` before any MCP server refactor. Read
`consolidationPrompt.ts` before improving session-handoff memory quality.

## Smart RAG / Content-Linking Research (2026-04-13, session 51)

Investigation into retrieval techniques beyond keyword/vector RAG — triggered by wanting
career chatbot, Claude Code, web-research, and llm repo to note relations across all content
without blowing up context. 7 sources reviewed (see `ref:smart-rag-research`).

**Five philosophies identified:**
1. **Pre-compile into interlinked wiki** (Karpathy llm-wiki v1+v2) — highest relevance; v2
   adds typed knowledge graph + hybrid search (BM25+vector+graph). Maps cleanly to our
   "prepared artifact before HF push" constraint.
2. **Graph-first via wikilinks** (obsidian-mind) — validates exploiting our existing
   `ref:KEY` + `.memories/` graph instead of building a new one.
3. **Code-graph + git co-change** (repowise) — biggest genuinely new idea: files that
   change together without importing each other is an edge type static analysis misses.
4. **Hybrid observation store** (claude-mem) — steal the pattern (FTS over calls.jsonl),
   don't install it (conflicts with session-log + autoDream).
5. **Hierarchical spatial memory** (MemPalace) — 34% recall gain from scoping alone
   validates `.memories/` per-folder convention.

**Cross-cutting patterns (3+ sources):**
- Hybrid = BM25 + vectors + graph (table stakes)
- Pre-compile once, query many
- Exploit existing graph structure (our `ref:KEY` system is the seed)
- Hierarchical scoping beats smarter embeddings
- Filter-before-fetch via IDs (critical for Opus context discipline)
- Supersession / contradiction tracking (addresses stale-memory problem)
- Git co-change edges (scoped to code repos)

**Architectural direction (refined from prior conversation):**
```
raw sources → LLM-authored wiki (pre-compile)
            → indexed wiki (hybrid + graph from refs/links/co-change)
            → retriever (MCP tool + HTTP endpoint)
            → consumers: chatbot, Claude Code, web-research Dispatcher
```
One wiki per domain (profile, llm, web-research, expense), one federating retriever.
Chatbot = static artifact; Claude Code = live MCP service; same artifacts underneath.

**Rationale:** Off-the-shelf RAG (Dify) fails the content-linking problem; we have
infrastructure (`ref:KEY`, `.memories/`, ollama-bridge, evaluator, overlay system) to
build minimum-viable from primitives at <500 lines of Python.
**Implication:** Phase 3 chatbot work and Layer 7 RAG (task 7.11) converge on this
substrate. Build once in llm repo, consume from everywhere via federation layer.
Full file-by-file notes: `docs/research/smart-rag-*.md` (ref keys `rag-*`).

## Latent Topic Graph — Concept + Plan (2026-04-13, session 51)

Synthesis of the smart-rag research into a named construct: **Latent Topic Graph (LTG)**.

**The construct:** retrieval substrate where **topic nodes** (extracted by LLM, possibly
non-contiguous within a file) are primary, **files are containers not nodes**, edges are
embedding-space weighted, and hand-curated `ref:KEY` structures become first-class anchor
nodes with confidence 1.0 while LLM-inferred edges carry model-derived confidence. File-to-
file relationships are derived aggregates, not direct edges.

**Distinguishing properties:**
1. Topic-level abstraction (not entity-level like GraphRAG, not chunk-level like vector RAG)
2. Non-contiguous topic recognition (a topic = "what this is about," not "what's contiguous")
3. Files as containers — drops the vertical/horizontal relationship distinction in favor of
   pure topic-to-topic with containers as metadata
4. Anchor stratification — hand-curated edges preserved with provenance, LLM edges traceable
5. Derived structure rebalances on content change (raw embeddings do not) — salience,
   rankings, and community assignments shift; the underlying vectors stay fixed
6. Multi-scale via community detection at multiple resolutions

**Cognitive framing (distinctive):** files are a crude physical-world storage container;
a topic graph is a closer model of how knowledge actually holds together in the mind. The
framing is what makes the concept potentially publishable rather than just pragmatic.

**Relation to plan-v2:** LTG is Layer 7 task 7.11 **promoted** from vanilla RAG to a cross-
cutting substrate consumed by Layers 3, 4, 7, 8, 9 + career chatbot Phase 3. Executes in
parallel with Layers 5/6, does not block them.

**Concept paper:** `ref:concept-latent-topic-graph` (`docs/research/latent-topic-graph.md`)
— model-agnostic, publishable-grade idea note.
**Implementation plan:** 10 phases (0–9); acceptance test is the `relate(file_a, file_b)`
pairwise query returning specific verifiable answers. **Moved (T-33 split, session 107):**
the plan and all engine knowledge now live in the sibling `latent-topic-graph` repo
(`docs/plans/2026-04-13-latent-topic-graph-implementation.md` there); llm keeps the
instance at `ltg/` and the split record at `docs/plans/ltg-repo-split.md`.

**Rationale:** The research cluster showed that off-the-shelf RAG falls short on content-
relation queries; existing infrastructure (`ref:KEY` as seed graph, `.memories/` as tier-0,
ollama-bridge + local models for free extraction passes, evaluator for scoring) covers
most of what's needed; the novel combination (topic-level + non-contiguous + files-as-
containers + anchor stratification) is a step beyond GraphRAG.
**Implication:** Next session executes Phase 0 + 1 of the plan. Do not skip Phase 0
decisions. Phase 1 topic-extraction quality is load-bearing for everything else.

## LTG Phase 1 Extractor Spike — Findings (2026-04, sessions 54-58)

Topic-extractor A/B across 4 models × 8 corpus files, 11-dim rubric (dims 5-8 manual).
Weighted quality = `0.35·dim5 + 0.35·dim6 + 0.20·dim7 + 0.10·dim8`, exit threshold ≥ 2.2.

**Final results (8/8 files scored, Claude draft + user HTML-viz reconciled — session 58, Branch C):**

| Model | Raw (Claude) | Raw (User) | Speed pen. | Adj. (Claude) | Adj. (User) | Pass |
|---|---|---|---|---|---|---|
| qwen3:14b         | 2.69 | 2.86 | −0.25 | **2.44** | **2.61** | ✅ |
| qwen3:8b          | 2.27 | 2.63 | 0     | **2.27** | **2.63** | ✅ |
| qwen2.5-coder:14b | 2.01 | 2.41 | −0.25 | **1.76** | **2.16** | ❌ (borderline under user) |
| gemma3:12b        | 1.61 | 1.82 | −0.25 | **1.61** | **1.82** | ❌ |

Speed penalty: −0.25 if model runs <15 tok/s. Both rater tracks produce identical ranking + identical pass/fail. User track is systematically more lenient (Δ_avg +0.17 to +0.40 weighted-quality points) but does not change any binary verdict. Full findings: `ref:ltg-phase1-results`.

**Production routing (Branch C, session 58):** 2-arm specialized — `qwen2.5-coder:14b` for code files, `qwen3:14b` for prose files. Cross-reference-index 3rd-arm hypothesis (qwen3:8b candidate) deferred to Phase 2 pending determinism re-run + MoE eval; the qwen3:8b > qwen3:14b flip on `smart-rag-index.md` survived only in the Claude draft, not the user track. See `ref:ltg-phase1-routing-hypothesis`.

**Key insights:**
- Whole-section drops under topic-budget pressure (dim 8 catches) — both sub-optimal models silently omitted a section rather than merging
- Hierarchical containment (child ⊆ parent span) is a feature (supports LTG multi-scale); crossed partial overlap is the bug — mechanical check: `intersection == smaller_span`
- qwen2.5-coder:14b has a striking prose/code split: off-by-one on prose, tight boundaries on code → motivates 2-arm routing
- Two-rater reconciliation: rubric is fit-for-purpose for **binary** decisions (ranking + pass/fail robust across raters); absolute scores diverge by ~0.2–0.4 across raters, so reuse as a continuous quality metric (e.g., DPO scoring at Layer 7) would need calibration first

**Viz tooling pattern (`retrieval/viz_sweep.py` + `retrieval/ltg-rater.template.html`):**
- Template-based rendering: `build_html()` reads `ltg-rater.template.html` from disk, replaces three tokens
- DATA token must inject an **envelope**, not a bare array: `{tag, weights, exit_threshold, data: [...]}`
- SOURCES token is a bare map: `{filepath: content}` (accessed as `SOURCES[path]`)
- Scores persist in browser `localStorage` keyed by `sweep-scores-<TAG>`; export as markdown rubric

**Rationale:** Extractor quality is load-bearing for all downstream LTG phases — bad extraction means bad graph edges and bad retrieval. The spike gates Phase 2 VRAM co-residence probe.
**Implication:** Do not freeze extractor choice until all 8 files scored + two-rater reconciliation (Claude draft vs user HTML-viz scores). qwen3:14b is the provisional winner; qwen3:8b is viable backup (4× faster, same threshold).

## Ollama Monitoring Stack (2026-05-30, session 76)

Prometheus + Grafana monitoring via the NorskHelsenett/ollama-metrics transparent proxy.

**Architecture decision — port-swap over client reconfigure:** Moving Ollama to `:11435`
(one systemd env var) avoids touching the MCP bridge, benchmarks, Aider, and Claude Code
tool configs across three repos. Proxy takes `:11434`, all clients unaffected.

**WSL2 networking gotcha:** `host.docker.internal` in Docker Desktop resolves to the
Windows host IP, not the WSL2 instance. Fix: `extra_hosts: ["host.docker.internal:host-gateway"]`
on the Prometheus service — `host-gateway` resolves dynamically to the bridge gateway at start,
surviving network recreation. Do NOT hardcode the gateway IP (shifts with Docker network creation order).

**node-exporter removed:** Known `/sys` mount compatibility issues in WSL2 make it
unreliable. CPU/MEM panels in the pre-built dashboard are empty as a result; all
Ollama-specific panels (token rates, latency, model memory) work correctly.

**Native `/metrics` watch:** PR #11159 (OTel-based, per-model labels) is the long-term
replacement. When merged, the port-swap proxy becomes unnecessary.

**Rationale:** No native Prometheus endpoint in Ollama (issue #3144, open since 2024).
Proxy pattern is the only option without modifying Ollama itself.
**How to apply:** `make proxy && make stack` in `~/workspaces/clones/ollama-metrics`.
Full setup details: `ref:ollama-monitoring`.

## Structured Output via Grammar-Constrained Decoding (2026-02)

Always use Ollama's `format` parameter for JSON output — 100% reliable, no speed penalty.
This constrains the model's token generation to valid JSON matching a schema.
Never rely on prompt instructions alone for structured output.

**Rationale:** Prompt-only JSON extraction fails 10-30% of the time at 7-8B tier.
Grammar-constrained decoding makes it deterministic.
**Implication:** Every tool that needs structured output uses `format` param, not
post-processing or retry loops.

## Model Landscape Update (2026-05-26, session 68)

Comprehensive model survey covering Qwen, Microsoft, Llama 4, Mistral, frontier-distilled models, and embedding models. Full findings: `docs/findings/model-updates-2026-05.md`.

**Claimed supersessions (gated on local benchmark — not yet confirmed):**
- `qwen2.5-coder:14b` → `qwen3.6-coder:14b` (HumanEval ~85%→~88%, LiveCodeBench ~55%→~62% — **from secondary sources, not independently verified**; swap gated on M-P0a local benchmark; keep both until confirmed. Ollama: `qwen3.6-coder:14b` — tag unverified)
- `bge-m3` → `qwen3-embedding:8b` (MTEB 63.0→70.58, +7.5pts, ~5GB VRAM, on Ollama — MTEB numbers independently verifiable via HF leaderboard; **VRAM co-residence probe is a hard gate** before LTG Phase 2 embed.py; bge-m3 used 0.6GB vs ~5GB for this model)

**What has NOT changed:**
- `qwen3:14b` — still SOTA for reasoning at ≤14B (no model has surpassed it)
- `qwen3:4b-q8_0` — still best classifier/router at its tier
- `deepseek-r1:14b` — still the best validated reasoning-distilled model in 12GB VRAM

**New capability class — Llama 4 Scout (`llama4:scout`):**
- 10M token context window (no current model in our stack approaches this)
- Multimodal (text + image), ~10GB Q4, ~12–16 tok/s on RTX 3060
- Does NOT replace qwen3:14b for reasoning; adds a new long-context use case

**New tiny models (256K ctx, multimodal, Qwen3.5 family):**
- `qwen3.5:0.8b` (1GB), `qwen3.5:2b` (2.7GB) — can co-reside in VRAM alongside a 14B model
- First time a classifier and a 14B generation model can be simultaneously warm in 12GB
- `phi4-mini` (3.8B, 2.3GB) — Microsoft, strong reasoning per parameter, on Ollama

**Frontier-distilled models:**
- `deepseek-r1:14b` (already in setup) IS a distilled model — distilled from DeepSeek-R1's reasoning traces
- Community Claude-distilled models exist (`Jackrong/Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled`) but: no verified benchmarks, Anthropic ToS gray area, no Ollama tag — watch, don't pull yet
- TeichAI org (102 models) distills from Claude/GPT-5.2/Gemini — same caveats

**LTG Phase 2 outcomes (all resolved):**
- `qwen3-embedding:8b` adopted (session 73, M-P0b) — WARN verdict, sequential constraint unchanged → `ref:ltg-m-p0b-probe`
- VRAM co-residence probe with qwen3:14b complete — load-time eviction only, zero query-time evictions
- M-P0a closed NO SWAP (session 74) — `qwen3.6-coder:14b` is a phantom tag on Ollama; `qwen2.5-coder:14b` remains primary coder
- LTG Phase 2 complete (session 72) — 69 topics, 8 files, 7/8 acceptance pass → `ref:ltg-phase2-findings`

**Rationale:** Qwen3.6-Coder was released April 2026; qwen3-embedding:8b released alongside it. Both are now production-stable on Ollama. The survey was triggered by a user question about model updates.
**Implication:** All P0 swaps resolved. Phase 3 anchor decisions FROZEN (session 82 — dual-path RAG + alias-link). Full benchmark outcomes in `docs/findings/model-updates-2026-05.md`.

## Career Chatbot RAG Context Budget + Heading-Vocabulary Contract (2026-07-01, session 99)

The HF Space free backend (Llama 3.3 70B via Groq router) has a **12K tokens-per-minute
budget counting input + max_tokens across ALL calls in the minute** (routing + answer).
Groq reports overruns as `413 Payload Too Large` — it is a rate limit, not a message-size
limit; a single request over the budget is unretryable.

**Three-cap budget design in `docs/portfolio/hf-space/app.py` (all env-tunable on the Space):**
- Static baseline: only the 3 root quick files injected (3,000 chars each); all other
  `*-quick.md` sections live in the routed index. `CONTEXT_CHAR_BUDGET` (default 20,000)
  drops whole files largest-first with a startup warning.
- Routing index: **headings-only** (per-section snippets would cost ~7.6K tokens).
- History: `HISTORY_CHAR_BUDGET` (default 3,000 chars) — newest whole messages kept.
Worst case ≈ 11.9K vs 12K; transient clips absorbed by retry (incl. Groq's `NNms` waits).

**Heading-vocabulary contract (load-bearing for ALL `.memories/` authors):** because the
router only sees section headings, `##` headings must carry the query vocabulary a
visitor would use (RAG, embedding, vector store, project names) — insider headings like
"Phase 2 — Results" are invisible to retrieval. Proven live: "work on RAG?" matched 0
LTG sections before the `retrieval/.memories/` heading rename, 4/4 after.

**Warning (T-67 scope):** this repo's own QUICK.md files are over the ~30-line Tier-0
contract — root 7.8K chars (chatbot truncates root quick files at 3K: **bottom ~60%
never reaches the model**), retrieval/ 7.5K. Consolidate in the T-67 session alongside
the handoff-skill fix (same episodic-append root cause as the expenses audit,
`~/workspaces/expenses/code/.claude/quick-memory-audit-2026-07-01.md`).
