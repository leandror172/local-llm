---
name: session-handoff
description: End-of-session workflow that updates all tracking files for continuity across Claude Code sessions. Use when wrapping up a session or when the user says they're done for now.
disable-model-invocation: false
argument-hint: "[optional summary of session focus]"
---

# Session Handoff Skill

You are closing out a Claude Code session. The tracking files (`session-log.md`,
`tasks.md`, `session-context.md`) ARE the handoff. Your job is narrow:

> **Decide what changed → author ONE payload file → make ONE call to the pipeline → report.**

A deterministic pipeline (`run-handoff.sh`) owns every mechanic: the date, the
session number, log rotation, locating each region, applying the edits, verifying
nothing outside a registered region moved, committing, and rolling back on failure.
**You do NOT read whole tracking files, compute dates or session numbers, run
rotation, or make per-section Edits.** You decide content; the pipeline does the
surgery. If the pipeline's verifier sees a byte change outside a registered region,
it rolls the whole transaction back — so authoring a clean payload is the whole job.

## What you're feeding: roles, modes, scalars

`run-handoff.sh --payload <file>` reads a payload you write and applies each section
to a **registered region**. A per-repo register (`registry.yaml`) maps each *role* to
a file + location + write mode. You author roles; you never name a file or a line.

Payload-authorable roles:

| Role | Mode | What you author |
|------|------|-----------------|
| `log-entry` | prepend | The new session-log entry, inserted newest-first |
| `current-status` | replace | Full updated interior of `ref:current-status` |
| `active-decisions` | replace | Full updated interior of `ref:active-decisions` |
| `reading-guide` | replace | Full updated interior of `ref:session-reading-guide` |
| `user-prefs` | replace | Full updated interior of `ref:user-prefs` (rarely changes) |
| `tasks-append` | append | Newly-discovered tasks, each a fresh `(T-NN)` line |

Plus two frontmatter **scalars** and a **checkoff list**:

- `session_title` → the "Current Session" header field (the pipeline applies it).
- `current_layer` → the "Current Layer" header field (the pipeline applies it).
- `checkoffs: [T-05, T-08]` → task ids completed this session; the pipeline flips
  `[ ]`→`[x]` by id, wherever they live in `tasks.md`.

The header fields and log rotation are **`nomodel`** — script-owned. **Never put them
in the payload as `## role:` sections.** The scalars above are how you influence them;
the pipeline refuses a `nomodel` role appearing as a block.

## Step 1 — Pre-flight (before you author anything)

1. **The tracking tree must be clean.** Run:
   ```
   git status --porcelain -- .claude/session-log.md .claude/session-context.md .claude/tasks.md
   ```
   If it prints anything, **STOP** and ask the user to commit or stash those files
   first. The pipeline aborts on a dirty tracking tree — catching it now avoids
   wasting the whole payload-authoring round-trip.

2. **Determine the session number** from context — you are closing a specific
   session, so you know it; if unsure, read the N from the latest `session-log.md`
   entry heading (one cheap line, not the whole file). Today's date comes from
   `date +%Y-%m-%d`. You write these into the `log-entry` heading; the pipeline
   independently maintains the header's counter, and the `--dry-run` in Step 4 lets
   you confirm the two agree before committing.

## Step 2 — Gather the session summary

From the conversation (seeded by `$ARGUMENTS` if the user supplied a focus), identify:

- **What was done** — tasks completed, files created/modified, decisions made.
- **What was decided** — design choices and deferred items, with rationale if non-obvious.
- **What's next** — the pending work / next task the following session should start with.
- **New gotchas** — anything surprising worth recording.
- **Uncommitted non-tracking changes** — to warn about at the end (never auto-commit).

Keep everything proportional to the session: a short session gets a short handoff.

## Step 3 — Fetch ONLY the replace-mode interiors you will edit

Replace-mode roles need their CURRENT interior so you can produce the full new one.
Fetch the small bounded block — **not the whole file** — via `ref-lookup.sh`:

```
.claude/tools/ref-lookup.sh current-status
.claude/tools/ref-lookup.sh active-decisions
.claude/tools/ref-lookup.sh session-reading-guide
.claude/tools/ref-lookup.sh user-prefs        # only if it actually changed
```

