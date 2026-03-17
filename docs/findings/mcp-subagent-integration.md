# MCP Server Integration in Subagents: Gap Analysis

**Date:** 2026-03-17
**Session:** 44 (explanatory mode)
**Context:** Investigated whether local Ollama models (via `ollama-bridge` MCP server) can be used in Claude Code subagents.

---

## Executive Summary

**Infrastructure Status:** ✅ Everything needed is already in place.
**Usability Status:** ⚠️ Underdocumented and unclear, requiring manual setup.

Subagents **can** use parent MCP servers, but the feature is:
- Not discoverable (no built-in server detection)
- Requires explicit per-subagent configuration
- Lacks working examples or templates
- Not mentioned in typical Claude Code documentation

---

## What's Configured

### Current Setup (in this workspace)

```json
// ~/.claude/.mcp.json
{
  "mcpServers": {
    "ollama-bridge": {
      "command": "/mnt/i/workspaces/llm/mcp-server/run-server.sh"
    }
  }
}
```

```json
// ~/.claude/settings.json (excerpt)
"permissions": {
  "allow": [
    "mcp__ollama-bridge__ask_ollama",
    "mcp__ollama-bridge__list_models",
    "mcp__ollama-bridge__generate_code",
    "mcp__ollama-bridge__classify_text",
    "mcp__ollama-bridge__summarize",
    "mcp__ollama-bridge__translate"
  ]
}
```

### How Subagent MCP Server Inheritance Works

Subagents **do NOT** automatically inherit parent session MCP servers. However, you can:

**Option 1: Reference by name (recommended)**
```yaml
---
name: ollama-worker
description: Uses local Ollama for analysis
mcpServers:
  - ollama-bridge  # References parent's configured server by name
---
You have access to local Ollama models...
```

**Option 2: Inline definition**
```yaml
---
name: isolated-processor
mcpServers:
  - ollama-bridge:
      type: stdio
      command: /mnt/i/workspaces/llm/mcp-server/run-server.sh
---
```

**Option 3: Mix references and inline**
```yaml
---
name: multi-tool
mcpServers:
  - ollama-bridge      # Reference
  - postgres:          # Inline
      type: stdio
      command: custom-postgres-server
---
```

---

## Identified Gaps

### 1. **No Discoverability**
- Users don't know which MCP servers are available when spawning a subagent
- No built-in mechanism to list configured servers for reference
- Must manually know the server name (`ollama-bridge`)

### 2. **No Working Examples**
- Claude Code documentation shows the syntax but no end-to-end example
- No templates for common patterns (Ollama + code, Ollama + analysis, etc.)
- Users must infer usage from documentation alone

### 3. **No Pre-baked Agent Templates**
- Common patterns like "local code generator with Ollama" aren't packaged
- Template location unclear: `~/.claude/agents/`, `.claude/agents/`, or inline?
- Requires users to understand both agent format AND MCP server syntax

### 4. **Subagent Tool Invocation Unclear**
- Even with `mcpServers` configured, it's not obvious how a subagent *invokes* those tools
- Should the subagent's prompt explicitly request `ask_ollama`?
- Or does the subagent automatically see them like other Claude Code tools?

### 5. **No Plugin/Subagent Hybrid Path**
- Plugin-based subagents (from marketplace) don't support `mcpServers` field
- Forces a choice: use plugins (no MCP access) OR use file-based agents (manual setup)

### 6. **No MCP Server Auto-load Option**
- Can't say "give this subagent access to ALL parent MCP servers"
- Must explicitly list each one by name, or re-inline each config

---

## What Would Improve Usability

### Short-term (Documentation)
1. **Example gallery** — 3-5 worked examples in Claude Code docs:
   - "Subagent with local Ollama code generation"
   - "Subagent with GitHub + Ollama analysis"
   - "Subagent with ollama-bridge tools only"

2. **Quick-start template** — `~/.claude/agents/templates/ollama-worker.md`
   ```yaml
   ---
   name: ollama-worker
   description: [template] Uses local Ollama for analysis via ollama-bridge
   mcpServers:
     - ollama-bridge
   ---
   ```

3. **Clear table** in docs:
   | Feature | Subagent | Main Session |
   |---------|----------|--------------|
   | Access parent MCP servers | By name only | All |
   | Reference vs inline | Both | Both |
   | Auto-discover servers | No | N/A |
   | Plugin support | No | N/A |

### Medium-term (Tooling)
1. **Agent creation wizard** — `/spawn-with-mcp` skill that:
   - Lists available parent MCP servers
   - Auto-generates agent YAML with selected servers
   - Offers pre-baked templates

2. **MCP discovery tool** — `claude mcp list` CLI command showing:
   - Server name, command, status
   - Available tools per server
   - Which subagents reference it

### Long-term (Architecture)
1. **Subagent MCP inheritance flag** — `inheritMcpServers: true` to auto-pass all parent servers
2. **Dynamic server loading** — MCP server hot-reload without Claude Code restart
3. **Server aliases** — Name servers by purpose (`local-models`, `external-apis`, etc.) for clarity

---

## Tested & Verified

✅ Parent MCP server can be referenced by name in subagent config
✅ Subagent can invoke ollama-bridge tools (via `ask_ollama`, etc.)
✅ Both reference and inline configs work
⚠️ No permission issues observed (tools are whitelisted at user level)
⚠️ No documented example exists in Claude Code official docs

---

## Recommendations for This Workspace

### Immediate
Create template at `~/.claude/agents/ollama-worker.md`:
```yaml
---
name: ollama-worker
description: Subagent with access to local Ollama models
mcpServers:
  - ollama-bridge
---

You have access to local Ollama models via the ollama-bridge MCP server.

Available tools:
- ask_ollama(prompt, model?, persona?) — Run inference on a local model
- generate_code(prompt, language?, model?, persona?) — Auto-route to language-specific persona
- classify_text(text, categories, model?) — Classify text using local LLM
- summarize(text, max_points?, model?) — Generate bullet-point summary
- translate(text, target_language, source_language?, model?) — Translate text

Example usage in your prompt:
  "Use ask_ollama to generate a bash script for..."
  "Classify this into: [category1, category2, category3]"
```

### For Future Sessions
Add to deferred infrastructure with reference to `docs/findings/mcp-subagent-integration.md` § "What Would Improve Usability"
