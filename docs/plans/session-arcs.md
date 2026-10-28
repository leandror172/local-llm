# Session arcs — named, resumable, harness-neutral session tracking

**Created:** 2026-10-08 — designed in a Claude Code session on `feat/session-arcs`; no session number assigned (see § "The live case")
**Branch:** `feat/session-arcs` (from master `71c1fa0`)
**Status:** PLAN — decisions ARC-D1…ARC-D15. **ARC-D1–D5 decided by the user**; ARC-D6's direction decided, its mapping open; the rest open with leans. **Codex behaviour verified from source** (2026-10-08) **and live** (2026-10-10 / 2026-10-22, codex-cli 0.162.1; Claude Code 2.1.308) — § "Codex facts"; `merge=union` measured unsafe (ARC-D6). **No code written.**
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
- **Skill and hook install locations** differ per harness (§ "Codex facts").
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
| ARC-D6 | Shared vs arc context split | **Decided** (user, 2026-10-28) |
| ARC-D7 | Ref-key namespace for arc files | **Decided** (user, 2026-10-28): **(b′)** an `arc:` marker prefix |
| ARC-D8 | Arc lifecycle status in v1 | **Decided** (user, 2026-10-28): store `open \| closed` + the current `branch`; derive the rest from git |
| ARC-D9 | Repo identity for the user-level config | **Open** |
| ARC-D10 | External-mode concurrency guard | **Open** — lean: required for external mode |
| ARC-D11 | Starting vs adopting an arc | **Decided** (user, 2026-10-28): `start` / `adopt` / `bind`, plus the handoff asks; no worktree conversion in v1 |
| ARC-D12 | Two sessions on the same arc at once | **Decided** (user, 2026-10-28): a stale-base check in every mode + a bound-branch check (the entry-number check is dropped) |
| ARC-D13 | Key uniqueness and retirement | **Decided** (user, 2026-10-28): three refusal checks at creation; uppercase, 2–6 chars |
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
| Skill | one source, installed per harness: `.claude/skills/` + `.agents/skills/` | one source, installed per harness: `~/.claude/skills/` + `~/.agents/skills/` |
| SessionStart hook | optional. Codex takes project hooks from the **main checkout's** `.codex/`, so one definition serves every arc worktree | user-level (`~/.claude/settings.json`, `~/.codex/hooks.json`); **silent in repos with no tracking configured** (the current shim's exit-0 guard) |
| Worktrees | anywhere | **outside the repo** (a sibling `../<repo>.arcs/<arc>/`), so the repo shows no untracked dirs |
| Local-only ignores | `.gitignore` | `.git/info/exclude` — never the shared `.gitignore` |

The user confirmed that "don't commit" also covers rules, skills and hooks (2026-10-08).

<!-- ref:session-arcs-numbering -->
### ARC-D5 — Numbering B: per-arc keys *(decided)*

**Every id is minted by its only writer.** An arc has one writer (its branch/worktree), so anything it
numbers cannot collide, and no allocator is needed.

- **Session handle:** `KEY#N` (`HR#3`) — as short in prose as `s141`.
- **Task id:** `KEY-N` (`HR-7`).
- **Key format:** starts with a letter; uppercase letters and digits only, 2–6 characters
  (ARC-D13) — **no hyphen**. Checkoff's matcher
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
| `reading-guide` | one table | **split by row** — see "Decided" below | measured 2026-10-28: 6 arc-specific, 6 oficina-wide, 11 cross-cutting of 23 (an earlier "mostly P3-specific" was wrong) |
| `active-decisions`, `user-prefs`, `quick-pointers` | `session-context.md` | **shared** | cross-cutting, low churn |
| `tasks-append`, `tasks-checkoff` | `tasks.md` | **shared**, ids per ARC-D5 | the backlog is project-wide |

**The split is most of the concurrency fix.** The regions rewritten every session move into
single-writer files, so what stays shared changes rarely — and in in-branch mode its rare collisions
surface as merge conflicts, not silent overwrites. Two residues:

