<!-- ref:independent-derivations -->
# Independent Derivations: Ideas Reasoned Out, Then Found Already Named

**Compiled:** 2026-07-22 (session 126). **Scope:** the `llm` repo only — 740 `*.md` files
across `docs/`, `.claude/` (incl. `archive/`), `.memories/`, `overlays/`, `personas/`.
**Sibling repo `latent-topic-graph` swept separately** — see § "Sibling-repo sweep".

**What this catalogues:** instances where a mechanism was reasoned out from first principles
— described in the user's own words, from an understanding of how LLMs work — and only later
discovered to be an established technique with a name, a paper, or a shipping implementation.

**Ordered by how cleanly each fits that pattern**, not by how well-evidenced it is. The two
axes diverge: `ref:KEY`-as-knowledge-graph is the most explicitly documented instance in the
repo and simultaneously the *loosest* fit, because nothing about it was reasoned out.

---

## How to read the evidence

Every genuine instance is recorded in **second person** — "You've independently arrived at…",
"Your framing → Name in the literature" — because the reconciliation happened inside a Claude
conversation that was then saved verbatim as a doc. The literal phrase "turns out this is
called…" appears **zero times** in the repo. Searches that assume first-person retrospection
(`reinvented`, `I later learned`, `from first principles`) return almost nothing; searches on
`you've|your intuition|independently|prior art` return everything.

Corollary for anyone extending this file: `docs/ideas/` and `docs/findings/` hold raw
preserved conversation and are where the instances live. `docs/research/` is the **opposite**
direction — deliberate prior-art surveys run *before* designing. They pattern-match on the
same keywords and are not instances.

---

## Category 1 — Mechanism reasoned from how LLMs work

The purest form: reasoning from "models are matrix multiplications" or "files are an
arbitrary container" to a mechanism that turned out to have a paper. All three cluster in
**Feb–Apr 2026**.

### 1.1 Detachable adapter layers → **LoRA / QLoRA** (+ layer offloading → AirLLM)

**Original intuition** (`docs/findings/LoRA.md:3-9`, user's own words):

> "there must be a way to inject 'extra training' into the existing model, with a way that is
> cheaper than inputing a textual description (including the SYSTEM prompt in personas), so
> that we can better 'parameterize' a model/persona with more detail of the behavior we want,
> while using up less context/tokens; in fact, since the models themselves work through
> vectors/matrixes multiplications and whatnot, injecting this directly into the model - or an
> extra layer incorporated into the model on-demand, seems to be the way, and something that
> should theoretically be possible… so an 8B model could, over time, be 'trained' to get
> better at what we want to do, by improving and injecting this layer, and have it be the
> customization and learning layer… and extra layers could be added to different processing
> (and even reused when upgrading to another model)"

A second, distinct intuition in the same paragraph:

> "if this could truly be an extra 'layer', it could process a result from a model (before
> output), when perhaps not 'all' of the 'model' needs to be loaded into memory, when applying
> this (or a different) extra layer. But this is starting to sound like how AirLLM might work"

**Established name:** LoRA (Low-Rank Adaptation); QLoRA for the 12 GB-VRAM variant. The second
intuition maps to **layer-by-layer offloading** — self-identified as AirLLM mid-thought.

**Where + when:** `docs/findings/LoRA.md`, added **2026-02-26** (last touched 2026-03-10).
Reconciliation at lines 13 and 19-20:

> "You've independently arrived at several real, named techniques. Let me map your intuitions
> to what exists."
>
> "Your core intuition — 'inject learned behavior directly as matrices, cheaper than text
> prompts, detachable, reusable' — is essentially the definition of LoRA (Low-Rank
> Adaptation). You reinvented it from first principles, which means you understood the problem
> correctly."

