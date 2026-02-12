# Layer 1 Research Archive

**Completed:** 2026-02-12 (Session 13)
**Task:** 1.1 — Research MCP server specification and Claude Code integration

---

## MCP Protocol Specification

**Version:** 2025-06-18 (latest stable)
**Spec:** [modelcontextprotocol.io](https://modelcontextprotocol.io)
**Protocol:** JSON-RPC 2.0 over transports

### Transports

| Transport | How | Best For |
|-----------|-----|----------|
| **stdio** | JSON-RPC over stdin/stdout (subprocess) | Local tools, Claude Code |
| **Streamable HTTP** | HTTP POST + optional SSE streaming | Remote/network servers |
| **SSE** | Server-Sent Events (deprecated) | Legacy only |

**For our use case:** stdio — Claude Code spawns the MCP server as a subprocess.

### MCP Primitives

| Primitive | Purpose | Example |
|-----------|---------|---------|
| **Tools** | Functions the LLM can call | `generate_code`, `summarize` |
| **Resources** | Data the LLM can read | File contents, DB records |
| **Prompts** | Reusable prompt templates | Code review template |

Tools are the primary primitive for Layer 1.

### Tool Registration

Tools declare: `name`, `description`, `inputSchema` (JSON Schema).
The AI host (Claude) sees descriptions and autonomously decides when to call each tool.

---

## Claude Code MCP Integration

### Configuration

| Method | Scope | File | Use Case |
|--------|-------|------|----------|
| `claude mcp add` | Local (default) | `~/.claude.json` | Private, current project |
| `.mcp.json` | Project | `.mcp.json` in repo root | Shared via git |
| `--scope user` | User | `~/.claude.json` | All projects |

**Important:** MCP config goes in `~/.claude.json` or `.mcp.json`, **NOT** in `settings.json` or `settings.local.json` (silently ignored!).

### Commands

```bash
# Add server (stdio transport)
claude mcp add --transport stdio <name> -- <command> [args...]

# Example for our server:
claude mcp add --transport stdio ollama-local -- python3 /path/to/server.py

# Management
claude mcp list                    # List configured servers
claude mcp get <name>              # Show server details
claude mcp remove <name>           # Remove server
/mcp                               # In-session status check
```

### Operational Limits

| Parameter | Default | Env Var |
|-----------|---------|---------|
| Timeout | 10 seconds | `MCP_TIMEOUT=10000` |
| Max output | 25K tokens | `MAX_MCP_OUTPUT_TOKENS` |
| Dynamic updates | Supported | `list_changed` notification |

### How Claude Decides to Use MCP Tools

Claude sees ALL tool descriptions at conversation start. It autonomously chooses when to call tools based on the user's request and tool descriptions. **Good descriptions are critical** — they're the routing mechanism.

---

## Language Decision

### Evaluated Options

| Language | SDK | Maturity | Startup | Deploy | Tool Friction |
|----------|-----|----------|---------|--------|---------------|
| **Python** | Official (`mcp[cli]`, FastMCP) | v1.x stable, most docs | ~300ms | Script + runtime | **Low** (~8 lines/tool) |
| **Go** | Official (Google-maintained) | v1.2.0+, 3.8k stars | ~5ms | Single binary | Medium (~25 lines/tool) |
| **Java** | Official (Spring AI team) | v0.17.2, still v0.x | ~1000ms | JAR + JDK 17+ | High (~35 lines/tool) |
| **Kotlin** | Official (JetBrains) | Newer | ~1000ms | JAR + JDK | Medium-High |
| **TypeScript** | Official, most documented | v1.x stable | ~200ms | Node.js runtime | Low |

### Decision: Python

**Chosen for these reasons:**
1. **Lowest tool-addition friction** — decorator + function + docstring = complete tool (docstring auto-generates schema)
2. **Richest ecosystem** for general-purpose tasks (PDF, scraping, data processing, NLP)
3. **Most MCP documentation** and community examples — local models can reference these
4. **Already in the environment** — Python 3.10+ in WSL2, benchmark framework already Python
5. **FastMCP pattern** is clean and Pythonic — fits the rapid prototyping needs

**Trade-offs accepted:**
- ~300ms startup (one-time per session, not per tool call — acceptable)
- GIL limits true parallelism (asyncio covers I/O-bound Ollama calls fine)
- Runtime dependency (Python 3.10+) vs Go's single binary

**Not chosen:**
- **TypeScript:** User preference against JS/TS ecosystem
- **Go:** Best runtime characteristics, but higher tool-addition friction; reconsidered for performance-critical components later
- **Java:** JVM startup too slow for stdio subprocess, SDK still v0.x
- **Kotlin:** Same JVM penalty, less familiarity

### FastMCP Minimal Pattern

```python
from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("ollama-local")

@mcp.tool()
async def generate_code(prompt: str, language: str = "go") -> str:
    """Generate code using local Ollama model.
    Args:
        prompt: The coding task to accomplish
        language: Target language (go, java, python)
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post("http://localhost:11434/api/chat", json={
            "model": "my-coder-q3",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False, "options": {"think": False},
        })
    return resp.json()["message"]["content"]

mcp.run(transport="stdio")
```

---

## Existing Tools Landscape

### Existing Ollama MCP Servers

| Project | Language | Direction | Stars | Notes |
|---------|----------|-----------|-------|-------|
| [rawveg/ollama-mcp](https://github.com/rawveg/ollama-mcp) | TypeScript | Generic API wrapper | — | 14 tools, `npx -y ollama-mcp`, stdio. Dumb passthrough. |
| [hyzhak/ollama-mcp-server](https://github.com/hyzhak/ollama-mcp-server) | TypeScript | OpenAI-compat chat | — | Actively maintained fork |
| [patruff/ollama-mcp-bridge](https://github.com/patruff/ollama-mcp-bridge) | TypeScript | Inverse bridge | — | Makes Ollama an MCP client (opposite direction) |
| [Sethuram2003/MCP-ollama_server](https://github.com/Sethuram2003/MCP-ollama_server) | Python | Tools FOR Ollama | 19 | Modular: files, calendar, web, email, GitHub. Apache 2.0. |
| [paolodalprato/ollama-mcp-server](https://lobehub.com/mcp/paolodalprato-ollama-mcp-server) | — | Ollama wrapper | — | Listed on LobeHub |

### Related Smart Routing / Orchestration Projects

| Project | Language | What It Does | Relevance | License |
|---------|----------|--------------|-----------|---------|
| [ultimate_mcp_server](https://github.com/Dicklesworthstone/ultimate_mcp_server) | Python 3.13+ | "AI agent OS" — browser, PDF, RAG, memory, multi-provider routing | **Patterns:** cognitive memory (working/episodic/semantic/procedural), caching, cost optimization | Check repo |
| [locallama-mcp](https://github.com/Heratiki/locallama-mcp) | TypeScript | Cost-optimized routing: local vs cloud | **Patterns:** decision engine, complexity analysis, cost thresholds | Check repo |
| [llm-use](https://github.com/llm-use/llm-use) | Python 3.10+ | Planner→Workers→Synthesis orchestrator with router | **Patterns:** learned routing (cosine similarity), heuristic fallback, Ollama workers | 29 stars |
| [MCP-ollama_server](https://github.com/Sethuram2003/MCP-ollama_server) | Python | Modular services for Ollama | **Patterns:** microservice modules, selective deployment | Apache 2.0 |

### Patterns Worth Borrowing

| Pattern | Source Project | Applicable Layer |
|---------|---------------|-----------------|
| Learned routing (cosine similarity on past tasks) | llm-use | Layer 2 (Smart Routing) |
| Planner → Workers → Synthesis flow | llm-use | Layer 4 (Orchestration) |
| Cognitive memory (working/episodic/semantic/procedural) | ultimate_mcp_server | Layer 7 (Memory) |
| Cost/complexity decision engine | locallama-mcp | Layer 2 (Smart Routing) |
| Modular capability services | MCP-ollama_server | Layer 1 (architecture) |

### Inverse-Direction Value

Projects that give tools TO local LLMs (MCP-ollama_server, patruff bridge) are still valuable:
- Layer 8+ (local LLM with cloud fallback) can use these
- More local tools = fewer tasks need cloud escalation
- The same MCP server can serve both directions if designed well

---

## MCP Server Discovery Resources

| Registry | URL | Notes |
|----------|-----|-------|
| mcp.so | [mcp.so](https://mcp.so/) | Community-driven, most comprehensive |
| mcpservers.org | [mcpservers.org](https://mcpservers.org/) | Curated with categories |
| awesome-mcp-servers | [GitHub (punkpeye)](https://github.com/punkpeye/awesome-mcp-servers) | Also: appcypher, wong2 forks |
| mcp-awesome.com | [mcp-awesome.com](https://mcp-awesome.com/) | 1200+ servers, quality-verified |
| mcpmarket.com | [mcpmarket.com](https://mcpmarket.com/) | Marketplace with categories |
| LobeHub MCP | [lobehub.com/mcp](https://lobehub.com/mcp/) | Lobe ecosystem integration |
| MCP official SDKs | [modelcontextprotocol.io/docs/sdk](https://modelcontextprotocol.io/docs/sdk) | 10 official SDKs |

---

## SDK Quick Reference (All Official)

| Language | Repo | Maintainer |
|----------|------|------------|
| TypeScript | [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) | Anthropic |
| Python | [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | Anthropic |
| Go | [modelcontextprotocol/go-sdk](https://github.com/modelcontextprotocol/go-sdk) | Google collab |
| Java | [modelcontextprotocol/java-sdk](https://github.com/modelcontextprotocol/java-sdk) | Spring AI team |
| Kotlin | [modelcontextprotocol/kotlin-sdk](https://github.com/modelcontextprotocol/kotlin-sdk) | JetBrains |
| C# | [modelcontextprotocol/csharp-sdk](https://github.com/modelcontextprotocol/csharp-sdk) | Microsoft collab |
| Swift | [modelcontextprotocol/swift-sdk](https://github.com/modelcontextprotocol/swift-sdk) | — |
| Ruby | [modelcontextprotocol/ruby-sdk](https://github.com/modelcontextprotocol/ruby-sdk) | — |
| Rust | [modelcontextprotocol/rust-sdk](https://github.com/modelcontextprotocol/rust-sdk) | — |
| PHP | [modelcontextprotocol/php-sdk](https://github.com/modelcontextprotocol/php-sdk) | PHP Foundation |
