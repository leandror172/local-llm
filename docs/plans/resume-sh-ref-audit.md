# resume.sh — Ref Tag Audit & Improvement Plan

**Created:** 2026-05-15 (session 60)
**Purpose:** Work item for a future session — which ref tags to add/remove from `.claude/tools/resume.sh`, and structural fixes identified during the index/session-context/tasks.md cleanup.

---

## What resume.sh currently does

Five sections, output target ~30 lines:

1. **`ref:current-status`** via `ref-lookup.sh` — layer/branch/next/open deferred (head -20 truncated)
2. **Last session Next pointer** — parsed from `session-log.md` via awk
3. **Recent git commits** — `git log --oneline -5`
4. **Uncommitted changes** — `git status -s` (conditional)
5. **`ref:user-prefs`** + full key list — flattened to single line (poor readability)

---

## Ref tags worth ADDING

### 1. `ref:quick-pointers` — **HIGH PRIORITY**
**Location:** `.claude/index.md` (added session 60)
**Content:** 6-row table — tasks.md, plan-v2.md, session-log.md, session-context.md, CLAUDE.md, MEMORY.md

**Why:** Every session an agent needs to know where `tasks.md` and `plan-v2.md` are. Currently this knowledge is implicit (the agent has to search or recall). Adding it to resume.sh makes the file-location contract explicit at session start.

**Size:** ~8 lines. Negligible.

**Placement:** Between section 1 (current-status) and section 2 (last-session Next), or replace the "Use ref-lookup.sh" footer hint with this concrete table.

---

### 2. `ref:active-decisions` — **MEDIUM PRIORITY**
**Location:** `.claude/session-context.md` (trimmed to ~10 lines in session 60)
**Content:** Cross-cutting principles — routing patterns, licensing rule, Layer 5 model choice, `think:false` fix, num_ctx rule, DPO pairs workflow, plus pointers to frozen-layer archives.

**Why:** After the session 60 trim, this block is now compact enough (~10 lines) to include at session start. It gives agents the "why are we doing things this way" context that prevents them from re-asking decided questions. Previously it was 75 lines and unsuitable; now it fits.

**Caveat:** Only include if the block stays lean. If it grows again, remove.

**Placement:** After section 1 (current-status), as a separate short section.

---

### 3. Open deferred count / summary — **LOW PRIORITY**
**Location:** `ref:deferred-infra` in `.claude/tasks.md`
**Content:** 18 open `[ ]` items (as of session 60)

**Why:** Knowing how many open deferred items exist helps agents gauge project momentum and avoids re-proposing already-logged items. But the full list (18 items) is too long for session start.

**Proposed approach:** Don't include the full block. Instead, add a one-liner count:
```bash
OPEN=$(grep -c "^- \[ \]" "$PROJECT_ROOT/.claude/tasks.md" 2>/dev/null || echo "?")
echo "  Open deferred items: $OPEN (ref:deferred-infra for full list)"
```

**Placement:** Footer section, after the key list.

---

## Ref tags explicitly NOT worth adding

| Tag | Reason |
|-----|--------|
| `ref:bash-wrappers` | 50+ lines; only needed when running scripts. Already accessible via `ref-lookup.sh bash-wrappers`. |
| `ref:model-selection` | Only needed for local model work. Moved to `docs/findings/layer-0-runtime-refs.md`. |
| `ref:thinking-mode` | Same — local model work only. |
| `ref:structured-output` | Same — local model work only. |
| `ref:personas` | Only needed when selecting/creating personas. Now in `personas/personas-reference.md`. |
| `ref:git-safety` | Only needed before destructive git ops, not at session start. Moved to `technology-conventions.md`. |
| `ref:git-worktrees` | Same — branch management context, not session-start. |
| `ref:memory-files` | Only needed when wiring a new folder into the memory system. |
| `ref:mcp-integration` | Active MCP setup is stable; rarely changes. On-demand via ref-lookup. |
| `ref:indexing-convention` | Only needed when adding new docs. |
| `ref:layer4-status` | Layer 4 complete. Open stragglers are 2 items, already in session-context "Next". |

---

## Structural fixes needed

### Fix 1: `head -20` on `ref:current-status` is too aggressive
After the session 60 trim, `ref:current-status` is now ~60 lines (down from ~64, but still contains the full session 58-59 summaries, active branch, open deferred list, and Next pointer). `head -20` cuts it off mid-content.

**Fix:** Increase to `head -35` or remove the truncation entirely (the block is now small enough to display in full given the overall trim).

### Fix 2: `ref:user-prefs` is flattened to unreadable single line
Current code:
```bash
PREFS=$("$SCRIPT_DIR/ref-lookup.sh" user-prefs 2>/dev/null | tr '\n' ' ' || true)
echo $PREFS
```
The `tr '\n' ' '` collapses multiline markdown into an unreadable blob.

**Fix:** Remove the `tr` and display as-is, with `grep -v "^<!-- "` to strip tag lines:
```bash
"$SCRIPT_DIR/ref-lookup.sh" user-prefs 2>/dev/null \
  | grep -v "^<!-- " | grep -v "^$" || true
```

### Fix 3: Key list is hard to scan
Current: All keys printed on one line separated by spaces. With 50+ keys this wraps and is unreadable.

**Fix:** Print one key per line, or print a count + instruct agent to call `ref-lookup.sh --list` for discovery:
```bash
KEY_COUNT=$("$SCRIPT_DIR/ref-lookup.sh" list 2>/dev/null | wc -l || echo "?")
echo "  $KEY_COUNT ref keys available — run: .claude/tools/ref-lookup.sh --list"
```

---

## Proposed new resume.sh structure

