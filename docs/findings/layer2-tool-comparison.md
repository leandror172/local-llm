# Layer 2 Comparison — Findings

**Date:** 2026-02-17
**Setup:** RTX 3060 12GB, WSL2, Ollama — Qwen2.5-Coder-7B + Qwen3-8B local; Groq free tier for frontier.

---

## Test Matrix Results

| Tool | Model | Test 1 Spring Boot | Test 2 Visual | Test 3 MCP tool | Executed? |
|------|-------|--------------------|---------------|-----------------|-----------|
| **Aider** | qwen2.5-coder:7b (local) | ⚠️ Partial | ⚠️ Broken physics | ✅ Mostly spec | ✅ Yes |
| **Claude Code** | claude-sonnet | ✅ Full | ✅ Correct | ✅ Spec-compliant | ✅ Yes |
| **OpenCode** | qwen3:8b (local) | ❌ No file writes | — | — | ❌ No |
| **OpenCode** | Groq Llama 3.3 70B | ❌ TPM exceeded | ❌ TPM exceeded | — | ❌ No |
| **Qwen Code** | qwen3:8b (local) | ❌ No file writes | — | — | ❌ No |
| **Goose** | qwen2.5-coder:7b (local) | ❌ Incomplete tool args | — | — | ❌ No |

---

## Tool-by-Tool Analysis

### Aider — ✅ Executed, ⚠️ Quality limits

**What worked:**
- Single-shot execution on all 3 tests without crashing
- Created files reliably (text-format `whole` mode bypasses JSON tool-calling)
- Reasonable structure for Spring Boot (service + repository + controller layers)
- MCP tool added; error messages actionable per-exception

**What failed:**

| Test | Issue | Root cause |
|------|-------|------------|
| Spring Boot | `javax.persistence` instead of `jakarta.persistence` | Training data predates Spring Boot 3.x / Jakarta namespace migration (2020) |
| Spring Boot | `spring-boot-starter-webflux` instead of `spring-boot-starter-web` | Wrong stack selection — project would not run as a standard REST API |
| Spring Boot | `@Autowired` field injection (spec said constructor injection) | Missed a stated requirement |
| Spring Boot | No `mvnw`, no DTOs, no exception handler | Incomplete scaffolding |
| Visual | Collision detection in canvas coords, not rotated square frame | 7-8B spatial reasoning failure — cannot implement coordinate transforms |
| Visual | "Trail" is a single fading arc, not a position history | Misunderstood the trail requirement |
| MCP tool | No character-based fallback on embed failure | Missed a stated requirement |

**Verdict:** Executes reliably but produces non-compiling code on modern stacks and breaks on any task requiring spatial reasoning or precise spec adherence.

---

### Claude Code — ✅ Executed, ✅ High quality

**What worked:**
- All 3 tests completed correctly in single-shot
- Spring Boot: `jakarta.persistence`, `spring-boot-starter-web`, constructor injection, DTOs, `@JsonManagedReference` to prevent circular serialization, `GlobalExceptionHandler`, `mvnw` included — project compiles and runs
- Visual: Proper coordinate transforms (`toLocal`/`toWorld`/`velToLocal`/`velToWorld`), delta-time physics, real 120-position trail with opacity gradient, speed normalization after bounce
- MCP tool: Full spec compliance including character-based fallback, detailed docstring with example output

**Minor gaps:**
- Spring Boot: No service layer (controller → repository directly) — simpler but less layered
- MCP tool: Groups all exceptions in one `except` block rather than per-exception messages

**Verdict:** Production-ready output on all 3 tasks. Correct on modern framework knowledge, spatial math, and spec details.

---

### OpenCode, Qwen Code, Goose — ❌ Did not execute

All three are **tool-calling agents** (model must emit structured JSON to write files). Local 7-8B models cannot produce valid JSON tool calls reliably:

| Tool | Observed failure |
|------|-----------------|
| OpenCode + qwen3:8b | Emitted Python pseudocode (`write_file(...)`) — wrong interface entirely |
| OpenCode + qwen2.5-coder:7b | Malformed JSON (`{"name": "skill", ...}`) — wrong schema |
| Qwen Code + qwen3:8b | Described plan, output code as prose, never invoked file-write tool |
| Goose + qwen2.5-coder:7b | Sent tool call with missing `content` field — partial JSON, never executed |

Secondary findings:
- **Groq free tier incompatible with OpenCode:** Tool-calling agents send ~15-16K tokens of system prompt + tool definitions per request. Groq's 12K TPM free limit is always exceeded before the user prompt is added.
- **Qwen3 thinking token leak:** User-typed `exit` was echoed back as `exit /think` — the model's reasoning tokens bleed into interactive input. Affects both OpenCode and Qwen Code TUIs.
- **Context pollution:** `.claude/` directory (session files, skills, CLAUDE.md) was present in worktrees. Local models read these instructions and attempted to follow them (session-handoff loop). Worktrees need their Claude Code artifacts stripped before use with other tools.

