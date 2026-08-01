# Edit operation vocabularies — primary-source notes

## 1. Anthropic text_editor (str_replace_based_edit_tool)
URL: https://platform.claude.com/docs/en/agents-and-tools/tool-use/text-editor-tool
- versions: text_editor_20241022 (view/create/str_replace/insert/undo_edit),
  20250124 (same), 20250429 (REMOVES undo_edit; renamed str_replace_based_edit_tool),
  20250728 (adds max_characters; else identical to 20250429)
- view(path, view_range?) ; str_replace(path, old_str, new_str) ;
  create(path, file_text) ; insert(path, insert_line, insert_text)
- old_str "must match exactly, including whitespace and indentation"
- error guidance: "Error: Found 3 matches for replacement text. Please provide more
  context to make a unique match." / "Error: No match found for replacement."
- pricing 700 extra input tokens (20250429)
- Anthropic recommends host app implement backups (backup_file) — no undo command in 4.x
- view results carry line numbers; needed for view_range + insert_line

## 2. OpenAI Codex apply_patch / V4A
Source: repos/openai/codex codex-rs/prompts/templates/apply_patch_tool_instructions.md
Grammar: codex-rs/core/src/tools/handlers/apply_patch.lark
Matcher: codex-rs/apply-patch/src/seek_sequence.rs, lib.rs compute_replacements
- Envelope *** Begin Patch / *** End Patch
- FileOps: *** Add File: / *** Delete File: / *** Update File: (+ optional *** Move to:)
- Hunk := "@@" [header] { (" "|"-"|"+") text }  [ "*** End of File" ]
- explicitly "Do not include line numbers"; 3 lines context above/below
- @@ class BaseClass / @@ def method(): = context marker, may stack multiple
- MATCHING LADDER (seek_sequence): exact -> rstrip -> trim both -> Unicode punct normalise
  ("mirrors the fuzzy behaviour of git apply")
- change_context resolved via seek_sequence on the ctx line => BYTE matching, not symbol lookup
- failure: ApplyPatchError::ComputeReplacements "Failed to find context '{ctx}' in {path}" /
  "Failed to find expected lines in {path}"

## 3. Aider
docs: https://aider.chat/docs/more/edit-formats.html
coders: Aider-AI/aider aider/coders/__init__.py
formats: whole, diff (SEARCH/REPLACE), diff-fenced, udiff, udiff-simple, patch (V4A),
  editor-diff, editor-whole, editor-diff-fenced, ask, help, context, architect
- editblock rules (editblock_prompts.py): "<<<<<<< SEARCH / ======= / >>>>>>> REPLACE",
  "EXACTLY MATCH ... character for character", "only replace the FIRST match occurrence",
  new file = empty SEARCH section, move code = 2 blocks (delete + insert)
- matching ladder (editblock_coder.py): perfect_replace -> missing-leading-whitespace flexible
  -> ... ; on total failure tries the OTHER files in chat
- failure msg: "# N SEARCH/REPLACE blocks failed to match!" + "## SearchReplaceNoExactMatch"
  + find_similar_lines "Did you mean to match some of these actual lines" +
  "Are you sure you need this SEARCH/REPLACE block? The REPLACE lines are already in {path}!"
  + "The other N blocks were applied successfully. Don't re-send them."
- udiff errors: UnifiedDiffNoMatch / UnifiedDiffNotUnique (explicitly requires UNIQUE match)
- base_coder: max_reflections = 3; auto_lint=True default (lint errors -> reflected_message),
  auto_test=False default
