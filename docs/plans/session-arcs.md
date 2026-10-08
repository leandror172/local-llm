# Session arcs — named, resumable, harness-neutral session tracking

**Created:** 2026-10-08 — designed in a Claude Code session on `feat/session-arcs`; no session number assigned (see § "The live case")
**Branch:** `feat/session-arcs` (from master `71c1fa0`)
**Status:** PLAN — decisions ARC-D1…ARC-D15. **ARC-D1–D5 decided by the user**; ARC-D6's direction decided, its mapping open; the rest open with leans. **No code written.**
**Extends:** `docs/plans/session-handoff-pipeline-design.md` (`ref:handoff-pipeline-design`), `docs/plans/resume-config-steps.md` (R-D1…R-D9).
**Touches:** `overlays/session-tracking/` (package + overlay); `overlays/session-tracking/KNOWN-ISSUES.md` #1 (ARC-D7 is its plural form).
**Not to be confused with:** `ref:multi-session-contention` and its siblings — those are T-102, concurrent sessions contending for the **GPU**, not for tracking state.

---

## What the user asked for

Two requirements, stated across one design discussion (2026-10-08):

1. **Named, context-specific sessions** — a named unit of work, detached from whatever the harness
   calls its conversation, identified "at some point (when resuming or handing off)". A handoff
   writes files specific to it; a later session — in Claude Code, or *maybe* Codex — resumes it. A
   shared context plus a per-unit context. Ideally each unit owns a branch/worktree: hand off, start a
   new harness session, resume in the same worktree. Cleanup of accumulated units: needed eventually,
   **not in v1**.
2. **Harness neutrality** — a neutral folder instead of `.claude/`, compatibility with Codex (skills,
   tools), and **at work, nothing committed**: tracking data may live in an external folder
   (OneDrive), not merely gitignored.

## Today's design assumes one writer and one harness

<!-- ref:session-arcs-single-writer -->
### Single-writer assumptions (measured 2026-10-08)

| # | Assumption | Where | Failure under concurrent sessions | Signal |
|---|---|---|---|---|
| 1 | Replace-mode regions are singletons: `current-status`, `active-decisions`, `reading-guide`, the "Current Session" header | register roles; clean-tree precondition `orchestrator.py:47` | B fetched an interior before A's handoff committed; B's pre-flight passes (the tree is clean again); B's replace erases A's update | **Silent** in one checkout — the verifier guards bytes *outside* registered regions only. A loud merge conflict across worktrees |
| 2 | `(T-NN)` task ids: the model picks max+1 | skill prose | two sessions file the same id | **Silent at creation, loud at checkoff** — `locator.py:150` refuses an ambiguous id, possibly sessions later |
| 3 | Harvest boundary = newest `chore(session-handoff): session ` commit | `handoff-harvest.sh:28` | on a shared branch, B sweeps A's commits or loses its own pre-A commits | Silent (misattribution) |
| 4 | Session number = max heading + 1, computed **at handoff** | `mechanics.py:97`, `:164` | two worktrees both mint the same N | Loud — a conflict in the one shared `session-log.md`. **Becomes silent once entries live in per-arc files** (ARC-D5) |
| 5 | Every session hands off | the workflow | a session that never hands off is invisible; the next harvest on its branch credits its commits to whoever runs next | Silent. **Live instance:** § "The live case" |
<!-- /ref:session-arcs-single-writer -->

### Harness coupling — smaller than it looks

- **The engine is harness-neutral already.** `st-handoff`/`st-resume` are CLIs over git and markdown;
  harvest reads `git log`, not transcripts.
- **`.claude` is hardcoded at ~10 code sites, all from one root:** `handoff/cli.py:56`,
  `handoff/runlog.py:40,47,88`, `handoff/mechanics.py:153`, `handoff/orchestrator.py:242`,
  `resume/cli.py:36,45`, `resume/steps.py:216` (plus error-message strings). The register's `file:`
  paths are already config.
- **The rules file:** session rules are merged into `CLAUDE.md`; Codex reads `AGENTS.md`. "Run resume
  on session start" never reaches a Codex session.
