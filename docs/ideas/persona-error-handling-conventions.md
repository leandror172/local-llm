# Per-Language Error Handling & Logging Conventions for Coding Personas

*Originated: 2026-05-26, session 67. Prompted by observing consistent antipatterns
across 5 consecutive `generate_code` calls during `patch_file` acceptance testing.*

---

## What triggered this

During acceptance testing of the `patch_file` MCP tool, five consecutive
`generate_code` calls to `qwen2.5-coder:14b` produced the same two unrequested
patterns regardless of the prompt:

1. `logging.basicConfig(level=logging.INFO, ...)` at module level
2. `try/except Exception as e: log(...); raise` wrapping logic that cannot fail

Neither was asked for. Both had to be patched out. The pattern was consistent
enough to be a training artifact, not random variation — the model has learned
"professional Python = logging + try/except" as a surface feature without
understanding when each is appropriate.

---

## The two distinct problems

### Problem 1: `logging.basicConfig()` as a module-level side effect

`logging.basicConfig()` configures the **root logger** for the entire Python
process — every library loaded by the application. Calling it inside a library
module is an ownership violation: the library is reaching outside its own scope
to configure something that belongs to the application entry point.

The correct library pattern is:

```python
# Library code — correct
logger = logging.getLogger(__name__)

# Application entry point — correct
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, ...)
```

The `__name__`-scoped logger is silent by default. The application decides
whether and how to wire it up. This is the established Python community
convention (see PEP 282, Python logging HOWTO).

The local model conflates the two because most of its training data is scripts
and tutorials — standalone programs where `basicConfig()` at the top is fine.
It hasn't learned the library/application distinction.

### Problem 2: Catch-log-reraise the same exception type

```python
# Noise — adds nothing
try:
    return int(years_str)
except ValueError as e:
    logger.warning("Invalid value: %s", e)
    raise ValueError(f"same message") from e
```

This pattern:
- Does not change the exception type (caller sees the same `ValueError`)
- Does not recover (re-raises unconditionally)
- Produces a log line the caller's exception handler will also produce
- Results in duplicate log entries up the stack

The only time catch-reraise adds value is when it **transforms** the exception
into a domain-specific type or **adds callsite context** that the original
exception lacks:

```python
# Adds value — transforms to domain error with context
try:
    return int(years_str)
except ValueError:
    raise ValueError(f"Invalid numeric component {years_str!r} in duration {s!r}")
```

The user's "programming by proxy" concern is valid here: if we have to specify
*which* exceptions to handle and *how*, we have not delegated the task — we have
just outsourced the typing. The model should decide what error handling is
semantically necessary. The directive is about eliminating noise, not
eliminating judgment.

---

## Language-specific rules

The surface symptoms differ by language even though the underlying principle
is the same: **only handle errors where you can add semantic value**.

### Python

| Pattern | Rule |
|---|---|
| `logging.basicConfig()` in library module | Forbidden. Use `logging.getLogger(__name__)` only. |
| `try/except E as e: log(e); raise E(same)` | Forbidden. Re-raises with no transformation = noise. |
| `try/except E: raise DomainError(context)` | Correct. Type transformation adds value. |
| `try/except E: return default` | Correct. Recovery adds value. |
| `logging.basicConfig()` in `__main__` block | Fine. Entry point owns root logger config. |

### Java

Java has no equivalent of `basicConfig()` — logging frameworks (SLF4J + Logback,
Log4j 2) are configured externally via XML/properties files, never in code. The
standard pattern `LoggerFactory.getLogger(MyClass.class)` is already correct and
class-scoped; the model should do this by default.

The antipattern to watch for:

```java
// Noise — identical to Python catch-log-rethrow
catch (Exception e) {
    log.error("Error: {}", e.getMessage());
    throw e;  // or throw new SameException(e.getMessage(), e)
}
```

Java's checked exceptions create additional pressure to add these blocks
(compiler requires handling), which makes the antipattern more prevalent in
generated code. The correct response to a checked exception you cannot handle
is to declare it (`throws`) or wrap it in an appropriate unchecked exception,
not to log-and-rethrow.

