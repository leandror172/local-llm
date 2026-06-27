# Cache-Warmed Subagent Fan-Out (deferred task injection)

**Captured:** 2026-06-26 (session 97 discussion). Status: pattern + ready-to-use prompts; not yet exercised end-to-end with these exact templates.

A pattern for spawning **many subagents that share one large, expensive context** (the
project's contextualization reads) while paying for that context **once per model tier**, and
delivering each agent its task-specific instructions *after* it is warmed — without breaking the
prompt cache and without a race on the task hand-off.

It is the manual (Agent-tool + SendMessage) sibling of a dynamic workflow. See
`.claude/workflows-feature-guide.md` for when to prefer a workflow instead — the decision
section below draws the line.

---

<!-- ref:cache-warmed-fanout -->
## The protocol

Three phases, gated so the orchestrator (main session) controls timing:

1. **Phase 0 — Contextualize (on spawn).** Every agent receives an **identical** shared prompt:
   run `ref-lookup.sh list`, read the base files, learn the per-folder `.memories` rule. When
   done it replies **exactly `Ready`** and stops. The shared prompt is byte-identical across all
   agents of a tier, so it forms a cacheable prefix.
2. **Phase 1 — Receive task (on order).** Told to read its task, the agent **copies the task
   file to a private unique name** (`mktemp`), works only from the copy, and **never touches the
   original again**. It replies **exactly `copied`** (the ack) and stops. The ack tells the
   orchestrator it is now safe to overwrite the shared `tmp-task.md` for the next agent.
3. **Phase 2 — Work (on "proceed").** The agent reads its private copy, calls **advisor first**
   (≤3 total), applies the per-folder `.memories` rule for folders it will touch, and produces
   its output (a plan, or an implemented + verified change).

### Why each piece exists

- **Task delivered after warming, not in the spawn prompt.** Putting task specifics in the spawn
  prompt makes every agent's prompt diverge (no shared prefix → no cross-agent cache) *and* makes
  each agent start working immediately. Deferring the task keeps the prefix identical and gates
  execution. This was the failure mode of the first attempt.
- **Copy-to-unique + ack solves the hand-off race.** A single well-known `tmp-task.md` written
  serially while N agents read it is the same collision class the handoff stage/promote redesign
  fixed with UUID-named files (T-55/T-56). The copy freezes each agent's task into a private file;
  the `copied` ack gives the orchestrator an observable, safe point to overwrite the shared file
  for the next agent. (Alternative: write distinct `tmp-task-<N>.md` per agent and never
  overwrite — then the ack is belt-and-suspenders. Pick one; the templates below use the ack.)

### Why the cache actually holds (the load-bearing detail)

Anthropic prompt caching reuses the **longest cached prefix up to a breakpoint**, and breakpoints
land at **structural seams** — after system/tools and at **turn boundaries** — not mid-message.

- Here the shared context is **Phase 0 = turn 1**, and the task arrives in a **later turn**
  (via the "read your task" order). The shared block ends at a turn boundary → it gets its own
  cached breakpoint → every same-model agent reuses exactly that block.
- A naive workflow `agent(SHARED + TASK_N)` puts the shared/task seam **mid-message**, with no
  breakpoint the script can place there. Cross-agent reuse then extends only through system/tools;
  the big SHARED context is re-read per agent. **This is why the manual multi-turn pattern reuses a
  large shared context more reliably than a single-shot workflow agent.**

### Two hard constraints

- **Cache is per-model.** Opus planners and Sonnet implementers maintain **separate** cache
  lineages — a Sonnet agent cannot hit an Opus-warmed prefix. Warm each tier once (first agent of
  the tier pays the miss; the rest hit). For the prefix to share *within* a tier, every agent in
  that tier must get the **identical** shared prompt and the **same model**.
- **TTL ≈ 5 min, refreshed on every hit.** Warm, then spawn the rest promptly. If a tier goes idle
  longer than the TTL (e.g. a fast no-plan task finishes, then a gap while plans complete), the
  next agent pays a fresh miss. Keep a same-model agent active across the gap, or accept one miss.
<!-- /ref:cache-warmed-fanout -->

---

## Two-tier application (planner → implementer)

| Tier | Model | Effort | Isolation | Output |
|------|-------|--------|-----------|--------|
| Planner | Opus | medium thinking | none (text only) | a detailed, executable plan |
| Implementer | Sonnet | high (or higher) | **worktree** | implemented + verified change |

- **Planners need no worktree** — they emit text, mutate nothing.
- **Implementers run in worktrees** so parallel edits don't collide.
- **Pipeline trick:** tasks that need *no* plan (fully specified already) go straight to a Sonnet
  implementer and can launch **while the planners are still planning** — they double as the
  **Sonnet-tier cache warmer**, so the later plan-executing implementers hit an already-warm
  Sonnet cache.
- **Watch global side effects.** Worktrees isolate *files*, not GPU/model state. A task whose
  verification runs `ollama create` / a generate call (e.g. persona rebuilds) must run **alone and
  serially** — never fanned across parallel worktrees (12 GB VRAM, eviction contention).

### Operational note — per-spawn effort (resolved 2026-06-26)

The Agent tool exposes `model` and `isolation` per spawn, but **not** a reasoning-effort param
(only Workflow's `agent()` opts do). Confirmed via the Claude Code docs (subagent frontmatter
reference): the **only** way to vary effort per subagent is to bake it into a **subagent type
definition** — an `effort:` frontmatter field in a `.claude/agents/<name>.md` (or
`~/.claude/agents/`) file. Values: `low|medium|high|xhigh|max` (model-dependent); it **overrides**
session effort, and a definition with no `effort:` **inherits** the session's current effort.

So for "planners medium / implementers high": define two agent types, e.g. `plan-warm` with
`effort: medium` and `impl-warm` with `effort: high` (+ `model:` if you want it pinned), and spawn
by `subagent_type`. Setting session effort per-batch is the cruder fallback (applies to all
spawns uniformly).

---

## When to use this vs a dynamic workflow

| Use **this manual pattern** when… | Use a **workflow** when… |
|-----------------------------------|--------------------------|
| Tasks are assigned/reviewed **by hand**, with sign-off between phases | Tasks are known up front; **no mid-run user input** needed |
| A **large shared context** must be cached across agents (turn-boundary reuse) | Fan-out is **at scale** (dozens–hundreds); orchestration worth codifying |
| You want to stay in the loop (interactive pacing — this repo's preference) | The orchestration itself should be a **rerunnable script** |

For our 6-task batch (known tasks, but a **human review gate between planning and
implementation**, heavy shared context), the manual pattern wins. A workflow can't pause between
its planning and implementation stages — its remedy is "one workflow per stage," which fragments
the run. `ultracode` (`/effort ultracode`) would auto-author a workflow per substantive task; it
clashes with the review gate and is reserved for genuine scale-fan-outs (ref-integrity audits,
model-survey refreshes, large migrations).

---

## Ready-to-use shared prompts

Both tiers share Phase 0 and Phase 1 verbatim (keep them **byte-identical within a tier** so the
prefix caches). Only Phase 2 differs. Spawn with `run_in_background: true` and drive Phases 1–2
with `SendMessage`.

### Planner (Opus, medium thinking)

```
You are a PLANNING subagent. Produce a detailed, executable implementation plan for ONE task —
do NOT implement it. A separate implementation subagent will execute your plan later.

== Phase 0: Contextualize (do this now) ==
1. Run: .claude/tools/ref-lookup.sh list      (lists every ref:KEY)
2. Read in full:
   - .claude/index.md
   - .claude/session-context.md
   - .memories/QUICK.md
   - .memories/KNOWLEDGE.md
   - docs/patterns/code-design-conventions.md
3. Standing per-folder rule (applies in Phase 2 once you know which folders your task touches):
   if a folder has a .memories/ dir, read its QUICK.md; if your plan will edit a file in that
   folder, also read its KNOWLEDGE.md.
When Phase 0 is complete, reply with EXACTLY:
Ready
and nothing else. Then stop and wait.

== Phase 1: Receive your task (only when told to read it) ==
1. Copy the task file to a private, unique name and use ONLY the copy:
     t=$(mktemp ./tmp-task-XXXXXX.md) && cp tmp-task.md "$t"
2. Reply with EXACTLY:
copied
   and nothing else. Do NOT read the copy yet. Stop and wait.
Never read, reference, or write the original tmp-task.md again — only your "$t" copy.

== Phase 2: Plan (only when told to proceed) ==
1. Read your private copy ("$t").
2. Call advisor NOW — this MUST be your first advisor call, immediately after reading the task.
   You may call advisor at most 3 times total.
3. Apply the per-folder .memories rule for every folder your plan will touch.
4. Produce a DETAILED plan an implementer can execute without re-deriving context. It MUST cover:
   - Contextualization: tell the implementer to do the SAME Phase-0 reads + per-folder rule.
   - TDD: tests first — name the test file(s), the specific cases, and the red→green order.
   - Files to change and exactly where: paths, functions/sections, nature of each edit; call out
     any existing test surface that must NOT break.
   - Advisor use: implementer may call advisor up to 3 times, first after reading its task.
   - Verification: exact commands (bash wrappers — never python3 directly), expected results,
     and any acceptance check.
   - Conventions: named-method pattern (code-design-conventions.md); update .claude/index.md /
     ref blocks if files/sections are added; attribution if external code is used.
Return the plan as your final message. Implement nothing.
```

### Implementer (Sonnet, high effort, worktree)

```
You are an IMPLEMENTATION subagent. Execute ONE plan/task end to end with TDD, and verify it.
You are in an isolated git worktree — do not touch files outside your task's scope.

== Phase 0: Contextualize (do this now) ==
   [identical to the planner Phase 0 — reply EXACTLY "Ready", then stop]

== Phase 1: Receive your task (only when told to read it) ==
   [identical to the planner Phase 1 — copy to "$t", reply EXACTLY "copied", then stop]

== Phase 2: Implement (only when told to proceed) ==
1. Read your private copy ("$t") — it contains a detailed plan (or a fully-specified task).
2. Call advisor NOW — MUST be your first advisor call, right after reading the task; ≤3 total.
3. Apply the per-folder .memories rule for every folder you edit (read QUICK.md; read KNOWLEDGE.md
   before editing a file in that folder).
4. TDD: write the failing test(s) first, confirm RED, implement, confirm GREEN.
5. Honor conventions: named-method pattern (code-design-conventions.md); never invoke python3
   directly — use the bash wrappers (run-*.sh); update .claude/index.md / ref blocks if you add
   files/sections; add attribution if you use external code.
6. Verify exactly as the plan specifies (run the named wrappers; report pass/fail with output).
   Do NOT claim done if tests fail.
7. Commit only what the plan scopes.
Return a concise report: what changed, test results, deviations from the plan, follow-ups.
```

---

## Orchestrator (main session) loop

1. Warm the **Opus** tier: spawn 1 planner, await `Ready` (cache written). Spawn the rest;
   each replies `Ready`.
2. *(Optional, overlapping)* Warm the **Sonnet** tier with the no-plan implementers (e.g. T-59):
   spawn, await `Ready`.
3. For each agent: write its task to `tmp-task.md` → `SendMessage` "read your task" → await
   `copied` → (safe to overwrite for the next) → `SendMessage` "proceed".
4. Collect planner plans; review them (the human gate).
5. Feed approved plans to fresh Sonnet implementers (same shared prompt, worktree) — they hit the
   warm Sonnet cache. Drive Phases 1–2 the same way.

Related: `.claude/workflows-feature-guide.md` (workflow alternative), handoff stage/promote
UUID-file lesson (T-55/T-56), `docs/patterns/code-design-conventions.md` (named-method rule the
plans must enforce).
