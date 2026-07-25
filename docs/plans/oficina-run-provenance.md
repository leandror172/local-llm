# oficina run provenance — squash the message, keep the bytes (T-118)

Session 129, 2026-07-24. Raised by the user while reviewing how an accepted run lands:
`oficina iteration 3 (<run_id>)` explains nothing about what changed, so mainline history
carries meaningless messages *and* the model is not named anywhere in git. The proposed fix —
squash-merge with a real message — is right, and on its own it silently destroys the run's
provenance. **Not frozen; decisions R-D1–R-D6 are proposed.**

<!-- ref:oficina-run-provenance -->
## The coupling to break

`workspace.py:110` branches each run as `oficina-run-<run_id>`; `snapshot()` commits one
`oficina iteration N (<run_id>)` per iteration on top of an `oficina C0 baseline (<run_id>)`.
Teardown removes the *worktree* and keeps the branch; `retention.py` prunes `artifacts/` and
`workspace/` and deregisters the worktree but **never deletes a branch** (`retention.py:12,81-111`).

Branches are therefore deleted only by hand — and s126's cleanup pass did exactly that. So today
those commits survive **only because they were merged into master**. Verified: `git branch --list
'oficina-run-*'` is empty, yet `git merge-base --is-ancestor 6f673cb master` succeeds.

**Merge is currently doing double duty: shipping the code AND being the sole mechanism keeping the
model's raw output reachable.** Squash-merging while keeping the branch-deletion habit therefore
makes the commits unreachable and eventually GC'd — the failure is silent and arrives months later.

The `git diff <model output> <shipped>` capability this destroys is not incidental: it is what
makes a claim like T-114's "iteration 1 lands 90–95%" auditable rather than remembered, and it is
the code half of the DPO corpus.

## Three separable concerns

| Concern | Mechanism |
|---|---|
| Mainline reads as intent | **Squash-merge** with an authored conventional-commit message |
| Provenance is legible in git | **Trailers** on the squashed commit (survive squashing; iteration messages do not) |
| The model's bytes survive | **`refs/oficina/<run_id>`**, set independently of the merge decision |

```bash
git update-ref refs/oficina/<run_id> <branch-tip>   # GC-safe, invisible to git branch/log
git branch -D oficina-run-<run_id>
```

`git diff refs/oficina/<run_id> HEAD -- <target>` then still yields exactly the review delta.

Proposed trailer block:

```
feat(oficina): parse `go build` stderr into ParsedFailure (T-92 Phase 3)

<what the change does and why>

oficina-run: bIbxrIOo69Ty1fafoxPiAw
oficina-model: my-python-q25c14-16k
oficina-outcome: exhausted (3 iterations, 1 fresh start)
oficina-source: 1a27488  (best attempt; retained at refs/oficina/bIbxrIOo69Ty1fafoxPiAw)
```

Trailers are greppable and machine-readable (`git log --grep`, `git interpret-trailers`).

## The inversion this fixes

A **rejected** (verdict 0) run is never merged, so under today's scheme its commits are never made
reachable and its bytes are the first thing lost. But a rejected output is the *negative half of a
DPO preference pair* — the most valuable signal the run produced. The current pipeline reliably
preserves what the model got right and reliably discards what it got wrong. Retention-by-ref fixes
this as a side effect, precisely because it stops depending on the merge decision.
<!-- /ref:oficina-run-provenance -->

<!-- ref:oficina-run-provenance-decisions -->
## Decisions (proposed, not frozen)

- **R-D1 — Squash-merge on a non-rejected verdict**, with an authored message stating what the
  change does. Replaces the current `merge: oficina run <id> (…)` + follow-up fix pair. The s127
  pair (`3be617c` merge + `3a24c87` review fix) is the worked example of what this replaces.
- **R-D2 — Retention is by ref, not by merge.** `refs/oficina/<run_id>` is written for **every**
  terminal run regardless of verdict, before the branch is deleted. This is the load-bearing
  decision; R-D1 is unsafe without it.
- **R-D3 — Provenance rides as trailers** on the squashed commit (`oficina-run`, `oficina-model`,
  `oficina-outcome`, `oficina-source`). `oficina-source` records the **best attempt**, not the
  branch tip — see R-D5.
- **R-D4 — Name the model in the iteration message too** (`oficina iteration N (<run_id>,
  <model>)`). It is *derivable* today by joining `calls.jsonl` on `run_id`, but T-105's lesson is
  that a fact requiring a join to recover is a fact that gets lost. One-line change at the
  `snapshot()` call site. Lower value than R-D3, since the squashed commit is what survives.
- **R-D5 — Merge/record the best attempt, not the branch tip.** An `Exhausted` run records
  `best_attempt_ref`, which may be an *earlier* iteration: run `bIbxrIOo`'s best attempt was
  iteration 1 (`1a27488`) while the tip was iteration 3 (`6f673cb`). s127 merged the tip and the
  merge message literally reads *"best attempt to be restored"*. Reading the terminal event first
  removes that manual restore step.
- **R-D6 — Do NOT use `Co-Authored-By` for the local model.** That trailer denotes a person; a
  synthetic identity there pollutes contributor stats. `oficina-model:` is the honest encoding.

## Open: is `refs/oficina/*` worth pushing?

`refs/oficina/*` sits outside `refs/heads/*`, so the default push and fetch refspecs ignore it —
**it is local-only, and therefore not a backup.** Pushing needs both halves:

```bash
git push origin <sha>:refs/oficina/<run_id>
git config --add remote.origin.fetch '+refs/oficina/*:refs/oficina/*'
```

**For pushing:** it is the code half of the DPO corpus and cost real GPU hours to produce, so a
disk failure loses training data that cannot be regenerated identically; it makes the shas recorded
in every ledger resolvable from any clone; and it is the same question T-86 asks about new-machine
enablement (oficina is machine-global, but its provenance would be machine-local).

**Against:** unbounded growth — every iteration of every run, forever, including rejected output
that exists precisely because it was bad; and it is noise in a repo whose history is otherwise
curated.

**Middle grounds to weigh:** push only runs that reached a deliverable; or give refs their own TTL
sweeper. Note a ref TTL cannot simply reuse `retention.py`'s run-dir-mtime staleness — the point of
the ref is to outlive the workspace, so it needs a separate, longer horizon. Decide alongside T-86.
<!-- /ref:oficina-run-provenance-decisions -->