---

## Key Findings

### 1. The tool-calling wall at 7-8B scale

The single biggest factor determining local-model viability is **edit format**:

- **Text-format agents** (Aider: `whole` mode) — model returns complete file content in a fenced code block. No JSON required. Works reliably with 7-8B models.
- **Tool-calling agents** (OpenCode, Qwen Code, Goose) — model must emit `{"type": "tool_use", "name": "write_file", "input": {...}}`. 7-8B models fail at this systematically: wrong schema, incomplete arguments, or wrong format entirely (Python pseudocode, XML tags).

This is not a prompt engineering problem — it's a model capability threshold. Tool-calling requires both JSON discipline and knowing the exact schema, which 7-8B models don't have reliably enough for agentic loops.

### 2. Training data cutoff is a hard quality ceiling for local models

Aider's `javax.persistence` bug is the canonical example: the correct answer changed in 2020 (Jakarta EE namespace migration), but most 7-8B training data predates or underrepresents post-migration examples. For any technology that evolved significantly in 2021-2024, local 7-8B models will produce subtly outdated or incorrect output — and won't know it.

### 3. Spatial reasoning requires scale

The visual test exposed this directly. The prompt was 9 sentences. The correct implementation requires:
- Understanding that collision must be computed in the *rotated* coordinate frame
- Implementing the inverse rotation transform to convert world→local coords
- Converting velocity vectors the same way
- Pushing corrected position/velocity back to world space after collision

Qwen2.5-Coder-7B understood the task description but could not implement the math. Claude produced correct transforms in a single pass. This pattern repeats across any task involving coordinate geometry, physics, or multi-step mathematical transformations.

### 4. Frontier overhead for tool-calling agents

Groq free tier (12K TPM) is structurally incompatible with any tool-calling agent — the tool definition overhead alone exceeds the limit. Practical frontier options for OpenCode:
- **Gemini free tier** — 1M TPM on Flash, 250K on Pro. Suitable.
- **Groq paid** — Dev tier removes the per-minute limit.
- **Anthropic API** — Pay-per-use, no free tier.

---

## Decision Guide: When to Use What

### Use Aider + local model when:

- **Boilerplate generation** in well-established, stable technologies (pre-2022 versions OK)
- **Adding to existing code** where the model can see patterns to follow (repo map helps)
- **Privacy-sensitive work** — no data leaves the machine
- **High-iteration exploration** — zero cost, no rate limits, instant feedback
- **Offline / airgapped environment**
- You will **review and fix output** before using it (treat it as a first draft)
- Tasks that are **narrow and explicit** — "add a method X that does Y" rather than "build a REST API"

### Use Claude Code when:

- **Modern stack** (Spring Boot 3.x, Python 3.11+, React 18+, any framework with significant 2022+ changes)
- **Spatial / mathematical reasoning** (physics, geometry, transforms, algorithms)
- **Precise spec compliance** required — attending to all stated requirements
- **Multi-file scaffolding** with internal consistency (DTOs matching controllers matching entities)
- **Production-bound code** — quality bar is "compiles and runs correctly"
- **Test 3-style targeted edits** — reading existing code and extending it to match patterns

### The middle path — Aider architect mode:

When a Gemini/Groq API key is available:
```
aider --architect --model gemini/gemini-2.5-flash
```
Frontier model plans the change in natural language; local Qwen2.5-Coder-7B writes the code. Good for: spec-heavy tasks where frontier planning prevents the `javax` / WebFlux class of mistakes, while keeping code generation local and fast.

### Tool-calling agents (OpenCode, Qwen Code, Goose) with local models:

**Not viable at 7-8B scale.** Require either:
- 30B+ model locally (exceeds 12GB VRAM)
- Frontier API (Gemini free tier is the practical path — high limits, already configured)

---

## Appendix: Failure Taxonomy

| Failure type | Example | Mitigation |
|---|---|---|
| Training cutoff | `javax.persistence` on Spring Boot 3.x | Use Claude Code; or add correcting context to Aider prompt |
| Spatial reasoning | Fixed-axis collision in rotating frame | Use Claude Code — not fixable at 7B scale |
| Spec inattention | `@Autowired`, missing fallback | Break prompt into smaller tasks; review output carefully |
| Tool-call format | Python pseudocode instead of JSON | Use text-format agent (Aider) or frontier model |
| Thinking token leak | `exit /think` echoed to user | Known Qwen3 bug in interactive TUIs; use `think: false` in API |
| Context pollution | Claude Code `.claude/` dir confuses other tools | Strip `.claude/` and `CLAUDE.md` from worktrees before using other tools |
| Rate limit overhead | Groq 12K TPM < tool definition overhead | Use Gemini free tier for frontier-backed tool-calling agents |