**Closeness: identical on the core mechanism; partial on reuse.** Frozen base + small trained
delta + detachable file is the canonical definition. Diverged where the intuition expected
cross-model portability — `LoRA.md:59` corrects it to *partial* ("adapters are shape-bound to
the base architecture"), and resolves that the **correction log**, not the adapter file, is the
transferable asset. Also flagged diverged-in-practice: selective per-layer adapter application
is "valid architecturally but not yet a mainstream feature in Ollama/llama.cpp."

**Reconciled publicly** in `docs/portfolio/engineer-profile.md:66` (added **2026-03-24**) —
the one instance written up for external audiences.

### 1.2 Topic-graph retrieval → **GraphRAG / propositional indexing / RAPTOR / ColBERT**

**Original intuition:** preserved as a six-row mapping table rather than raw prose
(`docs/ideas/smart-rag4.md:17-25`). Left column is the user's framing, verbatim:

| User's framing | Name in the literature |
|---|---|
| "Graph by content relation, not by title/hyperlink" | Semantic similarity network / latent topic graph |
| "Topics pieced together from non-contiguous parts of a file" | **Propositional indexing** (Chen et al., "Dense X Retrieval", 2023) |
| "Multi-level topic identification per file" | **RAPTOR** + Leiden community detection at multiple resolutions |
| "Relationship strength changes when more files arrive" | Dynamic / online graph construction with relative salience |
| "A hash/embedding for each section, compared against the whole file" | **Multi-vector retrieval** (ColBERT late interaction, BGE-M3) |
| "Adjacency matrix of (N+T) × (N+T)" | Bipartite/multipartite knowledge graph, document + topic nodes |

**Established name:** no single one. The doc is explicit that it is a *convergence*, closest to
**Microsoft GraphRAG** one abstraction level up.

**Where + when:** `docs/ideas/smart-rag4.md`, added **2026-04-14** (session 51), line 6:

> "What you've independently derived has a name, and it's the *current frontier* of retrieval
> research — not a one-technique name, but a convergence: **propositional indexing +
> multi-scale topic decomposition + embedding-space graph + hierarchical community
> detection**. The combination you're describing is roughly what Microsoft GraphRAG does,
> pushed one level more abstract (topic-level instead of entity-level nodes)."

Line 15: *"You walked through six distinct ideas; every one has a name in current retrieval
research, and the combination is genuinely close to the frontier."*

The formal write-up followed: `docs/research/latent-topic-graph.md` (**2026-04-13**,
`ref:concept-latent-topic-graph`), whose "Novel Contributions" section opens with the
disclaimer:

> "LTG does not invent embedding-based retrieval, knowledge-graph construction from text,
> hierarchical clustering, or confidence-weighted edges. Each of these exists in the
> literature. LTG's contribution is the specific *combination*, which does not appear
> assembled in the systems surveyed at time of writing"

**Closeness: partial-to-diverged, deliberately.** Each component idea maps *identically* to an
existing technique. The assembly claims novelty on one axis — **topic-level nodes vs
GraphRAG's entity-level nodes** — which smart-rag4 endorses ("Entity-level vs topic-level is
the distinction that matters").

One sub-intuition was **right about the phenomenon, wrong about the mechanism**, and the
correction became load-bearing: "adding a file changes existing relationships"
(`smart-rag4.md:30-40`; concept paper §5) — fixed embeddings don't move; only *relative
ranking*, *topic salience*, and *community structure* rebalance. Implementation consequence:
only the derived layer needs recomputing on ingest, not the embeddings.

**Not an instance:** HyDE. It appears at `docs/ideas/smart-rag.md:44` as a technique
*presented to* the user, with no evidence of independent derivation.

---

## Category 2 — Systems/infrastructure reasoned from a failure

Real reinventions, but of **software-engineering mechanisms, not LLM mechanisms** — a
different domain from the category above, and worth keeping visibly separate. These cluster in
**Jul 2026**, and the prior art is found faster (usually same-session) because by then it was
being searched for deliberately.

### 2.1 Install-time baseline → **dpkg conffiles / 3-way merge**

**Original intuition:** root-caused the installer's unconditional `[TODO] manual merge` noise
to one missing fact (`docs/plans/overlay-install-baseline.md:12-14`):

> "**The installer records nothing about what it installed**, so it can never distinguish *'the
> overlay source moved since you last reconciled'* from *'this file legitimately differs from
> source.'*"

**Established name:** `dpkg` **conffiles**; the primitive is a 3-way merge (`git merge-file`).

**Where + when:** `docs/plans/overlay-install-baseline.md`, **2026-07-09** (session 111),
line 46:

> "**Prior art is exact.** `dpkg` calls these *conffiles*. On upgrade it compares three things
> — the file as shipped in the *old* package (the baseline), the file *currently on disk*, and
> the file in the *new* package — and only prompts when the last two both changed… Our
> `manual_if_exists` prompts unconditionally because it only ever sees two of the three."

**Closeness: identical.** Same three artifacts, same prompt condition. The doc's own framing —
"a hand-rolled package manager **for config**" — is the point: the hardest sub-problem of a
package manager was rebuilt before noticing a package manager had been built. Task copy:
`.claude/tasks.md` T-83; index row `.claude/index.md:69`.

### 2.2 "Deterministic spine, models at the edges" → **Agentless**

**Original intuition:** a principle transplanted from the user's own session-handoff pipeline —
harness code does all mechanics, models only decide content.

**Established name:** **Agentless** (MIT) — deterministic localize→repair→validate phases
around narrow LLM calls, no agentic loop; best cost/performance on SWE-bench-lite among the
compared systems.

**Where + when:** `docs/vision/coding-delegate/vision.md:55-58`, **2026-07-11**:

> "**Deterministic spine, models at the edges.** Harness code does all mechanics (locate,
> fetch, splice, verify, log); models only decide content. Direct transplant of the
> session-handoff pipeline lesson, independently validated by Agentless beating agentic
> harnesses on cost *and* correctness"