- **Skill and hook install locations** differ per harness (§ "Unverified").
- **`agent_targets:` is declared in all three overlay manifests and consumed by nothing** —
  `install-overlay.py` never reads it. The multi-harness seam exists as dead config: the
  `ref:declared-unconsumed-spec-fields` shape.

<!-- ref:session-arcs-vocabulary -->
## Vocabulary

| Term | Meaning |
|---|---|
| **arc** | A named, context-specific line of work spanning several harness sessions; ideally 1:1 with a branch/worktree. In instructions to agents write **"tracking arc"** — the qualifier keeps a model from conflating it with a team's or a platform's "workstream" (two live meanings at the user's work). |
| **session** | One harness conversation (Claude Code, Codex). Its handoff writes one **session entry**. |
| **key** | An arc's short identifier (`HR`). It mints the arc's session handles and task ids (ARC-D5). |
| **handle** | A session entry's citable id: `HR#3` inside an arc, `s141` outside any arc. |
| **shared context** | Tracking state every arc reads: decisions, preferences, pointers, the backlog. |
| **arc context** | Tracking state only its own arc writes: status, Next, reading guide, entries. |
<!-- /ref:session-arcs-vocabulary -->

Names rejected (2026-10-08): `workstream` (two meanings at the user's work), `thread` (Codex app),
`epic`/`story`/`lane` (agile/Jira), `saga` (the distributed-transaction pattern),
`squad`/`chapter`/`guild` (org structures), `topic` (LTG). Runners-up: `strand`, `trail`, `track`,
`dossier`.

## Decision register

| ID | Decision | State |
|---|---|---|
| ARC-D1 | The unit is an **arc** | **Decided** (user) |
| ARC-D2 | Storage: **in-branch by default**, plus an **external** mode | **Decided** (user) |
| ARC-D3 | Root folder **`.tracking/`**, configurable | **Decided** (user); the back-compat default `.claude` is a lean |
| ARC-D4 | Two install profiles: **in-repo** and **zero-footprint** | **Decided** (user) |
| ARC-D5 | Numbering **B — per-arc keys** | **Decided** (user, after comparing A/B/C) |
| ARC-D6 | Shared vs arc context split | Direction **decided** (user); role mapping **open** |
| ARC-D7 | Ref-key namespace for arc files | **Open** — new constraint; lean (b) |
| ARC-D8 | Arc lifecycle status in v1 | **Open** — lean: required |
| ARC-D9 | Repo identity for the user-level config | **Open** |
| ARC-D10 | External-mode concurrency guard | **Open** — lean: required for external mode |
| ARC-D11 | Starting vs adopting an arc | **Open** |
| ARC-D12 | Two sessions on the same arc at once | **Open** — lean: refuse |
| ARC-D13 | Key uniqueness and retirement | **Open** |
| ARC-D14 | Harness adapters via `agent_targets` | **Open** — lean: make it live |
| ARC-D15 | Rules-file layout for the in-repo profile | **Open** — lean: `AGENTS.md` canonical |

### ARC-D1 — The unit is an arc *(decided)*

See § Vocabulary. It pairs with "session": an arc spans sessions, so "session" keeps meaning the
harness conversation and nothing existing is renamed.

<!-- ref:session-arcs-storage-modes -->
### ARC-D2 — In-branch by default, external as a mode *(decided)*

**In-branch:** an arc's folder is committed on its branch, travels with the code and merges with the
PR. A harness started inside the arc's worktree sees its own files. Listing arcs from elsewhere needs
no stored index: `git worktree list`, or `git ls-tree <ref> <root>/arcs/` per branch.

**External:** the tracking root is a path outside the repo (e.g. a OneDrive folder), for repos where
nothing may be committed. The setting that names that path cannot live inside it, so it comes from a
**user-level config keyed by repo** (e.g. `~/.config/session-tracking/repos.yaml`), overridable by an
environment variable. Nothing is written into the repo.

**Git does four jobs in today's transaction; external mode must replace each:**

| Job | Today (`orchestrator.py`) | External mode |
|---|---|---|
| Precondition | `git.is_clean(touched)` (`:47`) | the tracking files are unchanged since the session read them |
| Rollback | `git.checkout(...)` (`:82`) | snapshot before writing, restore on failure |
| Persist | `git.add` + `git.commit` (`:79–80`) | none — the write is the record |
| Harvest boundary | newest handoff commit by subject (`handoff-harvest.sh:28`) | `last_handoff_head` recorded in the arc's metadata |

**The seam exists:** `run_handoff()` receives `git` as an injected dependency (`orchestrator.py:36`),
so external mode is a second implementation of that dependency, not a rewrite of the pipeline.

**Adopt the recorded boundary in BOTH modes.** `git log <last_handoff_head>..HEAD` removes the
dependence on commit-subject wording, which ARC-D5 changes anyway. When the SHA is unreachable
(rebase, squash), fall back to the legacy subject grep, then to the last-20 fallback, each with a
stderr note.

**The safety story differs by mode.** In-branch, concurrent edits to shared files become loud merge
conflicts. External mode has no merge: lost updates are silent again, and OneDrive adds its own silent
failure — conflict copies such as `context-LAPTOP.md`. Hence ARC-D10.
<!-- /ref:session-arcs-storage-modes -->

### ARC-D3 — Root `.tracking/` *(decided)*

```
.tracking/                      # external mode: <external-root>/<repo-id>/
  context.md                    # shared context
  tasks.md                      # shared backlog
  config/
    registry.yaml               # today: .claude/handoff/registry.yaml
    resume.yaml                 # today: .claude/resume.yaml
  arcs/<name>/
    arc.yaml                    # key, branch, worktree, status, created, last_handoff_head; ticket (optional)
    context.md                  # arc context: status, Next, reading guide
    sessions/<NNN>-<slug>.md    # one entry per handoff
```

The root is a config value, and **its default stays `.claude`** so the other four repos on v11 change
nothing until they opt in (§ Migration). Tracking files are project memory, not harness config — they
sat in `.claude/` only because Claude Code was the first harness, so the move is a reclassification,
not a rename. Out of scope: `.claude/tools/ref-lookup.sh` and its siblings belong to the ref-indexing
overlay, and Codex can run scripts from any path, so their location is not a Codex blocker.

### ARC-D4 — Two install profiles *(decided)*

| | **In-repo** (personal repos) | **Zero-footprint** (work) |
|---|---|---|
| Tracking data | `.tracking/`, committed | external root (OneDrive), named by user-level config |
| Rules | repo `AGENTS.md` (+ `CLAUDE.md` import, ARC-D15) | user-level: `~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md` |
| Skill | per harness, user- or project-level | user-level only, per harness |
| SessionStart hook | optional | user-level; **silent in repos with no tracking configured** (the current shim's exit-0 guard) |
| Worktrees | anywhere | **outside the repo** (a sibling `../<repo>.arcs/<arc>/`), so the repo shows no untracked dirs |
| Local-only ignores | `.gitignore` | `.git/info/exclude` — never the shared `.gitignore` |

The user confirmed that "don't commit" also covers rules, skills and hooks (2026-10-08).

<!-- ref:session-arcs-numbering -->
### ARC-D5 — Numbering B: per-arc keys *(decided)*

**Every id is minted by its only writer.** An arc has one writer (its branch/worktree), so anything it
numbers cannot collide, and no allocator is needed.

- **Session handle:** `KEY#N` (`HR#3`) — as short in prose as `s141`.
- **Task id:** `KEY-N` (`HR-7`).
- **Key format:** starts with a letter; letters and digits only — **no hyphen**. Checkoff's matcher
  (`locator.py:140`) treats letters, digits and `.` as id-internal but not `-`, so a hyphenated key
  could contain another id (`T-7` inside `HR-T-7`). Digits allow ticket-derived keys
  (`PLAT-1234` → `PLAT1234`); an optional `ticket:` field in `arc.yaml` is the alternative.
- **A key is never reused**, including after its arc is closed (ARC-D13).
- **`s` and `T` are reserved for work outside any arc.** The main checkout is a single writer too, so
  `s141`/`T-142` continue there. `s1–s140` and `T-1…T-141` are never renumbered.
- **Chronology** across arcs is a generated view sorted by entry timestamp, never a stored list.

**Why the global baseline is out, not merely worse:** it was safe only because every entry went into
one shared file, so a duplicate `s141` surfaced as a merge conflict. ARC-D6 moves entries into per-arc
files, which never conflict — **the split that makes content conflicts loud makes number collisions
silent.** A global scheme would now need a real allocator.

**Compared (2026-10-08):** **A** — global `sN`/`T-NN` from a lock + counter in
`git rev-parse --git-common-dir` (safe on one machine; an allocation at every session and task;
seamless continuity). **B** — per-arc keys (no coordination; one allocation per arc, the key;
provenance in the id; two schemes coexist). **C** — per-arc sessions, globally allocated tasks. The
user's inputs: tasks are cited more, but that does not count against B — no id names its subject, and
tasks already record where they were found in prose, so that argument was withdrawn; two coexisting
schemes are acceptable if nothing breaks; arcs map to tickets "with a reasonable chance, not always".

**"If nothing breaks" — checked.** Every code site that parses either kind of id is inside
session-tracking. Task ids: `payload.py:314` and `locator.py:140`, which **already accept `HR-7`**
(the id check is `^[A-Za-z\d][A-Za-z\d.\-]*$`, widened in session 86). Session numbers and handoff
subjects: `mechanics.py:164`, `payload.py:159`, `rotate-session-log.sh:59,75,77`,
`orchestrator.py:250`, `cli.py:150`, `handoff-harvest.sh:28` — all rewritten by this plan anyway.
Hooks, mcp-server, LTG and `scripts/` mention `T-NN` only in comments.
<!-- /ref:session-arcs-numbering -->

### ARC-D6 — Shared vs arc context *(direction decided; mapping open)*

The user's direction: a central/shared context plus one context per arc. Proposed mapping of today's
register roles:

| Role | Today | Proposed | Reason |
|---|---|---|---|
| `log-entry` | `session-log.md` (newest only) | **arc**: `sessions/<NNN>-<slug>.md` | single writer |
| `header-current-session`, `header-current-layer` | `session-log.md` header | **arc**: `arc.yaml` / arc context | a singleton per arc |
| `current-status` | one block | **split**: arc status + Next / shared environment and cross-repo notes | today's block is mostly one line of work |
| `reading-guide` | one table | mostly **arc**; cross-cutting rows (verdict recording, running tests) **shared** | most rows today are P3-specific |
| `active-decisions`, `user-prefs`, `quick-pointers` | `session-context.md` | **shared** | cross-cutting, low churn |
| `tasks-append`, `tasks-checkoff` | `tasks.md` | **shared**, ids per ARC-D5 | the backlog is project-wide |

**The split is most of the concurrency fix.** The regions rewritten every session move into
single-writer files, so what stays shared changes rarely — and in in-branch mode its rare collisions
surface as merge conflicts, not silent overwrites. Two residues:

- **Parallel arcs appending tasks** at the same block end still conflict at merge, even with unique
  ids. Candidate: `merge=union` on the shared tasks file (in-repo profile), safe once ids cannot
  collide. **Unverified** — see § "Unverified".
- **Register schema:** each role gains `scope: shared | arc`, and arc-scoped paths are templated
  (`arcs/{arc}/context.md`) → register `version: 2`.

### ARC-D7 — Ref-key namespace for arc files *(open — new constraint)*

If every `arcs/<name>/context.md` carries the same ref-block keys (`current-status`,
`session-reading-guide`, …), those keys are duplicated repo-wide:

- `ref-lookup.sh` emits **one line per key**, so it can resolve only one of them.
- `check-ref-integrity.py` reports a duplicate definition as an **ERROR** and exits 1 — which gates
  commits wherever the ref-indexing pre-commit hook is active. (In this repo it is not: `core.hooksPath`
  is unset and `.githooks/pre-commit` is `100644`, the T-138 class. Baseline on master, 2026-10-08:
  39 errors, 169 warnings.)
- The session-tracking locator itself is unaffected — `ref_block` lookup is per file.

This is the plural form of `KNOWN-ISSUES.md` #1: the two overlays disagree about what "consumed"
means. Options:

- **(a) Templated keys per arc** (`arc-HR-status`) — unique, but every arc mints keys and the namespace
  grows with arcs.
- **(b) Arc files use non-ref-block locators** — the register already supports `structural` and
  `field` locators. Arc files are owned by session-tracking alone and need not join the ref namespace.
- **(c) Exclude `<root>/arcs/` from ref-indexing scans.**

**Lean: (b).** It keeps ref-indexing's namespace for content agents look up by key, while arc files
are reached through the register, never by key. External mode is unaffected either way — ref-indexing
never scans outside the repo.

### ARC-D8 — Arc lifecycle status in v1 *(open — lean: required)*

Cleanup is deferred (user), but status is not cleanup. In in-branch mode a merged arc's folder lands on
master; without `status: open | merged | closed` in `arc.yaml`, a resume from master lists every arc
ever merged as open. Lean: v1 records status; deleting or archiving arc folders stays deferred.

### ARC-D9 — Repo identity for the user-level config *(open)*

Zero-footprint mode looks up the external root by repo, and the lookup must give the same answer from
every worktree. Candidates: `git rev-parse --git-common-dir` (stable across worktrees; changes if the
clone moves) vs the remote URL (stable across moves; shared by multiple clones). Decide together with
ARC-D10's two-clone note.

### ARC-D10 — External-mode concurrency guard *(open — lean: required for external mode)*

The payload records a hash of each shared region it was based on, and the pipeline refuses if the
region changed since — a loud refusal, the repo's standing shape. Also detect OneDrive conflict copies
(a `*-<MACHINE>.*` file beside a tracking file) and refuse while one exists. Two clones sharing one
external root: documented as unsupported in v1.

### ARC-D11 — Starting vs adopting an arc *(open)*

- **Start named:** create branch + worktree + arc folder before work begins.
- **Adopt:** bind the current branch to a new arc at handoff. Moving it into a worktree later requires
  freeing the branch from the main checkout — git will not check out one branch twice — which changes
  the user's checkout, so the git-safety protocol applies (explain → backup → dry-run → execute →
  verify). A separate, explicit step; never folded into the handoff.

### ARC-D12 — Two sessions on the same arc *(open — lean: refuse)*

Per-arc numbering assumes one writer per arc; two harness sessions in one worktree break that. Lean: at
write time, refuse if `sessions/<NNN>-*` already exists for the number about to be minted.

### ARC-D13 — Key uniqueness and retirement *(open)*

A key is checked once, at arc creation: against local branches (`git ls-tree` per ref), worktrees, and
the external root. A closed arc keeps its key reserved — a retired key must still block reuse after
cleanup exists.

### ARC-D14 — Harness adapters via `agent_targets` *(open — lean: make it live)*

Per harness: the rules-file target, the skill install path, the hook install path. `agent_targets:`
already names `tools_dir` and `rules_file` for `claude-code` in three manifests and is read by
nothing. Make it live (add `codex`) or delete it — leaving it declared is the
`ref:declared-unconsumed-spec-fields` shape.

### ARC-D15 — Rules-file layout, in-repo profile *(open — lean: `AGENTS.md` canonical)*

`AGENTS.md` carries the session rules; `CLAUDE.md` imports it with `@AGENTS.md`. The `@` import is
already proven on this machine — the user's global `CLAUDE.md` imports `@RTK.md` and `@WSL.md`.
Codex's `project_doc_fallback_filenames` is the alternative, but it is user-level Codex config, so it
does not answer the repo-level question.

<!-- ref:session-arcs-unverified -->
## Unverified — test before freezing

Nothing below may be encoded as a path or a behaviour until it is checked.

| Claim | Source | Check |
|---|---|---|
| Codex repo skills live in `.agents/skills/` (walked from cwd up to the repo root); user skills in `~/.agents/skills/` | official skills page — but the official create-skill page uses `.codex/skills/` | read the Codex source: `github.com/openai/codex`, Apache-2.0, public (verified 2026-10-08) |
| Codex SKILL.md: `name` ≤100 and `description` ≤500 chars, single line; extra frontmatter keys ignored | official skills page | source |
| Codex has SessionStart/Stop hooks, configured in `.codex/hooks.json` **or** a `[hooks]` table in `config.toml` | third-party only, mutually contradictory | source |
| Codex reads `AGENTS.md` from root to cwd; `project_doc_fallback_filenames` exists | official AGENTS.md guide | low risk; confirm on install |
| `codex --oss` runs against local Ollama with **no login** | Ollama docs + third parties | install and run. **Verified here:** `/v1/models` answers HTTP 200 on both `:11434` and `:11435`. Codex recommends ≥32K ctx while the 14B personas run 16K — enough to check skill discovery, `AGENTS.md` loading and hook firing, not for real work |
| Claude Code does not read `.agents/skills/` | assumption | if false, one skill copy could serve both harnesses |
| `merge=union` on the shared tasks file keeps both sides' appended lines and leaves ref-block markers intact | git docs, recalled from memory | a **two-branch merge fixture**: (1) both branches append different tasks → both present, marker count unchanged (the handoff verifier enforces a ref-marker-count invariant); (2) both check off the same task → expect a duplicated line and a loud refusal at the next checkoff (`locator.py:150`); (3) one appends while the other checks off → clean |
<!-- /ref:session-arcs-unverified -->

## Migration — v11 → v12

- **Opt-in.** The root defaults to `.claude` and storage to in-branch, so a repo that changes nothing
  keeps working. All five tracked repos run v11.
- **Register `version: 2`** (role `scope:`, templated arc paths). `registry_io.load_register` already
  validates `version:` against `SUPPORTED_REGISTER_SCHEMA`, refuses unknown values and treats an
  absent key as 1 — the existing mechanism.
- **Legacy stays readable:** `session-log.md` and its 95 archived entries are not rewritten;
  `s1–s140` / `T-1…T-141` remain valid citations; work outside any arc continues `sN` / `T-NN`.
- **Code sites rewritten:** the parsers listed under ARC-D5, plus the `.claude` literals listed under
  "Harness coupling".
- **Harvest:** `last_handoff_head` when an arc records one; the legacy subject grep otherwise.

## The live case

`feat/p3-d10-freeze` holds **4 commits from 2026-09-08** (P3-D10 frozen, the locator graduated into
`LanguagePack`, step 1 recorded) that are in no PR and no handoff — and, verified 2026-10-08, **on no
remote**: the branch is local-only. The newest session-log entry is still s140, whose Next ("Freeze
P3-D10") that branch already did. It is single-writer assumption #5, live — and the natural first
**adopt** (ARC-D11), as an oficina-P3 arc.

It is also #4 in miniature. If this design session hands off on `feat/session-arcs` under today's
scheme, and the P3 branch later hands off too, **both mint `s141`** on different branches, and nothing
reports it until two documents cite `s141` for different sessions. Whichever hands off second should
do so as an arc, or after the first has merged.

## Non-goals for v1

- Cleanup / retention of arcs (deferred by the user) — beyond recording status (ARC-D8).
- Two clones or machines sharing one external root.
- Harness-neutral verdict capture (T-107 / T-109 — a different overlay).
- Registering the ollama-bridge / LTG MCP servers with Codex.
- Moving ref-indexing's tools out of `.claude/tools/`.

## Sources

- Codex Agent Skills — https://developers.openai.com/codex/skills
- Codex create-skill — https://developers.openai.com/codex/skills/create-skill
- Codex AGENTS.md guide — https://developers.openai.com/codex/guides/agents-md
- Codex hooks deep dive (third-party) — https://codex.danielvaughan.com/2026/03/26/codex-cli-hooks-deep-dive
- Ollama: Codex — https://docs.ollama.com/codex
- Codex CLI source — https://github.com/openai/codex
