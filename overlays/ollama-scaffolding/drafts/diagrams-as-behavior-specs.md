# DRAFT — "Diagrams as behavior specs" section for local-model-conventions.md

**For T-93** (revise local-model conventions — mermaid diagrams as coding
context). Authored in the LTG repo (session 18, 2026-07-15) with measured
evidence; parked here so T-93 can merge it into the overlay source
(`overlays/ollama-scaffolding/files/local-model-conventions.md`) alongside the
oficina P3 `context.refs` mechanism when it fires. The LTG repo's installed
copy (`.claude/overlays/local-model-conventions.md`) already carries this
section as an intentional local divergence — overlay `--verify` will show
DIFF there until T-93 lands it upstream; a re-install would clobber it
(backup is taken), so complete T-93 before any reinstall into LTG.

**Placement:** immediately after "How to prompt: describe behavior, not
implementation" — a diagram is that section's thesis in graphical form.

**Evidence base (LTG session 18):** zero-model index probe of the already-indexed
`docs/diagrams/ltg-phase4-dataflow.md` — qwen3:14b extracted correct semantic
sub-topics from *inside* the mermaid block (spans matching individual
subgraphs, descriptions inheriting node-label specifics like τ=0.70/K=10 and
model names), including one topic whose spans cross between the diagram and a
prose table. Those diagram-derived topics are among the file's best-connected
graph nodes (deg 14–18, precise cross-file edges to the master plan).
Complements T-93's own session-119 evidence (oficina P2 plan anchoring).

First registered consumer: LTG engine-integration TDD layer 2
(`ltg:docs/plans/ltg-t39-engine-integration.md`) — the loop state machine
(`ref:ltg-t39int-loop`) goes into the `generate_code` prompt, verdict recorded
with "+diagram".

---

## Section text (merge verbatim)

### Diagrams as behavior specs: mermaid is model-readable

A mermaid state machine or flowchart is behavioral intent in compact form —
control flow, stop conditions, and edge cases without writing the code out.
Local models parse them semantically, not as opaque text (measured: qwen3:14b
extracted correct sub-topics from *inside* a mermaid block, with spans crossing
between the diagram and prose — LTG session 18, `docs/diagrams/` precedent).

- When the plan doc for the code being generated carries a mermaid diagram of
  the logic, include it in the prompt or `context_files` — often the cheapest
  high-signal behavior description available.
- Record the verdict as usual; note "+diagram" in the verdict so the value of
  diagram context accumulates evidence across calls.
