# Code Design Conventions

Reusable structural patterns for Python code in this project.
These are distinct from technology choices (`technology-conventions.md`) —
they govern how code is shaped, not which tools are used.

Query `ref:patterns-code-design-index` for a summary; drill into any
`ref:patterns-code-*` key for details.

---

<!-- ref:patterns-code-design-index -->
## Patterns Index

| Key | Pattern | One-liner | Revisit? |
|-----|---------|-----------|----------|
| `patterns-code-named-methods` | Named semantic methods | Public API names intent; private methods own generic dispatch | Role set becomes dynamic/config-driven at runtime |
| `patterns-code-value-or-error` | Value-or-error over sentinel | Internal helpers return `(value, error)` or raise; sentinel `Error:` strings only at the human/LLM boundary | Value space provably excludes the sentinel |
| `patterns-code-extract-keep-divergence` | Extract mechanism, keep divergence explicit | Drifted duplicate mechanisms → one helper + explicit per-caller seams (default + optional callback) | A single caller, or copies that are byte-identical (plain extraction) |
| `patterns-code-return-not-mutate` | Return, don't mutate | Return your contribution; pass cross-step deps as explicit params, not shared mutable state | One genuine owner + a measured hot path where merging copies costs |
| `patterns-code-paired-span-bookkeeping` | Paired-span bookkeeping via one closure | Emit enter/exit (log/metric/trace) from one closure or context manager, not inlined per return | Exactly one exit path exists |
<!-- /ref:patterns-code-design-index -->

---

<!-- ref:patterns-code-named-methods -->
## Named Semantic Methods (Code as Documentation)

**Decision:** Public API methods are named after their semantic intent. Generic parameterized dispatch is private.

**Why:**

Calling `client.call(prompt, role="extraction_prose")` is stringly typed —
the legal values for `role` live nowhere in the type system, IDE autocomplete,
or call site. A reader must find the config or enum to know what's valid.

Calling `client.extractProse(prompt)` is self-documenting: the call site
tells the full story. The method name *is* the documentation. This applies
equally to Python, Go, Java, and TypeScript — it is a structural principle,
not a language feature.

**Structure:**

```python
class ModelClient:
    # Public: named by intent
    def extract_prose(self, prompt: str) -> ChatResult:
        return self._chat(prompt, role="extraction_prose", schema=TOPIC_SCHEMA)

    def extract_code(self, prompt: str) -> ChatResult:
        return self._chat(prompt, role="extraction_code", schema=TOPIC_SCHEMA)

    # Private: owns protocol details, generic dispatch
    def _chat(self, prompt: str, role: str, schema=None) -> ChatResult: ...
```

```go
// Public: named by intent
func (c *Client) ExtractProse(prompt string) (ChatResult, error) {
    return c.chat(prompt, "extraction_prose", topicSchema)
}

// Private: owns protocol details
func (c *Client) chat(prompt, role string, schema any) (ChatResult, error) { ... }
```

**Rules:**

1. Named methods are **thin wrappers** — they bind the role and any fixed params. No logic belongs here.
2. The private method owns all protocol details, quirks, and error handling.
3. Fixed params (schemas, flags, timeouts) belong to the **named method**, not the caller.
4. Named methods are the unit of discovery — when a new operation is needed, add a named method.

**When this does NOT apply:**

- Roles are **dynamic at runtime** (user-selectable, loaded from a registry, unknown at compile time).
  In that case a parameterized call is the only viable option.
- The set of roles is so large or volatile that maintaining named wrappers becomes noise.

<!-- /ref:patterns-code-named-methods -->

---

<!-- ref:patterns-code-value-or-error -->
## Value-or-Error over a Sentinel String

**Decision:** A helper that can fail returns its result and its failure on **separate channels** — a `(value, error)` tuple or a raised exception — never a sentinel `"Error: …"` string in the value channel. Sentinel-string returns are a *boundary* convention (a human or an LLM reads them as prose), justified only where the value space provably cannot collide with the sentinel.

**Why:**

