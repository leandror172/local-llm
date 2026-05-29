# Advisor Review of MCP Plans 1–3

*Reviewed 2026-05-22 against plans in `docs/plans/ollama-bridge-{refs-param,output-file,patch-file}.md`.*

---

<!-- ref:mcp-refs-param-advisor-notes -->
## Plan 1 (refs param) — Review Notes

### Blockers

**1. Redundant marker output.** `ref-lookup.sh`'s sed prints from `<!-- ref:KEY -->` through `<!-- /ref:KEY -->` inclusive. The plan's `_build_refs_block` then wraps each result with `### ref:KEY` — every ref ends up labelled twice (once as HTML comment, once as markdown heading). Decide one: (a) keep the HTML-comment markers from sed and drop the `### ref:KEY` prepend — simpler, zero post-processing; (b) strip HTML markers in `_resolve_ref_key` and rely on the `###` label. Recommend (a). Test 5 (`labels_each_key`) must be updated to match whichever you pick.

**2. `refs_root` fallback diverges from existing `ref_lookup` tool.** The existing tool (server.py:1094-1098) passes `--root` only when path is not None; otherwise lets the script use its own default. The plan's `_build_refs_block` explicitly resolves None → REPO_ROOT in Python before invoking. Two tools, same conceptual root, two different fallback policies. Either (a) match the existing tool's behaviour (omit `--root` when None, let the shell script handle it), or (b) refactor `ref_lookup` to share the new fallback. Don't ship a silent divergence.

### Should fix

**3. `generate_code` integration test missing.** All 9 tests target `ask_ollama`. `generate_code` has different prompt-assembly (language-hint position). Duplicate test 8 against `generate_code` so the ordering invariant is enforced in both tools.

**4. Acceptance test #2 doesn't actually test cross-folder.** It passes `refs_root="/mnt/i/workspaces/llm"` — that's REPO_ROOT, the default. Replace with a truly external path (e.g., `/tmp/external-refs/` containing test markers) to exercise the `--root` flag end-to-end.

**5. `refs_root` relative-path semantics unspecified.** If a caller passes `refs_root="docs/plans"`, behaviour depends on server CWD at subprocess launch. Pick: (a) resolve client-side via `pathlib.Path(refs_root).resolve()` before invoking, or (b) reject non-absolute paths with error. Document.

**6. Caller responsibility for context-window size not stated.** A 10-ref call could deliver 50KB of text — beyond the 16384-token default `num_ctx` for 14B personas. Add one line to the docstring; optional: warn above a threshold (~48KB combined).

**7. Private-function testing convention.** Tests import `_resolve_ref_key` and `_build_refs_block` by underscore name. Decide: keep underscore and document that direct unit-testing is intentional, or rename without underscore. Don't leave it ambiguous.

### Nits

**8. Test 8 sentinel collision risk.** If the mocked model output ever contained literal `"<refs>"`, the index-based ordering check would behave confusingly. Use `find()` and assert both ≥ 0 first.

**9. ref-lookup.sh has no internal timeout** — a stuck grep across a huge tree consumes the full 10s `_resolve_ref_key` budget. Note in docstring that ref folders are expected to be small.

**10. Acceptance test #4 uses `local-model-conventions`** — but Plan 1's own overlay update modifies that ref's surrounding file. Run acceptance against an unmodified ref (e.g., `indexing-convention`) to avoid coupling the test to the same change under verification.
<!-- /ref:mcp-refs-param-advisor-notes -->

---

<!-- ref:mcp-output-file-advisor-notes -->
## Plan 2 (output_file) — Review Notes

### Blockers

**1. Body insertion description is mechanically wrong.** Step 2 says: "Add body (after `return response.content`, insert before returning)". Code placed after a `return` is unreachable. The actual change *replaces* the bare `return response.content` line with the new block. The code snippet itself is correct; only the prose is misleading. Rewrite: "Replace the single `return response.content` line with the block below."