- benchmark (https://aider.chat/2023/12/21/unified-diffs.html):
  gpt-4-1106 SEARCH/REPLACE 20% -> udiff 61%; lazy comments 12/89 -> 4/89
  gpt-4-0613 26% -> 59%
  "GPT is terrible at working with source code line numbers ... backed up by many
   quantitative benchmark experiments"
  "Experiments without 'high level diff' prompting produce a 30-50% increase in editing errors"
- aider patch_prompts.py = V4A: "Each file MUST appear only once in the patch",
  "Do not include line numbers", "@@ [CLASS_OR_FUNCTION_NAME]" markers

## 4. Serena (SYMBOL-ADDRESSED — the positive result)
docs https://oraios.github.io/serena/01-about/035_tools.html ; repo oraios/serena
src/serena/tools/symbol_tools.py:
  replace_symbol_body(name_path, relative_path, body)
  insert_after_symbol(name_path, relative_path, body)
  insert_before_symbol(name_path, relative_path, body)
  rename_symbol(name_path, relative_path, new_name)
  find_symbol / get_symbols_overview / find_referencing_symbols (retrieval)
- name_path e.g. "MyClass/my_method"
- "IMPORTANT: Only replace symbol bodies if you have previously made a retrieval with
   include_body=True and thus know what constitutes the body!"
- rename_symbol docstring: "for languages with method overloading, like Java, name_path may
   have to include a method's signature to uniquely identify a method"  <-- ambiguity admission
- src/serena/code_editor.py _find_unique_symbol:
   "No symbol with name {name_path} found in file {relative_file_path}"
   "Found multiple {n} symbols with name {name_path} in file {file}"
- validation: EditingToolWithDiagnostics but ENABLE_DIAGNOSTICS = False
   "per-edit diagnostics are a questionable feature, since individual edits often intentionally
    introduce diagnostics ... that are then resolved in subsequent edits"
- string fallback: ReplaceContentTool(relative_path, needle, repl, mode=literal|regex,
   allow_multiple_occurrences) — "use the symbol-level editors when replacing a whole
   method/class"; also DeleteLines/ReplaceLines/InsertAtLine (optional, line-addressed)
- insert_before_symbol docstring names import insertion: "or a new import statement before the
  first symbol in the file"  <-- their ensure_import analogue

## 5. Academic
"Inside the Scaffold: A Source-Code Taxonomy of Coding Agent Architectures"
  arXiv 2604.03515 (Benjamin Rombaut) — 13 agents surveyed
  Table 6 verbatim:
   String replacement (function calling) | OpenHands and SWE-agent (str_replace_editor),
     Codex CLI (apply_patch), OpenCode (edit)
   Write tool (function calling) | Gemini CLI, Cline
   Text-parsed edit blocks | Aider (13 formats), DARS-Agent
   Simulated tool use | Agentless (Anthropic path)
   Pydantic-schema actions | Moatless Tools, Prometheus
  "str_replace_editor ... appears in 5 of 13 agents"
  "This convergence is notable because these agents were developed independently; the shared
   interface reflects a common discovery that exact string matching is more reliable than
   line-number-based or unified-diff-based editing for LLM-generated patches"
  VERIFIED against raw HTML (curl arxiv.org/html/2604.03515v1) — Table 6 + 5-of-13 sentence
  are verbatim. CORRECTION: the sentence "No agents use symbol-based or AST-based editing
  mechanisms" is NOT in the paper — it was a WebFetch summarizer paraphrase. The paper's
  word "symbol" occurs exactly TWICE, both about RETRIEVAL/navigation (OpenCode's
  "experimental LSP integration for symbol navigation"; aider's tree-sitter repomap
  "extract symbol definitions"). => the negative result is MY INFERENCE from Table 6 having
  no symbol/AST edit category + those two mentions being retrieval-only.
  AutoCodeRover: custom XML-like <original>/<patched> tags (per WebFetch, unverified verbatim)
  mini-swe-agent: only agent editing via shell commands
  SWE-agent supports 10 output parsers (FunctionCallingParser, ThoughtActionParser,
    XMLThoughtActionParser, ...) [verbatim]

CODESTRUCT arXiv 2604.05407 — structured AST action space
  readCode(path, selector?, line_range?, threshold τ)
  editCode(path, operation ∈ {insert, replace, removal}, selector, replacement_code)
  selector: unscoped `load` or scoped `User.load`; node path form file.py::ClassName::method
  "Edits that would introduce syntax errors are rejected, ensuring post-edit syntactic validity
   via AST validation"
  "if n=∅ then return Error('Selector not found')"
  SWE-Bench Verified pass@1:
   GPT-5      66.0 -> 67.2 (input -19.1%, output -45.7%, cost -19.5%)
   GPT-5-mini 60.4 -> 62.0 (input -31.9%, output -72.4%, cost -32.6%)
   GPT-5-nano 19.6 -> 40.4 (input +40.8%, output +10.5%, cost +40.8%)
  "GPT-5-nano improves by 20.8% as empty-patch failures drop from 46.6% to 7.2%"
  "For higher-capacity models (GPT-5, GPT-5-mini, Qwen3-Coder), CodeStruct reduces errors per
   instance by 76-88%"
  paper does NOT address adding imports or edits outside named symbols
  ALL NUMBERS VERIFIED against raw HTML (curl arxiv.org/html/2604.05407v1). AWS AI Labs
  (Myeongsoo Kim, Joe Hsu, Dingmin Wang, Shweta Garg, Varun Kumar, Murali Krishna Ramanathan).
  Extra verified rows: SWE-Bench Qwen3-Coder 61.2 -> 66.2 (+5.0), tokens -12.5%.
  CodeAssistBench: Qwen3-32B 15.6 -> 20.0 (+4.4); Qwen3-8B 13.3 -> 14.1 (+0.8).
  "empty patches drop from 233 to 36" (GPT-5-nano), "a 20% increase in tool-level errors
   despite a 20.8pp accuracy gain, reflecting a redistribution rather than a reduction of
   failures: structured navigation enables correct localization and more edit attempts while
   dramatically reducing early agent terminations"
  Ablation: removing readCode costs more than removing editCode
   (-7.8 Pass@1 Qwen3-32B, -5.2 GPT-5-mini)
  Fig 1 verbatim: "Text-based agents (left) read ~300 lines to locate a function and
   regenerate ~44 lines verbatim for removal, making edits brittle to formatting changes.
   CodeStruct (right) reads only the target symbol (~50 lines) and specifies removal in
   ~2 lines via a symbol-scoped edit."
  Appendix B.3 verbatim on why editCode matters: without it agents rely on str_replace which
   "(1) require exact string matching, leading to frequent failures from whitespace or
   formatting mismatches; (2) cannot verify syntactic correctness before application,
   resulting in broken code that requires additional repair cycles; and (3) lack scope
   awareness"
  Selector matching is FuzzyMatch(E, sigma) — deterministic name-based, "guf can match
   get_user_file"

## 6. Moatless Tools (Pydantic-schema actions — closest analogue to our JSON schema)
repo aorwall/moatless-tools moatless/actions/
  edit actions: string_replace.py, insert_line.py, append_string.py, create_file.py,
    claude_text_editor.py
  retrieval actions (SYMBOL-addressed): find_function.py, find_class.py, find_code_snippet.py,
    semantic_search.py
  StringReplaceArgs(path, old_str, new_str) with docstring rules: exact match, unique,
    "Do not include line numbers in old_str or new_str"
  validators: strips line numbers (r"^\s*(\d+)\t*"), rejects empty old_str, rejects null new_str
    ("Return an empty string if your intention was to remove old_str")
  failure taxonomy: string_not_found, multiple_occurrences, multiple_potential_occurrences,
    string_already_exists, no_changes; flags: auto_corrected_indentation,
    targeted_in_context_replacement, lines_not_in_context

## LOCAL PROJECT CONTEXT (do not re-litigate silently)
- docs/plans/oficina-p2-edit-mode.md — E-D1: M2 = whole-file-with-context; code-anchored
  (locate_unit symbol locator -> patch_file exact anchor) kept as ON-FILE FALLBACK with an
  explicit trigger: "a real edit run shows silently dropped sibling code".
- Session 127 RESULTS addendum: module docstring deleted in 4 of 4 runs on parser/evaluator,
  including runs whose objective explicitly said do NOT modify the module docstring.
  => that IS the drift evidence; it is doc, not sibling code, so trigger not formally fired.
- docs/plans/oficina-language-widening-notes.md ref:oficina-function-kind-write-model:
  "locator is a per-language LanguagePack member (locate_unit(source, name) -> span)";
  "named-unit kinds (function, class) are code-anchorable (the name is the locator);
   arbitrary patch kinds are not"
- ollama-bridge patch_file already = exact-anchor str_replace with replace_all + count errors
  (docs/plans/ollama-bridge-patch-file-acceptance-results.md, 10/10 scenarios)
- 14B output reliability ceiling ~800 tokens (root KNOWLEDGE)

## 7. FAST APPLY (subagent, primary sources verified via raw .md endpoints)
Morph wrapper: <instruction>..</instruction><code>..</code><update>..</update>
  marker literal `// ... existing code ...` (fixed, ALL languages)
  tool schema edit_file(target_file, code_edit, instructions)
  RULE (verbatim): "ALWAYS use \"// ... existing code ...\" for unchanged sections
    (omitting this marker will cause deletions)"   <-- NOT fail-safe
  "Token usage drops 40% compared to full-file rewrites"
  models morph-v3-fast 10500 tok/s @96%, morph-v3-large 2500-5000 tok/s @98% (docs disagree)
  errors documented: 200/400/401 only — NO semantic failure code
  prompting guide: "If you've suggested a reasonable code_edit that wasn't followed by the
    apply model, you should try reapplying the edit."
Relace: same 3-tag wrapper; marker NOT fixed — "// ... rest of code ...",
  "// ... keep existing code ...", "// ... keep calculateTotalFunction ..."
  relace-apply-3, LoRA on 3-8B base; response = {mergedCode, usage} only
  "Smoothing" = model deliberately auto-corrects the sketch (e.g. adds missing import)
    and that counts as a CORRECT merge
  "We strongly recommend passing the code changes back to the agent in UDiff format"
    — client-side difflib, detects no-op not wrong-merge
  rename example: "A standard merging algorithm would likely just add a new function called
    messageHandler, duplicating the original function." => symbol identity fails on rename
Cursor (cursor.com/blog/instant-apply, Aman Sanger 2024-05-14): apply model REWRITES WHOLE FILE
  "By default, we have language models generate the fully rewritten file"
  rejects diffs: "Thinking in Fewer Tokens", "Diffs are Out of Distribution",
   "Outputting Line Numbers ... models are notoriously bad at counting line numbers"
  ~1000 tok/s via speculative edits, 70B ft; Fireworks validates speculation with greedy decode
   => decoding-fidelity guarantee, NOT merge-correctness
Osmosis-Apply-1.7B: <code>/<edit> tags; planner rule "Provide 2-3 lines of context above and
  below your changes ... so that Osmosis-Apply-1.7B can locate where to insert the edit"
  => explicit statement that addressing = surrounding context
Kortix FastApply: <code>/<update> -> <updated-code>; README: "simple file comparison isn't
  always sufficient" (insert flexibility, function ordering)
3rd-party guard plugin (opencode-morph-fast-apply): marker-leakage guard, catastrophic
  truncation guard (>60% chars + >50% lines lost), dropped-imports guard
  => the guards vendors don't ship
NO independent accuracy benchmark of any apply model exists.

## SYNTHESIS DRAFT (load-bearing ops that recur)
Ops present in >=3 independent systems:
  1. replace-a-region  (str_replace / SEARCH-REPLACE / Update-File hunk / editCode replace /
     replace_symbol_body / string_replace)  — UNIVERSAL
  2. create-file       (create / *** Add File / CreateFile / create_python_file / whole)  — UNIVERSAL
  3. delete-file       (*** Delete File / safe_delete_symbol)  — common, file-level
  4. insert-at-position (insert(insert_line) / insert_after_symbol / insert_line / editCode insert)
     — present in Anthropic, Serena, moatless, CODESTRUCT; ABSENT from aider diff + codex V4A
       (both express insertion as a hunk with zero '-' lines)
  5. delete-region     (usually expressed as replace-with-empty; only CODESTRUCT has an explicit
     `removal` op; moatless: "Return an empty string if your intention was to remove old_str")
  6. move/rename file  (*** Move to: — codex only)
  7. rename symbol     (Serena only)
ensure_import: ZERO LLM edit vocabularies have it. Only the non-LLM structural lineage
  (libcst AddImportsVisitor, OpenRewrite AddImport) + Relace's "Smoothing" (implicit,
  model-inferred, not an op). Serena degrades it to insert_before_symbol(first symbol).

