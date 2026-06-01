# Claude Code Dynamic Workflows — Reference & When-to-Use

**Source:** https://code.claude.com/docs/en/workflows (research preview)
**Captured:** 2026-06-01 (session 81). Verify against live docs before relying on details.
**Availability:** Claude Code ≥ 2.1.154. This repo's machine runs 2.1.159 ✓. All paid plans;
on Pro, enable via the "Dynamic workflows" row in `/config`.

---

## What it is (and is NOT)

A **dynamic workflow** is a **JavaScript script** that orchestrates [subagents](https://code.claude.com/docs/en/sub-agents)
*at scale*. Claude writes the script for a task you describe; a runtime executes it in the
**background** while your session stays responsive. It returns **only the final result** to
Claude's context — intermediate results live in **script variables**, not the context window.

**It is NOT a session-tracker / progress-follower.** For "follow this session's work across
steps," the right tools are this repo's tracking files (`tasks.md`, `session-context.md`,
`.claude/handoffs/`) plus the harness Task tools (`TaskCreate` / `TaskUpdate`). Do not reach
for a workflow to checkpoint a small sequential punch-list.

---

## The core distinction — "who holds the plan"

|                          | Subagents            | Skills              | Agent teams              | **Workflows**            |
|--------------------------|----------------------|---------------------|--------------------------|--------------------------|
| What it is               | A worker Claude spawns | Instructions Claude follows | Lead agent supervising peers | **A script the runtime executes** |
| Who decides what's next  | Claude, turn by turn | Claude, per prompt  | Lead agent, turn by turn | **The script**           |
| Intermediate results live in | Claude's context | Claude's context    | A shared task list       | **Script variables**     |
| What's repeatable        | Worker definition    | The instructions    | Team definition          | **The orchestration itself** |
| Scale                    | A few per turn       | Same                | A handful of peers       | **Dozens–hundreds/run**  |
| Interruption             | Restarts the turn    | Restarts the turn   | Teammates keep running   | **Resumable in-session** |

Moving the plan into code also enables a **repeatable quality pattern**: independent agents
can adversarially review each other's findings, or draft a plan from several angles and weigh
them — a more trustworthy result than a single pass.

---

## When to USE a workflow

Reach for one when a task needs **more agents than one conversation can coordinate**, or when
you want the orchestration **codified as a rerunnable script**. Canonical fits:

- Codebase-wide bug/security sweep (independent agent per region)
- Large migration (e.g. 500 files, one agent per slice)
- Research that must **cross-check sources against each other** → see bundled `/deep-research`
- **A hard plan worth drafting from several independent angles** before committing to one

## When NOT to use a workflow

- Small, **sequential** task lists (a few tool calls) — overhead + token cost, no parallelism gain.
- Work that needs **mid-stage human sign-off**. The runtime allows **no mid-run user input**
  (only agent permission prompts can pause). For sign-off between stages, run each stage as its
  own workflow. ⚠️ This clashes with this repo's **interactive-pacing preference** (pause after
  each phase) — workflows blow past those checkpoints.
- Tasks needing the workflow itself to touch the filesystem/shell — **the script has no direct
  FS/shell access**; only the agents it spawns do. The script just coordinates.

---

## How to run one

| Action | How |
|--------|-----|
| Bundled research workflow | `/deep-research <question>` (needs WebSearch tool) |
| One-off for your task | Include the word **`workflow`** anywhere in your prompt → Claude writes a script. Dismiss the trigger with `Option/Alt+W`. |
| Auto-orchestrate everything | `/effort ultracode` — `xhigh` reasoning + auto-workflow per substantive task. Resets each session; drop back with `/effort high`. |
| Watch / manage runs | `/workflows` → arrow-select a run → Enter. Keys: `p` pause/resume, `x` stop, `r` restart agent, `s` save as command. |
| Save for reuse | In `/workflows`, press `s` → save to `.claude/workflows/` (shared) or `~/.claude/workflows/` (personal). Runs as `/<name>` thereafter. Project beats personal on name clash. |

**Approval:** in Default/acceptEdits mode you're prompted every run (unless "don't ask again"
for that workflow). Subagents always run in `acceptEdits` and inherit your tool allowlist —
add commands the agents need to the allowlist first to avoid mid-run prompts.

---

## Behavior & limits

| Constraint | Why |
|------------|-----|
| No mid-run user input | Only agent permission prompts pause a run |
| No direct FS/shell from the script | Agents do the I/O; the script coordinates |
| ≤ 16 concurrent agents (fewer on limited CPU) | Bounds local resource use |
| 1,000 agents total per run | Prevents runaway loops |
| Resume only **within the same session** | Exiting Claude Code restarts the workflow fresh next session |

**Cost:** many agents → meaningfully more tokens than doing the task in conversation. Gauge
spend by running on a **small slice first** (one dir, narrow question); `/workflows` shows
per-agent token usage; stop anytime without losing completed work. Every agent uses your
session's model unless the script routes a stage elsewhere — check `/model` before a big run.

**Script location:** each run writes its script under the session dir in `~/.claude/projects/`.
Ask Claude for the path to read/diff/edit it and relaunch from the edited version.

**Disable:** `/config` toggle, `"disableWorkflows": true` in `~/.claude/settings.json`, or
`CLAUDE_CODE_DISABLE_WORKFLOWS=1`.

---

## Where workflows fit THIS repo (candidates, not commitments)

| Backlog item | Why it's a workflow shape |
|--------------|---------------------------|
| **LTG Phase 3 anchor design** | "Draft a plan from several independent angles" → fan out 3 design drafts, cross-review, recommend. The showcase use case. |
| **Backfill SOLID + error-handling directives across all coding personas** | Fan-out across many Modelfiles — audit each, propose constraint lines, one agent per file. |
| **Model survey refreshes** (cf. session 68's 5 manual research agents) | Exactly what `/deep-research` automates: cross-checked, cited, vote-filtered. |
| **`ref:KEY` / stale-reference integrity audits** | Codebase-wide sweep, independent agent per region. |

**Not a fit:** the LTG extractor retrofit close-out (small sequential punch-list, needs
interactive sign-off) — handled by a sub-agent + Task tracking instead.