- **Parallel arcs appending tasks** at the same block end still conflict at merge, even with unique
  ids. The candidate fix, `merge=union` on the shared tasks file, was **measured and is UNSAFE**
  (2026-10-22: a two-branch fixture per case, judged by the real checkoff locator, not by a grep):

  | Case | Merge | Result |
  |---|---|---|
  | both append different tasks | clean | ✓ both kept, ref markers 1/1. Without union: a conflict — the control |
  | both check off the same task | clean | ✓ one line |
  | **one appends after T-2 while the other checks off T-2** (adjacent lines) | **clean, exit 0** | **T-2 resurrected as an open duplicate** beside its checked copy — and checkoff later *succeeds* on the open copy, so nothing ever reports it |
  | one checks off T-1 while the other edits its text | clean | **same resurrection** |
  | both edit T-1's text | clean | two open T-1 lines → the next checkoff **refuses** (the only loud case) |

  The checkoff locator matches only **unchecked** lines (`locator.py:146`), so a resurrection that
  pairs a checked and an unchecked copy is invisible to it. And the adjacent case is the *common*
  one: appends land at the block end, next to the newest — most likely to be closed — task.
  **Remaining options:** (a) **per-arc task files** — each arc appends only to its own
  `arcs/<name>/tasks.md` (single writer, ARC-D5's principle again), with the shared backlog a
  generated view and legacy `T-NN` tasks staying in the shared file; (b) plain merges, accepting a
  loud conflict whenever two arcs both file tasks. **Lean: (a)** — but an arc's still-open tasks must
  then outlive the arc, which ties this to ARC-D8.
- **Register schema:** each role gains `scope: shared | arc`, and arc-scoped paths are templated
  (`arcs/{arc}/context.md`) → register `version: 2`.

**Decided (user, 2026-10-28)** — each choice measured against what today's regions actually hold:

1. **The session digest is GENERATED.** Today 15 of `current-status`'s 19 top-level bullets are
   per-session summaries written by hand beside the log entry. Each session entry now carries its
   own one-paragraph `summary:`, authored once at handoff; "recent sessions" renders the newest N
   across arcs. **A later session may correct an earlier entry's summary in place, with a dated
   note** — 1 of the 15 digests (s137) carries exactly such a correction by s139, and a view built
   from immutable entries would silently re-show the claim that was retracted.
2. **The watch list stays HAND-WRITTEN.** "Open deferred tasks" is *not* a restatement of
   `tasks.md`, as this doc first assumed. It annotates 32 of the 76 open tasks; all 32 exist in
   `tasks.md` and 28 of the notes mostly overlap their task line word-for-word — but the bullet
   carries what `tasks.md` does not: **which** tasks matter now (the selection), and **live
   progress** (T-132's "now SIX sessions behind at 217 lines" appears nowhere in `tasks.md`).
   Generating it would drop both. It becomes a watch-list region, split arc / shared.
3. **"Next" lives in the arc only** — today it is written twice, in `current-status` and in the
   log entry, and resume prints both.
4. **Header fields:** "Current Session" is dropped (it is the newest entry); "Current Layer"
   becomes a `phase:` in each `arc.yaml` plus one shared project-status line.
5. **Tasks:** per-arc task files. A **general** task found inside an arc may still go to the shared
   file (user) — **but its id is still minted by the filing session's key** (`HR-9`), or two arcs
   each minting `T-142` at once brings back the collision ARC-D5 removed. So the id no longer
   names its file; checkoff searches every task file, which is safe because ids are unique by
   construction. Two arcs appending to the shared file conflict loudly at merge — no `merge=union`.
   On arc close, its open tasks move to the shared file **keeping their ids** (ARC-D8).
6. **The reading guide splits by row.** Measured over its 23 rows:

   | Home | Rows |
   |---|---|
   | **arc** (oficina-P3) | 1 P3-D1 frozen / criterion 3 · 3 superseded probe framing · 5 before designing the edit schema · 6 correct claim corrupted (P3 artifacts) · 12 prompt assembly · 15 T-122 feasibility band |
   | **developing oficina ⚑** | 9 before authoring a phase plan · 11 before touching `judge.py` · 20 oficina, the built system |
   | **shared** | 2 delegating — the brief · 4 prior art before a survey · 7 verify a task's premise · 8 a falsified claim survives · 10 before deleting a declared-unused field · 13 a check that can only pass · 14 magnitude and reachability · 16 a tool's silence as evidence · 17 delegating — what works · 18 using LTG · 19 recording a verdict · 21 running tests · 22 asserting a set is complete · 23 LTG engine / instance |

   An oficina-P3 session sees all 23, exactly as today; a session in any other arc sees 14.
   **A first pass grouped six rows as "oficina-wide" and conflated two audiences** (user,
   2026-10-28): rows 2 and 17 are advice for *using* oficina — which is machine-global, so any
   session delegating code needs them, like "using LTG" (18) — and row 10 is a general lesson with
   an oficina example. Only 9, 11 and 20 are about *developing* oficina. (Row 17's one clause about
   `intake.py` being undelegable on the 16K coder is development-specific; it rides along.)
   **Decided (user, 2026-10-28): (ii)** — the three development rows live in the oficina-P3 arc.
   When a second oficina arc exists, copy them into it, and only then promote them to the folder
   memory `docs/vision/coding-delegate/.memories/` that row 20 already points to —
   `ref:patterns-refactoring-duplicate-first`: extract once a second consumer is real. (Rejected:
   (i) shared, which shows three development-only rows to every arc.)

### ARC-D7 — Ref-key namespace for arc files *(decided: (b′))*

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

**Decided (user, 2026-10-28): (b′) — the `ref:` block syntax with an `arc:` prefix**
(`<!-- arc:status -->` … `<!-- /arc:status -->`), refining (b): the register already *has* a span
locator (`ref_block`), so (b′) parametrises its prefix instead of inventing a new locator type.
Measured: all four consumers of block markers match only the literal `ref:` prefix —
`check-ref-integrity.py:22` (`RE_OPEN`), `ref-lookup.sh:48,65`, the LTG engine's `markers.py:34-44`,
and the handoff verifier's `_collect_markers` (`verifier.py:120`). So arc blocks are invisible to
ref-indexing and LTG with **no change to either overlay** — and invisible to session-tracking's own
verifier too, which is the trap:

- **Requirement:** the verifier's marker-set invariant must count `arc:` markers as well. Without
  it, a payload that duplicates or drops an arc marker passes verification silently.
- **Rejected:** (a) per-arc `ref:` keys (the namespace grows with arcs; every arc's blocks are
  orphan warnings); (c) scan exclusions (three tools, two overlays, plus the LTG engine's repo, in
  every consuming repo); (d) one file per region (more files per arc, for no gain over (b′)).

**What it costs LTG (user question, 2026-10-28):** little. Arc blocks stop being anchor *targets*,
so a hit on arc text cannot hand back a key to look up. But the text is still indexed as prose, and
`ref:KEY` mentions *inside* arc files still create edges into the anchor graph (`MENTION_RE` matches
anywhere). Nothing cites arc blocks by key — resume reaches them through the register. And it is
reversible: one regex in `markers.py`. Filed as **LTG `L-34`** (user): verify against the arcs
version whether `arc:` blocks should become anchors — noting that arc keys repeat across arc files
by design, so an arc anchor's identity would have to be (file, key).

**The real LTG risk is the MOVE, not the marker.** LTG's `corpus.yaml` names
`.claude/session-context.md`, `.claude/tasks.md` and `.claude/archive/` **by path** (and excludes
the live `session-log.md` as ephemeral). Files moved to `.tracking/` would silently drop out of LTG
— the `ref:corpus-divergence-pattern` shape. → § Migration. Zero-footprint repos keep tracking
outside the repo, so a repo-scoped corpus cannot see it at all: **accepted** (user).

### ARC-D8 — Arc lifecycle status in v1 *(decided)*

Cleanup is deferred (user), but status is not cleanup: in in-branch mode a merged arc's folder lands
on master, and without a status a resume from master would list every arc ever merged as open.

**Merged is not done — measured (2026-10-28).** The oficina-P3 line of work has already passed
through four branches, each merged by its own PR — #88 `feature/oficina-p3-context-assembly`, #89
`feature/oficina-p3-unit-addressing`, #92 `feat/p3-t0-criterion-5`, #94 `feat/p3-d1-freeze` — and
`feat/p3-d10-freeze` is the fifth. **An arc outlives its branches.** So (user, 2026-10-28):

- **Store only what git cannot tell:** `status: open | closed` (a human decision) and `branch:` (the
  arc's *current* branch).
- **Derive the rest at resume time:** whether that branch exists, how far it is ahead of master,
  whether it is merged. A stored `merged` flag would go stale; git cannot.
- **Closing is an explicit step:** the arc's open tasks move to the shared file keeping their ids
  (ARC-D6); the user chooses which of its reading-guide and watch-list rows to promote to shared;
  the folder stays (cleanup is deferred); the key stays reserved (ARC-D13).
- **Resume from master** lists open arcs with their derived state — "P3 — open,
  `feat/p3-d10-freeze`, 4 ahead of master", or "open, no current branch".

### ARC-D9 — Repo identity for the user-level config *(open)*

Zero-footprint mode looks up the external root by repo, and the lookup must give the same answer from
every worktree. Candidates: `git rev-parse --git-common-dir` (stable across worktrees; changes if the
clone moves) vs the remote URL (stable across moves; shared by multiple clones). Decide together with
ARC-D10's two-clone note.

### ARC-D10 — External-mode concurrency guard *(open — lean: required for external mode)*

The payload records a hash of each shared region it was based on, and the pipeline refuses if the
region changed since — a loud refusal, the repo's standing shape. **ARC-D12 makes this stale-base
check apply in every mode**, so what remains specific to external mode is the rest of this entry.
Also detect OneDrive conflict copies
(a `*-<MACHINE>.*` file beside a tracking file) and refuse while one exists. Two clones sharing one
external root: documented as unsupported in v1.

### ARC-D11 — Starting vs adopting an arc *(decided)*

Because an arc outlives its branches (ARC-D8: P3 needed a new branch after every merge),
**re-binding is the normal way an arc continues**, not an edge case. Decided (user, 2026-10-28) — a
plain CLI either harness can run:

| Command | Does |
|---|---|
| `start <name> --key K [--worktree]` | a new branch from master + the arc folder; with `--worktree`, also a worktree at a configured location, and tells the user to start the harness there |
| `adopt <name> --key K` | makes the **current** branch a new arc; nothing moves |
| `bind <name>` | moves an existing arc to the current branch — the post-merge continuation, like P3's fifth branch |
| *(at handoff, no arc bound)* | the skill asks: name an arc (`adopt`), or hand off as a no-arc `sN` session — "identified at handoff" |

**No "convert an adopted arc into a worktree" step in v1.** An arc binds a *branch*; a worktree is
only one place to check it out. Parallel work starts the *other* arc with `--worktree` and leaves
the main checkout on the adopted one — which removes the one side-effecting step (freeing a branch
from the main checkout, since git will not check a branch out twice) entirely. Claude Code and
Codex each have their own native worktree features, kept in harness-specific places; arcs depend on
neither.

### ARC-D12 — Two sessions on the same arc *(decided)*

**The earlier lean was a check that could not fire.** It refused if `sessions/<NNN>-*` already
existed for the number about to be minted — but the pipeline mints the number when it *writes*, so
a second session in the same checkout simply gets the next one. What is actually lost is **region
content**: session B replaces the arc's status with text it authored before A's handoff landed —
single-writer assumption #1 again, inside one arc. Decided (user, 2026-10-28):

1. **A stale-base check, in every mode.** When a session fetches a region it will replace, it gets
   that region's hash; the payload carries it; the pipeline refuses if the region has changed since.
   The same mechanism as ARC-D10, so it also protects the *shared* regions from the same-checkout
   lost update, which ARC-D6's split made rarer but did not remove.
2. **A bound-branch check.** The handoff refuses when the current branch is not the arc's bound
   branch. That stops one arc writing entries on two branches at once — which would merge cleanly
   with duplicate numbers — and makes moving an arc an explicit `bind` (ARC-D11).

### ARC-D13 — Key uniqueness and retirement *(decided)*

**Measured (2026-10-28), `KEY-N`-shaped prefixes already in tracked markdown:** `T` (2,035), `SP`
(52 — the LTG split plan's SP-1…SP-14), `L` (40 — mostly LTG task citations), and technical terms
— `GPT` (32, as in "GPT-5"), `UTF`, `MCP`, `GPL`, `ISO`, `SHA`, `AES`, `BSD`. An arc keyed `GPT`
would mint task `GPT-5`, and every existing "GPT-5" would become ambiguous. Decided (user,
2026-10-28): at arc creation, **refuse** a key that

1. another arc already uses — scan the `arc.yaml` files on local and remote branches, and the
   external root;
2. already occurs as a `KEY-N` prefix in the repo's tracked text — one grep;
3. is reserved — `s` and `T` (work outside arcs), plus keys other repos mint tasks with, such as
   LTG's `L`.

**Format:** uppercase letters and digits, starting with a letter, 2–6 characters. **Retirement** is
free in v1, because closed arcs keep their folders and so keep their keys under check 1; once cleanup
exists, a retired-keys list must outlive the deleted folders. (This doc's own example keys `HR` and
`PLAT` already fail check 2 — they occur only here. The live case's `P3` passes: no `P3-N` occurs
anywhere; the plan's `P3-D1` / `P3-T0` have a letter before the number, so they cannot match.)

### ARC-D14 — Harness adapters via `agent_targets` *(open — lean: make it live)*

Per harness: the rules-file target, the skill install path, the hook install path. `agent_targets:`
already names `tools_dir` and `rules_file` for `claude-code` in three manifests and is read by
nothing. Make it live (add `codex`) or delete it — leaving it declared is the
`ref:declared-unconsumed-spec-fields` shape.

Verified install targets (§ "Codex facts"): skills → `.agents/skills/` (repo; not trust-gated) or
`~/.agents/skills/` (user); hooks → `.codex/hooks.json` (project; trust-gated, and worktrees read the
main checkout's) or `~/.codex/hooks.json` (user); rules → `AGENTS.md` or `~/.codex/AGENTS.md`.
**Do not use Codex's built-in Claude importer as the mechanism:** it copies once (skills →
`.agents/skills/`, `CLAUDE.md` → `AGENTS.md`), so the two copies drift from the first edit — the
installer should generate both harnesses' files from one source instead. The handoff skill's
frontmatter already parses in Codex; its **body** does not port as-is — `$ARGUMENTS` is a Claude Code
substitution, and the body cites `.claude/tools/` paths.

**What the live check adds (2026-10-10):**

1. **The skill's `description` is the trigger text** Codex shows the model, so it must be
   harness-neutral — today's says "across Claude Code sessions".
2. **An untrusted or *modified* hook is skipped silently** in `codex exec`. So the hook's command
   string must stay **byte-stable across engine upgrades** — a fixed command such as
   `st-resume --hook`, with all behaviour inside the engine — or every upgrade silently disables
   auto-resume until the user re-approves it. The install step must tell the user to approve it once
   via `/hooks`.
3. **Prefer `.agents/skills/`** even though `.codex/skills/` also loads ungated: it is the documented
   location and is walked from the project root down to cwd.

**And from 2026-10-22:**

4. **The installer must be *able* to write each harness's locations; which harnesses is an
   install-time selection** (user, 2026-10-22) — e.g. `--harness claude-code,codex`. That is what
   making `agent_targets` live means. Claude Code does not read `.agents/skills/`, so selecting both
   means two skill copies, generated from one source.
5. **Approval is once, and loud:** the interactive TUI prompts for a new or changed hook, after which
   `codex exec` runs it. The install step should say "start `codex` once interactively and trust the
   hook" — and `exec`-only users get the silent skip.
6. **Never shift an existing hook's position.** Trust keys are positional, so inserting our hook
   *before* the user's own entries in a shared `hooks.json` would silently revoke **their**
   approvals. Append, or own a separate file.
7. **The probe is the acceptance test.** An isolated `CODEX_HOME`, sentinel skill / `AGENTS.md` /
   hook files, and the model-free `codex debug prompt-input` check exactly what the installer's
   Codex target produces — no model quality involved.

### ARC-D15 — Rules-file layout, in-repo profile *(open — lean: `AGENTS.md` canonical)*

`AGENTS.md` carries the session rules; `CLAUDE.md` imports it with `@AGENTS.md`. The `@` import is
already proven on this machine — the user's global `CLAUDE.md` imports `@RTK.md` and `@WSL.md`.
Codex's `project_doc_fallback_filenames` is the alternative, but it is user-level Codex config, so it
does not answer the repo-level question.

Two constraints from the source (§ "Codex facts"): Codex's loader has **no `@`-import handling**, so
`AGENTS.md` must be self-contained — the import can only point one way, `CLAUDE.md` → `AGENTS.md`.
And Codex caps the combined project docs at **32 KiB** (`project_doc_max_bytes`); this repo's
`CLAUDE.md` is 16,001 bytes today.

<!-- ref:session-arcs-codex-facts -->
## Codex facts — verified from source

Read from `github.com/openai/codex` at `780d7ab` (2026-10-08; Apache-2.0). Paths are under
`codex-rs/`. This replaces the doc pages and third-party guides, which contradicted each other.

| Topic | Fact | Evidence |
|---|---|---|
| Repo skills | `.agents/skills/` in **every directory from the project root down to cwd**. Not trust-gated | `ext/skills/src/host_roots.rs:137-175` |
| Project skills | `<project>/.codex/skills/`, from the project config layer. The trust gate covers that layer's config, hooks and exec policies — **but the live check listed this skill root in an untrusted project**, so reading the source as "skills gated too" was wrong | `host_roots.rs:83-91`; `config/src/loader/mod.rs:1113-1131`; live check below |
| User skills | `~/.agents/skills/`, and `~/.codex/skills/` ("deprecated … kept for backward compatibility") | `host_roots.rs:93-106` |
| The two official doc pages | **Both right.** `.agents/skills` and `.codex/skills` are different layers, not a contradiction | as above |
| SKILL.md | YAML frontmatter required. `name` optional (defaults to the folder name), **≤64 chars** — not the 100 the docs state. `description` required and non-empty; the parser caps nothing else. Both collapsed to one line. Unknown keys are ignored, and prose such as `argument-hint: <…: …>` is repaired rather than rejected | `skills/src/parser.rs:4,44-85` |
| Claude Code's skills | `.claude/skills/` is **not read** at runtime. Codex ships a **one-shot importer** from Claude Code: `.claude/` skills → `.agents/skills/`, `CLAUDE.md` → `AGENTS.md` (the filename rewritten inside the content), plus hooks and MCP servers from `.claude.json` | `external-agent-migration/src/source/cla.rs:20-21`, `service.rs:692,712,761`, `rewrite.rs:41`, `hooks_cla.rs`, `mcp.rs:11` |
| Hook events | 12, Claude-style: PreToolUse, PermissionRequest, PostToolUse, PreCompact, PostCompact, SessionStart, SessionEnd, UserPromptSubmit, SubagentStart, SubagentStop, Stop, Interrupt | `hooks/src/lib.rs:24-37` |
| Hooks feature | key `hooks` (legacy alias `codex_hooks`): **Stable, enabled by default** | `features/src/lib.rs:1320-1323` |
| Hook config | **Both** a `hooks.json` in a config folder and a `hooks` table in config TOML — the third-party "contradiction" was two supported forms | `hooks/src/engine/discovery.rs:343,387` |
| SessionStart | matcher sources `startup` / `resume` / `clear` / `compact`; **plain stdout becomes model context**; JSON output may add `additional_context`; only SessionStart honours `continue:false` | `hooks/src/events/session_start.rs:24-38,221-223` |
| Hook trust | each hook is trusted by content hash — a new or changed hook needs approval | `discovery.rs:679-718` |
| Hooks in worktrees | in a **linked worktree**, project hooks come from the **main checkout's** `.codex/`; the worktree's own `hooks` table is dropped | `config/src/loader/mod.rs:1133-1143`; `local.rs:225-246` |
| AGENTS.md | per directory from project root to cwd; candidates in order `AGENTS.override.md`, `AGENTS.md`, then `project_doc_fallback_filenames`; combined cap `project_doc_max_bytes` = **32 KiB**; no `@`-import handling found in the loader | `core/src/agents_md.rs:43,45,272-290`; `config/src/config_toml.rs:75` |
| `--oss` | provider `ollama`, port 11434, `requires_openai_auth: false` — **no login**. It speaks the **Responses** API: local Ollama 0.17.5 answers `POST /v1/responses` with 400 on an empty body (the endpoint exists; absent would be 404) | `model-provider-info/src/lib.rs:654-682,736-774` |
| `--oss` gotcha | it **pulls the model if missing** — the default is `gpt-oss:20b`. Always pass `-m <an already-pulled model>`. In 0.162.1 it also needs `--local-provider ollama` (or `oss_provider` in config) — `--oss` alone fails with "No default OSS provider configured" | `ollama/src/lib.rs` (`ensure_oss_ready`); live check |

**Live check — 2026-10-10, codex-cli 0.162.1.** Isolated `CODEX_HOME`, a scratch git repo, model
`qwen3.5:0.8b`. Every probe was a sentinel string required either present or absent, so each could
fail. The skill and `AGENTS.md` probes used `codex debug prompt-input`, which renders the
model-visible prompt **without calling a model**; the hook probes needed a real `codex exec` session.

| Probe | Expected | Observed |
|---|---|---|
| `AGENTS.md` | loaded | loaded — injected verbatim inside `<INSTRUCTIONS>` |
| an `@IMPORTED.md` line inside `AGENTS.md` | not expanded | **passed through as literal text**; the imported file's sentinel absent |
| `CLAUDE.md` | not read | absent |
| skill in `.agents/skills/` | listed | listed, as `- name: description (file: …)` |
| skill in `.codex/skills/`, untrusted project | gated (inferred) | **listed** — the inference was wrong |
| skill in `.claude/skills/` | not listed | absent |
| skill `name` of 64 / 65 chars | accepted / rejected | accepted / rejected |
| the real `session-handoff` SKILL.md | parses | listed — and its `description` ("…across **Claude Code** sessions…") is sent verbatim as the trigger text |
| user-level SessionStart hook, untrusted | skipped | skipped — **silently**: no notice on stderr in `codex exec` |
| same hook with `--dangerously-bypass-hook-trust` | runs | runs; its stdout lands as a `developer` message tagged `hooks.additional_context` |
| *(2026-10-22)* the interactive TUI, same untrusted hook | prompts or skips? | **prompts**: "Hooks need review — 1 hook is new or changed", offering *Review hooks* / *Trust all and continue* / *Continue without trusting (hooks won't run)*. Loud in the TUI, silent only in `exec` |
| *(2026-10-22)* after "Trust all" in the TUI, plain `codex exec` (no bypass flag) | runs | **runs** — one approval is enough |
| *(2026-10-22)* then change the hook's command string | skipped | **skipped silently** — neither the old nor the new sentinel, nothing on stderr |
| *(2026-10-22)* TUI with `--oss --local-provider ollama` on the command line | no sign-in | **ChatGPT sign-in screen** in 0.162.1. With `model_provider = "ollama"` in `config.toml` instead, sign-in is skipped (HEAD's `tui/src/lib.rs:2350-2357` skips it for OSS providers; the CLI-flag path evidently differs in this release) |

Trust is persisted in `config.toml` when the user approves (`config/src/hook_config.rs:28-32`,
`tui/src/hooks_rpc.rs:58-70`). Observed shape:

```toml
[hooks.state."/abs/path/to/hooks.json:session_start:0:0"]
trusted_hash = "sha256:781d63e0…"
```

The key is **positional** — file path, event, matcher-group index, hook index — and the hash covers
the hook's content. So *editing* a hook and *shifting its position* both invalidate the approval.
<!-- /ref:session-arcs-codex-facts -->

<!-- ref:session-arcs-unverified -->
## Still unverified — test before freezing

Closed 2026-10-22: **Claude Code does not read `.agents/skills/`** (live, below); the interactive
TUI **prompts** for an untrusted hook (§ "Codex facts"); `merge=union` is **unsafe** for the shared
tasks file (ARC-D6).

**Claude Code live check — 2026-10-22, v2.1.308.** `claude -p` in the same probe repo, with
`--settings '{"disableAllHooks": true}'` and `--strict-mcp-config` so the user's own hooks and MCP
servers stayed out of it, reading the `skills` list from the `stream-json` `system/init` event: the
`.claude/skills/` probe **loaded** (the positive control), the `.agents/skills/` and `.codex/skills/`
probes did **not**. The stream carried no hook events.

| Claim | Check |
|---|---|
| A SessionStart hook fires in the **interactive** TUI as it does in `exec` | the TUI probe's prompt never submitted, so no session record was written. Low risk — both modes share the hook engine and `exec` fired it — but unobserved |
| Claude Code reads `AGENTS.md` directly only when no `CLAUDE.md` exists (v2.1.277+), and expands `@AGENTS.md` inside `CLAUDE.md` | Claude Code memory docs (`code.claude.com/docs/en/memory.md`), via a docs agent's summary — not yet seen live |
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
  Candidate: `--no-merges` — a merge that lands after a handoff is otherwise credited to the next
  session (measured on the P3 branch, § "The live case").
- **Every tool that names a `.claude/` tracking path follows the move — found by grep, not by
  memory.** Known: LTG's `ltg/corpus.yaml` (`include_roots` lists `.claude/session-context.md`,
  `.claude/tasks.md`, `.claude/archive/`); the arc equivalents are the shared `context.md`, the task
  files, and `arcs/*/sessions/` in place of `archive/`.

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

**The plan for it (user, 2026-10-28):** the P3 session is not orphaned — it becomes the first
**adopted** arc. Order:

1. Build arcs and migrate llm's tracking on `feat/session-arcs`; merge to master.
2. On `feat/p3-d10-freeze`, merge master — the branch gains the engine and the new layout.
3. `adopt` it as the oficina-P3 arc, key `P3` (passes ARC-D13), bound to that branch; its six arc
   rows and three developing-oficina rows of the reading guide (ARC-D6) and its watch-list items
   move into the arc context. Its *next* branch, after this one merges, is a `bind` (ARC-D11).
4. Hand off there: the first entry `P3#1` covers the 2026-09-08 work. The next P3 session resumes
   the arc.

Measured on that branch (2026-10-28): the harvest boundary is the s140 handoff commit `36aa48a`, and
`36aa48a..feat/p3-d10-freeze` lists the four 2026-09-08 commits **plus `71c1fa0`**, the PR #94
merge — s140's work, merged after s140 handed off. The seed is a skeleton the author edits, so the
line is dropped by hand; `--no-merges` would drop it by construction (§ Migration).

This design session can hand off under the legacy scheme as `s141` on `feat/session-arcs`. That is
safe **as long as the P3 branch's next handoff happens as an arc** — it is then the only legacy
`s141`.

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
- Codex CLI source — https://github.com/openai/codex (read at `780d7ab`, 2026-10-08)