ANCHOR-BURDEN axis (the column no source has):
  whole-file      -> reproduce EVERY byte of the file
  SEARCH/REPLACE  -> reproduce the bytes of the region + enough for uniqueness
  V4A / udiff     -> reproduce 3 lines context above+below verbatim
  lazy sketch     -> reproduce 2-3 context lines + the changed body
  symbol selector -> NAME the unit; reproduce only the new body
  line numbers    -> count (universally rejected)

## 8. STRUCTURAL LINEAGE (subagent, raw-doc verified)
ast-grep: rule{pattern|kind|inside|has|follows|precedes|all|any|not|matches} + fix + transform
  metavars $A, $$$ARGS. HARD LIMIT (verbatim): "ast-grep rule can only fix one target node at
  one time by replacing the target node text with a new string."
  NO import operation (zero hits for "import" in the fix/rule reference).
  zero matches = exit 0 no-op; many = bulk with -U/--update-all or -i interactive.
Comby: match/rewrite templates with holes :[v], :[[ident]], :[v~regex], :[v:e]; -config TOML
  with [name] match= rewrite= rule=. Text/delimiter-aware, NO symbol resolution.
  zero = no diff no write; many = bulk unless -review.
Semgrep: only TWO autofix keys — `fix:` (metavar substitution) and `fix-regex:` (regex+
  replacement+count). Deletion = fix: "". No import mgmt, no multi-hunk.
  --autofix docs warning verbatim: "WARNING: data loss can occur with this flag ... this mode
  is experimental and not guaranteed to function properly." Overlapping fixes: one picked
  arbitrarily (vendor blog + issues #3577/#4428).
OpenRewrite: THE symbol-addressed one. Method patterns are AspectJ-style, TYPE-AWARE, over a
  Lossless Semantic Tree: `org.foo.Bar baz(String, int)`; wildcards `*` (one) `..` (zero+);
  `org.Foo#bar()` alias form.
  Recipes: ChangeMethodName(methodPattern,newMethodName,matchOverrides?,ignoreDefinition?);
   ChangeType(oldFQN,newFQN,ignoreDefinition?); AddMethodParameter(methodPattern,parameterType,
   parameterName,parameterIndex?); ChangeMethodTargetToStatic(...); RemoveUnusedImports (NO opts).
  *** AddImport is NOT a declarative recipe *** — it is a JavaIsoVisitor:
   AddImport(String type, @Nullable String member, boolean onlyIfReferenced)
   reached via maybeAddImport()/maybeRemoveImport() from type-touching recipes.
   => "add import if absent" is an INVARIANT maintained by the framework, not an opcode.
   There is even a lint recipe RemoveImportBeforeAddImport policing call order.
  zero matches = silent no-op empty diff; many = bulk by construction.
LLM harnesses driving them:
  * Moderne MCP (docs.moderne.io/user-documentation/agent-tools/mcp/overview/) — SECOND
    production instance of model-callable SYMBOL-ADDRESSED EDITS:
      change_type ("Renames or moves a type across the entire codebase. Updates all imports,
        references, declarations, and usages")
      change_method_name  ("Uses AspectJ-style method patterns")
      pattern_replace (Refaster template)
      + find_types/find_methods/find_annotations/find_implementations/symbols_overview
      + trigrep_structural_search (Comby inside an LLM tool)
    rationale verbatim: "the work that can be done deterministically should be done
    deterministically, so the agent can spend its inference budget on work that actually
    requires reasoning."  vendor datum: agent hand-writing transforms burned "tens of millions
    of tokens with only about a quarter of the work completed" vs run_recipe "completed in
    minutes using roughly 30,000 tokens".
  * ast-grep-mcp (441*): EXPERIMENTAL, SEARCH-ONLY — no rewrite tool.
  * semgrep/mcp (682*): official but ARCHIVED 2025-10-28, autofix NOT exposed.
  * GenAIScript: ast-grep locates, LLM writes replacement text, changeset applies —
    the model does NOT emit rules.
  * RuleFlow arXiv 2602.09051 — LLM discovers optimizations then converts to rewrite rules.

## 9. SWE-agent / OpenHands (subagent, source-pinned)
Repos renamed: princeton-nlp/SWE-agent -> SWE-agent/SWE-agent;
  All-Hands-AI/OpenHands -> OpenHands/OpenHands (now a TS frontend);
  agent moved to OpenHands/software-agent-sdk. openhands-aci ARCHIVED.
SWE-agent bundles (mutually exclusive):
  windowed: open/goto/scroll_up/scroll_down/create
  search: find_file/search_dir/search_file
  windowed_edit_linting (the PAPER tool): `edit <start_line>:<end_line>\n<text>\nend_of_edit`
  windowed_edit_replace: `edit <search> <replace> [<replace-all>]` scoped to DISPLAYED LINES;
    `insert <text> [<line>]`
  windowed_edit_rewrite: `edit <text>` = replace whole window
  edit_anthropic (CURRENT DEFAULT in config/default.yaml): str_replace_editor, docstring
    copied FROM OpenHands (in-source comment) which copied from Anthropic
LINT-REVERT (paper Appendix A):
  flake8 --isolated --select=F821,F822,F831,E111,E112,E113,E999,E902
  pre-edit lint vs post-edit lint diff; if NEW errors -> wf.undo_edit(), exit 1
  message shows: errors + "how your edit would have looked" + "the original code" +
   "Your changes have NOT been applied" + "DO NOT re-run the same failed edit command"
  ABLATION (Table 3, SWE-bench Lite, GPT-4 Turbo):
    edit w/ linting 18.0 | edit w/o linting 15.0 (-3.0) | no edit tool 10.3 (-7.7)
    (adjacent: viewer 100 lines 18.0 vs full file 12.7; context last-5-obs 18.0 vs full 15.0)
  FREQUENCY: 1185/2294 (51.7%) instances had >=1 failed edit; median 3, MAX 33.
   Among RESOLVED: 113/286 (31.5%), median 2. "likelihood of recovery decreases as n increases"
  *** the +3.0 lint-revert is OFF in today's default: edit_anthropic's linter is warning-only
      and gated by USE_LINTER which defaults "false" and is set by no config ***
  *** linting REMOVED ENTIRELY from the OpenHands SDK file_editor ***
MALFORMED-ACTION LADDER: max_requeries = 3; four exception classes consume the budget
  (FormatError, _BlockedActionError, ContentPolicyViolationError, BashIncorrectSyntaxError);
  on exhaustion -> autosubmit with exit_format (not a crash).
  De-noising: a corrected malformed turn is REMOVED from message history.
  *** KEY: lint-rejected edits raise _RetryWithOutput via RETRY_WITH_OUTPUT_TOKEN and do NOT
      increment n_format_fails => "edit didn't apply" and "output didn't parse" are SEPARATE
      budgets. That is why max=33 failed edits is possible. ***
OpenHands SDK presets: default=FileEditorTool(str_replace_editor);
  gpt5=ApplyPatchTool (V4A); gemini=EditTool(old_string,new_string,expected_replacements)
  + PlanningFileEditorTool (same 5 cmds, writes restricted to PLAN.md)
  ACI fork additions: enable_linting (REPORT-ONLY, never reverts), old_str.strip() retry,
   binary/office view via MarkdownConverter, MAX_FILE_SIZE_MB=10,
   FileHistoryManager(max_history_per_file=10)
OpenHands LLM DRAFT EDITOR (legacy, opt-in, did NOT survive SDK rewrite):
  edit_file(path, content, start, end); "the assistant may skip unchanged lines using comments
  like `# ... existing code ...`"; a SECOND model (draft_editor_llm) merges
  <original_code>/<update_snippet> -> <updated_code>; on lint error a THIRD LLM pass
  (CORRECT_SYS_MSG) repairs rather than reverting; range-too-large degrades to top-k similar
  chunk hints with `open_file(path, midline)` suggestions.
SYMBOL ADDRESSING: NO. grep for ast.parse/tree_sitter/libcst across both projects' edit paths
  = ZERO hits; all hits are viewer (filemap), linter, or indexing/localization.
  V4A `@@ def foo(self):` near-miss ruled out at the parser: `s == def_str` raw string equality
  with one `.strip()` fallback recorded as `fuzz`. No parse, no symbol table.
  locagent retrieval strips a "def " prefix from query terms => symbols are a RETRIEVAL
  vocabulary, never an EDIT vocabulary.
windowed_edit_replace error set (richest recovery in the survey):
  _NOT_FOUND / _NOT_FOUND_IN_WINDOW_MSG (searches WHOLE FILE, returns line numbers +
   tells the model to `goto` them) / _MULTIPLE_OCCURRENCES_MSG / _NO_CHANGES_MADE_MSG
  exit codes 1 no file open, 2 no-op, 3 not found, 4 multiple/lint
  success msg ships a 3-point review checklist (indentation / duplicate lines / broken
   functionality)
