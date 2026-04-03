# Roadmap: Smart Portfolio Chatbot

*2026-04-02. Upgrade the career chatbot from static context injection to
on-demand retrieval across all 3 repositories.*

---

## Goal

Transform the HF Space chatbot from a "closed book exam" (all context in the system
prompt at startup) into an "open book" system that retrieves relevant material per
question — approaching the experience of opening Claude Code on the combined repos.

### Target use cases

1. **Deep profile conversations** — career background, professional experience,
   engineering philosophy (current capability, to be preserved)
2. **Project-specific Q&A** — "How does the evaluator framework work?", "Explain the
   verdict protocol", "What did you learn about Ollama context limits?"
3. **Tool applicability** — "I have X challenge at work, could any of your tools help?"
   (overlays, ref-indexing, session tracking, persona system)
4. **Implementation details** — "Show me how the MCP bridge handles cold starts",
   "How is structured output enforced?" (requires source code access)
5. **Cross-project reasoning** — "How do the 3 repos connect?", "What patterns are
   shared across projects?"

---

## Architecture: Tier-Based Context Injection

Modeled on the per-folder agent memory architecture (`docs/research/memory-architecture-design.md`):

| Tier | Source | Injection strategy | Token cost |
|------|--------|--------------------|------------|
| **Always** | QUICK.md from all 3 repos + slim profile | System prompt, every question | ~2K tokens |
| **On demand** | KNOWLEDGE.md sections, portfolio.md, topic docs | LLM router selects per question | ~2-6K tokens |
| **Deep dive** | Source code files, evaluator rubrics, config files | File index + targeted read | ~2-8K tokens |
| **Identity** | engineer-profile.md (full) | Always in system prompt | ~3.5K tokens |

Total context budget per question: ~8-18K tokens (well within 128K model window).

---

## Phases

### Phase 0: Foundation — Establish `.memories/` across repos

**Status:** In progress (this session)

| Task | Repo | Approach |
|------|------|----------|
| Create `.memories/QUICK.md` + `KNOWLEDGE.md` | llm | Write directly (deep context available) |
| Create `.memories/QUICK.md` + `KNOWLEDGE.md` | expenses | Prompt-driven, run in expenses session |
| Review/update existing `.memories/` | web-research | Prompt-driven, run in web-research session |

**Convention (from `memory-architecture-design.md`):**
- `QUICK.md` — working memory, ~30 lines, always injected. Status + structure + key rules + "next"
- `KNOWLEDGE.md` — semantic memory, read on demand. Accumulated decisions with rationale, findings, patterns

**Deliverable:** All 3 repos have standardized `.memories/` files ready for chatbot consumption.

### Phase 1: Static context expansion

Wire the chatbot to load `.memories/` files alongside the existing profile.

| Task | Detail |
|------|--------|
| Create `context/` folder in HF Space dir | Holds bundled memory files from all repos |
| Sync script | Copies `.memories/` files + selected READMEs from all 3 repos into `context/` |
| Modify `app.py` | Load `context/*.md` at startup, append to system prompt |
| Update `career_chat_upload_hf` | Run sync before uploading to HF |

**No routing yet.** Total memory content across repos is ~3-4K tokens — fits in the
system prompt alongside the profile without bloating.

**Deliverable:** Chatbot answers cover all 3 projects. "What are you working on?" gets
a live answer from QUICK.md files.

### Phase 2: Per-question retrieval (LLM-as-router)

Add a routing step when static injection is no longer enough.

| Task | Detail |
|------|--------|
| Build section index | Titles + descriptions from all KNOWLEDGE.md files + other docs |
| Routing prompt | "Given this question and this file index, which sections are relevant?" |
| Two-call flow | Call 1: routing (select files) → Call 2: answer (with enriched context) |
| Slim system prompt | Identity + rules only; dynamic context injected per question |

**Trigger to move here:** When total always-injected content exceeds ~15-20K tokens,
or when answer quality degrades due to irrelevant context dilution.

**Backend choice:** Free tier model (Llama 3.3 70B via Groq) is sufficient for routing.
The routing task is classification/extraction — well within 70B capability.

