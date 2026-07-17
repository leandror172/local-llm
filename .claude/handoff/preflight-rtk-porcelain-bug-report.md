# Bug report — handoff pre-flight always reports DIRTY under the RTK hook

**Filed:** 2026-07-16
**Found in:** career-search (session 94), during a normal `/session-handoff` run
**Component:** `overlays/session-tracking/files/session-handoff/SKILL.md` — Step 1 (Pre-flight)
**Severity:** Low blast radius, high nuisance — false STOP on every handoff in any repo where the RTK hook is active. No data risk; the pipeline itself is unaffected.

## Symptom

Step 1 of the skill instructs:

```bash
test -z "$(git status --porcelain -- .claude/session-log.md .claude/tasks.md .claude/session-context.md)" && echo CLEAN || echo DIRTY
```

with the rule: *"If it prints DIRTY, **STOP** and ask the user to commit or stash those files first."*

In career-search this printed **DIRTY** while the three tracking files were, in fact, byte-for-byte clean — `git diff` on them was empty and `git status --porcelain` had no entries. Following the skill as written, the agent stopped and asked the user to stash files that had no changes.

## Root cause

The user's global `CLAUDE.md` installs an **RTK (Rust Token Killer) hook** that transparently rewrites `git …` invocations to `rtk git …`. RTK's git filter is token-optimizing: for `git status` it emits a **compact confirmation** rather than passing porcelain output through. With no changes to report, `rtk git status --porcelain -- <paths>` prints:

```
ok
```

`test -z` is asking "is this string empty?" — and `"ok"` is not empty. So the test takes the `DIRTY` branch **precisely when the tree is clean**. The check is inverted under RTK, not merely noisy.

Confirmed by bypassing the filter:

```bash
$ rtk proxy git status --porcelain -- .claude/session-log.md .claude/tasks.md .claude/session-context.md | cat -A
# (no output — genuinely clean)

$ test -z "$(rtk proxy git status --porcelain -- ...)" && echo CLEAN || echo DIRTY
CLEAN
```

## Why it matters

- **It fires on the clean path, not the dirty path.** A check meant to catch a rare bad state instead misfires on the common good state, so the signal is worse than useless — an agent that trusts it stops every time.
- It burns a user round-trip on every handoff ("please stash these files" → "they're not modified").
- The failure is silent and plausible: `DIRTY` looks like a real finding, and an agent that obeys the skill has no reason to double-check. This one was only caught because the follow-up `git diff` came back empty.
- Any porcelain-emptiness test elsewhere in the toolchain has the same defect under RTK.

## Suggested fix

Make the pre-flight immune to output-rewriting hooks. Options, roughly in order of preference:

1. **Use the plumbing command**, which RTK has no filter for and which is the right tool anyway:
   ```bash
   git diff --quiet -- .claude/session-log.md .claude/tasks.md .claude/session-context.md \
     && git diff --cached --quiet -- .claude/session-log.md .claude/tasks.md .claude/session-context.md \
     && echo CLEAN || echo DIRTY
   ```
   Exit-code-driven, so it cannot be fooled by a filter that rewrites stdout.

2. **Bypass the filter explicitly** in the documented command: `rtk proxy git status --porcelain …`. Correct here, but couples the skill to RTK's existence — bad for the other three consumer repos if they lack the hook.

3. **Have `run-handoff.sh` own the check.** The pipeline already aborts on a dirty tracking tree; if it exposed a `--preflight` mode returning a proper exit code, the skill could drop the shell one-liner entirely. This removes the whole class of problem and matches the overlay's stated philosophy — *"the pipeline does the surgery"* — since the pre-flight is arguably pipeline mechanics that leaked into the model's instructions.

Option 1 is the minimal change; option 3 is the right one if the pre-flight is going to stay load-bearing.

## Propagation

`SKILL.md` Step 1 is overlay-distributed, so the fix must go to the **source** at `overlays/session-tracking/files/session-handoff/SKILL.md:55`, then re-propagate to the consumer repos (llm, expenses/code, web-research, career-search). Only repos with the RTK hook active actually misbehave, but the plumbing-command fix is strictly better everywhere and carries no RTK dependency.