This project's MCP tools deliberately return `Error:` strings instead of raising, so Claude reads them conversationally (mcp-server `KNOWLEDGE.md`, "Error Handling as Return Values"). That is correct *at the tool boundary*. Reusing the same idiom *inside* a module overloads the success channel.

Concretely: `_assemble_prompt(base, …)` wraps a caller-supplied `base` prompt. A base like `"Error: handle this exception in Go"` is a legitimate prompt. Had the helper returned a plain string and the caller distinguished failure with `.startswith("Error:")`, that prompt would be misclassified as a failure — a bug the pre-extraction *inline* code never had, because it only ever prefix-tested the *blocks* it built, never the base. The tuple keeps success and failure on different channels, so the value is never inspected to decide which happened.

**Structure:**

```python
async def _assemble_prompt(base, context_files, refs, refs_root) -> tuple[str, str | None]:
    """Returns (assembled_prompt, None) on success, or (base, error) on failure."""
    full = base
    if context_files:
        block = _build_context_block(context_files)
        if block.startswith("Error:"):
            return base, block          # error on the second channel
        full = f"{block}\n\n{full}"
    ...
    return full, None                    # value on the first channel

# caller — distinguishes on the channel, never by inspecting the value
full_prompt, err = await _assemble_prompt(prompt, context_files, refs, refs_root)
if err is not None:
    return err
```

**Rules:**

1. Separate channels: `(value, error=None)` or `raise`. The caller decides success/failure from the **channel**, never by pattern-matching the value.
2. Sentinel strings only at the outermost boundary, and only when the value space excludes the sentinel *by construction* (an Ollama response never starts with your sentinel; a caller-supplied prompt can).
3. When extracting inline code into a helper, check whether the inline version ever prefix-tested the value it is now returning. If it did **not**, a sentinel return introduces a *new* false-positive — this is a silent regression a refactor can smuggle in.

**When this does NOT apply:**

- The outermost tool/API boundary where the consumer reads the string as prose **and** the value space cannot collide with the sentinel. There, an `Error:` string is the more ergonomic contract.

<!-- /ref:patterns-code-value-or-error -->

---

<!-- ref:patterns-code-extract-keep-divergence -->
## Extract the Mechanism, Keep the Divergence Explicit

**Decision:** When several copies of a mechanism have **drifted** at their edges, extract the shared mechanism once and expose each caller's divergence as an explicit **seam** — a default for the common case plus an optional callback/parameter for the outliers. Copy-paste *hides* drift; a seam *names* it.

**Why:**

Five subprocess-runner copies (`_resolve_ref_key`, `detect_persona`, `build_persona`, `create_persona`, `ref_lookup`) had silently diverged on error reporting — some preferred `stderr`, one preferred `stdout`, one hardcoded its message and ignored both. That inconsistent behavior reached users precisely *because* it lived in five copies nobody diffed against each other. Unifying them under one helper makes the drift visible at the call site:

```python
async def _run_script(args, *, timeout, label, on_error=None, on_success=None) -> str:
    """create_subprocess_exec → wait_for → returncode → decode, once.
    Default non-zero message is 'Error: {label} exited with code N: …';
    on_error overrides it for callers whose wording differs."""
```

The three persona tools that share the default template collapse to **one line each**; the two ref tools declare their divergent wording via `on_error`. The historical drift is now a visible parameter, not buried duplication.

**Rules:**

1. **Drift is both the trigger and the map.** That copies disagree is the signal to extract; *where* they disagree tells you where the seam goes.
2. Default the common case inside the helper. A caller passes a seam only to **opt out**.
3. Each optional seam must map to a **real, test-pinned difference** — not speculative generality. If only one caller would ever pass it and there is no drift risk, inline instead of adding the parameter.
4. **Characterize the drifted behavior with tests before unifying** (see `ref:patterns-refactoring-characterize-first`), so "preserve each caller's message" is a verifiable claim, not a hope.

**When this does NOT apply:**

