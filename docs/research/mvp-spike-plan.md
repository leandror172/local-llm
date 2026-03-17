<!-- ref:mvp-spike-plan -->
# MVP Spike Plan: Web Research Extraction

*Session 44 (genesis fork). Concrete plan for validating the core hypothesis.*

---

## Hypothesis to Validate

**Can a local 14B model (Qwen2.5-Coder-14B or Qwen3-14B) reliably extract structured, useful information from web pages?**

This is the foundation everything else rests on. If extraction quality is too low, no amount of architecture helps.

---

## What the Spike Produces

A single Python script that:
1. Takes a URL (or list of URLs) as input
2. Fetches the page content → converts to clean text/markdown
3. Sends content to Ollama with an extraction prompt → gets structured JSON
4. Writes results to markdown files
5. Optionally: sends content with a focus directive ("extract info about X")

**Not in scope:** search, link following, iteration, agents, knowledge graph, SearXNG, CLI framework.

---

## Environment Findings

| Component | Status | Notes |
|-----------|--------|-------|
| **Ollama** | Running | 50+ models available including Qwen2.5-Coder-14B, Qwen3-14B |
| **httpx** | Available | In MCP server venv (`0.28.1`) |
| **html2text / trafilatura** | Not installed | Need to add for HTML→markdown conversion |
| **SearXNG** | Not set up | Not needed for spike (using known URLs, not search) |
| **Firecrawl CLI** | Not installed | Not needed for spike |
| **Crawl4AI** | Not set up | Not needed for spike |
| **Python** | 3.10 (WSL2) | uv available for dependency management |

### Dependency Decision

For HTML→markdown conversion, two main options:

| Library | Size | Quality | JS support |
|---------|------|---------|------------|
| **html2text** | Tiny (~50KB) | Good for simple pages | No |
| **trafilatura** | ~5MB | Excellent — extracts main content, removes boilerplate | No |

**Recommendation:** `trafilatura` — it handles article extraction, removes nav/footer/ads, and outputs clean text. This matters because sending full HTML with navigation cruft to a 14B model wastes context tokens on noise.

For JS-heavy pages (SPAs), neither works — but that's a scraper-layer problem (Crawl4AI/Firecrawl), not a spike problem. Most documentation and tool pages render server-side.

---

## Script Design

### Location

`docs/research/spike/` — isolated from the main codebase. This is a throwaway experiment, not production code.

```
docs/research/spike/
├── extract.py          # Main spike script
├── prompts.py          # Extraction prompts (separate for easy tweaking)
├── urls.txt            # Test URLs (one per line)
├── output/             # Generated extraction results
│   ├── {slug}-raw.md   # Raw fetched content (for replay)
│   └── {slug}-extracted.json  # Structured extraction output
└── README.md           # How to run, what we learned
```

### Core Flow

```python
# Pseudocode — actual implementation in next session

async def spike(url: str, focus: str | None = None) -> dict:
    # 1. Fetch
    html = await httpx.get(url)

    # 2. Clean
    text = trafilatura.extract(html, include_links=True)
    save_raw(url, text)  # for replay without re-fetching

    # 3. Truncate if needed (14B context ~10K tokens)
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]  # naive truncation for spike

    # 4. Extract via Ollama
    prompt = build_extraction_prompt(text, focus)
    response = await ollama_chat(
        model="qwen2.5-coder:14b",  # or qwen3:14b
        messages=[{"role": "user", "content": prompt}],
        format=EXTRACTION_SCHEMA,    # structured output
        options={"temperature": 0.1}
    )

    # 5. Save
    save_extraction(url, response)
    return response
```

### Extraction Prompt Strategy

Two prompts to test:

**Prompt A — Open extraction (no focus):**
```
Given the following web page content, extract:
- name: What is this tool/project/library?
- summary: What does it do? (2-3 sentences)
- key_features: List of main capabilities (max 8)
- use_cases: What is it used for?
- technical_details: Language, license, dependencies, hosting model
- links: Important links found (docs, repo, API reference)
- limitations: Any noted limitations or caveats

Page content:
{content}
```

**Prompt B — Focus-directed extraction:**
```
Given the following web page content, extract information relevant to: {focus}

Extract:
- relevant_facts: Facts from this page relevant to the focus area
- key_details: Specific technical details related to {focus}
- links: Links worth following for more information about {focus}
- assessment: How relevant is this page to {focus}? (high/medium/low with reason)

Focus: {focus}
Page content:
{content}
```

### JSON Schema (for Ollama `format` param)

