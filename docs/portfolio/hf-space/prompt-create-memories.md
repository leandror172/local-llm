# Prompt: Create `.memories/` Files for Portfolio Chatbot

*Use this prompt in a Claude Code session within each repo (expenses, web-research).
Recommended: Sonnet, medium effort.*

---

## The prompt

Paste this into a Claude Code session in the target repo. Adjust the `[REPO]` placeholder.

---

```
I need to create (or review/update) `.memories/` files for use by a portfolio chatbot.
The chatbot is a Gradio app on HF Spaces that discusses my engineering profile and
projects — it needs curated, structured context about each of my 3 repos.

## Convention

Two files (or more) **per relevant folder** (not just repo root), modeled on cognitive memory types.
Any folder with its own distinct domain — a major component, a self-contained tool, a
subsystem — gets its own `.memories/` with QUICK.md + KNOWLEDGE.md - read 
/home/leandror/workspaces/web-research/docs/research/memory-architecture-design.md and 
/home/leandror/workspaces/web-research/docs/research/memory-layer-design.md for details on memories 
folder idea details - descriptions of the workings of these memories in those files may supersed/conflict
with instructions below; in which case, the descriptions in the file have higher "priority"

Root-level memories cover the overall project. Sub-folder memories cover that component's
specific decisions, findings, and status.

### `.memories/QUICK.md` — Working memory (~30 lines max)
- **Always injected** into the chatbot's system prompt
- Current status, repo structure, key rules, what's next
- Compressed, telegram-style — every line earns its place
- Should answer: "What is this project and where does it stand?"

### `.memories/KNOWLEDGE.md` — Semantic memory (no hard limit, but curated)
- **Injected on demand** when a question needs depth on a topic
- Accumulated decisions with rationale, key findings, architecture patterns
- Each section: fact/decision → **Why:** → **How it applies:**
- Should answer: "What were the important decisions and why?"

## Format

```markdown
# [repo-name]/ — Quick Memory (repo root)

*Working memory for the repo. Injected into agents and chatbot. Keep under 30 lines.*

## Status
[current phase, what's complete, what's next]

## Repo Structure
[brief tree showing key directories]

## Key Rules
[3-5 rules that govern how work happens in this repo]

## Deeper Memory → KNOWLEDGE.md
[4-5 bullet pointers to KNOWLEDGE.md sections]
```

```markdown
# [repo-name]/ — Knowledge (Semantic Memory)

*Repo-wide accumulated decisions. Read on demand by agents and chatbot.*

## [Topic] ([date])
[Decision or finding]
**Rationale:** [why]
**Implication:** [how this shapes future work]
```

## What the chatbot needs from these files

The chatbot serves visitors who ask about my engineering profile and projects.
The memories should help it answer questions like:
- "What is the [REPO] project?" → QUICK.md
- "What architecture decisions shaped [REPO]?" → KNOWLEDGE.md
- "What did you learn building [REPO]?" → KNOWLEDGE.md findings sections
- "How does [REPO] connect to the other projects?" → QUICK.md or KNOWLEDGE.md

## Important guidelines

- **Accuracy over completeness** — only include things you can verify from the codebase.
  Don't guess at decisions you can't trace to code, config, or docs.
- **Outsider-readable** — a visitor won't know your internal conventions. Write for
  someone who has never seen the repo. Avoid jargon without context.
- **Highlight what's interesting** — what would surprise a senior engineer? What's
  non-obvious? What required empirical discovery?
- **Cross-repo connections** — mention how this repo connects to the other two
  (llm platform, expense classifier, web research tool) where relevant.
- **No secrets** — no API keys, paths, personal info. This feeds a public chatbot.

## Examples

Here's what web-research/.memories/ looks like (already created):

### QUICK.md (~36 lines)
```
# web-research/ — Quick Memory (repo root)
*Working memory for the repo. Injected into agents. Keep under 30 lines.*

## Status
Phase 2A complete (2026-03-27). Search + extraction pipeline working in tools/web-research/.
Phase 2B next — content guard, usable-result filtering, FirecrawlFetcher for JS sites.

## Repo Structure
web-research/
  spike/          # frozen — Phase 1 extraction proof-of-concept
  engine/         # future Phase 2B — Conductor, Dispatcher, Auditor, Lens
  tools/          # self-contained tools (polyglot, own deps each)
    web-research/ # Phase 2A — search + extraction pipeline (Python)
  docs/

## Key Rules
- **Tools don't import each other** — engine dispatches via MCP/CLI/HTTP
- **No shared Python libs** preemptively — MCP bridge is the integration layer
- **Per-folder .memories/** — QUICK.md (working) + KNOWLEDGE.md (semantic)

## Deeper Memory → KNOWLEDGE.md
- **Tool Isolation** — no shared imports, MCP is integration layer
- **Search Provider Strategy** — Protocol-based, Firecrawl first, SearXNG later
- **Phase Plan** — 1 (done) → 2A (search) → 2B (orchestrator) → 3+ (agents)
```

### KNOWLEDGE.md (~42 lines)
```
# web-research/ — Knowledge (Semantic Memory)
*Repo-wide accumulated decisions. Read on demand.*

## Tool Isolation (2026-03-26)
Each tool is self-contained: own package, own pyproject.toml, own dependencies.
Tools communicate through MCP, CLI subprocess, or HTTP — never shared Python imports.
**Rationale:** DDD bounded contexts communicate through defined interfaces.
**Implication:** Allows polyglot tools and independent deployment.

## Search Provider Strategy (2026-03-26)
Protocol-based: SearchEngine interface, multiple implementations.
Firecrawl first (already available via MCP skill), SearXNG later (Docker, local-first).
**Rationale:** Validate pipeline with available provider before building local infra.
```

## Identifying relevant folders

Before writing, scan the repo structure and identify which folders have their own
distinct domain. Criteria for "needs its own `.memories/`":
- Has its own package/module structure (own go.mod, pyproject.toml, main.go, etc.)
- Has distinct architectural decisions separate from the parent
- A developer working in this folder would need context the parent doesn't provide
- Has enough substance to warrant both a QUICK.md and KNOWLEDGE.md

Do NOT create memories for:
- Simple directories that are just file organization (e.g., `scripts/`, `docs/`)
- Folders with <5 files and no independent decisions
- Test fixtures or generated output directories

## Task

[FOR EXPENSES REPO]: Scan the repo structure to identify folders that need `.memories/`.
At minimum, the repo root needs them. Read the codebase (CLAUDE.md, key source files,
recent git history) to understand the project deeply before writing. Create QUICK.md +
KNOWLEDGE.md for each relevant folder.

[FOR WEB-RESEARCH REPO]: Review the existing `.memories/` files at root and all
sub-folders (engine/, spike/, tools/web-research/). Update if stale (check git log for
recent changes since the files were written). Identify any new folders that should have
memories. Add a note in KNOWLEDGE.md about the cross-repo connection to the chatbot if
not already present.

Write the files directly — do not propose content for approval. I'll review after.
```