**2. Validate `output_file` path BEFORE the Ollama call.** Current flow: (1) call Ollama, (2) receive response, (3) try to write. If `output_file` is relative and `REPO_ROOT` is None, the call wastes 5–30s of GPU time and battery just to fail at write time. Add an early resolution pass at the top of `ask_ollama`/`generate_code`: if `output_file` is set, resolve it once; fail-fast on resolution error before any LLM I/O. Reuse the resolved path for the actual write (don't resolve twice).

**3. Path canonicalization.** `pathlib.Path(REPO_ROOT) / relative_path` is non-canonical if `relative_path` contains `..` or symlinks. The displayed `"Written N bytes to {path}"` should be canonical so Claude can pass it back as `context_files`. Call `.resolve()` AFTER `mkdir(parents=True, exist_ok=True)` so parents exist for full resolution.

### Should fix

**4. Atomicity.** `pathlib.Path.write_text(content)` is non-atomic — failure between truncate and full-write corrupts/truncates the target. Use temp-file-then-rename: write to `{path}.tmp`, then `os.replace({path}.tmp, path)`. Atomic on POSIX. Three lines, removes a real risk that compounds in `patch_file`.

**5. `output_only` without `output_file` — commit to one behaviour.** Decisions row says "Silently ignored (or warn)". Test 5 verifies silent ignore. Drop the `(or warn)` parenthetical. Match implementation to test.

**6. Sync file I/O in async function.** `write_text` blocks the asyncio event loop. Negligible for tiny outputs; blocks other in-flight tool calls for multi-megabyte responses from a 30B model. Either `asyncio.to_thread(...)` or document the trade-off explicitly. Not a blocker for normal use.

**7. `generate_code` integration test missing.** Same gap as Plan 1 — only `ask_ollama` exercised. Add at least one `generate_code` end-to-end test (file written, content returned, language hint preserved in the prompt).

**8. Decisions table omits atomicity.** If you adopt fix #4, update the "File write mode" row to mention atomic replace.

### Nits

**9. Byte count source.** `len(content.encode())` re-encodes. Cheaper: `pathlib.Path(path).stat().st_size` post-write. Negligible.

**10. Docstring wording.** "Content is always returned to the caller as well, unless `output_only=True`" → clearer: "If `output_only=True` and `output_file` is set, only a status string is returned. Otherwise the full content is returned."

**11. Acceptance test #5 is unrunnable in normal dev env** (requires unset `LLM_REPO_ROOT`). Automated test 8 already covers it via monkeypatch. Drop from manual acceptance.

**12. Windows path normalization.** Not a concern for this WSL-only project, but one-line note in docstring: paths are interpreted in the server's filesystem namespace.
<!-- /ref:mcp-output-file-advisor-notes -->

---

<!-- ref:mcp-patch-file-advisor-notes -->
## Plan 3 (patch_file) — Review Notes

### Blockers

**1. No atomic write — data loss risk.** Plan does `read_text` then `write_text` directly. `patch_file`'s risk is *higher* than `output_file`'s because the existing file IS the source of truth — a failed write between truncate and full-write leaves the file corrupted, often empty or truncated to half its size. Losing this file means losing Claude's prior generation work. Use temp-file-then-rename: write to `{path}.tmp`, then `os.replace({path}.tmp, path)`. Atomic on POSIX. Same mechanism as recommended for Plan 2; here it's load-bearing.

### Should fix

**2. Test 4 assertion `"2" in result` is too loose.** Pytest's `tmp_path` includes counter digits (e.g., `/tmp/pytest-of-user/pytest-23/test_4_0/code.py`); `"2" in result` passes trivially on path digits. Tighten to `assert "found 2 times" in result` — match Plan Step 1.6's specified error format literally.

**3. Missing test: `replace_all=True` with count==1.** Current matrix:
- count==1, replace_all=False (test 1, default)
- count==2, replace_all=False (test 4)
- count==2, replace_all=True (test 5)

The combination `replace_all=True` + count==1 should succeed. Add one test to catch a stray `if count > 1: replace else: no-op` branch. One line.

**4. UTF-8 round-trip not exercised.** Write a file with non-ASCII (`"# café\nreturn 1\n"`), patch `"return 1"` → `"return 42"`, assert `"café"` survives. Catches bytes-vs-str regressions in the read-replace-write chain.

**5. CRLF line endings unspecified.** A file with CRLF + an `old_string` written with LF won't match. Don't auto-normalize (Edit tool doesn't either) — fail explicitly. But: the count==0 error message should hint at line-ending mismatches when the file content contains `\r\n`. Optional, high-value for debuggability.

**6. Path resolution duplication risks drift.** Plan inlines the same 4-line resolution `_write_output_file` uses. If Plan 2's logic gains `.resolve()` (per recommendation 3 above), `patch_file` won't pick it up. Either extract a `_resolve_output_path(path: str) -> str | None` helper used by both (recommended), or add a cross-reference comment so drift is visible at review.

**7. Acceptance test #3 setup is unclear/wrong.** Comment says "First write a file with a repeated string" — but the immediately-preceding state (`/tmp/p.py` from test #1) contains `"return 42"`, only one occurrence of `"42"`. The test isn't reproducible from the inline comments. Either add explicit setup or drop this scenario (automated test 4 already covers it).

### Nits

**8. Test 1 name vs default behaviour.** `test_basic_replacement_changes_file_content` calls with no `replace_all` arg (default False = strict-uniqueness). Reader may not realise default is strict. Rename to `test_basic_replacement_unique_match` to make the contract explicit.

**9. Step 1 line estimate.** "~50 lines" — actual will be ~30 with docstring + type hints. Update or accept padding.

**10. Error-message punctuation consistency.** Plan 1 error strings often end in a period; Plan 3 Step 1.5 omits trailing period. Make consistent across all three plans.

**11. Deferred `line_range` overload** — useful when `old_string` is repeated or ambiguous, but out of scope. The current `replace_all` + uniqueness check covers ~95% of cases. Mention as a follow-up only.
<!-- /ref:mcp-patch-file-advisor-notes -->

---

<!-- ref:mcp-plans-advisor-summary -->
## Summary (cross-cutting)

**Two real blockers, both quick fixes:**
- Plan 1 marker redundancy — pervasive (every refs prompt sent to Ollama), but trivial fix
- Plan 2 prose-vs-code mismatch on body insertion — will confuse the implementer

**One safety blocker:**
- Plan 3 non-atomic write — `os.replace` fixes both Plans 2 and 3 in one pass

**One efficiency blocker:**
- Plan 2 wastes Ollama calls on pre-validatable path errors — move validation upstream

**One cross-plan refactor opportunity:** extract `_resolve_output_path` shared by `_write_output_file` and `patch_file` before Plan 3 ships, to avoid drift.

**Tests still missing in two plans:** `generate_code` integration coverage. Currently only `ask_ollama` is exercised in Plans 1 and 2.
<!-- /ref:mcp-plans-advisor-summary -->