**Deliverable:** Chatbot can answer deep questions by pulling relevant sections on demand.

### Phase 3: Source code awareness

The chatbot can read actual source files when questions are implementation-specific.

| Task | Detail |
|------|--------|
| Structural memory / file index | Map of key source files with descriptions (the "structural memory" type from the architecture doc) |
| Source bundling strategy | Selected source files bundled in `context/source/` or fetched from HF dataset |
| Section extraction | Use `<!-- ref:KEY -->` blocks to load specific sections, not whole files |
| Self-awareness | Chatbot can read its own `app.py` to discuss its implementation |

**Deliverable:** "How does the MCP bridge handle cold starts?" returns an answer grounded
in actual code, not just a summary.

### Phase 4: Cross-project intelligence (the "Claude Code on all repos" experience)

| Task | Detail |
|------|--------|
| Cross-repo search | Given a question, identify which repo + which files are relevant |
| Tool recommendation | Match visitor's described challenges to specific tools/overlays |
| Career context integration | Career project files (from Claude Desktop) available as additional context |
| Auto-update pipeline | Memory files regenerated on push/deploy (consolidation/"dream" pass) |

**Deliverable:** An engineer can ask "I'm struggling with context across AI-assisted sessions"
and get pointed to the overlay system, ref-indexing, and session-handoff — with implementation
details available on follow-up.

---

## Cross-Repo File Sync

The chatbot lives in the llm repo (`docs/portfolio/hf-space/`) but reads from all 3 repos.

**Sync strategy (Phase 1):** A pre-upload script copies memory files and READMEs:

```
# Run before career_chat_upload_hf

# --- .memories/ files (all folders, all repos) ---
cp ~/workspaces/llm/.memories/QUICK.md       context/llm-quick.md
cp ~/workspaces/llm/.memories/KNOWLEDGE.md   context/llm-knowledge.md
# + sub-folder memories: mcp-server, evaluator, personas, benchmarks, overlays
cp ~/workspaces/expenses/.memories/QUICK.md   context/expenses-quick.md
cp ~/workspaces/expenses/.memories/KNOWLEDGE.md context/expenses-knowledge.md
# + sub-folder memories (expense-reporter, etc.)
cp ~/workspaces/web-research/.memories/QUICK.md context/web-research-quick.md
cp ~/workspaces/web-research/.memories/KNOWLEDGE.md context/web-research-knowledge.md
# + sub-folder memories (engine, spike, tools/web-research)

# --- READMEs (high-value subset) ---
# Always-load (root-level project overviews):
#   llm/README.md, expenses/code/README.md, web-research/README.md
# On-demand (component READMEs, loaded when question targets a specific component):
#   llm/mcp-server/README.md, llm/evaluator/README.md, llm/overlays/README.md
#   expenses/code/expense-reporter/README.md, web-research/spike/README.md
# Skip: .pytest_cache, overlay-test, tests/layer2-comparison, hf-space README
```

**Later (Phase 3+):** Move to an HF dataset for larger content, or auto-sync via CI.

---

## Hosting: Branch in llm repo (for now)

The chatbot remains in `docs/portfolio/hf-space/`. Reasons:
- Still fundamentally a portfolio piece — no independent domain logic, tests, or CI
- The `career_chat_upload_hf` alias handles deployment from this subfolder
- Extract to own repo when it gains: own test suite, own CI pipeline, or complex dependency tree

**Branch:** `feature/smart-chatbot`

---

## Open Questions

- **Claude backend for routing?** Haiku is fast enough for routing and already wired.
  Could use it instead of doubling free-tier calls. Cost: ~$0.001/question for routing.
- **Conversation memory within a chat session?** Currently stateless per question for
  context injection (routing happens fresh each turn). Could cache routing results across
  a conversation to reduce calls.
- **KNOWLEDGE.md freshness:** How often do memory files need updating? Tie to session-handoff?
  Or manual ("dream" consolidation pass)?
- **Profile deduplication:** engineer-profile.md and `_PROFILE` in app.py overlap significantly.
  Phase 1 should consolidate to single source of truth.
