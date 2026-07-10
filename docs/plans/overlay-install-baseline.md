# Overlay installer: an install-time baseline (the lockfile)

**Created:** 2026-07-09 (session 111)
**Status:** PLAN — decisions B-D1…B-D8 proposed, **not frozen**. No code written.
**Task:** #6 in the session-111 list. Root cause under T-54 and (formerly) T-80(a).
**Related:** T-54 (`--force-manual` override), T-82 (`--verify` ownership questions),
`docs/plans/resume-config-steps.md` R-D9 (code ships as a package, config as an overlay).

---

## The problem in one sentence

**The installer records nothing about what it installed**, so it can never distinguish
*"the overlay source moved since you last reconciled"* from *"this file legitimately
differs from source."*

Every consequence follows from that single missing fact:

| Symptom | Where | Today |
|---|---|---|
| `[TODO] manual merge` on every install | `handle_manual_if_exists` | **7 lines across 4 repos, every run.** None necessarily actionable |
| Cannot locate a keep-region in an unmarked file | `handle_customizable` (T-80a) | Can only ask "is the overlay default present verbatim?" — a proof of safety, never of danger |
| No first-class way to push the canonical file through | T-54 | Unbuilt, because there is nothing to merge *against* |

## What changed, and why urgency dropped

T-82 (session 111) removed the **safety** stakes. `--verify` no longer gates on
user-managed divergence, and its new locator contract catches the genuinely dangerous
case — a register declaring ownership of a region that does not exist.

So the baseline now buys **precision, not safety.** It is worth doing because the noise it
removes is the same alarm-fatigue mechanism that hid three bugs in one session — but it is
not urgent, and it should not be started with a long context. Freeze the decisions in one
sitting; build in the next.

---

## The insight this rests on

R-D9 removed the installer's hand-rolled package manager **for code** — `always_user_files:`
copied ten `.py` files into `~/.claude/tools/handoff/`, and `uv tool install` replaced it.

What remains is a hand-rolled package manager **for config**. And the thing every config
package manager needs, and this one lacks, is a **baseline of what it last shipped**.

**Prior art is exact.** `dpkg` calls these *conffiles*. On upgrade it compares three things —
the file as shipped in the *old* package (the baseline), the file *currently on disk*, and
the file in the *new* package — and only prompts when the last two both changed. If you never
edited it, it upgrades silently. If the package never changed it, it leaves you alone. Our
`manual_if_exists` prompts unconditionally because it only ever sees two of the three.

`git merge-file` is available and is the same 3-way primitive.

---

## Design

### The three-way question

For each baseline-tracked path, three artifacts exist:

```
BASE   = the overlay source content at the time this repo last reconciled  (the lockfile)
OURS   = what is on disk in the repo now
THEIRS = the overlay source content now
```

That yields four states, of which today's code can only see the last two collapsed together:

| BASE vs THEIRS | OURS vs BASE | Meaning | Report |
|---|---|---|---|
| same | same | Nothing happened | `SAME` |
| same | changed | Repo customized; source didn't move | `CUSTOMIZED` (non-gating) |
| changed | same | Source moved; repo never touched it | **auto-update, no prompt** |
| changed | changed | Both moved | `TODO` — the only case a human is needed |

Only the last row deserves a `[TODO]`. Today all four produce one (or none).

### B-D1 — Where the lockfile lives

Lean: `.claude/overlays/<overlay-name>.lock` — one per overlay, per repo.

Alternatives: a single `.claude/overlays.lock` (fewer files, more merge conflicts); inside
`.claude/local/` (gitignored — loses the reviewability that makes this worth having).

### B-D2 — Hash-only, or a content snapshot?

- **Hash-only** (`sha256` of overlay source per path). Answers *"did source move since I
  reconciled?"* — the main win. Cannot reconstruct BASE, so no 3-way merge.
- **Content snapshot** (`.claude/overlays/<name>/base/<path>`). Enables a real
  `git merge-file` 3-way merge, and lets `handle_customizable` diff the installed file
  against what was actually shipped — which is what T-80(a) needed and could not have.

Lean: **hash-only for v1**, snapshot as v2. The 3-way merge is the prize but it is a
separate, larger behavior; shipping the noise fix first is cheap and independently valuable.
Record the snapshot as the intended v2 so v1's format leaves room for it.

### B-D3 — Is the lockfile git-tracked?

Lean: **yes.** It is per-repo state that must survive a clone, and its diffs are exactly the
audit trail ("this repo reconciled registry.yaml at overlay v11"). The cost is that a
lockfile is one more thing to conflict on in a merge — acceptable for a file of hashes.

### B-D4 — Which categories get a baseline

| Category | Baseline? | Why |
|---|---|---|
| `manual_if_exists` | **yes** | The primary consumer. This is where the noise is |
| `customizable` | **yes** | Lets T-80(a)'s check become "what did the repo change relative to what we shipped", instead of "is the default present verbatim" |
| `templates` | probably not | Divergence is total and expected. The locator contract (T-82) already covers what actually matters — the structures the register depends on |
| `files`, `user_files` | **no** | Overlay-owned; a byte-diff against current source is the correct and complete question |