```
═══════════════════════════════════════════════
  PROJECT RESUME — YYYY-MM-DD
═══════════════════════════════════════════════

── Status (ref:current-status) ─────────────────
[full block, no truncation]

── Key file locations (ref:quick-pointers) ──────
[6-row table]

── Active decisions (ref:active-decisions) ──────
[~10 lines]

── Last session Next pointer ────────────────────
[awk-parsed from session-log.md]

── Recent commits ───────────────────────────────
[git log --oneline -5]

── Uncommitted changes ──────────────────────────  ← conditional
[git status -s]

═══════════════════════════════════════════════
  User preferences:
[ref:user-prefs — multiline, not flattened]

  Open deferred items: N (ref:deferred-infra for full list)
  Ref keys available: N — run: .claude/tools/ref-lookup.sh --list
═══════════════════════════════════════════════
```

---

---

## Advisor review (session 60) + responses

### Critical bug introduced this session: `ref:active-decisions` tag was stripped

During the session-60 trim of `session-context.md`, the `<!-- ref:active-decisions -->` open/close tags were removed along with the bulk content. The trimmed "Active Decisions" section is now an untagged H2. `ref-lookup.sh active-decisions` returns nothing.

**Action (do before any resume.sh edit — this is a live regression):**
Re-add `<!-- ref:active-decisions -->` / `<!-- /ref:active-decisions -->` around the trimmed block in `session-context.md`. Two-line fix.

*Response: Confirmed. This must be step 0 before anything else in this plan.*

---

### Autoloaded context duplication

`index.md` and `session-context.md` are autoloaded as system-reminder context at session start, which means `ref:quick-pointers` and `ref:active-decisions` may already be in the agent's context before resume.sh runs. If reliable, both adds are redundant.

**Recommendation:** Keep them anyway. resume.sh's value is being a deterministic single source. Autoload is harness-controlled and could change. Document the assumption explicitly.

*Response: Agree. The plan's assumption is: autoload is unreliable and resume.sh must be self-contained.*

---

### Open-deferred count: drop the number

`"Open deferred items: 18"` reads as an actionable stat. Agents respond to numbers as priorities — risk is they suggest deferred work when the user wants something specific.

**Fix:** Reframe to a quiet pointer:
```
(items pending — see ref:deferred-infra)
```

*Response: Agreed. Updated in proposed structure below.*

---

### Section ordering: Next pointer before decisions

Proposed layout put decisions before the Last Session Next pointer. Reverse this — "what was I about to do" is more action-relevant than "what's decided" at the moment of resuming.

**Corrected order:**
1. Status (`ref:current-status`)
2. Last session Next pointer
3. Quick file pointers (`ref:quick-pointers`)
4. Active decisions (`ref:active-decisions`)
5. Recent commits / uncommitted changes

*Response: Agreed. Updated in proposed structure below.*

---

### Line-count contract: docstring promises ~30 lines, new structure delivers 50–70

The existing docstring says "~30 lines". Un-truncated status + 2 new sections + multi-line user-prefs (currently flattened to 1 line but ~15 lines expanded) blows past this.

**Options:**
- Update docstring to "~50 lines"
- Apply `head -N` caps per section (e.g., `head -40` on current-status, `head -10` on each new block)
- Show only headings/first-line of new blocks with `Use ref-lookup.sh KEY for detail` hint

*Response: Prefer `head -N` caps with hints. Keeps the script honest without hiding content. Specific caps: `head -30` on current-status (was -20, loosen slightly), `head -12` on active-decisions (the trimmed block is ~10 lines), no cap on quick-pointers (it's 8 lines). Update docstring to "~50 lines".*

---

### Graceful degradation must be explicit

The plan does not say new `ref-lookup.sh` calls must keep the `|| true` pattern. Add as an explicit implementation requirement.

**Rule:** Every new `ref-lookup.sh` call must follow the existing pattern:
```bash
"$SCRIPT_DIR/ref-lookup.sh" KEY 2>/dev/null \
  | grep -v "^<!-- " | grep -v "^$" || true
```
With a fallback `echo "(no KEY block found)"` if output is empty.

*Response: Added to implementation notes.*

---

### Structural fix 2 caveat: multi-line user-prefs adds ~14 lines

The current flatten-to-single-line is unreadable but compresses to 1 line. Switching to multi-line correctly adds ~14 lines. The docstring update to "~50 lines" accounts for this.

*Response: Noted. The line-count update handles it.*

---

## Updated proposed resume.sh structure (post-advisor revision)

```
═══════════════════════════════════════════════
  PROJECT RESUME — YYYY-MM-DD
═══════════════════════════════════════════════

── Status (ref:current-status) ─────────────────
[head -30]

── Last session Next pointer ────────────────────
[awk-parsed from session-log.md]

── Key file locations (ref:quick-pointers) ──────
[full — 8 lines]

── Active decisions (ref:active-decisions) ──────
[head -12]

── Recent commits ───────────────────────────────
[git log --oneline -5]

── Uncommitted changes ──────────────────────────  ← conditional
[git status -s]

═══════════════════════════════════════════════
  User preferences:
[ref:user-prefs — multiline, not flattened]

  (items pending — see ref:deferred-infra)
  Ref keys available: N — run: .claude/tools/ref-lookup.sh --list
═══════════════════════════════════════════════
```

---

## Implementation notes

- All changes are in `.claude/tools/resume.sh` only
- No CLAUDE.md edits needed — it already says to run resume.sh without specifying what it outputs
- After editing, run `.claude/tools/resume.sh` and verify output is ≤ 50 lines on a clean working tree
- The `ref:active-decisions` add is conditional: if the block grows past ~15 lines, skip it and keep on-demand only
