# Layer 2 Comparison Tests

Five-way comparison across local and frontier coding tools.

## Tool Matrix

| Tool | Model | Type | Format |
|------|-------|------|--------|
| **Aider** | qwen2.5-coder:7b (local) | Local | Text (whole-file) |
| **Qwen Code** | qwen3:8b (local) | Local | JSON tool-calling |
| **Goose** | qwen2.5-coder:7b (local) | Local | JSON tool-calling |
| **OpenCode** | Groq Llama 3.3 70B (free tier) | Frontier | JSON tool-calling |
| **Claude Code** | Claude Sonnet (paid) | Frontier | Tool-use |

> **Note:** OpenCode with local 7-8B models is known to fail (models can't produce valid JSON
> tool calls). OpenCode is tested here with Groq as a frontier-backed TUI comparison.

## Setup

Worktrees (all branch from commit `a1a1859`):
```
/mnt/i/workspaces/llm-test-aider      ← test-aider branch
/mnt/i/workspaces/llm-test-opencode   ← test-opencode branch  (has .env with GROQ_API_KEY)
/mnt/i/workspaces/llm-test-qwencode   ← test-qwencode branch
/mnt/i/workspaces/llm-test-goose      ← test-goose branch
/mnt/i/workspaces/llm-test-claude     ← test-claude branch
```

All worktrees have `.claude/` and `CLAUDE.md` removed (those files confused local models).

Model personas:
- `my-aider` — Qwen2.5-Coder-7B, temp=0.1, 16K context, no SYSTEM prompt

## Test Suite

| # | Test | Prompt file | What it measures |
|---|------|-------------|-----------------|
| 1 | Spring Boot REST API | `test1-springboot.md` | Multi-file project scaffolding, Java conventions, 2 entities with relationship |
| 2 | Bouncing Ball visual | `test2-visual.md` | Self-contained creative coding (HTML/Canvas/JS), physics simulation |
| 3 | Add MCP tool | `test3-mcp-tool.md` | Reading existing code, following patterns, targeted multi-file edits |

**Tip:** Run Test 3 (MCP tool) last — it modifies existing files and is most sensitive to
accumulated state from earlier tests.

## Running Tests

Open one terminal per tool. For each test, paste the same prompt into all terminals.

---

### Aider (local, text-format)
```bash
cd /mnt/i/workspaces/llm-test-aider
aider
```
- For **Test 3 only**: before pasting the prompt, run:
  ```
  /add mcp-server/src/ollama_mcp/server.py mcp-server/src/ollama_mcp/client.py
  ```
- Auto-commit is disabled (`no-auto-commits: true`). Commit manually when satisfied.
- Useful commands: `/undo` to revert last edit, `/tokens` to check context usage.

---

### Qwen Code (local, tool-calling)
```bash
cd /mnt/i/workspaces/llm-test-qwencode
OLLAMA_API_KEY=ollama qwen
```
- Runs qwen3:8b via Ollama. Tool-calling may or may not succeed (known reliability issues
  with 7-8B models — this is part of what the test measures).
- Uses `--approval-mode default` by default; approve file writes as prompted.
- To auto-approve all actions: `OLLAMA_API_KEY=ollama qwen --yolo`

---

### Goose (local, tool-calling)
```bash
cd /mnt/i/workspaces/llm-test-goose
GOOSE_DISABLE_KEYRING=1 goose session
```
- Runs qwen2.5-coder:7b via Ollama (better tool-call compliance than qwen3:8b for Goose).
- `GOOSE_DISABLE_KEYRING=1` is required in WSL2 (no D-Bus secrets service).
- To resume a session: `GOOSE_DISABLE_KEYRING=1 goose session --resume`

---

### OpenCode + Groq (frontier, TUI)
```bash
cd /mnt/i/workspaces/llm-test-opencode
/home/leandror/.opencode/bin/opencode
```
- In the model selector: choose **Groq (free tier)** → **Llama 3.3 70B**
- All requests go to Groq (no local model involvement — 100% cloud for this session).
- Groq free tier: 500K tokens/day, no credit card required.
- The `.env` file in this worktree contains the GROQ_API_KEY.

---

### Claude Code (frontier)
```bash
cd /mnt/i/workspaces/llm-test-claude
claude
```
- Paste the test prompt directly. Claude Code will read, plan, and execute autonomously.

---

## Measuring Results

For each test × tool, record:
- **Executes?** — Did the tool actually write files, or just describe what to do?
- **Compiles/runs?** — Spring Boot: `./mvnw spring-boot:run` | Visual: open in browser | MCP: `uv run python -m ollama_mcp`
- **File coverage** — Did it create all necessary files?
- **Code quality** — Idiomatic? Correct patterns? Proper relationships?
- **Wall-clock time** — Prompt to finished output
- **Interaction count** — How many turns/retries needed
- **Errors** — Crash, malformed edits, tool-call failures, hallucinated APIs

## Comparing Outputs

```bash
# Spring Boot — compare all vs aider baseline
diff -r /mnt/i/workspaces/llm-test-aider/springboot-api /mnt/i/workspaces/llm-test-qwencode/springboot-api
diff -r /mnt/i/workspaces/llm-test-aider/springboot-api /mnt/i/workspaces/llm-test-goose/springboot-api
diff -r /mnt/i/workspaces/llm-test-aider/springboot-api /mnt/i/workspaces/llm-test-opencode/springboot-api
diff -r /mnt/i/workspaces/llm-test-aider/springboot-api /mnt/i/workspaces/llm-test-claude/springboot-api

# Visual
for dir in aider qwencode goose opencode claude; do
  echo "=== $dir ===" && ls /mnt/i/workspaces/llm-test-$dir/visual-test/ 2>/dev/null || echo "missing"
done

# MCP tool
for dir in aider qwencode goose opencode claude; do
  echo "=== $dir ===" && grep -n "count_tokens" /mnt/i/workspaces/llm-test-$dir/mcp-server/src/ollama_mcp/server.py 2>/dev/null || echo "missing"
done
```

## Cleanup

```bash
# Remove worktrees
git worktree remove /mnt/i/workspaces/llm-test-aider
git worktree remove /mnt/i/workspaces/llm-test-opencode
git worktree remove /mnt/i/workspaces/llm-test-qwencode
git worktree remove /mnt/i/workspaces/llm-test-goose
git worktree remove /mnt/i/workspaces/llm-test-claude

# Delete test branches (optional — keep for reference)
git branch -d test-aider test-opencode test-qwencode test-goose test-claude
```