### B-D5 — Bootstrap: five repos have no lockfile

The dangerous move. "No lockfile" must not read as "everything changed" (regressing to
today's noise), nor silently as "you are reconciled" (which would mark a genuinely-behind
repo as current and suppress a real `[TODO]`).

Options:
- **(a)** Absent lock → record current source hashes, report `BOOTSTRAP` (non-gating), and say
  loudly that reconciliation status is *asserted, not verified*.
- **(b)** Absent lock → today's behavior (unconditional `TODO`) until an explicit
  `--adopt-baseline` run.

Lean: **(b)**, with `--adopt-baseline` as the one-time migration. It is the honest default:
we genuinely do not know whether these repos are reconciled, and this session proved that
assuming reconciliation is how stale files survive (three repos ran a v8-era
`handoff-harvest.sh` for months). **Do not let the tool assert a fact it cannot check.**

### B-D6 — `--dry-run` and `--verify` never write the lockfile

Non-negotiable. Both are read-only contracts. A dry-run that writes a baseline would make
the next real run believe a reconciliation happened.

### B-D7 — What invalidates a baseline entry

Content hash of the overlay source, **not** the manifest version. A version bump with no
content change should produce no prompt; a content change without a version bump must.
(This session shipped both kinds.)

### B-D8 — Relationship to T-54

T-54 asks for `--force-manual`: a way to push the canonical file through. With a baseline
that request mostly dissolves — the three-way merge handles the common case, and what
remains is "take THEIRS wholesale," which is a one-line `--theirs` flag rather than a
category of behavior.

**Sequence T-54 after this plan**, and re-scope it then. It may shrink to nothing.

---

## Decision register (PROPOSED — not frozen)

| id | Decision | Lean | Open? |
|---|---|---|---|
| **B-D1** | Lockfile location | `.claude/overlays/<name>.lock` | lean |
| **B-D2** | Hash-only vs content snapshot | hash-only v1; snapshot v2 (3-way merge) | lean, format must leave room |
| **B-D3** | Git-tracked | yes | lean |
| **B-D4** | Categories covered | `manual_if_exists` + `customizable` | lean |
| **B-D5** | Bootstrap for 5 existing repos | `--adopt-baseline`; do not assume reconciliation | lean, **highest risk** |
| **B-D6** | `--dry-run` / `--verify` never write | non-negotiable | decided |
| **B-D7** | Invalidation key | source content hash, not manifest version | lean |
| **B-D8** | T-54 disposition | re-scope after this lands; likely shrinks to `--theirs` | lean |

---

## Phases

1. **Freeze** B-D1…B-D8 in one sitting. (Half a session. Do not skip — B-D5 is a data-loss-adjacent
   decision and B-D2 constrains the file format forever.)
2. **Lockfile read/write** + `--adopt-baseline`. Hermetic tests: absent lock, stale lock, lock
   ahead of source, dry-run writes nothing.
3. **Rewire `handle_manual_if_exists`** onto the four-state table. Acceptance: on the five
   current repos, `[TODO]` count drops from 7 to 0 immediately after `--adopt-baseline`, and
   rises again exactly when `files/registry.yaml` changes in the overlay.
4. **Rewire `handle_customizable`'s decision-3** to diff against BASE rather than ask whether
   the default is present verbatim. Keep the asymmetric polarity (silence only on proof of
   safety) — the baseline strengthens the proof, it does not change the rule.
5. **Propagate + adopt** in all five repos. Commit the lockfiles.
6. **Re-scope T-54** (B-D8).

Estimated: **half a session to freeze, one session to build and propagate.** Phase 4 could be
deferred without loss — `customizable:` has zero call-sites today.

---

## Acceptance

- `--adopt-baseline` on the five repos produces a committed lockfile per repo and drops
  `[TODO]` from 7 to 0.
- Editing `overlays/session-tracking/files/registry.yaml` makes exactly the repos that also
  edited their own copy report `TODO`; the rest auto-update silently.
- A repo that edited its register while source stood still reports `CUSTOMIZED`, not `TODO`.
- `--dry-run` and `--verify` leave the lockfile byte-identical (assert with `sha256`).
- No lockfile present and no `--adopt-baseline` → today's behavior exactly. No silent change.

## What is NOT decided

B-D5 (bootstrap) and B-D2 (format) block execution. Everything else is a lean.

## The honest caveat

This is a **noise fix wearing a bugfix's clothes.** After T-82 nothing unsafe depends on it.
Its value is that `[TODO]` becomes a signal a human should act on — which matters because a
signal that fires unconditionally is exactly the defect that let T-54, T-80(a) and T-82 hide.
Judge it on that, not on urgency.
