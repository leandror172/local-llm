# Ollama KV Prefix Cache — Research Findings (2026-06)

<!-- ref:ollama-kv-prefix-cache -->
## How Prefix KV Reuse Works in Ollama

Ollama uses llama.cpp internally. llama.cpp maintains an `InputCache` (KV cache) per loaded
model slot. When a new request arrives, it scans the existing slot for the longest matching
prefix and skips recomputing KV tensors for those tokens. The result:

- **System prompt** (baked into the Modelfile): always in the prefix — reused on every call
  to the same persona as long as the model is loaded.
- **context_files / refs blocks**: prepended at the start of the user message by the server
  (see `ref:mcp-server-side-context`). If content is identical across calls, they form a
  stable prefix and are reused.
- **User prompt tail**: always recomputed (it's the only part that varies).

**Condition for reuse:** the model must stay loaded in VRAM. Controlled by `keep_alive`.

### keep_alive default (added 2026-06, client.py)

`chat()` now passes `keep_alive: str = "15m"` in the payload. Rationale: Ollama's built-in
default is 5 minutes. 15 minutes covers retry windows (a timeout + immediate retry) and
multi-call sessions where the same context files are passed repeatedly.

Any tool that calls `chat()` inherits this. Callers can override per-call if needed:
```python
await client.chat(prompt=..., model=..., keep_alive="30m")
```

### num_keep — when relevant, when not

`num_keep` (in `options`) pins the first N tokens in the KV cache, preventing eviction when
the context window fills during a long generation (sliding-window eviction drops the oldest
KV entries). **Does not affect response time** — that's prefix reuse (a different mechanism).

For typical `generate_code` workloads on 14B models (32K ctx):
- Prompt + context files + output rarely exceeds ~5K tokens — well under 32K.
- Sliding-window eviction does not occur. `num_keep` is irrelevant.

Where `num_keep` would matter: LTG Phase 3+ batch extraction over large corpus files where
total context (system + docs + output) approaches 32K. If that becomes a problem, add:
```python
num_keep = 512 + len(context_block or "") // 3   # 512 = system prompt budget
payload["options"]["num_keep"] = num_keep
```
<!-- /ref:ollama-kv-prefix-cache -->

---

<!-- ref:ollama-explicit-cache-api -->
## What Ollama Does NOT Expose (June 2026)

Research conducted June 2026 against Ollama GitHub, llama.cpp GitHub, and Ollama DeepWiki.

**No explicit slot or session API in Ollama:**
- No `id_slot` field in `/api/chat` or `/api/generate`
- No `cache_prompt` field
- No slot save/restore endpoint
- GitHub issue #8494 (Jan 2025) requested session ID support — closed without implementation
- No roadmap item for exposing slot-level controls

**The `/api/generate` `context` array** (which returns token IDs for conversation replay)
is **deprecated** (issue #10576: "will be removed in a future version") and does not bypass
recomputation — it is conversation history serialization, not KV cache resumption.
`/api/chat` never had an equivalent.

### What llama-server (llama.cpp direct) has — but Ollama doesn't expose

| Feature | llama-server | Ollama |
|---|---|---|
| Implicit prefix KV reuse | ✅ automatic | ✅ automatic |
| `cache_prompt` request field | ✅ | ❌ |
| `id_slot` request field | ✅ | ❌ |
| Slot save/restore to disk | ✅ `--slot-save-path` | ❌ |

The slot save/restore is particularly powerful: a June 2025 llama.cpp discussion (#20572)
documents pre/post hooks that save slot state after each response and restore before the
next, reducing prefill from minutes to ~0.2s on 100K-token contexts. Inaccessible through
Ollama's API layer.

**Practical implication for this repo:** implicit prefix reuse via `keep_alive` is the
complete and correct solution within Ollama's API surface. For explicit control over cache
pinning or cross-session persistence, running `llama-server` directly is required — but
that trades away model management, the persona registry, and `warm_model`.
<!-- /ref:ollama-explicit-cache-api -->

---

## Sources

- [KV Cache System — Ollama DeepWiki](https://deepwiki.com/ollama/ollama/5.3-kv-cache-system)
- [Tutorial: KV cache reuse with llama-server (Discussion #13606)](https://github.com/ggml-org/llama.cpp/discussions/13606)
- [Tutorial: Persistent KV cache per session with llama-server hooks (Discussion #20572)](https://github.com/ggml-org/llama.cpp/discussions/20572)
- [Ollama API docs](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [context field deprecated — Issue #10576](https://github.com/ollama/ollama/issues/10576)
- [Session parameters in /api/chat — Issue #8494](https://github.com/ollama/ollama/issues/8494)
