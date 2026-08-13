# Declared-and-unconsumed run-spec fields (T-133) — 2026-07-31, session 135

*Two fields of oficina's run spec are declared on the pydantic models and read by nothing.
Found s134 (`context.callers`), extended s135 (`acceptance.validators`) while re-grounding the
P3 plan against the inception docs. Evidence and mechanism live here; `.claude/tasks.md` T-133
carries the pointer, and the register entry is **P3-D6**.*

<!-- ref:declared-unconsumed-spec-fields -->
## The two fields

| Field | Declared | Consumers |
|---|---|---|
| `context.callers` | `intake.py:44` — `callers: List[str] = Field(default_factory=list)` | **none** |
| `acceptance.validators` | `intake.py:58` — `validators: List[str] = Field(default_factory=list)` | **none** |

Verified by grep over all of `mcp-server/src` and `mcp-server/tests`: each symbol appears
**exactly once** — its declaration. Every other hit is the English word in a docstring
(`client.py:10`, `server.py:127`, `server.py:248`, `parser.py:268`, `transport.py:10`,
`workspace.py:23`, `test_parser.py:358`). No test names either field. `_check_context_files`
validates only `context.files`.

## The mechanism: declaring the field is what creates the silence

Both `Context` and `Acceptance` set `extra="forbid"`, and the allowed-key sets are derived from
`model_fields` (P1-D3, so schema and check cannot drift). An **undeclared** key is therefore
**rejected at intake**. These two are accepted *precisely because, and only because, they are
declared* — the schema converts what would have been a loud rejection into a silent swallow.

That is the inverse of **first principle 4** (*"most 'the model should ask' cases are really
'the harness should refuse'"*): here the harness declines to refuse and says nothing instead.

**Knowledge-divergence sibling of `ref:corpus-divergence-pattern`, by a different mechanism.**
Unlike T-125/T-126's checkers — which report a true answer about a too-narrow set — nothing here
reports anything at all. A caller reading the schema concludes the rule is enforced; silence is
read as compliance. No audit could have surfaced it.

## Why `callers` matters more than a dead field

`ref:delegate-conventions-mapping` — described in `integration.md` as *"the design's core
justification"* — routes this exact rule to P3:

| Convention (manual today) | Becomes |
|---|---|
| **Callers included in context (0-verdict prevention)** | **Intake/fetcher rule (P3)** |

It is the one row whose effect was **measured**. `ref:delegate-evidence-verdicts`:

> *"Context quality already fixed a defect class: the March re-declaration cluster (models
> re-declaring types instead of importing) disappeared after the conventions started requiring
> protocol files + callers in context."*

A context-assembly change killed a whole defect class — and the field that would carry it into
the mechanized harness is inert.

## The two want opposite remedies, and the reason is written nowhere else

- **`callers` gets WIRED** — a compiler-resolved segment (P3-D6 option (i)). It has measured
  evidence behind it and no derivable substitute: nothing in the harness can discover a target's
  callers today.
- **`acceptance.validators` gets DELETED** — `evaluator.evaluate()` selects stages via
  `language_pack(spec)` → `resolve_language` (T-92 Phase 4, `LanguagePack`), so validator
  selection is **derived from the language**. A spec field for a derivable fact is what **E-D2**
  refuses (*"Mode discriminator: the target exists at HEAD… No new spec fields"*).

Record the asymmetry wherever the disposition lands. Without it, the next reader sees one dead
field wired and one deleted with no rule distinguishing them.

## Two instances make the trigger countable

The T-119 house rule: *"a detector fired by one incident is deferred, not built — and its
trigger must be countable."* One instance justified a fix; **two justify a standing check.**

**The check must be behavioural, not reference-based.** A grep/reference check is the cheap
version of `ref:corpus-divergence-pattern` — it validates *mention*, not *consumption* — and this
investigation is its own counter-example: every false hit was the English word in a docstring, so
a single `# callers are resolved later` comment would keep such a check green forever.

The discriminating shape: **submit a spec carrying `context.callers`, assert the caller content
reaches the assembled prompt.** That fails today. A meta-check over
`Context.model_fields` / `Acceptance.model_fields` is legitimate only if it asserts each field is
*read*, which means a consumer test per field — not a symbol scan.

**Its test must fail today**, or it encodes the bug (`feedback_review_rederive_invariants`).

## Open: a routing conflict between two phases

`docs/vision/coding-delegate/.memories/QUICK.md` § Next already routes *"dead
`acceptance.validators` removal"* to **Axis B** (the kind-widening pass), while `callers` sits in
**P3-D6**. Two members of one class, split across two phases.

Note the asymmetry in justification strength: the kind taxonomy has an explicit written trigger
(**E-D8** — *"trigger: the Axis-B kind-widening pass, which must touch the taxonomy anyway"*),
whereas `validators` is routed to Axis B only by a QUICK.md "Next" line — and
`acceptance.validators` **is not a kind at all**. The mechanism argument places it beside
`callers` in P3-D6.

## Scope note on `callers` as an intake *requirement*

P3-D6 option (ii) — refuse a spec that names no callers for a target with importers — is
first principle 4's *harness-should-refuse* applied directly, but it needs a caller-discovery
mechanism the harness does not have. **T-77** (signature/doc extractor) is the natural supplier,
and `ref:delegate-estate-map` says explicitly *"this system is its second consumer … **do not
block on it**."* Record (ii) as deferred with T-77 as its named trigger.
<!-- /ref:declared-unconsumed-spec-fields -->