`docs/vision/coding-delegate/evidence.md:62-65`: *"External validation of S4, and the evidenced
fallback: if iterations flail, narrow the coder step, don't add agency."*

**Closeness: identical in principle, and the discovery direction is clean** — derived from
local experience, then found published and benchmarked.

**Counterweight recorded beside it, and it matters:** the *planner/coder two-small-model split*
is the same design's least-evidenced piece. `docs/vision/coding-delegate/decisions.md:80`:
*"Literature is thin — nothing tests two cooperating small models in this split."* Filed as
hypothesis V-D2, gated behind H1 run logs. A search for prior art that came back **empty**, and
was recorded as such rather than as a convergence.

### 2.3 Workspace seam → OpenHands `LocalWorkspace`/`DockerWorkspace` — *convergent engineering, not technique reinvention*

**Deliberately demoted.** `workspace: in_place | worktree` behind a swap seam
(`docs/vision/coding-delegate/architecture.md:152-154`, **2026-07-11**, parameterization
attributed to the user in-file) does converge with OpenHands' factory:

> "designed as an abstraction seam so a container backend can slot in later without redesign
> (OpenHands independently converged on workspace-as-abstraction: `LocalWorkspace`/
> `DockerWorkspace` behind one factory)"

But "backend abstraction behind a factory" is the Strategy/Factory pattern — table-stakes OO,
not a named technique that was rediscovered. Two competent designs landing on a factory is not
remarkable the way LoRA is. **Keep as a data point; do not rank beside 2.1/2.2.**

---

## Category 3 — Artifacts that turned out to be techniques

The inverse direction: something was built for a mundane local reason and *later* learned to
have a name. No reasoning-from-LLM-mechanics step. Loosest fit to the pattern, despite (in the
first case) being the most explicitly documented instance in the repo.

### 3.1 `ref:KEY` tags → a hand-curated knowledge graph

Built as a documentation-navigation convention. Named in `docs/ideas/smart-rag.md:54`
(**2026-04-13**):

> "The GraphRAG angle is particularly interesting because you've been *manually* maintaining a
> lightweight knowledge graph for a year (every `ref:KEY`, every `.memories/QUICK.md` pointer,
> every `index.md` entry). Exploiting that structure is probably a bigger win than running a
> generic extraction pass over raw text."

Sharper, same day, `docs/ideas/smart-rag2.md:45`:

> "**This is already a knowledge graph.** The ref keys are nodes, the cross-references
> (`ref:patterns-index` → `ref:patterns-*`) are edges. You've been hand-curating a graph for a
> year."

**Closeness: structurally identical, entirely unintentional.** It became LTG's *anchor node*
primitive at confidence 1.0. Externally corroborated: `docs/research/smart-rag-obsidian-mind.md:6`
("directly validates exploiting the `ref:KEY` + `.memories/` graph we already have");
`docs/ideas/smart-rag3.md:37` ("You already have `ref:KEY` + `.memories/` — same trick").

### 3.2 Passive verdict logging → **DPO preference triples** — ⚠️ INFERRED FROM DATES, NOT QUOTED

**This caveat is load-bearing and must not harden into a claim.**

The repo contains **no line** saying "I built verdict logging, then learned it was DPO data."
What exists is a chronology:

- Verdict machinery built **2026-02-26/27** —
  `.claude/archive/session-log-2026-02-26-to-2026-02-26.md:30-34` describes
  `compare-models.py` / `record-verdicts.py` as "same prompt → N models → side-by-side output →
  verdict → JSONL". No DPO framing anywhere in that session.