```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "summary": {"type": "string"},
    "key_features": {"type": "array", "items": {"type": "string"}},
    "use_cases": {"type": "array", "items": {"type": "string"}},
    "technical_details": {
      "type": "object",
      "properties": {
        "language": {"type": "string"},
        "license": {"type": "string"},
        "hosting": {"type": "string"}
      }
    },
    "links": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "url": {"type": "string"},
          "description": {"type": "string"}
        }
      }
    },
    "limitations": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["name", "summary", "key_features"]
}
```

Using the `format` parameter ensures 100% valid JSON output — no regex parsing needed (Layer 0 finding).

---

## Test URLs

Chosen to span different page types and content densities:

```
# Tool landing pages (well-structured, moderate content)
https://crawl4ai.com
https://docs.stagehand.dev

# GitHub READMEs (structured, technical)
https://github.com/LearningCircuit/local-deep-research
https://github.com/jina-ai/node-DeepResearch

# Documentation pages (dense, long)
https://docs.crawl4ai.com/core/quickstart
```

These are specifically chosen because:
- We already know what's on these pages (from the research agents)
- We can manually assess extraction quality against our own knowledge
- They represent the actual use case (researching AI tools)

---

## Models to Test

| Model | VRAM | tok/s | Why test |
|-------|------|-------|----------|
| **qwen2.5-coder:14b** | 9.0GB | ~32 | Best code/structured output quality in our benchmarks |
| **qwen3:14b** | 9.3GB | ~32 | Thinking capability might help extraction |
| **qwen3:8b** | 5.2GB | ~51-56 | Faster; test if 8B is "good enough" for extraction |

Start with `qwen2.5-coder:14b` (proven structured output quality), then compare.

---

## Success Criteria

The spike succeeds if:
1. **Extraction is factually accurate** — the structured output matches what's actually on the page
2. **Key features are captured** — not just surface-level (name, description) but technical details
3. **Links are identified** — the model finds links worth following (docs, API references)
4. **Focus-directed extraction works** — Prompt B extracts different information than Prompt A for the same page
5. **Processing time is acceptable** — under 60 seconds per page for 14B

The spike fails if:
- Extraction hallucinates features not on the page
- Key technical details are consistently missed
- Links are fabricated (not from the actual content)
- Focus directive is ignored (same output regardless of focus)

---

## Execution Plan

### Session N+1 (implementation, ~1-2 hours)

1. Create `docs/research/spike/` directory
2. `uv add trafilatura` (or use a standalone venv for the spike)
3. Write `extract.py` — reuse `httpx` and Ollama HTTP call pattern from MCP client
4. Write `prompts.py` — both extraction prompts + JSON schema
5. Run against 5 test URLs with `qwen2.5-coder:14b`
6. Save all outputs (raw + extracted) for review
7. Manually assess: accurate? useful? what's missing?

### Session N+2 (evaluation + comparison)

8. Run same URLs with `qwen3:14b` and `qwen3:8b`
9. Compare extraction quality across models
10. Test focus-directed extraction (Prompt B) on 2-3 URLs
11. Write up findings in `docs/research/spike/README.md`
12. Update QUICK-MEMORY.md with results

---

## What Comes After the Spike

If the spike **succeeds** (extraction quality is useful):

| Next Step | Why | Sessions |
|-----------|-----|----------|
| **SearXNG setup** | Adds search capability (query → URLs → extract) | 0.5 |
| **Link extraction + following** | Page extraction identifies links → follow them | 1 |
| **Batch processing** | Process a list of URLs, generate comparison | 1 |
| **CLI wrapper** | Make it usable beyond a script | 1 |
| → Enters the MVP build tracked in QUICK-MEMORY.md |||

If the spike **partially succeeds** (extraction works but with issues):

| Issue | Mitigation |
|-------|-----------|
| Content too long for context | Add chunking: split page, extract per chunk, merge |
| Key details missed | Improve prompt with few-shot examples (Layer 0 technique) |
| Links fabricated | Post-validate: check extracted URLs exist in raw content |
| 14B too slow | Use 8B for extraction if quality is acceptable |

If the spike **fails** (extraction quality is too low):

- Test with frontier model (Claude) to establish quality ceiling
- If frontier succeeds but local fails: this tool needs frontier-model extraction, not local
- Reassess whether local-model-first is viable for web research extraction
- Consider: local models for search/navigation, frontier for extraction

---

## Relationship to Other Angles

The spike result informs:
- **Language decision**: If Python spike works well, momentum favors Python for MVP
- **DDD agent modeling**: Extraction quality determines whether Conductor needs to evaluate/retry
- **Tool calling benchmarks**: If extraction needs retries, the orchestration layer matters more
- **Mastra deep-dive**: Only relevant if progressive autonomy is needed (spike validates basic extraction first)
<!-- /ref:mvp-spike-plan -->