- The copies are byte-identical — plain extraction, no seam needed.
- There is a single caller — extract for naming if you like, but no divergence exists to model.

**Related:** divergence is a defect marker in the same family as a special-case comment — both are the residue of an accident, surfaced rather than justified.

<!-- /ref:patterns-code-extract-keep-divergence -->

---

<!-- ref:patterns-code-return-not-mutate -->
## Return, Don't Mutate (Compose over Accumulate)

**Decision:** Prefer functions that **return** their contribution over functions that **mutate a passed-in accumulator**. Express cross-step data dependencies as explicit parameters (`skip=`, `seen=`), not as shared mutable state threaded through signatures.

**Why:**

`retention.sweep()` ran two prune policies that shared a mutated `pruned` set and appended into a `records` list passed by reference. The natural "extract a function" move produced a six-argument function that mutated two of its arguments — and the effect was invisible at the call site (`records` grew, but nothing in the call said so). Rewritten so each policy *returns* its records:

```python
def _prune_over_keep_limit(store, config, dry_run) -> tuple[set, list[Record]]: ...
def _prune_past_ttl(store, config, now, skip, dry_run) -> list[Record]: ...

# orchestrator — the cross-policy dependency is one readable keyword
pruned, records = _prune_over_keep_limit(store, config, dry_run)
records += _prune_past_ttl(store, config, now, skip=pruned, dry_run=dry_run)
```

Each policy is now independently testable and reusable, and the dependency (TTL must skip what keep-limit already pruned) is an explicit `skip=pruned` rather than a mutation ordering the reader has to reconstruct.

**Rules:**

1. A function's output is its **return value**, not a mutated argument. The call site should show what changed.
2. Cross-step dependencies become **explicit parameters** (`skip=`, `seen=`), never an implicitly shared mutable that two functions both reach into.
3. Compose at the orchestrator: `records = a(); records += b(skip=…)`. Preserve ordering deliberately if downstream depends on it.

**When this does NOT apply:**

- A single genuine owner of a large accumulator on a **measured** hot path, where returning and merging copies costs real time/memory. Then mutate — and document that the mutation is deliberate.

<!-- /ref:patterns-code-return-not-mutate -->

---

<!-- ref:patterns-code-paired-span-bookkeeping -->
## Paired-Span Bookkeeping via One Closure

**Decision:** Emit paired enter/exit bookkeeping — logging, metrics, tracing spans — from **one closure or context manager**, not inlined at every return site.

**Why:**

`generate_code` inlined its full `tool_exit` debug call five times; `ask_ollama` and `patch_file` already factored the same thing into a `_done(ok, **fields)` closure. The inlined form is not just verbose — it is a correctness hazard: one branch (the prompt-assembly error path) returned *without* a `tool_exit`, emitting a `tool_enter` with no matching exit. That orphaned span is invisible until you diff the trace, and the debug-log playbook (mcp-server `KNOWLEDGE.md`) relies on `tool_enter`-without-`tool_exit` meaning "server-side wedge" — an orphan poisons that signal. Making "log the exit" one cheap line means every branch actually does it.

```python
def _done(ok: bool, **fields):
    debug_log.debug("tool_exit", tool="generate_code", ok=ok,
                    ms=round((time.perf_counter() - t0) * 1000, 2), **fields)

# every return path is now one line — easy enough that none is forgotten
if prompt_err is not None:
    _done(False, reason="prompt_assembly_error")
    return prompt_err
```

**Rules:**

1. One definition of the exit record; call sites pass only what varies (`ok`, a `reason`, a `model`).
2. Prefer a **context manager** when the exit must fire on *every* path including exceptions (`finally`-guaranteed); a **closure** suffices when you call it explicitly at each return.
3. Cross-cutting concerns of the record (reserved-field filtering, timing, the `tool=` label) belong in the helper, set once — not repeated per call.

**When this does NOT apply:**

- A function with exactly one return/exit — there is no pairing to protect, and a closure is ceremony.

<!-- /ref:patterns-code-paired-span-bookkeeping -->