### Go

Go has no exceptions — errors are explicit return values. The equivalent
antipatterns:

```go
// Noise — logs and returns unchanged; caller also logs
if err != nil {
    log.Printf("error in parseISO: %v", err)
    return err
}

// Correct — wraps with callsite context, no logging
if err != nil {
    return fmt.Errorf("parse duration %q: %w", err)
}
```

The `%w` verb is essential: it wraps the error while preserving unwrappability
(`errors.Is`, `errors.As`). Logging mid-library is the antipattern because in
Go, errors typically travel up the call stack and get logged once at the
boundary (handler, main, top-level goroutine). Logging at each intermediate
site produces the same duplicate-line problem as Python's catch-log-reraise.

Go's standard library itself models this: functions return `error` with
contextual wrapping, never log internally.

---

## Proposed persona directive language

These are candidate additions to the system prompt / Modelfile `SYSTEM` block
for each coding persona. They follow the existing SOLID + scope constraint
pattern already added in sessions 63/65.

**Python (`my-python-q25c14`, `my-codegen-q3` for Python targets):**

```
ERROR HANDLING (Python):
- In library/module code, use logging.getLogger(__name__) only.
  Never call logging.basicConfig() — that belongs to the application entry point.
- Only add try/except where you can recover, return a default, or transform the
  exception into a more specific type with useful context.
- Do not catch-and-reraise the same exception type just to log it — this adds
  noise without changing behavior. Let exceptions propagate naturally.
```

**Java (`my-java-*` personas, when created):**

```
ERROR HANDLING (Java):
- Logger field: private static final Logger log = LoggerFactory.getLogger(MyClass.class).
  Never configure logging programmatically — that is the application's concern.
- Only catch exceptions you can handle (recover, transform to domain type, or
  convert checked to unchecked). Do not catch-log-rethrow the same type.
- Prefer declaring checked exceptions (throws) over wrapping them in a
  try/catch that just re-throws.
```

**Go (`my-go-q25c14`):**

```
ERROR HANDLING (Go):
- Wrap errors with context using fmt.Errorf("operation %q: %w", arg, err).
  Do not log errors mid-library — log once at the boundary that owns the request.
- Never add log.Printf before returning an error. The caller decides whether to
  log. Duplicate log lines are worse than no logs.
- Use errors.Is / errors.As for type-specific handling; preserve the chain with %w.
```

---

## Implementation plan

1. **Audit session** — grep all Modelfiles for the existing SOLID block pattern;
   identify which personas are Python/Java/Go and which are language-agnostic.
   Reference: `docs/tasks/backfill-persona-constraints.md` (same pass).

2. **Draft directives** — use `my-mcp-q25c14` or `my-python-q25c14` to generate
   candidate Modelfile patches (practicing what we preach: use local model for
   boilerplate Modelfile edits).

3. **Evaluate with a test prompt** — after patching, run the same "write a Python
   function that parses ISO-8601 duration" prompt and score the output. Expect
   `getLogger(__name__)` usage, no `basicConfig()`, no catch-log-reraise.
   Record verdict per the standard scale.

4. **Pair with backfill session** — this is the same class of work as the SOLID
   constraint backfill. Do both in one session to avoid two separate Modelfile
   rebuild passes.

---

## The deeper question: when is generated error handling trustworthy?

The user's "programming by proxy" framing points at a real limit of local model
delegation. The model can be told *not* to add noise, but the inverse — trusting
it to add *correct* error handling — requires more care.

Current position: the model is reliable for structural correctness (right
return types, right control flow) and unreliable for semantic correctness of
error boundaries (what to catch, what to transform, what to let propagate).
Until that changes, the right division of labor is:

- **Local model:** generates the happy-path logic; adds error handling only where
  the error contract is obvious from the signature (`ValueError` for parse
  functions, `KeyError` for dict lookups with no default).
- **Claude (or human):** reviews and patches edge cases, boundary conditions, and
  exception policy that requires understanding of the caller's context.

This is consistent with the existing `0/1/2` verdict model: a `1` often means
"correct structure, needs error handling review."
