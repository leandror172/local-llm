# Claude Code Scaffolding Template

This document describes the `.claude/` convention used in this project.
Any new project can follow this checklist to gain session continuity, ref-lookup,
and the session-handoff skill from day one.

---

## Directory Structure

```
.claude/
├── tools/
│   ├── resume.sh              # Session-start summary (run this at start of every session)
│   ├── ref-lookup.sh          # Resolve [ref:KEY] tags to their content
│   └── rotate-session-log.sh  # Archive old session entries
├── skills/
│   └── session-handoff/
│       └── SKILL.md           # End-of-session workflow skill
├── archive/                   # Historical session logs and completed phase notes
├── local/                     # Gitignored: secrets, personal data, local overrides
├── index.md                   # Knowledge index — every topic mapped to a file
├── session-log.md             # Running log: one entry per session (most recent first)
├── session-context.md         # Ref blocks: user-prefs, current-status, resume-steps, active-decisions
└── tasks.md                   # Layer/phase task list with checkboxes
```

---

## File Purposes

| File | Purpose |
|---|---|
| `tools/resume.sh` | Prints current-status ref block, last session "Next" pointer, recent commits, and available ref keys. Run at session start. |
| `tools/ref-lookup.sh` | Searches all `*.md` files for `<!-- ref:KEY -->` blocks and prints the content. Use `list` to enumerate available keys. |
| `tools/rotate-session-log.sh` | Moves old session entries to `.claude/archive/session-log-YYYY-MM-DD.md`, keeps the 3 most recent in `session-log.md`. |
| `skills/session-handoff/SKILL.md` | Claude Code skill invoked at session end. Updates `session-log.md`, `session-context.md`, and `tasks.md` for continuity. |
| `index.md` | Quick reference: one-line description of every file/directory, organized by category. Update whenever a file is added. |
| `session-log.md` | Chronological record. Most recent entry first. Each entry has: What was done, Key decisions, Blockers, and Next pointer. |
| `session-context.md` | Stable reference context wrapped in `<!-- ref:KEY -->` blocks. Loaded by agents via `ref-lookup.sh`. |
| `tasks.md` | Layer/phase progress. Checkboxes. Archive completed layers rather than deleting them. |
| `local/` | Personal data, API keys, local settings. Always gitignored. |
| `archive/` | Old session logs, completed phase notes. Reference-only. |

---

## ref:KEY Two-Tier Documentation Convention

The project uses `[ref:KEY]` tags in `CLAUDE.md` to point agents to detailed
runtime-relevant content, and `§ "Heading"` for background navigation pointers.

### Ref blocks in Markdown files

Wrap runtime-relevant content with HTML comment markers:

```markdown
<!-- ref:current-status -->
## Current Status

- **Active layer:** Layer N — Description
- **Next:** Task N.1

<!-- /ref:current-status -->
```