- DPO framing appears **one month later**, self-dated: `.memories/KNOWLEDGE.md:97` —
  "## DPO Data Collection Strategy (**2026-03**)", rationale at line 106: *"Fine-tuning requires
  labeled preference data. Collecting it passively during normal work avoids the cost of
  dedicated annotation."*

The sequence is consistent with the pattern (and sits one month after the LoRA conversation
that made fine-tuning concrete), but **the moment of recognition was never written down**.
Confirming it requires the user's memory, not this repo.

**Where the mapping *is* evidenced:** `docs/research/coding-subagent-prior-art.md:160`
(**2026-07-11**) is the one place a paper is cited —

> "**General pattern, confirmed across multiple 2024–2025 papers:** generate code → run against
> tests → if it fails, feed error back and regenerate → treat the final passing version as the
> DPO 'chosen' and one or more earlier failing attempts as 'rejected.' This is essentially what
> the planned system is already going to produce as a side effect of its iterate-until-pass
> loop… Source pattern confirmed by [Target-DPO/IterPref](https://arxiv.org/html/2503.02783v3)"

**⚠️ Do not let this feed portfolio copy without the measured caveat.**
`.memories/KNOWLEDGE.md:108-119` explicitly forbids restating design intent as fact: coverage is
**18.7% (106 verdicts / 566 calls)**; corpus is **106 labeled triples**; **no fine-tuning has
been run**; ~81% of calls carry no judgment in any form (T-105). The passive-collection *idea*
was right; the passive-collection *pipeline* mostly did not fire.

### 3.3 Evaluator rubric + judge pipeline → Phoenix's vocabulary

**The real convergence is narrow: LLM-as-judge, one call per criterion.** Lead with that.
`docs/portfolio/hf-space/observability-instrumentation.md:25` (**2026-04-02**):

> "This is the automated/static part of what Phoenix calls 'Phase 1 evals.'"

The doc also carries a six-row "Direct mapping to Phoenix concepts" table, but most rows are
**vocabulary mapping, not convergence** — "eval template = rubric YAML" is naming a config file,
not rediscovering a mechanism. Discount those rows.

**Closeness: identical vocabulary, different purpose — stated in-file** (line 44): *"The
difference: this feeds a fine-tuning pipeline rather than a monitoring dashboard."* Build order
was also inverted vs. industry norm — evaluation first, observability second, "because there was
no production application generating traffic to monitor."

### 3.4 `.memories/` per-folder convention → hierarchical scoping before retrieval — weak

`docs/ideas/smart-rag3.md:23` (**2026-04-13**): *"**hierarchical scoping before retrieval** is a
bigger win than smarter retrieval inside a flat space. Your `.memories/` per-folder convention is
already doing this on a simpler axis."*

**Closeness: partial.** Same principle, much cruder implementation, no evidence it was framed as
a retrieval decision when built.

### 3.5 Session-log / MEMORY.md → claude-mem, autoDream, Obsidian Mind — weak; arguably not an instance

`docs/research/smart-rag-claude-mem.md:42` (**2026-04-13**): *"`.claude/session-log.md` —
hand-curated equivalent of what claude-mem automates."*
`docs/research/smart-rag-obsidian-mind.md:26`: *"The `~/.claude/` auto-loaded `MEMORY.md` pattern
is basically what we already do with the auto-memory system."*

**Closeness: partial, wrong direction.** These are surveys where an existing tool overlapped with
an existing convention. The thing built is a *convention*, not a reasoned mechanism. Retained for
completeness; **do not use in narrative.**

### 3.6 Few-shot injection by keyword match → retrieval-augmented classification — weak

`docs/ideas/smart-rag2.md:95` (**2026-04-13**): *"Your few-shot injection pattern (5.7) already
does this manually: keyword pre-match training data → inject top-K examples. That *is*
retrieval-augmented classification, just using BM25-style matching."*

**Closeness: identical mechanism, degraded matcher** (keyword where the canonical version uses
embeddings + reranker). Weak because it is one clause in a larger doc, and
`docs/portfolio/portfolio.md:275` records the embedding upgrade as *deliberately deferred* — so
this reads as "your simple version is the same family," not as a discovery.

---

## Explicit non-matches — do not reach for these

- **DDD-as-agent-modeling** (`docs/research/ddd-agent-modeling.md`, **2026-03-17**) — the
  **reverse** of the pattern. User's own words, `docs/research/web-research-tool-user-notes.md:35`:
  *"Really, saying this is **'domain driven design thought as agent/model modeling'** just occurred
  to me, and makes sense."* A formalism already known was transplanted onto a new domain. Analogy,
  not reinvention.
- **Conductor / Dispatcher / Auditor / Lens** (`docs/research/agent-naming-convention.md`,
  **2026-03-17**) — legacy names (Agent A / Agent Tool / Agent B / Agent A2) were reconciled to
  *internal role names chosen by the user*, never to industry terms. The underlying architecture
  does map to orchestrator-worker + critic + context-proxy, but **no doc in this repo makes that
  mapping**.
- **`docs/research/*` broadly** — `coding-subagent-prior-art.md`, `coding-subagent-clones-survey.md`,
  `smart-rag-*.md` are prior-art surveys run *deliberately, before designing*. They keyword-match on
  everything above and invert the pattern.
- **Phase-3 source-class weighting** (`docs/phase-3-decision-questions.md:13`, **2026-06-02**) — the
  pattern running *forward*: *"Your idea… is a **strict generalization** of that property… it
  upgrades the published concept from 'binary provenance' to 'configurable provenance-class
  weighting.'"* The intuition went **past** the prior art rather than rediscovering it. A different
  story, and possibly a better one.

---

## The shape of the pattern

The three categories above are the finding, not just an ordering. Two observations:

**The domain shifted.** Category 1 (LLM-mechanism reasoning) is Feb–Apr 2026. Category 2
(systems/infra reasoning) is Jul 2026. The reinvention did not stop; what was being reasoned
*about* changed as the project moved from "understand the models" to "build the harness."

**The recording degraded, not the pattern.** Category 1 is documented richly because those
sessions were *questions* ("could this be used to enhance the local models?") whose answers were
saved verbatim into `docs/findings/` and `docs/ideas/`. Later sessions were *designs*, and designs
get written as decision records — which capture the conclusion, not the moment of recognition.
The absence of a documented DPO discovery moment (§3.2) is the clearest cost of that shift.

---

## Sibling-repo sweep (`latent-topic-graph`) — 258 `*.md`, swept 2026-07-22

**Method note, confirmed empirically:** the second-person heuristic that works in `llm`
**does not fire** in the engine repo — those sessions narrate in the third person
("the ~10 attractor is a KNOWN phenomenon"), not in dialogue. Third-person forms
(`coined`, `known phenomenon`, `independently converge`, `not novel`, `anticipated by`)
are what surface hits there. Anyone extending this file must run both.

Three items, all **later than the April concept paper** — which is where implementation
surfaced what desk research had not.

### S.1 The `~10 attractor` → **typicality bias / mode collapse** *(Category 1)*

**Original finding, and the term is the user's own.** Five prompt-wording arms plus a
baseline, run to a measured-negative close on **2026-07-14** (session 15). From
`.memories/KNOWLEDGE.md:115-119`:

> "T-39 thread-1 CLOSED 2026-07-14, measured-negative (five arms + baseline): the topic
> budget is NOT prompt-addressable — **~10 topics is the model's intrinsic list-length
> attractor** (a zero-numeral prompt still yields exactly 10×5 on every file); every wording
> treatment (open budget, count anchor, no numerals, h2-coverage requirement) made coverage
> WORSE"

The coinage is dated in-repo — `.claude/tasks.md:355` refers to *"new-coinage queries
('attractor', **coined the day before**)"* failing a retrieval probe through index lag, which
independently timestamps the word to 2026-07-13/14.

**Established name:** training-time **typicality bias / mode collapse**. Mechanism sourced to
Verbalized Sampling (Zhang et al., arXiv:2510.01171 — RLHF reward `r = r_true + α·log π_ref + ε`,
measured α̂ ≈ 0.57–0.65) and situated in a documented homogeneity family by Artificial Hivemind
(Jiang et al., arXiv:2510.22954 — 79% of repeated-sample pairs above 0.8 cosine across 70+
models). Cardinality control is shown to require **control tokens / training, not natural-language
instruction** (Ruler arXiv:2409.18943; the length-constraint benchmark line).

**Where + when:** found **2026-07-17** (session 21), three days after the coinage, by an
8-claim adversarially-verified deep-research pass. `.memories/KNOWLEDGE.md:170-176`:

> "**L-17 external validation (2026-07-17, deep-research, 8 claims adversarially verified):**
> the ~10 attractor is a KNOWN phenomenon — training-time typicality/mode-collapse;
> cardinality control requires control-tokens/training, NOT natural-language instruction, so
> the five failed wording arms now have external theory — **never retry prompt-only budget
> treatments.**"

**Closeness: identical phenomenon, and the finding was load-bearing before it had a name.**
The distinction from the Category-1 entries above: this was reached **empirically** (a
five-arm bracket) rather than reasoned from architecture — the reasoning was *"the budget is
a property of the model, not of my prompt,"* which is the right inference and is exactly what
the papers formalize. Practical payoff of the naming: it converted a local negative result
into a **closed** question ("never retry prompt-wording budget treatments") rather than an
open one. `ref:ltg-l17-novelty-audit` and `docs/research/l17-topic-budgets-and-prior-art.md` §A3.

**Note on the near-miss:** the same survey judged Artificial Hivemind *analogous, not
confirmatory* — it measures response-content similarity, not list cardinality. The
convergence is real but was recorded with its limits, not overclaimed.

### S.2 Multi-pass gap-fill loop → **Chain of Density** *(Category 2 — workaround shape)*

Having established the attractor was unbeatable by prompting, the engine's response was a
multi-pass loop. `.memories/KNOWLEDGE.md:175-178`:

> "Chain of Density independently converges on the same workaround (fixed per-pass yield,
> iterate coverage) — the multipass loop is the standard-shaped response, and the *directed*
> gap-fill variant is unclaimed in the literature"

