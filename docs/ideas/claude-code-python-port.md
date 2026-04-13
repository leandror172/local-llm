# Claude Code Source & Related Repos

**Noted:** 2026-04-09  
**Local clones:** `~/workspaces/clones/`

---

## Repo 1: claude-code (leaked TS source)

**How it leaked:** Source maps were accidentally included in the npm package (Bun default
behavior). The `.map` files embed full original source under `sourcesContent`. Discovered
2026-03-31 by @Fried_rice on X.

**Clone:** `~/workspaces/clones/claude-code/`  
**Also see:** `~/workspaces/clones/claude-code-sourcemap/` (raw v0.2.8 with maps; fork →
dnakov/anon-kode community reimplementation)

### Architecture (src/ structure)
```
QueryEngine.ts          # Core LLM logic — tool dispatch lives here
Tool.ts                 # Base tool definitions
tools/                  # 40+ tools: BashTool, FileReadTool, GrepTool, AgentTool, MCPTool, SkillTool...
coordinator/            # Multi-agent orchestration (Swarm pattern)
services/
  mcp/                  # MCP client: MCPConnectionManager, client.ts, normalization.ts, config.ts
  autoDream/            # Background memory consolidation (autoDream.ts, consolidationPrompt.ts)
  extractMemories/      # Memory extraction from session logs
  SessionMemory/        # Active session memory management
  compact/              # Context compression
  memdir/               # Memory directory management
bridge/                 # IDE integration layer
buddy/                  # Tamagotchi companion system (PRNG-seeded, 18 species)
```

### Key Systems

**autoDream** — background subagent that runs periodically:
1. Orient: read `MEMORY.md`
2. Gather: find new signals from daily logs
3. Consolidate: update durable memory files
4. Prune: keep context efficient

This is exactly what our session-handoff skill does manually. autoDream is the automated
version. The `consolidationPrompt.ts` file contains the prompt — worth reading for improving
our own memory consolidation quality.

**KAIROS** — "always-on" proactive assistant watching logs and acting without input.
This is the hook-based auto-resume idea on our deferred list, at a more sophisticated level.

**ULTRAPLAN** — offloads to a remote Opus 4.6 session for up to 30min of deep planning.
Relevant to our ULTRAPLAN-equivalent concept for long-running agent tasks.

### Most Actionable File: `services/mcp/normalization.ts`
Claude Code normalizes MCP tool responses before they reach the prompt. Reading this file
would reveal exactly what format Claude Code expects, letting us optimize how `ollama-bridge`
formats its tool return values. Currently our format choices are based on observation.

**When to read:** Before any MCP server refactor or when debugging "Claude ignores tool output" issues.

---

## Repo 2: open-multi-agent

**Clone:** `~/workspaces/clones/open-multi-agent/`  
**GitHub:** https://github.com/JackChen-me/open-multi-agent  
**License:** MIT | **Runtime deps:** 3 (`@anthropic-ai/sdk`, `openai`, `zod`)

### What It Is
TypeScript multi-agent orchestration framework. One `runTeam(team, goal)` call
auto-decomposes into a task DAG, resolves dependencies, runs agents in parallel.

### Architecture
- `orchestrator/` — task DAG, dependency resolution, parallel execution
- `agent/` — AgentRunner: conversation loop + tool dispatch
- `llm/` — LLMAdapter: AnthropicAdapter, OpenAIAdapter, GeminiAdapter, GrokAdapter
- `tool/` — ToolRegistry: 5 built-in tools (bash, file_read, file_write, file_edit, grep)
- `team/` — Team: MessageBus + SharedMemory
- `memory/` — shared memory across agents

### Local Model Integration (key pattern)
```typescript
// Any local model: provider='openai' + baseURL
const localAgent: AgentConfig = {
  model: 'qwen3:8b',
  provider: 'openai',
  baseURL: 'http://localhost:11434/v1',  // Ollama OpenAI-compat endpoint
  apiKey: 'ollama',  // required by SDK, ignored by Ollama
  timeoutMs: 120_000,
}
```

**Verified tool-calling:** Gemma 4, Llama 3.1, Qwen 3, Mistral, Phi-4.  
**Fallback:** If local model returns tool calls as text (not `tool_calls` wire format),
framework auto-extracts them — handles thinking models and misconfigured servers.

### Most Useful Pattern for This Project

**Example 06** — Claude writes code, local model reviews (no tool-calling required for reviewer):
```
Task 1 (Claude): write code → Task 2 (local Ollama): review it using file_read
```
This works without the local model needing native tool-calling, because `file_read` is
provided by the framework and the model just needs to ask for it.

This maps directly to our Layer 5 workflow: Claude architects, local model generates
boilerplate, another local model reviews.

### Relevance to This Project

| Feature | Relevance |
|---------|-----------|
| `runTeam(goal)` → auto DAG | Web-research multi-agent vision (session 44) |
| Ollama `baseURL` integration | Direct drop-in with our local models |
| `onTrace` observability | Feeds our DPO/evaluation pipeline |
| Lifecycle hooks | Verdict protocol hook point |
| Structured output (Zod) | Replaces our manual `format` param usage |
| Loop detection | Safety for longer-running local agent tasks |

### When to Use
Defer until Phase 2 of web-research tool (multi-agent execution). For current work
(chatbot, expense classifier), the MCP bridge pattern is sufficient. open-multi-agent
becomes relevant when we need parallel agent execution with dependency graphs.

---

## Gemma 3 / 4 Model Notes (researched same session)

**Available on Ollama:** `gemma3:4b`, `gemma3:12b`, `gemma3:27b`  
**GGUF source:** bartowski on HF (`bartowski/google_gemma-3-*-it-GGUF`)  
**QAT variants:** `google_gemma-3-12b-it-qat` and `google_gemma-3-27b-it-qat` — Quantization-Aware
Training: model trained with quantization noise built in → Q4 quality approaches Q8 standard PTQ.

**Gemma 4 31B** released 2026-04-02. Multimodal. Likely ~19GB. Too fresh + tight memory fit.
Check Ollama tag availability in ~4 weeks.

**Priority benchmark:** `gemma3:12b` vs `my-go-q25c14` on coding tasks. See `ref:model-selection`.

---

## RAM + VRAM Hybrid (clarified same session)

Ollama already supports hybrid offloading. Key insight: **dense partial offload > MoE partial offload**
for the same total model size:
- MoE (30B-A3B, 19GB): 10-20 tok/s due to sparse routing synchronization overhead
- Dense 27B spilling 4-6GB to RAM: estimated ~20-25 tok/s (bandwidth-limited but no routing overhead)
- Formula: PCIe + DDR bandwidth (~40-80 GB/s) << VRAM bandwidth (~360 GB/s) — spillover layers pay this cost
