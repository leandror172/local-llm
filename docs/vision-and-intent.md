# Vision & Intent

The design philosophy and goals behind this project, preserved from conversations during Phases 0-6 and the subsequent planning discussions.

**Last updated:** 2026-02-07

---

## Core Goal

Build a **local AI infrastructure** that maximizes what can be accomplished without relying entirely on frontier model API limits. The frontier model (Claude) remains available for tasks that require its quality, but the local stack handles everything it can — reducing cost, removing usage caps, and enabling experimentation at scale.

**The cost equation:** Claude Pro gives bursts of frontier quality with daily/hourly limits. Local models give unlimited usage at energy cost only. The goal is not to replace one with the other, but to build a system where they complement each other — frontier quality where it matters, local speed and freedom everywhere else.

---

## Design Principles

### 1. Quality compounds across everything

Any improvement to local model output quality amplifies across every use case. A better system prompt doesn't just help coding — it helps classification, translation, writing, evaluation. This is why "closing the gap" isn't a phase to complete and move on from; it's an ongoing discipline applied to every persona, every agent, every pipeline.

### 2. Right model for the right task

Not every task needs the best model. Classification can run on a 3B model. Heavy reasoning benefits from 14B even with reduced context. Code generation is best on code-specialized models. Translation needs multilingual training data. The architecture should support multiple models loaded on demand, with the system (or the user, or another agent) choosing the right one per task.

### 3. Agents mirror human collaboration — but aren't human

The multi-agent pattern maps naturally to how teams work: an architect designs, specialists implement, evaluators review, a manager coordinates. But AI agents have different failure modes than humans:

- **They don't know what they don't know.** A Java persona won't escalate to a Go specialist; it'll produce wrong Go confidently. Evaluators and routing are not optional — they're structural requirements.
- **They lose context between calls.** Every invocation starts from zero unless you build explicit memory (files, RAG, correction logs). Memory is prosthetic, not intrinsic.
- **Same-model "diversity" is shallow.** Two personas on the same base model share blind spots. Real diversity comes from different models, different temperatures, or different prompting strategies — not just different system prompts.
- **Compounding hallucination.** When agents build on each other's output, errors amplify. The evaluator must be the strongest available model (frontier when possible).

### 4. The interface matters

Different tasks need different interaction surfaces:

| Interface | Best for | Pattern |
|-----------|----------|---------|
| **ClaudeCode** (CLI) | Coding, file operations, git | Frontier-first, delegates simple tasks to local via MCP |
| **Aider or equivalent** (CLI) | Coding when local quality suffices | Local-first, escalates to frontier when stuck |
| **IDE extension** (Continue.dev) | Real-time autocomplete, inline edits | Local-only, speed matters more than reasoning |
| **Chat** (Telegram/WhatsApp) | Non-coding: expenses, coaching, general | Routes to local or frontier based on complexity |
| **Autonomous** (idle-time) | Self-improvement, benchmarking, research | Local-only, runs unattended |

The routing layer isn't a single component — it's three patterns depending on which interface initiates the request.

### 5. Agents can build agents

A key differentiator from static tooling: the system should be able to create its own specialists. Not just from a questionnaire, but conversationally, with the ability to:

- Analyze a codebase/domain and propose appropriate personas
- Test a persona against sample tasks and iteratively refine it
- Choose which base model and parameters suit the persona's role
- Archive or merge personas that aren't being used ("agent bloat" prevention)

This is the meta-layer that makes the whole system self-improving rather than manually maintained.

### 6. Not limited to coding

The same infrastructure serves multiple domains:

- **Career coaching:** Resume analysis, job matching, company research
- **Personal finance:** Expense classification via Telegram, learning from corrections
- **Writing:** PT-BR content with translator-agent pattern (prompt in PT → translate to EN → process → translate back)
- **Research:** Literature review, summarization, comparison
- **Project management:** Task breakdown, resource allocation, progress tracking

Each domain may have its own personas, its own preferred models, its own evaluation criteria — but they all run on the same local stack.

### 7. Memory enables learning

Agents should improve with use. The practical version today:

- **Correction logs:** When the user corrects an output, log the input/expected/actual. These become few-shot examples and eventually fine-tuning data.
- **Per-persona MEMORY.md:** Accumulated observations, successful patterns, known limitations.
- **Summarization:** Long memory files get compressed by a summarizer agent to prevent context bloat.
- **Fine-tuning as batch learning:** Periodically, correction logs feed QLoRA fine-tuning to bake improvements into the model weights.

True online learning (weights updating in real time) doesn't exist locally yet. But the file-based memory + periodic fine-tuning cycle approximates it.

### 8. Security is a prerequisite, not an afterthought

Autonomous agents with shell/file/network access require:

- Docker sandboxing for untrusted operations
- API spending limits at the provider level
- A security-specialist agent that audits the local stack
- Isolation between agent workspaces
- Prompt injection awareness (agents processing external documents)

OpenClaw or any similar autonomous framework needs its own security planning project before deployment.

---

## Use Cases (Concrete)

### Coding workflow
1. Open ClaudeCode for a task
2. Claude analyzes complexity — delegates boilerplate/simple functions to local Ollama (via MCP)
3. Claude handles architecture, multi-file reasoning, complex logic itself
4. Local Aider available for when Claude quota is depleted but work continues
5. Continue.dev provides real-time autocomplete from local model in IDE

### Expense tracking
1. User reports expense in Telegram group (existing behavior): "Uber R$23"
2. Local model classifies: Transportation (confidence: 92%)
3. If low confidence, asks user to pick from top 3 options
4. Calls Go tool to add to spreadsheet
5. Correction logged → few-shot examples updated → eventually fine-tuned

### Career coaching
1. User provides resume + target job description
2. Frontier model (Claude) analyzes fit, suggests improvements
3. Local model handles formatting, keyword extraction, ATS optimization
4. PT-BR interactions go through translator-agent pattern

### Project bootstrapping
1. User describes project goal to "architect" persona
2. Architect analyzes requirements, proposes structure
3. Architect "recruits" specialist personas (creating them if needed via persona creator)
4. Specialists discuss implementation approaches
5. Evaluator agents score proposals
6. User reviews, selects, iterates
7. Coding agents implement with pair-programming pattern (different model/persona perspectives)

### Idle-time improvement
1. User signals "going idle" (or system detects inactivity)
2. Runner picks top N prompts from the day's work
3. Runs each through multiple persona variants
4. Scores outputs against frontier model baseline (cached or queued for next frontier session)
5. Logs which personas/settings produced best results
6. Suggests persona refinements for next session

---

## Key Risks

| Risk | Mitigation |
|------|------------|
| Agent bloat (too many personas) | Usage metrics + archival policy |
| Memory bloat (context overflow) | Summarization agent + rotation policy |
| Hallucination cascading | Evaluator on strongest model, validation layers |
| Over-engineering before using | Start with concrete use case (expense classifier or MCP server), grow from there |
| Security exposure | Sandbox before autonomy, always |
| "Building infrastructure instead of using it" | Each layer must produce a usable artifact, not just scaffolding |

---

## Relationship to Existing Documents

| Document | Role |
|----------|------|
| `docs/closing-the-gap.md` | Technical techniques reference. Principles are ongoing; tasks are extracted into the plan. |
| `docs/model-strategy.md` | Which models for which roles, VRAM budgeting. (To be created) |
| `.claude/plan-v2.md` | Execution roadmap with layers, tasks, dependencies. (To be created) |
| `.claude/session-context.md` | Operational state for session continuity. |
| `docs/model-comparison-hello-world.md` | Baseline quality benchmark. Template for future comparisons. |
