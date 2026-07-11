# Coding-subagent prior art — web-research MCP findings

Research run: 2026-07-11, 12:15–13:01 (America/Sao_Paulo), via the local `web-research` MCP
server only (no WebSearch/WebFetch used, per task constraint). This is a comparison run against
a parallel agent using frontier web tools.

---

## Topic 1 — Embeddable coding-agent loops for local models

### Aider

- **License:** Apache 2.0 (confirmed via a secondary source; not stated on aider.chat's own
  landing/scripting pages).
- **Language:** Python.
- **Scripting/API:** Has both a CLI scripting mode and a Python entry point
  (`Coder.create()` / `Coder.init()` in `aider/coders/base_coder.py`), but aider's own docs
  state the Python API **"is not officially supported or documented"** and **may change without
  backward compatibility** between releases — i.e. not designed as a stable embeddable library.
- **Headless mode:** No-PTY headless mode exists, producing clean/parseable terminal output —
  usable in CI or from a wrapper process even without the informal Python API.
- **Architecture notes:** Git-first workflow (auto-commit + co-authored-by attribution),
  tree-sitter-based repo mapping for codebase context, model-agnostic via LiteLLM (100+
  providers, includes local/Ollama). No built-in sandboxing or containerized execution — it
  shells out directly; heavier dependency tree (~108 packages: LiteLLM, tree-sitter, NumPy,
  SciPy). Supports diff / whole-file / architect (planner+implementer two-model) edit formats.
- **Verdict for embedding:** Usable as a subprocess-driven CLI tool with structured/headless
  output; not a first-class embeddable library — the maintainers explicitly disclaim the Python
  API's stability.

### OpenHands (formerly OpenDevin)

