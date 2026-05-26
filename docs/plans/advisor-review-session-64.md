# Advisor Review — Session 64 (MCP Plan 2 Execution)
*Written 2026-05-22. Claude commentary inline as `> blockquotes`.*

---

## Overall Assessment

The session executed cleanly. TDD discipline held, helpers were extracted as planned for Plan 3 reuse, 19/19 tests pass, live acceptance covered all 4 spec scenarios, and docs were updated more broadly than the plan strictly required. The PR is ready to ship in the sense that nothing is broken.

That said, your self-check at the end ("Plan 2 fully verified") glossed over several quality issues that are individually minor but collectively worth fixing before they ossify. None block PR #37, but several should be addressed either in a follow-up commit on this branch or as the first work in the Plan 3 session.

---

## What Was Done Well

- TDD discipline: 9 tests confirmed red before any implementation.
- The few-shot sibling pattern paid off — `generate_code` modification jumped to verdict-2 directly.
- Saving `feedback_local_model_test_context.md` memory was high-value; that lesson would have repeated.
- Proactively updating Plan 3 with stale line numbers and the atomic-write prompt fix makes the next session ~30 minutes faster.
- Splitting helpers (`_resolve_output_path` separate from `_write_output_file`) per the plan is the load-bearing decision for Plan 3 not drifting.

---

## Issues to Address — Prioritized

### BLOCKER (only one)

**`retrieval/test_output.py` was left untracked in the repo.**
Chosen rationale was "orphaned acceptance test artifact, not worth tracking." This is wrong — `retrieval/` is a tracked directory with real LTG artifacts. The `~/workspaces/tmp` preference set this session exists precisely because test artifacts don't belong in the repo.

> **Action:** `rm retrieval/test_output.py` first thing next session. Was never tracked, no commit needed.

---

### Code-level concerns (non-blocking)

**1. Double path resolution.**
`ask_ollama`/`generate_code` call `_resolve_output_path(output_file)` and discard the result, then `_write_output_file(output_file, content)` resolves again. Plan 2 spec said "Reuse the resolved path for the actual write (don't resolve twice)." If `_resolve_output_path` ever gains state-dependent canonicalization, two calls could return different results.

> Fix: have `_write_output_file` accept a pre-resolved `pathlib.Path` as an optional fast path, OR accept only `pathlib.Path` and let callers resolve once. Pair with item 2 below as a single change.

**2. `.resolve()` before mkdir.**
Advisor note #3 from Plan 2 was specific: call `.resolve()` *after* `mkdir(parents=True, exist_ok=True)` so the canonical path is accurate for symlink-traversed parents. Current implementation resolves inside `_resolve_output_path` (before mkdir), so the returned `"Written N bytes to {resolved}"` string may be non-canonical for symlinked parents. No test exercises this, so it passes, but the bug is dormant.

> Fix: rearrange 3 lines in `_write_output_file` — mkdir first, then resolve. Combine with item 1 fix into one commit.

**3. Test 2 lost the strict-content assertion.**
The corrected file dropped `assert result == "mocked-model-output"`, leaving only `assert result == output_file.read_text(...)`. A buggy implementation returning empty string AND writing empty string would pass. The test name implies a stronger guarantee than the assertions deliver.

> Fix: restore `assert result == "mocked-model-output"` as the first assertion in `test_returned_content_equals_file_content`.

**4. Test 4 "any digit" check is too loose.**
`any(ch.isdigit() for ch in result)` passes on path digits alone (pytest's tmp_path includes counter digits). Mocked content is `"mocked-model-output"` (19 bytes), so the status string will say `"19 bytes"`.

> Fix: `assert "19" in result` (or `"19 bytes"` for extra specificity).

**5. Test 9 doesn't verify language hint preservation.**
Plan 2 advisor note #7 called for "language hint preserved in the prompt." Test 9 confirms file written + content returned but doesn't check `_client.chat` call args.

> Fix: add `assert "[Language: python]" in mock_ollama.chat.call_args.kwargs["prompt"]`.

---

### Test coverage gaps

**6. No test for `output_only=True` on `generate_code`.**
Only the happy-path (write + return content) is exercised for `generate_code`. `output_only` path is untested on that tool.

**7. No test for `..` canonicalization.**
Once item 2 is fixed, add: `output_file="subdir/../subdir/file.py"` — resolved path in status string should be canonical.

**8. No test for OSError handling.**
`_write_output_file` catches `OSError` and returns error string. Lower priority — manual reasoning sufficient for now, but a `chmod 444` tmp_dir test would close the gap.

---

### Documentation drift risks

**9. KNOWLEDGE.md says `_resolve_output_path` is "reused by Plan 3."**
Plan 3 isn't done yet. If implementation diverges, entry becomes incorrect.

> Fix: soften to "designed for reuse by `patch_file` (Plan 3, not yet implemented)". Update post-Plan-3.

**10. `feedback_local_model_test_context.md` is overly specific.**
Rule says "always include `mcp-server/pyproject.toml`" — won't generalize to other test directories.

> Fix: reframe as "include the relevant pytest config file (`pyproject.toml` or `pytest.ini`) for the directory under test."

**11. README "When to Delegate" section is stale.**
Parameter signatures were updated but the delegation guide doesn't mention the new edit-loop pattern. Optional follow-up.

---

### PR strategy note

**12. PR #37 bundles Plans 1+2 (12 commits).**
Reasonable judgment call — features are linked, bundling reduces overhead. Downside: if a reviewer finds an issue with Plan 1 refs-param, Plan 2 output_file is also blocked. For future: merge Plan N standalone first, then branch Plan N+1 off master.

> For PR #37: not worth splitting now. Just note the risk.

---

## Plan 3 Pre-Flight Notes

**A. Branch from `feature/ollama-bridge-output-file`, not master.**
`_resolve_output_path` only exists on the output_file branch.

**B. Updated impl prompt in `e7283f8` is load-bearing.**
Don't run the old prompt from memory — read the updated plan first.

**C. Plan 3 test 4 has the same loose `"2" in result` issue.**
Error format is `"Error: old_string found {count} times in {path}..."` — tighten to `"found 2 times" in result`.

**D. Double-resolution issue (item 1) applies to `patch_file` too.**
Fix in Plan 2 first so Plan 3 inherits the clean pattern.

**E. CRLF/UTF-8 round-trip tests are flagged in Plan 3 advisor notes.**
Worth implementing: `patch_file` is the only tool where a corrupted write loses the only copy of the file. Generation can always re-run; a botched patch cannot be un-done.

---

## Verdict

**Ship PR #37 as-is.** Issues are quality polish, not correctness bugs. Functional contract holds.

Before starting Plan 3, address in a single follow-up commit on `feature/ollama-bridge-output-file`:

1. `rm retrieval/test_output.py` (10 seconds)
2. Items 1+2: double-resolution fix + `.resolve()` ordering (10 lines)
3. Items 3+4: restore strict assertion in test 2, tighten digit check in test 4 (3 lines)
4. Item 5: add language hint assertion to test 9 (2 lines)

Total: ~30 minutes, one commit, PR history cleaner before Plan 3 stacks on top.

**Open question for user before Plan 3 starts:**
Does PR #37 need to be merged before Plan 3 begins, or is branching off an unmerged base acceptable? Current `session-context.md` assumes the latter but doesn't flag the risk.