**Strip the marker lines.** `ref-lookup.sh` prints the block WITH its surrounding
`<!-- ref:KEY -->` and `<!-- /ref:KEY -->` lines. The payload section must carry ONLY
the **interior** between them — drop those two lines. Replace mode swaps the interior
in place; if you include the markers you duplicate them and the verifier rolls the
entire run back (it enforces a ref-marker-count invariant).

**Omit any replace-role whose content is unchanged this session.** The pipeline applies
only the roles PRESENT in the payload, so an omitted role is left byte-for-byte untouched
(`user-prefs` is usually omitted). Do not re-author a block just to restate it.

## Step 4 — Author the payload, then make ONE call

Write the payload to `.claude/local/handoff-pending.md` (gitignored; the pipeline
persists it verbatim as the run's `input.md`, so it doubles as a recovery artifact).

Format: frontmatter fenced by the **first two** `---` lines, then `## role: <name>`
sections. Section bodies may themselves contain `---` and `##` headings — only the
first two `---` and lines matching exactly `## role: <name>` are structural.

```
---
session_title: <topic for the Current Session header>
current_layer: <full Current Layer value>
checkoffs: [T-08, T-12]
---
## role: log-entry

## YYYY-MM-DD - Session N: <brief title>

### Context
<how this session started / its entry point>

### What Was Done
- <accomplishments>

### Decisions Made
- <key decisions, rationale if non-obvious>

### Next
- <what the next session starts with>

## role: current-status
<full updated interior of ref:current-status>

## role: reading-guide
<full updated interior of ref:session-reading-guide>

## role: tasks-append
- [ ] (T-NN) **<short label>** — <newly discovered task>
```

Notes on authoring:
- `log-entry` is **prepend** — write only the new entry; the pipeline puts it newest-first.
- replace roles carry ONLY the **interior** (the lines between the ref markers, markers
  stripped — see Step 3); the applier swaps the interior in place.
- `tasks-append` adds only NEW tasks. Use the `(T-NN)` convention for new entries
  (one past the highest `T-NN` id in tasks.md): `- [ ] (T-NN) **label** — …`
  Tasks discussed but not stored anywhere belong here — but this is judgment-based,
  so **list the candidates to the user and confirm before including them.**
- `checkoffs` accepts any alphanumeric id (`T-01`, `5.R1`, `RUI-4`, `1.0`). The
  locator finds the id anywhere within the first ~40 chars of an unchecked line, so
  existing tasks with `**ID**` or bare-number formats are checkable without reformatting.
  Do not restate completed tasks as prose — the id list is sufficient.

Then rehearse, inspect, and apply:

```
# 1) rehearse — validates locate/apply/verify, writes NOTHING:
.claude/tools/handoff/run-handoff.sh --dry-run --payload .claude/local/handoff-pending.md
# 2) inspect the reported regions + confirm the header session N matches your log entry
# 3) apply for real (atomic; rolls back on any verify failure):
.claude/tools/handoff/run-handoff.sh --payload .claude/local/handoff-pending.md
```

> In the overlay's **home** repo (where the pipeline lives in source, not installed),
> use `overlays/session-tracking/files/handoff/run-handoff.sh` and pass
> `--registry overlays/session-tracking/files/registry.yaml`.

## Step 5 — Report

Relay the pipeline's `RunReport`: committed (with the session number) or rolled-back
(with the reason), and the regions touched. Then, if `git status` shows uncommitted
changes to **non-tracking** files, list them and ask whether the user wants to commit —
do NOT auto-commit. Finish with a short confirmation that the session is ready to close.

## Important rules

- **One payload, one call.** No per-section Edits, no whole-file reads on the write path.
- **Don't recompute** date, session number, or rotation — the pipeline owns them.
- **Never** put `nomodel` roles (the `header-*` fields, rotation) in the payload as sections.
- **Omit** unchanged replace-roles entirely.
- If the run rolls back, read the reason, fix the payload, and re-run — the tracking
  files were restored, so it is safe to retry.
- Do not create separate `session-handoff-*.md` files; the tracking files are the handoff.
- Do not start new project work after the handoff — the session is ending.
