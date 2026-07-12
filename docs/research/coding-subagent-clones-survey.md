# Coding-Subagent Design Survey — Locally Cloned Repos

Companion piece to `docs/research/coding-subagent-prior-art.md` and
`coding-subagent-prior-art-webresearch.md` (external tools: Aider, OpenHands, SWE-agent,
MCP async-job patterns). This survey covers six repos cloned locally under
`~/workspaces/clones/` (real path `/mnt/i/workspaces/clones/`), read for architectural
patterns applicable to the planned async coding-subagent system: an MCP submit→run_id→poll
surface, a detached worker loop where a local coder model (qwen2.5-coder:14b) produces one
deliverable per run, a deterministic evaluator gate (compile/lint/tests + LLM judge, budget
~2-3 iterations + one fresh start), Claude reviewing each delivered result, and future phases
(planner briefs, a question channel, stepwise generation, DPO harvest).

All file paths below are absolute under `/mnt/i/workspaces/clones/...` (identical to
`~/workspaces/clones/...` — symlinked, same inode).

## Inventory

| Repo | What it is | License | Relevance |
|---|---|---|---|
| `claude-code/` | Leaked/reconstructed TypeScript source of the Claude Code CLI (via an npm sourcemap leak, per its own README) | **No license — proprietary, all rights reserved (Anthropic PBC)** | **Relevant** — patterns only, see caveat below |
| `claude-code-sourcemap/` | A second copy/viewer of the same leaked source (`cli.mjs` + `vendor/` + `src/`), used here only as a navigation aid | Same Anthropic copyright notice in `LICENSE.md` | Tangential — navigation aid, not independently read |
| `open-multi-agent/` | TypeScript multi-agent orchestration framework (`@open-multi-agent/core`); goal→task-DAG coordinator, own agent runner, multi-provider LLM adapters including local/Ollama | MIT (`LICENSE`) | **Relevant** |
| `odysseus/` | Self-hosted AI workspace product (chat, agents, deep research, documents, email, notes, calendar, local model workflows); Python core + Docker | AGPL-3.0 (`LICENSE`) | Irrelevant |
| `ollama-metrics/` | Go Prometheus sidecar/proxy for Ollama (token counts, duration, tok/s) | Not inspected (no LICENSE read) | Irrelevant (tangential: could later wrap the worker's Ollama calls with Prometheus metrics, but out of scope for the current design questions) |
| `career-ops/` | Node.js/Playwright job-search pipeline built as Claude Code slash-command "modes" + a batch runner | MIT (`LICENSE`) | Irrelevant |

---

## 1. `claude-code/` — deep pass

**Provenance caveat, read first:** this repo's own `README.md` says it is a backup of source
leaked via an npm sourcemap in March 2026, and frames several features in showman language
("BUDDY — Terminal Tamagotchi," "Undercover Mode," "KAIROS," "ULTRAPLAN — remote Opus 4.6
session"). I verified these are not just README color: `feature('KAIROS')` and the ULTRAPLAN
poll loop are real, load-bearing code in `src/commands/ultraplan.tsx` and
`src/utils/ultraplan/ccrSession.ts`, gated behind the same `bun:bundle` `feature()` flag system
used throughout the codebase for every other capability. `claude-code-sourcemap/` (a second,
independently-obtained copy of the same leak, viewable via its bundled `cli.mjs`) contains the
same tool names, hook event names, and file layout, which cross-corroborates that this is a
genuine build artifact rather than a fabricated repo. Whether every narrative claim in the
outer README is accurate is not something I verified line-by-line — treat marketing framing
skeptically, but the source structure and mechanics described below are directly read from the
code, not from the README's prose.

**Handling rule for this report and any follow-up: READ FOR PATTERNS ONLY.** There is no
license grant of any kind on this code — no LICENSE file exists in `claude-code/`, and the
sibling `claude-code-sourcemap/LICENSE.md` states outright "© Anthropic PBC. All rights
reserved." Nothing below should be copied, adapted verbatim, or pasted into the llm repo. What
follows describes *architecture*, not implementation, specifically so a follow-up session can
reproduce the *idea* independently in Python without touching the source text.

### 1a. Main agent loop, tool scheduling, parallel vs. serial execution

- `src/query.ts` — `queryLoop()` (line 241) is a single `while (true)` per conversation turn.
  Each iteration: applies context-management passes (snip/microcompact/autocompact/collapse),
  calls the API, collects `tool_use` blocks as they stream (`toolUseBlocks`, comment at line
  554 notes `stop_reason === 'tool_use'` is unreliable so the loop tracks blocks directly),
  executes them, appends `tool_result`s, and `continue`s. The loop exits by `return { reason:
  'completed' }` when a turn produces zero tool-use blocks (line ~1357), not by a special
  "done" tool.
- A `StreamingToolExecutor` (referenced at `query.ts:563`, class not read in full) can start
  executing a tool as soon as its `tool_use` block finishes streaming, before the rest of the
  assistant message arrives — reduces latency versus waiting for the full turn.
- **Tool scheduling — the concurrency-safety partition worth stealing directly:**
  `src/services/tools/toolOrchestration.ts`. `partitionToolCalls()` (line 91) walks the
  model's tool-use blocks in order and groups consecutive *concurrency-safe* (read-only) calls
  into one batch; any non-safe call becomes its own single-item batch. `runTools()` (line 19)
  then runs each batch either via `runToolsConcurrently()` (bounded `Promise`-style fan-out,
  default cap 10, env override `CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY`, `getMaxToolUseConcurrency()`
  at line 8) or `runToolsSerially()` — one at a time, in order. Concurrency-safety is a
  per-tool method, `isConcurrencySafe(input)` (declared `Tool.ts:402`, default `false` at
  `Tool.ts:759` — unknown tools assume unsafe). This is a clean, small, directly portable
  pattern for a Python harness: partition-by-safety-then-batch, not "everything parallel" or
  "everything serial."

### 1b. Background/async work handling

- `src/Task.ts` is a generic run/job abstraction, not tool-specific. `TaskStatus = 'pending' |
  'running' | 'completed' | 'failed' | 'killed'` (line 15), `isTerminalTaskStatus()` (line 27),
  `TaskStateBase` (line 45) carries `id`, `status`, `startTime`/`endTime`, and critically
  `outputFile` + `outputOffset` for incremental output polling. `generateTaskId(type)` (line
  98) mints type-prefixed random IDs (`b...` bash, `a...` local agent, `r...` remote agent,
  etc.) from a 36-char alphabet, 8 random bytes — collision-resistant, human-scannable prefix.
- **Output streaming for a long-running background job:** `src/utils/task/diskOutput.ts`.
  `DiskTaskOutput` is a single-writer append queue per task (`#queue`/`#drain()`, explicit
  comments warning against adding `await` inside the hot write path to avoid buffer buildup).
  Writers call `appendTaskOutput(taskId, content)`; readers/pollers call
  `getTaskOutputDelta(taskId, fromOffset, maxBytes)` (line 304) which does a *byte-range* read
  (`readFileRange`) and returns `{content, newOffset}` — never loads the whole file. There's a
  disk cap (`MAX_TASK_OUTPUT_BYTES = 5GB`, line 30) with a truncation marker, and `O_NOFOLLOW`
  + `O_EXCL` on file creation as a symlink-attack guard for sandboxed writers (lines 17-21,
  400-416) — worth keeping if the worker ever runs inside a container/sandbox writing to a
  host-visible directory.
- **Auto-backgrounding of long synchronous calls:** `src/tools/BashTool/BashTool.tsx` — a
  foreground command that blows through an `ASSISTANT_BLOCKING_BUDGET_MS` gets *automatically*
  converted into a background task and the model is told: "Command exceeded the assistant-mode
  blocking budget (...) and was moved to the background with ID: {id}. It is still running —
  you will be notified when it completes." (line ~610). Manual backgrounding is
  `run_in_background: true` on the tool input (schema at line 241). This maps directly onto
  the vision's "submit→run_id→poll" surface: a synchronous wait with a hard timeout that falls
  back to returning a `run_id` is a good default UX rather than forcing every caller to always
  choose sync-vs-async up front.
- **The run/job abstraction with explicit CRUD + status polling — the closest one-to-one match
  to the planned MCP surface:** `src/tools/TaskCreateTool/TaskCreateTool.ts`,
  `TaskGetTool/TaskGetTool.ts`, `TaskListTool/TaskListTool.ts`,
  `TaskUpdateTool/TaskUpdateTool.ts` (406 lines, not fully read), `TaskStopTool/TaskStopTool.ts`
  (rejects stop if `task.status !== 'running'`, line 82). Backing store is
  `src/utils/tasks.ts`: one JSON file per task
  (`getTaskPath()` line 229 → `~/.claude/tasks/<sanitized taskListId>/<sanitized taskId>.json`),
  a `blocks`/`blockedBy` dependency graph on each `Task` (line 76-89), and a `claimTask()`
  function (line 541) that uses an **exclusive-create lockfile** (`writeFile(lockPath, '',
  {flag: 'wx'})`, line 518 — first writer wins, EEXIST ignored) around a check-then-claim
  sequence, explicitly to avoid the TOCTOU race of "check agent isn't busy, then claim" across
  concurrent workers. `findHighestTaskId()` (line 271) merges a filesystem scan with a
  persisted high-water mark so IDs stay monotonic across deletions. **This whole subsystem —
  file-per-run JSON state, lockfile-based atomic claim, offset-tracked output — is the
  strongest single architectural precedent found in this survey for the run_id/poll surface.**
- **Pause-for-input as a first-class poll phase, not a side channel:**
  `src/utils/ultraplan/ccrSession.ts`. `pollForApprovedExitPlanMode()` (line 198) polls a
  remote session on an interval with a cursor (`lastEventId`, incremental event fetch — same
  "never re-read from zero" idea as the output-offset pattern above), and derives a `phase:
  UltraplanPhase = 'running' | 'needs_input' | 'plan_ready'` (line 66) from a "quiet idle"
  heuristic: `sessionStatus === 'idle' | 'requires_action'` **and** zero new events this tick
  (`quietIdle`, line 283-290) — deliberately not just idle-status alone, because idle briefly
  flickers between tool turns and would cause false "waiting for input" flips (comment at line
  278). Phase transitions fire a callback (`onPhaseChange`) and a distinct analytics event
  (`tengu_ultraplan_awaiting_input`). A `shouldStop` callback lets the caller cancel a poll in
  flight, and failures are typed (`UltraplanPollError` with reasons `'stopped' |
  'network_or_unknown' | 'extract_marker_missing' | 'terminated'`). **This is the direct
  precedent for the planned "question channel"**: `needs_input` is a poll-visible run phase,
  not an exception or a different tool.

### 1c. Edit tool: uniqueness/match checks and post-edit validation

- `src/tools/FileEditTool/FileEditTool.ts`, `validateInput()` (line 137). Sequence: reject
  `old_string === new_string` (no-op edit, line 148); enforce **read-before-edit** — a
  `readFileState` map keyed by absolute path must have a timestamp from a prior Read call, or
  the tool refuses with "File has not been read yet. Read it first before writing to it." (this
  check lives at line ~275, same file); enforce the file hasn't changed since that read
  (mtime/hash comparison — "File has been modified since read, either by the user or by a
  linter. Read it again," line 306).
- **Fuzzy-but-safe matching:** `findActualString()` in `src/tools/FileEditTool/utils.ts` (line
  73) tries an exact substring match first; if that fails, it retries after normalizing curly
  vs. straight quotes on both the search string and the file (`normalizeQuotes`,
  `preserveQuoteStyle` re-applies the file's original quote style to `new_string` on output, so
  the edit doesn't silently flip file typography — line 104). This is the *only* fuzziness
  allowed; there is no fuzzy/whitespace-insensitive matching beyond quote normalization.
- **Uniqueness check:** after a match is found, `file.split(actualOldString).length - 1`
  (`FileEditTool.ts:329`) counts occurrences; if `matches > 1` and `replace_all` is false, the
  call is rejected with a message that names the count and instructs the caller to either pass
  `replace_all: true` or add more surrounding context to disambiguate (line 332-343). No
  silent "replace the first occurrence" fallback exists.
- **Post-edit validation via IDE diagnostics, not a build step:**
  `src/services/diagnosticTracking.ts`. `DiagnosticTrackingService.beforeFileEdited(filePath)`
  (line 135) snapshots current LSP diagnostics for a file *before* the edit via an IDE MCP RPC
  (`getDiagnostics`) as a baseline; `getNewDiagnostics()` (line 188) re-fetches after and
  diffs against the baseline, returning only diagnostics that are new (not just "any
  diagnostics present" — a file with 40 pre-existing lint warnings only surfaces the edit's own
  regressions). This is IDE-integration-dependent (silently no-ops if no IDE client is
  connected) but the *pattern* — snapshot-before, diff-after, report only the delta — is
  directly reusable for a compile/lint/test evaluator gate that shouldn't re-flag pre-existing
  failures as caused by the current iteration.

### 1d. Todo/task tracking and cross-turn state persistence

Two separate systems coexist, gated by a feature flag (`isTodoV2Enabled()`):

- **Legacy TodoWrite** (`src/tools/TodoWriteTool/TodoWriteTool.ts`) — a flat list, fully
  replaced on every call (`call({todos})` just overwrites), stored in in-memory `AppState`
  keyed by `agentId ?? sessionId` (line 65-94), **not persisted to disk** — it's turn-scoped UI
  state, not a durable job record. Notably it emits a soft nudge: if the caller just closed out
  3+ todos and none mentioned "verif", the tool result appends a reminder to spawn the
  verification agent before declaring done (lines 76-107) — a cheap structural hook.
- **TodoV2 (`Task*` tools)** — the durable version, described in 1b above: real files on disk,
  dependency edges, survives process restarts. The split matters as a design lesson: an
  ephemeral in-session checklist (what the model narrates as its plan) and a durable run
  ledger (what a poller/other process can observe) are *different data structures* in this
  codebase, not one system doing double duty.

### 1e. Hooks system: where results get injected

- `src/services/tools/toolExecution.ts`, function `checkPermissionsAndCallTool()` (line 599)
  is the single choke point. Order: zod-validate input → tool's own `validateInput` →
  `runPreToolUseHooks()` (defined in `src/services/tools/toolHooks.ts:435`) → resolve
  permission (`resolveHookPermissionDecision`, `toolHooks.ts:332` — a hook's `allow` does
  **not** bypass `settings.json` deny/ask rules, only session/interactive prompting) → `await
  tool.call(...)` → `runPostToolUseHooks()` (`toolHooks.ts:39`) → map to a `tool_result` block.
- Hooks are async generators (`executePreToolHooks`/`executePostToolHooks` in
  `src/utils/hooks.ts`, not fully read) yielding a discriminated union the caller switches on:
  `message` (progress/attachment to show inline), `blockingError` (deny + reason),
  `preventContinuation` + `stopReason` (halt the whole turn, not just this tool),
  `permissionBehavior` (`allow`/`ask`/`deny`, can carry `updatedInput`), `updatedInput` alone
  (passthrough — modify args without making a permission decision), `additionalContexts`
  (inject extra text into the transcript without touching the tool call itself). `PostToolUse`
  hooks additionally get `updatedMCPToolOutput` to rewrite an MCP tool's result before it
  reaches the model. Every hook phase is wrapped in try/catch that degrades to a
  `hook_error_during_execution` attachment rather than crashing the tool call.
- Timing/telemetry: hook duration is measured and only surfaced inline past a threshold
  (`HOOK_TIMING_DISPLAY_THRESHOLD_MS = 500`, `toolExecution.ts:134`), and a separate slower
  threshold logs a debug warning (`SLOW_PHASE_LOG_THRESHOLD_MS = 2000`, line 137) — a cheap
  "don't spam the user, but do log if hooks are the bottleneck" split.

### 1f. Subagent / verification-agent pattern (relevant to the evaluator's LLM-judge piece)

- `src/tools/AgentTool/built-in/verificationAgent.ts` defines a built-in subagent whose entire
  job is adversarial verification, not confirmation. Structurally relevant regardless of the
  prompt content: `disallowedTools` strips edit/write tools from the verifier (lines 139-145,
  it can run commands and read files but cannot touch the project) — a verifier that can't fix
  what it's grading is a real design constraint worth carrying into the evaluator/LLM-judge
  design. The verdict contract is a **literal, parseable terminal string**: `VERDICT: PASS` /
  `VERDICT: FAIL` / `VERDICT: PARTIAL` (line 117-127), each check must show a command + actual
  output (a check with no command output is explicitly "a skip, not a PASS," line 82),
  and `PARTIAL` is reserved for environment limits only, not uncertainty. `runAgent.ts`
  (`src/tools/AgentTool/runAgent.ts`) is the harness that spawns/executes such a subagent; not
  read in full, but `AgentTool.tsx`/`built-in/*` confirm this is one pattern among several
  built-in agent types (`generalPurposeAgent.ts`, `planAgent.ts`, `exploreAgent.ts`,
  `claudeCodeGuideAgent.ts`, `statuslineSetup.ts`) selected by `agentType`.

### Steal / Avoid / Not applicable — `claude-code/`

- **Steal (pattern, reimplement independently, never copy text):**
  - Async surface / run abstraction: file-per-run JSON state + atomic lockfile claim
    (`utils/tasks.ts`), `TaskStatus` enum with `isTerminalTaskStatus()`, type-prefixed random
    run IDs.
  - Worker loop: partition-by-concurrency-safety tool batching
    (`toolOrchestration.ts:partitionToolCalls`) if the worker ever runs more than one
    deterministic check concurrently.
  - Output polling: offset/cursor-based incremental reads (`diskOutput.ts:getTaskOutputDelta`,
    `ccrSession.ts` event cursor) instead of re-reading full logs each poll.
  - Question channel: `needs_input` as a first-class poll-visible phase derived from a "quiet"
    heuristic (idle **and** no new events), not a separate blocking call.
  - Evaluator gate: snapshot-before/diff-after for diagnostics (`diagnosticTracking.ts`) so a
    check only flags regressions the current iteration caused; verifier subagent pattern
    (disallowed edit tools, literal `VERDICT: PASS|FAIL|PARTIAL` terminator, "a check without
    command output is a skip") for the LLM-judge piece.
  - Edit safety: read-before-edit gate + uniqueness-count-with-ask-for-more-context (no silent
    first-match fallback) if the worker's deliverable-generation step includes file edits
    rather than only whole-file writes.
  - Auto-backgrounding on a blocking-time budget as the sync/async decision default.
- **Avoid:** treating README claims (Tamagotchi/Undercover/KAIROS narrative framing) as
  verified fact without checking the code — some claims check out, some are unverified color;
  and never reuse any source text — no license exists.
- **Not applicable:** the React/Ink terminal UI layer (`hooks/use*.ts`, `components/`), the
  full context-compaction machinery in `query.ts` (snip/microcompact/autocompact/collapse) —
  relevant to a long-lived interactive session, not to a single-deliverable bounded worker run.

---

## 2. `open-multi-agent/` — deep pass

MIT-licensed (confirmed: `/mnt/i/workspaces/clones/open-multi-agent/LICENSE`, "Copyright (c)
2025 open-multi-agent contributors"). Package README (`README.md`) states the project launched
2026-04-01. The published library is `@open-multi-agent/core`,
`/mnt/i/workspaces/clones/open-multi-agent/packages/core/`.

### 2a. Agent / loop / tool model

- `packages/core/src/agent/runner.ts` — `AgentRunner.run()` (loop body starts line 850) is the
  same shape as claude-code's: one outer `while (true)` per file header comment (line 12),
  bounded by `maxTurns` (line 857) and an optional `maxTokenBudget` (line 931). Each turn:
  optionally compress/compact prior tool results (`compressToolResults`,
  `contextStrategy` — pluggable, line 863-880), call the LLM, extract `tool_use` blocks
  (`extractToolUseBlocks`), run **loop detection** before executing tools (see below), execute
  tools, append results, loop.
- **Loop detection is a first-class, reusable component**:
  `packages/core/src/agent/loop-detector.ts`. `LoopDetector` keeps a sliding window
  (`windowSize`, default `max(loopDetectionWindow, maxRepetitions)`, line 44) of deterministic
  signatures — `computeToolSignature()` (line 102) sorts tool-call blocks by name and
  recursively sorts each input's object keys (`sortKeys`, line 19) before JSON-stringifying, so
  `{b:1,a:2}` and `{a:2,b:1}` collide as the same signature — and counts consecutive identical
  signatures at the tail (`consecutiveRepeats`, line 127). Triggers at `maxRepetitions`
  (default 3) for either repeated tool calls (`recordToolCalls`) or repeated text output
  (`recordText`). The runner wires this into `onLoopDetected: 'warn' | 'inject' | 'terminate' |
  (info) => action` (`runner.ts:844`) — first detection warns/injects a nudge into the
  conversation, a second consecutive detection force-terminates (`runner.ts:974-985`). **This
  is a directly reusable building block for the "budget ~2-3 iterations + one fresh start"
  requirement** — rather than just counting iterations, detect when the model is actually stuck
  (same tool+args repeating) and terminate/reset early instead of always burning the full
  budget.
- **Tool execution concurrency:** `packages/core/src/tool/executor.ts`, `ToolExecutor` —
  parallel execution via `Promise.all` under a configurable max-concurrency limit
  (`ToolExecutorOptions`, line 23-25), plus per-call Zod schema validation and error isolation
  (a failing tool call doesn't crash the batch). Simpler than claude-code's
  read/write-partitioned batching — no read-only/write distinction, just a flat concurrency
  cap — worth noting as the "MVP version" of the same idea.
- **Orchestrator/scheduler** (`packages/core/src/orchestrator/{orchestrator.ts,scheduler.ts}`,
  `task/queue.ts`): a `Scheduler` class with four strategies (`round-robin`, `least-busy`,
  `capability-match` — keyword overlap, `dependency-first` — BFS over a `dependsOn` graph to
  find which pending tasks unblock the most others, `scheduler.ts:51`). This is multi-agent DAG
  orchestration — a goal decomposed into parallel task nodes assigned across a pool of agents.
  **Not directly applicable** to a single bounded worker loop, but the `dependsOn` graph +
  `countBlockedDependents` critical-path heuristic is worth remembering if a later phase runs
  multiple concurrent coding-subagent workers that need ordering.

### 2b. Local-model tool-calling: prompt-based or schema coercion?

Neither purely — it's **native-first with a text-extraction fallback net**, confirmed from two
sources:

- `docs/providers.md` (`/mnt/i/workspaces/clones/open-multi-agent/docs/providers.md`),
  section "Local Model Tool-Calling": "Tool-calling is handled natively through the
  OpenAI-compatible API" — Ollama is configured as `provider: 'openai'` +
  `baseURL: 'http://localhost:11434/v1'` (same table lists vLLM, LM Studio, llama.cpp
  identically). Verified models: Gemma, Llama 3.1, Qwen 3, Mistral, Phi-4.
  Sampling knobs exposed for local/quantized servers: `topK`, `minP`, `frequencyPenalty`,
  `presencePenalty`, `parallelToolCalls`, `extraBody` (escape hatch merged into the request
  body). A concrete worked example,
  `packages/core/examples/providers/local-quantized.ts`, tunes a quantized MoE model against
  repetition/schema-hallucination failure modes: `topP=0.95, topK=40, minP=0.05,
  frequencyPenalty=0.3`, plus `extraBody: {repetition_penalty: 1.05}` (vLLM/llama-server
  specific, not OpenAI spec). Explicit caveat in the file: cloud OpenAI rejects `top_k`/`min_p`,
  so this config is not portable to `api.openai.com` — local-only.
- `packages/core/src/tool/text-tool-extractor.ts` (227 lines) is the **fallback, not the
  primary path** (file header: "This is a safety net, not the primary path. Native `tool_calls`
  from the server are always preferred," lines 14-15). Documented failure modes it exists to
  catch: Ollama's thinking-model bug where tool-call JSON lands inside an unclosed `<think>`
  tag; raw JSON tool calls the server didn't parse; markdown-fenced JSON; Hermes-format
  `<tool_call>...</tool_call>` tags. `extractToolCallsFromText()` (line 203) tries Hermes tags
  first, then strips code fences and does brace-depth-tracked JSON object extraction
  (`extractJSONObjects`, line 108 — correctly handles strings/escapes so braces inside quoted
  text don't confuse depth tracking), and **only accepts extracted calls whose `name` is in a
  caller-supplied whitelist of known tool names** (`knownToolNames`, checked at line 73) — it
  will not treat arbitrary JSON prose as a tool call.
- **Caveat for this repo's own use:** the llm repo's CLAUDE.md already states Ollama's native
  `format` JSON-schema parameter is "100% reliable, no speed penalty" for structured output —
  stronger than either of OMA's mechanisms. OMA's text-extraction fallback is a reasonable
  defense-in-depth pattern (worth having *a* fallback), but the primary mechanism for a
  qwen2.5-coder:14b-based worker should be Ollama's native structured-output/tool-calling
  support, matching this repo's existing validated practice, not the prompt-plus-regex
  approach OMA falls back to.

### 2c. Structured output (relevant to the future planner phase)

`packages/core/src/agent/structured-output.ts` — `buildStructuredOutputInstruction(schema)`
(line 21) converts a Zod schema to JSON Schema and appends an explicit "respond with ONLY valid
JSON, no fences" directive to the system prompt; `extractJSON(raw)` (line 50) tries direct
parse, then ```json fence, then bare fence, then first-`{`-to-last-`}` / first-`[`-to-last-`]`
slicing, in that order; `validateOutput(schema, data)` (line 117) does `schema.safeParse` and
formats a human-readable per-field error list on failure. This is the shape a Python
planner-brief step should follow if it needs a fallback beyond Ollama's native `format` param
(e.g., for a future non-Ollama backend) — but for this repo, prefer the native structured
output path already validated in CLAUDE.md over reimplementing this extractor.

### Steal / Avoid / Not applicable — `open-multi-agent/`

- **Steal:**
  - Loop detection as a distinct, reusable component (`loop-detector.ts`): deterministic
    signature over sorted tool name + sorted-keys input, sliding window, consecutive-repeat
    count, pluggable action (warn/inject/terminate/callback) — directly answers "when has the
    local model gotten stuck, independent of iteration count" for the evaluator/worker budget.
  - The provider-config pattern for local/quantized-model sampling
    (`local-quantized.ts`): explicit repetition-fighting knobs (`frequencyPenalty`,
    `repetition_penalty` via extra-body) and the explicit "this doesn't port to cloud OpenAI"
    caveat — good documentation discipline to replicate for qwen2.5-coder:14b's Ollama options.
  - Multi-strategy JSON extraction with whitelist-gated tool-name acceptance
    (`text-tool-extractor.ts`) as a defense-in-depth fallback, not primary mechanism.
- **Avoid:** treating OMA's text-based tool-call extraction or JSON-fence extraction as the
  primary structured-output mechanism for this repo — Ollama's native `format` param is already
  validated as superior and should stay primary; OMA's fallback is only worth having as a
  last-resort net, if at all.
- **Not applicable:** the DAG orchestrator/scheduler (`orchestrator.ts`, `scheduler.ts`,
  4-strategy task assignment) — built for coordinating *multiple* concurrent agents against a
  decomposed goal; the planned system is a single bounded worker per run. Revisit only if a
  later phase runs several coding-subagent workers concurrently and needs task-dependency
  ordering.

---

## 3. `odysseus/`

Self-hosted, general-purpose AI workspace product: chat + agents + MCP + deep research +
document editor + email (IMAP/SMTP) + notes/tasks/calendar + a model "cookbook." Author handle
in the repo is `pewdiepie-archdaemon`; default branch is `dev`. AGPL-3.0-licensed
(`/mnt/i/workspaces/clones/odysseus/LICENSE`). Docker-first deployment
(`docker-compose.yml`, GPU variants for both AMD and NVIDIA).

What's actually in the clone: `core/` is infrastructure only — `auth.py`, `session_manager.py`,
`database.py`, `middleware.py`, `atomic_io.py` — no agent-loop or tool-execution engine is
present in this tree. `companion/` is a pairing/routes module for a separate companion app.
`integrations/claude/` and `integrations/codex/` each contain a small (~218-line)
`odysseus_api.py` "skill" script that lets Claude Code / Codex CLI call *into* Odysseus's own
API — i.e., these are Odysseus-side glue for being driven by an external coding agent, not an
agent-execution engine of Odysseus's own that's visible in this clone. The actual chat/agent
orchestration logic (if present at all beyond these infra pieces) was not found in the cloned
tree within a reasonable search budget — either it lives in a part of the app not represented
here, or the product is thinner on the agent-loop side than its README markets it as.

**Verdict: irrelevant to this survey's purpose.** Nothing in the accessible tree bears on the
async submit/poll surface, worker loop, evaluator gate, or any other piece of the planned
design. Not worth a deeper pass unless a future task specifically needs email/calendar/document
patterns.

---

## 4. `career-ops/`

Node.js + Playwright job-search automation pipeline, authored to run *as* Claude Code slash
commands ("modes": `apply.md`, `scan.md`, `pipeline.md`, `batch.md`, etc., under
`/mnt/i/workspaces/clones/career-ops/modes/`) plus a `batch-runner.sh` for parallel offer
evaluation via subagents. MIT-licensed. Confirmed via `package.json` and `modes/` listing —
domain-specific (CV generation, job-board scraping, offer scoring), not an agent-framework or
MCP-server codebase. No architecture here maps onto async job orchestration, worker loops, or
evaluator gates in a way distinct from "Claude Code already does this, and this repo just
writes prompts for it."

**Verdict: irrelevant**, confirmed by directory skim (no MCP server code, no agent-loop
implementation — it's all markdown prompts + Playwright scripts).

---

## 5. `ollama-metrics/`

Go Prometheus sidecar (`go.mod`: `github.com/NorskHelsenett/ollama-metrics`) that
transparently proxies requests to Ollama while exposing `/metrics` for token counts, request
duration, inference speed, and memory usage. Single-purpose observability tool, ~zero
architectural overlap with agent loops, run abstractions, or evaluators.

**Verdict: irrelevant** to the current design questions. Tangential note for later: if the
future worker loop wants Prometheus-style observability on its Ollama calls (iteration count,
tokens/sec, verdict distribution), this is a working reference for a minimal Go metrics sidecar
pattern — but that's a distinct concern from anything in the current task's scope.

---

## Cross-repo notes that bear on the planned design

- **Nothing found here contradicts the planned design's core assumptions** (a bounded
  worker loop, deterministic evaluator gate, MCP submit/poll surface). If anything, the
  claude-code `Task*` subsystem and OMA's `LoopDetector` independently converge on the same two
  ideas the design already assumes: (1) durable, file-backed run state with atomic claiming
  beats in-memory state the moment more than one process needs to observe a run, and (2)
  bounding by "detected repetition" is a better trigger for "fresh start" than a bare iteration
  counter — worth considering as a refinement to the "budget ~2-3 iterations + one fresh start"
  rule: trigger the fresh start early if the local model's tool-call/edit signature repeats,
  not only after the iteration count is exhausted.
- Both codebases independently landed on offset/cursor-based incremental reads for
  polling long-running output (claude-code's `outputOffset` + `getTaskOutputDelta`; its own
  `ccrSession.ts` event cursor) — a pattern worth adopting verbatim in the Python worker's
  polling design regardless of which other pieces get reused.
