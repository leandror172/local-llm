## Local Model Usage

When working in this project, **try local models first** for code generation tasks
via the ollama-bridge MCP server. This generates training data for future distillation.

**Use `mcp__ollama-bridge__generate_code` or `mcp__ollama-bridge__ask_ollama` for:**
- Boilerplate code (structs, interfaces, simple functions, test stubs)
- Simple utilities and scripts
- Straightforward transformations (parsing, formatting, serialization)

**Do NOT use local models for:**
- Architectural decisions or multi-file reasoning
- Security-sensitive code
- Tasks requiring understanding of large context (>400 tokens of output needed)

### Verdict Protocol

**Evaluate every local model response explicitly:**
- `ACCEPTED` — used as-is (note the prompt that worked)
- `IMPROVED` — used with modifications (note what changed and why)
- `REJECTED` — not usable (note the failure reason: logic error / wrong API / off-task)

**On ACCEPTED or IMPROVED verdicts, add a rough token estimate:**
- Mentally apply `(chars in your prompt + chars in response) / 4` as a ballpark
- Note it inline: `ACCEPTED — ~300 est. Claude tokens saved`

### Handling Imperfect Output

When output is imperfect, classify by **defect type x fix scope x prompt cost** — not
line count.

| Dimension | Inline signal | Escalate signal |
|---|---|---|
| **Defect type** | Mechanical (slip, typo) | Structural or conceptual |
| **Fix scope** | 1-2 isolated sites | 3+ or interdependent |
| **Prompt cost** | Explaining > fixing | Explaining < fixing |

**Decision tree:**
- **Mechanical defect** (syntax, typo, wrong import) -> IMPROVED, fix inline always
- **Structural, 1-2 sites** -> inline (IMPROVED if trivial, REJECTED if effort > describing)
- **Structural, 3+ sites, interface definable** -> REJECTED + stubs-then-Ollama retry
- **Structural, 3+ sites, not definable** -> REJECTED, write from scratch
- **Conceptual** (correct syntax, wrong behavior) -> REJECTED, write from scratch
- **Prompt cost tiebreaker:** if explaining > fixing -> inline regardless of scope

**Stubs-then-Ollama pattern:** Write stub signatures, call Ollama with stubs in
`context_files`. First call = REJECTED triple; second call gets its own verdict.

### Cold Start Grace Period

A timeout on the **first call to a model in a session** is an infrastructure artifact,
not a quality verdict. Label it `TIMEOUT_COLD_START`, do not record a DPO triple,
and retry immediately. Use the `warm_model` MCP tool at session start to eliminate
cold starts.

### Training Data

Every call is automatically logged to `~/.local/share/ollama-bridge/calls.jsonl`.
The (prompt, local_response, verdict) pattern is the raw material for future DPO
fine-tuning.
