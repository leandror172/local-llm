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