**Closeness: identical in shape, and the divergence is the interesting half.** Chain of Density
(arXiv:2309.04269) iterates coverage at fixed output size but is **not directed at gaps**;
LightRAG's gleaning is undirected-by-default; ConExion is single-pass. The *directed* variant
survived the audit as genuinely unclaimed — see S.3.

### S.3 Reverse check — three of five claimed LTG contributions were **already prior art**

The counterpart to §1.2, and the reason this catalogue should not be read as a success record.
An adversarial 5-contribution novelty audit (`ref:ltg-l17-novelty-audit`, **2026-07-17**) found:

> "**Overall: the combination is genuinely unassembled as of 2026, but it is carried by two
> legs, not five.** Three of five are substantially anticipated by prior art the paper does not
> cite."

| Claimed contribution | Audit verdict | Anticipated by |
|---|---|---|
| #1 Topic-as-sole-primary node | **Qualified novel** — narrow to *LLM-extracted, embedded, entity-layer-skipped* | ISO/IEC 13250 **Topic Maps** (topics primary since ~1999, but hand-authored, no embeddings) |
| #2 Non-contiguous spans | **Novel** — cleanest of the five | — (SBTA is formally contiguous-only; Adaptive Chunking cannot even *evaluate* non-contiguous units) |
| #3 Files as derived aggregate | **Largely not novel** — demote to design stance | LDA/pLSI doc-similarity; ISO Topic Maps "occurrence" — *"demotes files by 2 decades"* |
| #4 Anchor stratification | **Weak-to-moderate** — integration of known parts | Confidence/provenance edges in uncertain KGs; typed nodes in HIN |
| #5 Cognitive framing | **Not novel** — move to motivation | **HippoRAG** (NeurIPS 2024, explicitly neurobiological); **FCA** framed concepts as "units of human thinking" in the 1980s |

> "**Biggest citation gaps:** ISO/IEC 13250 Topic Maps (threatens #1 and #3 at the ontology
> level — the single largest omission) and HippoRAG (#5)."

**And the inverse, in the same audit** — something genuinely novel that had *not* been claimed:

> "**Un-claimed 6th contribution:** the **directed multi-pass gap-fill loop** is more
> defensible as novel than #3 or #5 — LightRAG's gleaning is undirected-by-default, ConExion is
> single-pass, Chain of Density iterates at fixed size but not directed-at-gaps, and the
> ecology/Chao1 stopping work declines to operationalize any rule."

**Why this belongs in this file.** §1.2 records the April-2026 moment when six framings were
mapped to six existing techniques and the *combination* was judged novel. Fifteen months of
literature and one adversarial audit later, **three of the five surviving novelty claims turned
out to be prior art too — including one (ISO Topic Maps) that predates the concept paper by two
decades.** The pattern in this document is not only "reasoned it out, found the name"; it is also
"believed the assembly was new, found most of it wasn't." The honest version of the LTG story is
**two legs, not five, plus one unclaimed sixth** — not "reinvented GraphRAG one level up."

<!-- /ref:independent-derivations -->