Rules:
- One concept per block (don't mix current-status and user-prefs in one block)
- Use lowercase-kebab-case keys: `current-status`, `bash-wrappers`, `go-structure`
- Closing tag is optional but strongly recommended (enables accurate extraction)
- `ref-lookup.sh list` auto-discovers all blocks in `*.md` files — no registration needed

### CLAUDE.md ref pointers

```markdown
## Environment Context
[ref:go-structure] — Go package layout and conventions
```

This tells agents: "for detail, run `ref-lookup.sh go-structure`".

### When to use ref vs § pointer

| Use | When |
|---|---|
| `[ref:KEY]` | Agent needs the content at runtime (current status, conventions, schemas) |
| `§ "Heading"` | Background/archive reading (historical decisions, research) |

---

## Session Log Entry Format

```markdown
## YYYY-MM-DD — Session N

### Done
- Bullet point of what was completed

### Key decisions
- Decision made and why

### Blockers
- Any unresolved issues (or "none")

### Next
- [ ] Task N.X — description
- [ ] Task N.Y — description

---
```

---

## Setup Checklist (10 steps)

Bootstrap a new project with this scaffolding in ~15 minutes:

1. **Copy tools** — `cp llm-repo/.claude/tools/{resume,ref-lookup,rotate-session-log}.sh .claude/tools/`
2. **Copy skill** — `cp -r llm-repo/.claude/skills/session-handoff/ .claude/skills/`
3. **Create directories** — `.claude/{archive,local}/`, `docs/archive/`
4. **Create `CLAUDE.md`** — project identity, build commands, workflow rules, resume instruction
5. **Create `index.md`** — table of all files with one-line descriptions; add ref:indexing-convention block
6. **Create `session-context.md`** — ref blocks: `user-prefs`, `current-status`, `resume-steps`, `active-decisions`
7. **Create `session-log.md`** — first entry: pre-history summary + current session goals
8. **Create `tasks.md`** — current layer tasks; archive any pre-history work as "completed"
9. **Add `.gitignore` entries** — `.claude/local/`, personal data, build artifacts
10. **Verify** — run `resume.sh`, check it prints status + dynamic key list; run `ref-lookup.sh list`

---

## Tool Dependencies

All tools use only POSIX-standard utilities:

- `bash` ≥ 4.0
- `git` (for `resume.sh` git log/status)
- `grep`, `sed`, `awk` — standard POSIX implementations (GNU or BSD)
- `sort` — for `ref-lookup.sh list` deduplication

No Python, Node, or external packages required. Tools are safe to whitelist
per-script in Claude Code (use `./script.sh` form, not `bash script.sh`).

---

## Local Model Usage Convention

Projects using the ollama-bridge MCP server should follow this verdict pattern
whenever a local model generates code (via `mcp__ollama-bridge__generate_code`
or `mcp__ollama-bridge__ask_ollama`):

**Evaluate every local model response explicitly:**
- `ACCEPTED` — used as-is (note the prompt that worked)
- `IMPROVED` — used with modifications (note what changed and why)
- `REJECTED` — not usable (note the failure reason: logic error / wrong API / off-task)

**On ACCEPTED or IMPROVED verdicts, add a rough token estimate — do NOT read files or write code to compute it:**
- Mentally apply `(chars in your prompt + chars in response) / 4` as a ballpark of what Claude would have spent
- Note it inline in one phrase, e.g.: `ACCEPTED — ~300 est. Claude tokens saved`
- Rough is fine; the log records exact values automatically (`claude_tokens_est`, `prompt_eval_count`, `eval_count`) for later analysis

This pattern generates (prompt, local_response, verdict) triples that feed future
DPO fine-tuning pipelines.

### Handling Imperfect Output: Decision Tree

When Ollama output isn't perfect, classify the defect before deciding how to proceed.
The goal is to pick the action that produces the best outcome *and* the cleanest DPO
training signal (ACCEPTED triples > IMPROVED triples > REJECTED triples).

```
Ollama returns output
│
├─ Is the defect mechanical (slip, syntax, typo, wrong import)?
│  └─ IMPROVED — fix inline always
│
├─ Is the defect structural (missing sections, wrong interface, wrong pattern)?
│  │
│  ├─ Fix scope: 1–2 isolated sites?
│  │  └─ Inline (IMPROVED if trivial, REJECTED if effort > describing it)
│  │
│  ├─ Fix scope: 3+ sites or interdependent?
│  │  │
│  │  ├─ Is the interface/signature definable?
│  │  │  └─ REJECTED + stubs-then-Ollama retry
│  │  │     (stubs embed context structurally; second call gets own verdict)
│  │  │
│  │  └─ NO → REJECTED, write from scratch
│  │
│  └─ Prompt cost tiebreaker: would explaining the fix to Ollama
│     take more effort than the fix itself?
│     └─ YES → inline regardless of scope
│
└─ Is the defect conceptual (correct syntax, wrong behavior/mental model)?
   └─ REJECTED, write from scratch
      (stubs won't help — the model misunderstood the task, not the structure)
```

**Three classification dimensions** (replaces a simple line-count threshold):

| Dimension | What it measures | Inline signal | Escalate signal |
|---|---|---|---|
| **Defect type** | What kind of mistake Ollama made | Mechanical (slip) | Structural or conceptual |
| **Fix scope** | How many sites need changing | 1–2 isolated | 3+ or interdependent |
| **Prompt cost** | Effort to explain vs effort to fix | Explaining > fixing | Explaining < fixing |

### Stubs-then-Ollama Retry Pattern

A retry strategy for **distributed structural defects** where Ollama got the shape wrong
but the interface is definable. This is prompt decomposition applied to code generation —
analogous to decomposing monolithic benchmark prompts.

**When to use:** Ollama missed entire test cases, generated wrong method signatures,
or omitted required interface implementations across 3+ sites.

**How it works:**
1. Verdict the first call as `REJECTED` (with reason)
2. Write stub signatures / interface definitions that anchor the structure
3. Call Ollama again with the stub file provided via `context_files`
4. The second call gets its own independent verdict (often ACCEPTED)

**Why it improves DPO data quality:** The first call produces a clean REJECTED triple.
The second call uses an anchored prompt (stubs carry context structurally rather than
through natural language), so it's more likely to produce an ACCEPTED triple. Both
triples are high-quality training signal.

**Future refinement:** Conceptual defects (correct syntax, wrong behavior) may warrant
model escalation (8B→14B) rather than stubs-then-Ollama. Stubs anchor structure, not
semantics — they won't fix a model that misunderstood the task. Evaluate this when
enough REJECTED-conceptual triples exist to measure escalation success rates.

---

## Source

This scaffolding was developed iteratively over sessions 1–35 of the LLM
infrastructure project at `/mnt/i/workspaces/llm/`. Full context:
`.claude/session-context.md` § "Context Optimization".