- **License:** MIT (corroborated by 3 independent sources: SourceForge mirror, openhands.dev
  pricing page, and the GitHub repo's own license badge).
- **Language:** Python (backend/SDK), TypeScript/Node ≥22.12 (Agent Canvas frontend).
- **Scripting/API:** Ships an **official, embedding-first SDK** (`openhands.sdk`), unlike aider.
  Minimal example pulled directly from the SDK paper (arXiv 2511.03690):
  ```python
  from openhands.sdk import LLM, Conversation
  from openhands.tools.preset.default import get_default_agent
  llm = LLM(model="openhands/claude-sonnet-4-5-20250929", api_key="...")
  agent = get_default_agent(llm=llm)
  conversation = Conversation(agent=agent, workspace="/path/to/project")
  conversation.send_message("Write 3 facts about this project into FACTS.txt.")
  conversation.run()
  ```
  Swapping `workspace=` for a `DockerWorkspace(...)` moves execution into a sandbox with a
  one-line diff — `BaseWorkspace` is an ABC with `LocalWorkspace`/`RemoteWorkspace`
  implementations behind a `Workspace.__new__` factory.
- **Architecture notes (from the SDK paper):** `Action`/`Observation`/`ToolDefinition` schema
  objects convert to MCP tool format, OpenAI Chat-Completions tool format, and OpenAI Responses
  format — i.e. explicit, first-class MCP interoperability. Includes a `RouterLLM` abstraction
  for routing between models (e.g., cheap text model vs. multimodal model) inside one agent.
  Other engineering features: automatic secret detection/masking, stuck-loop detection,
  auto-generated conversation titles, dual-track testing (mocked LLM + real LLM CI runs).
- **Verdict for embedding:** The strongest "designed to be embedded" candidate of the three —
  explicit SDK, workspace abstraction for local vs. sandboxed execution, and MCP-native tool
  schema conversion. Heavier/more enterprise-oriented than aider or mini-swe-agent (separate
  Cloud/Enterprise/Agent-Canvas products sit on top of the open-source SDK).

### SWE-agent / mini-swe-agent (Princeton/Stanford, SWE-bench authors)

- **License:** mini-swe-agent confirmed **MIT** (GitHub license-badge parse). Full SWE-agent is
  the same org/lineage and almost certainly MIT too, but that specific repo's license was not
  independently confirmed by a fetched source in this run.
- **Language:** Python.
- **SWE-agent architecture** (from a detailed community deep-dive, corroborated by the repo
  structure): the central design thesis is the **Agent-Computer Interface (ACI)** — the agent
  is deliberately *not* given raw bash, but a small set of high-level tools defined as YAML
  manifests wrapping bash scripts (no Python plugin system, by design, for portability/
  inspectability): a **windowed file viewer**, an **edit+lint tool with rollback** (edits that
  fail linting are reverted), a **bounded search tool**, and a **submit tool** as the explicit
  "done" signal. The runtime/sandboxing layer was spun out into a separate library, **SWE-ReX**,
  supporting Docker/Singularity/local/remote execution with sentinel-based command-completion
  detection. The agent loop itself is reported as "the canonical 30 lines": read state → LLM
  call → parse action → execute via ACI tool → observe → loop. Termination has four explicit
  paths: task success, budget exhaustion (cost or turn count), a model-error "requery ladder"
  for recovering from malformed actions, and a deliberate **auto-submit-on-budget-exhaustion**
  pattern that treats running out of budget as a degraded success rather than a hard failure.
  Notably, the team **deliberately did not implement semantic "stuck" detection**.
- **mini-swe-agent architecture:** the minimal descendant — core agent loop is documented as
  **~100 lines of Python total**, with **no tool-calling API dependency at all**: actions are
  executed via plain `subprocess.run`, so it works with any LLM through litellm/openrouter/
  portkey and any bash-capable sandbox without needing structured tool-calling/function-calling
  support from the model. Despite the minimalism it's reported at **>74% on SWE-bench Verified**
  and is described as used by several organizations for benchmarking. Maintains a flat, linear
  history (useful for later fine-tuning/DPO-style data collection).
- **Verdict for embedding:** mini-swe-agent looks like the best fit for wrapping a **local
  7-14B Ollama model** in a generate→test→repair loop specifically *because* it has no
  tool-calling-schema dependency (many local models handle native function-calling poorly) and
  essentially zero framework overhead — it's closer to "a loop you could vendor" than "a
  framework you depend on."

---

## Topic 2 — MCP long-running task / async job patterns

- MCP has an official, currently **experimental/draft extension** for this: the **Tasks
  extension** (`modelcontextprotocol.io/extensions/tasks/overview`, spec/code in
  `github.com/modelcontextprotocol/experimental-ext-tasks`). Model: instead of a tool call
  blocking until completion, a server can return a **task handle**; the client polls (and/or
  receives optional notifications) for status among `working`, `input_required`, `completed`,
  `failed`, `cancelled`. The `input_required` status is the mechanism for mid-flight
  human-in-the-loop interaction (approval gates, additional input) inside a long task.
  Key stated properties: **no long-lived connection required** (avoids transport timeouts and
  gives crash resilience via durable task IDs — good over unreliable/mobile networks), and
  **cancellation is cooperative only** — a server is not obligated to actually stop work when
  asked to cancel. Both client and server must explicitly **opt in via capability negotiation**;
  host/client support for the extension currently varies (see the linked client-support matrix).
  Intended use cases per the spec: CI pipelines, batch processing, model training jobs,
  approval-gated workflows, and integration with external async job systems.
- This built on an earlier community design discussion (**GitHub Discussions #491**,
  "Asynchronous Operations in MCP"), which proposed a resource-based alternative: task status
  exposed as an MCP *resource* (`resource://tasks/{id}`), progress pushed via an `AsyncResource`
  class, and extensions to the `Tool`/`ResourceManager`/`ToolManager` classes — explicitly
  framed as transport-agnostic (compatible with Streamable HTTP) and as needing to be
  reconciled with MCP's pre-existing plain progress-notification mechanism. This discussion
  appears to be a direct ancestor of the shipped Tasks extension.
- A third-party analysis (WorkOS engineering blog, "MCP Async Tasks") walks through the same
  extension from an implementer's-checklist angle: durable task handles, progress reporting,
  full task lifecycle (create/cancel/complete), the `input_required` flag, completion/failure
  notifications — and flags **security considerations specific to async tasks** that the bare
  spec doesn't dwell on: task IDs are bearer-like handles to background work and must be
  protected/scoped per-caller, and a real implementation needs durable storage plus TTL and
  error-recovery handling for orphaned tasks.
- **Gap:** I could not find concrete, already-shipping **third-party MCP servers implementing a
  submit-then-poll job pattern** in production (3 separate query attempts returned zero usable
  results). Given the extension is explicitly labeled experimental, this may be a real adoption
  gap rather than a tool-search failure — but I can't rule out that the search tool's index
  simply doesn't reach GitHub code search / package registries well (see Operational appendix).

---

## Topic 3 — Test-feedback self-repair with 7-14B models

This is the weakest-covered topic; the literature located skews toward frontier-scale models,
and direct 7-14B convergence/iteration-count data was not found.

- **"Teaching Large Language Models to Self-Debug"** (Chen et al., arXiv 2304.05128): LLMs
  debug their own generated code using execution results plus a self-generated natural-language
  explanation, without human feedback; reports up to ~12% accuracy improvement on
  Spider/TransCoder/MBPP, and improves **sample efficiency** by reusing failed predictions
  rather than discarding them. The extraction (abstract page only — the full-text HTML URL
  404'd twice) could not surface model-size-specific numbers or a concrete iteration count for
  convergence.
- **"Self-Repair in Code Generation: A Large Language Model Perspective"** (2026 survey, arXiv
  2604.10508 — full text successfully extracted, 54k chars): frames the field as three
  paradigms — **Self-Refinement** (iterative correction from internal/tool feedback, e.g.
  linters), **Self-Collaboration** (multiple LLMs or human-in-the-loop cross-checking), and
  **Self-Adaptation** (learning from past errors over time). Reports, against Gemini 2.5 / Llama
  4-class models: 23% improvement in critical-bug resolution, 18% higher style/best-practice
  adherence, and 30% less repair time when feedback is prioritized (critical errors before style
  nits). Notes an explicit **exploration/exploitation trade-off** in how aggressively a repair
  loop should try novel strategies vs. proven fixes, and that repair effectiveness is sensitive
  to codebase complexity and initial-prompt clarity. All reported experiments are at
  frontier-model scale, not 7-14B.
- **SWE-Dev** (arXiv 2506.07636): a trained SWE agent evaluated on SWE-bench-Verified, reporting
  **23.4% success at 7B vs. 36.6% at 32B** parameters — a concrete, sourced capability gap
  between small and mid-size models on exactly the "generate, test, repair" task class the user
  cares about. The extraction could not confirm whether this is single-shot or multi-iteration
  performance, or whether a convergence-vs-iteration curve exists in the paper.
- **Indirect but relevant signal:** an EmergentMind summary touching on "Live-SWE-Agent"-adjacent
  work explicitly states that **"SLMs (small language models) without pretraining may fail to
  address complex code repair tasks,"** names Qwen-2.5/Llama-2/Gemma at 7B scale (with
  GGUF/AWQ quantization) as the small-model tier under test, and says **hybrid approaches
  (verifier-based inference)** are needed for robustness at that scale — i.e., the closest thing
  found to a direct answer suggests naive iterative self-repair does **not** reliably converge
  at 7B without extra scaffolding (a separate verifier, curriculum fine-tuning on something like
  SWE-Gym-Lite, or distillation from a larger teacher).
- **Bottom line (defensible claim only):** no source located gives a specific "N iterations is
  the sweet spot for 7-14B models" number. What's supported: (a) iterative self-repair
  measurably helps at frontier scale with diminishing/prioritizable returns per iteration, and
  (b) the thin small-model evidence available suggests convergence is not guaranteed at 7B
  without additional scaffolding — consistent with this repo's own existing local-model
  guardrails (CLAUDE.md already restricts local models to bounded tasks and requires explicit
  human verdict-scoring rather than trusting an unsupervised repair loop).

---

## Operational appendix — web-research tool experience

All calls used `mcp__web-research__search_topic`, `mcp__web-research__research_url`, and one
`mcp__web-research__query_knowledge`. Latencies below are the tool's own reported
`duration_seconds` per underlying page fetch+extraction (via a local Ollama `qwen3:14b`
extraction model), not round-trip including my own batching.

| # | Tool | Topic | Latency | Result | Quality note |
|---|------|-------|---------|--------|---------------|
| 1 | search_topic | Aider scripting/architecture | 2 iter, 3 pages, ~32-46s/page | success | Good coverage across 3 pages (docs, GitHub issue analysis, homepage); correctly surfaced Apache-2.0 license and the "Python API unsupported" caveat from a secondary source the homepage itself omitted. |
| 2 | search_topic | OpenHands architecture/license | 2 iter, 5 pages, ~26-43s/page | success, verdict "sufficient" | Best single call of the session — found the arXiv SDK paper (2511.03690) with real embedded code diffs (base64-encoded in the page, successfully decoded to readable Python), giving primary-source architecture detail no summary page would have. One page (OpenReview) was blocked by a bot-verification wall and returned near-empty content. |
| 3 | search_topic | SWE-agent/mini-swe-agent | 2 iter, 3 pages, ~34-48s/page | success | High-depth dev.to technical deep-dive (57k chars extracted) plus the official mini-swe-agent GitHub README with correctly parsed MIT license badge. |
| 4 | search_topic | MCP long-running tasks/async spec | 2 iter, 3 pages, ~36-43s/page | success | Excellent source authority: landed the *official* MCP spec extension page directly, plus the originating GitHub design discussion and a third-party implementer analysis (WorkOS). This is the strongest result of the whole run. |
| 5 | search_topic | MCP submit-poll job pattern (3rd-party servers) | 1 iter | **failure** — 0 results | No pages fetched at all; tool returned an empty result set with no diagnostic beyond "0 results found." |
| 6 | search_topic | small-model 7B/14B self-repair convergence | 1 iter | **failure** — 0 results | Same empty-result failure mode as #5. |
| 7 | search_topic | retry of #5 (reworded: "GitHub MCP server background jobs polling") | 1 iter | **failure** — 0 results | Reworded query, still zero results — suggests the underlying search backend (not just my phrasing) has no index hits, not a phrasing problem. |
| 8 | search_topic | retry of #6 (reworded: "self-debugging LLM code generation unit test feedback") | 1 iter | **failure** — 0 results | Same. |
| 9 | search_topic | 2nd retry of #6, further reworded | 1 iter, 1 page, 46s | technically succeeded, practically useless | Only hit was an OpenReview page blocked by bot-verification (357 chars, no content). 46s spent for zero usable information. |
| 10 | research_url | arXiv 2304.05128 abstract page | 26s | success but shallow | Correctly extracted the paper's high-level claim but abstract pages don't carry enough text for iteration/model-size specifics; tool's own self-assessed confidence was "medium." |
| 11 | research_url | arXiv 2506.07636 abstract page | 24s | success but shallow | Same limitation; self-assessed "low" relevance since the abstract doesn't discuss small-model convergence. |
| 12 | research_url | arXiv 2304.05128 **HTML** full text (manual URL) | fast | **failure** — HTTP 404 | Guessed the arXiv `/html/<id>` URL without a version suffix; wrong. |
| 13 | research_url | Same, with `v2` suffix | fast | **failure** — HTTP 404 | Guessed wrong version too; gave up after 2 tries per instructions. Contrast with #14, where `search_topic` itself found the correct fully-qualified HTML URL (with version) for a different paper and it worked — the fix here is to let search discover the URL rather than hand-constructing arXiv HTML links. |
| 14 | search_topic | "code LLM self-repair benchmark local models 7B" | 1 iter, 1 page, 40s | success, high quality | Found a full arXiv HTML paper (2604.10508, 54k chars) — a 2026 self-repair survey — via the tool's own search+URL-discovery rather than a guessed URL. Best per-call value-for-time of the failed-topic-3 recovery attempts. |
| 15 | query_knowledge | "self-repair small model iterations convergence" | instant | success (mechanically) but returned nothing | Returned `[]` even though, by this point, the knowledge store already held ~15 pages including one (EmergentMind) that literally contains the phrase "SLMs (small language models)... may fail to address complex code repair tasks." This strongly suggests `query_knowledge` does close-to-literal substring/keyword matching rather than semantic search — a real limitation for reusing prior research within a session. |

### Overall assessment

**Where web-research was adequate — even strong:** For topics with well-indexed, high-authority
primary sources (official docs sites, GitHub repos, arXiv papers with existing HTML renders),
`search_topic` reliably found and correctly extracted them, including decoding embedded
base64 code blocks and correctly parsing GitHub's UI-rendered license badges into a clean
`license` field. The auto-iterating research loop (search → extract → audit → follow-up query)
worked well for topics 1 and 2, needing no manual intervention.

**Where it fell short:**
1. **Narrow/compound queries return hard zero, not "fewer" results.** Topic 3's model-size-
   specific angle repeatedly returned literally zero fetched pages rather than degrading
   gracefully to loosely-related results — three independent rewordings all failed the same way,
   suggesting the underlying search index (not phrasing) is the bottleneck for less-mainstream
   queries.
2. **No bot-wall / paywall awareness.** Two calls spent 26-46s hitting OpenReview pages gated
   behind a client-side verification check, returning ~350 characters of boilerplate. The tool
   has no way to detect "this fetch produced no real content" ahead of time and skip/retry with
   an alternate source.
3. **No automatic URL-version resolution for arXiv-style HTML mirrors.** `research_url` takes
   whatever URL it's given at face value; when I hand-constructed an arXiv `/html/` URL without
   knowing the exact version suffix, it just 404'd instead of trying to resolve the canonical
   HTML link (which `search_topic`, using its own search step, found for a different paper).
4. **`query_knowledge` appears keyword/substring-based, not semantic**, so it under-recalls
   content already sitting in the local store — reducing its value as a within-session cache and
   forcing redundant re-search.
5. **Verdict/audit self-assessment is sometimes internally inconsistent** — several calls that
   fetched 3-5 good pages still reported `"reasoning": "Only 0 results found; below threshold"`
   in the verdict block, which doesn't match the `results` array actually returned. This looks
   like an auditor-vs-results bookkeeping bug rather than a real quality signal, and should not
   be trusted as-is to decide whether to stop or keep iterating.

**Concrete improvement suggestions:**
- Have `search_topic` fall back to broader/looser queries automatically when a query returns
  zero hits, rather than requiring the caller to guess rephrasings (which, per row 7/8 above,
  didn't help anyway).
- Detect low-content-yield fetches (very small `clean_chars`, verification/login-wall markers)
  and either retry with a different source URL from the same search or mark the result as
  low-confidence rather than returning it as if it were a normal success.
- Fix the verdict/auditor's result-count accounting so `"sufficient"`/`"reasoning"` reflects the
  actual `results` array length — right now it's not a reliable stopping signal.
- Make `query_knowledge` do at least lightweight semantic/fuzzy matching (or expose the raw
  extracted-page keyword list) so previously-fetched pages are actually reusable mid-session.
- For arXiv (and similarly structured) sources, canonicalize `/abs/` → `/html/<id>vN` internally
  rather than requiring the caller to guess the version suffix.
