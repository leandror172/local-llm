# B5.1 — Handoff preflight check (T-53)

**Status:** deferred / not built. Reference spec for a future session.
**Subsystem:** session-handoff pipeline (`overlays/session-tracking/files/handoff/`).
**Depends on:** Scope A (B1–B4), already merged via PR #50.

## Goal

A cheap, **payload-free** "can I even start?" check the skill runs *before* authoring a
payload, so unmet preconditions surface up front instead of being discovered inside F6 after
a wasted payload-assembly round-trip (F6 aborts on a dirty tracking tree — decision session 85).

This is **distinct from `--dry-run`**: `--dry-run` needs a payload (it stages the real edits and
verifies). Preflight validates only the *ground state* and needs no payload.

## What it checks

1. **Tracking tree clean** for the register's files — F6's clean-tree guard would abort otherwise.
2. **Every registered locator still resolves** in the current files — catches a `ref:` block /
   structural anchor / field that was renamed or moved out from under the register.
3. **Register loads** (PyYAML present, `roles:` well-formed) — already enforced by `registry_io`.

Nuance: the `checklist` locator (`tasks-checkoff`) needs a `task_id`, which preflight doesn't
have. So for checklist roles, only assert the **file exists** — skip the per-task locate.

## Code changes

- **New `preflight.py`**:
  ```python
  def check_preconditions(repo_root, register, git) -> list[str]:
      """Return a list of human-readable unmet preconditions ([] == ready)."""
      # files = {role_def["file"] for role_def in register.values()}
      # if not git.is_clean(sorted(files)): add "tracking files dirty: ..."
      # for role, role_def in register.items():
      #     if locator.type == "checklist": assert file exists, else skip
      #     else: try locator.locate(role_def, text_of(file)) except LocatorError -> record
  ```
  Reuses `locator.locate` / `LocatorError`, `gitio.SubprocessGit.is_clean`, and a small
  `text_of(rel)` cache (mirror `_collect_edits`' helper in `orchestrator.py`).

- **`handoff.py`**: add a `--preflight` flag; make `--payload` **not required** when it's set
  (custom argparse check, since `required=True` today). On `--preflight`: `load_register` →
  `SubprocessGit(repo_root)` → `check_preconditions` → print unmet list (or "preflight: ready") →
  exit `0` if ready, `1` if any unmet. Skip the whole payload/parse/run path.

- **`SKILL.md`** (`overlays/session-tracking/files/session-handoff/SKILL.md`) Step 1: replace the
  inline `git status --porcelain -- …` with `run-handoff.sh --preflight`. Keep the "STOP and ask
  the user to commit/stash" instruction on a non-zero exit.

- **`test_preflight.py`**: clean tree → `[]`; dirty tracking file → reported; a deliberately
  renamed `ref:` anchor → reported; checklist role only needs the file present.

## Optional follow-on (not required)
Option (c) from tasks.md — a hook fired when the skill loads that auto-injects the unmet
conditions — is heavier and can layer on top later. The `--preflight` flag is the foundation.

## Acceptance
- `run-handoff.sh --preflight` on a clean repo → `exit 0`, "preflight: ready".
- Make a tracking file dirty → `exit 1` naming the file.
- Rename a registered `ref:` key in `session-context.md` → `exit 1` naming the role.
- All existing 77 tests stay green.
