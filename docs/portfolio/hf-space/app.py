"""
Leandro R. — AI-Powered Engineer Profile
A chatbot that can discuss Leandro's engineering background, skills, and projects.
Supports HF Inference API (free) and Claude API (higher quality).
"""

import glob
import json
import math
import os
import re
import time
import traceback
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Generator

import gradio as gr
from huggingface_hub import InferenceClient

# ── HF backend (always available) ──────────────────────────
MODEL_ID = os.environ.get("MODEL_ID", "meta-llama/Llama-3.3-70B-Instruct")
HF_PROVIDER = os.environ.get("HF_PROVIDER", "groq")  # route via Groq by default
hf_token = os.environ.get("HF_TOKEN") or None
hf_client = InferenceClient(model=MODEL_ID, token=hf_token, provider=HF_PROVIDER)

# ── Claude backend (optional — only active if key is set) ──
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5")
claude_client = None
if ANTHROPIC_API_KEY:
    try:
        import anthropic
        claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        print(f"Claude backend enabled (model: {CLAUDE_MODEL})")
    except Exception as e:
        print(f"Claude backend failed to initialize: {e}")

# ── Rate limiting (Claude only — HF is free) ───────────────
CLAUDE_MAX_PER_HOUR = int(os.environ.get("CLAUDE_MAX_PER_HOUR", "30"))
_claude_usage: dict[str, list[float]] = defaultdict(list)


def _rate_limited(session_id: str) -> bool:
    """Check if this session has exceeded Claude calls/hour."""
    now = time.time()
    calls = _claude_usage[session_id]
    _claude_usage[session_id] = [t for t in calls if now - t < 3600]
    return len(_claude_usage[session_id]) >= CLAUDE_MAX_PER_HOUR

_PREAMBLE = """\
You are an AI assistant that discusses the engineering profile of Leandro R., \
a senior backend engineer with 16+ years of experience. Answer questions about \
his skills, projects, and approach grounded in the profile data below.

NOTE: This chatbot is itself part of Leandro's AI portfolio — he built and \
deployed this Gradio app on Hugging Face Spaces as a demonstration of his \
LLM infrastructure work. If asked whether this chat is an example of his work, \
the answer is yes."""

_HF_RULES = """
RULES:
- Ground your answers in the profile data below. You may synthesize and draw \
connections between different parts of the profile, but do NOT invent facts, \
projects, or achievements not mentioned here. If something is mentioned by name \
but not described in detail, do NOT elaborate using general knowledge — say \
"That's not described in detail in the profile I have."
- If a question is entirely outside what the profile covers, say "That's not \
covered in the profile I have — you'd need to ask Leandro directly."
- Prefer prose over bullet lists. Use concrete numbers and specifics from the \
profile when available. Give thorough answers — cover the topic fully, but do \
not pad with generic filler.
- When someone asks about tools or how they could help with a problem, explain \
the TOOL'S MECHANISM concretely — what it does, how it works, what it produces. \
Do NOT just say "Leandro's experience with X could help" — instead explain how \
the tool itself works and how it maps to the problem. Lead with the tool, not \
the person. If a tool is only loosely related, say so rather than overstating.
- Do NOT add praise just with the purpose of propping up the profile; the \
objective is to serve the user with relevant information for the question, be \
it about the profile, or the LLM tools being built, or Leandro's knowledge
- Do NOT mix technologies between companies. Each role has its own tech stack listed."""

_CLAUDE_RULES = """
RULES:
- Ground your answers in the profile data below. You may synthesize and draw \
connections between different parts of the profile, but do NOT invent facts, \
projects, or achievements not mentioned here.
- If a question is entirely outside what the profile covers, say "That's not \
covered in the profile I have — you'd need to ask Leandro directly."
- Use concrete numbers and specifics from the profile when available.
- Do NOT mix technologies between companies. Each role has its own tech stack listed."""

_PROFILE = """
---

# Engineer Profile: Leandro R.

## Identity

Senior backend engineer with 16+ years of experience building high-throughput \
distributed systems in Java. Currently exploring the frontier/local LLM boundary \
through a personal AI infrastructure project on consumer hardware (RTX 3060 12GB).

**Professional background:** Java backend systems — event-driven architectures \
(CQRS, Event Sourcing, Axon Framework), high-throughput data pipelines (Aerospike \
at 350K+ writes/sec, Kafka, Apache Camel), cloud platforms (GCP, AWS, Azure). \
Domains include ad tech (real-time bidding), fintech (tax calculation engines, \
banking), and telecom (customer management). Has led teams through technology \
transitions (C# to Java), introduced Event Modeling as a design practice, and \
consistently established TDD culture wherever he works.

**Current AI work:** Three interconnected repositories — an AI platform \
(Python/Bash; its components are the MCP Bridge Server, Persona System, and \
Benchmark Framework described in the AI Infrastructure Projects section below), \
an expense classification CLI (Go), and a web research tool (Python) — all using \
local Ollama models with frontier-model (Claude) escalation. \
This is self-directed work that started in early 2026, not a career-long AI focus. \
The AI work builds on the same engineering discipline (TDD, clean architecture, \
empirical validation, DDD) applied throughout the professional career.

## Technical Domains

### Java Backend & Distributed Systems (16+ years, primary professional skill)
Core stack: Java, Spring Boot, Spring Cloud, Kafka, event-driven architecture \
(CQRS, Event Sourcing, DDD). Has built systems at significant scale: an Aerospike \
data pipeline processing up to 3.2 billion records daily at 350K+ writes/sec \
(InMarket, ad tech), a configurable tax calculation engine with CQRS/Axon Framework \
that eliminated deployment dependency for operator changes (BNP Paribas, fintech), \
and a Kafka parallel processing system with Dead Letter Queue that eliminated \
message loss entirely (Vivere Brasil).

Consistently introduces quality practices: 89-96% test coverage at BNP Paribas \
(company record, <5 production bugs in first year), TDD mentorship at every \
significant role, Event Modeling pioneered as a domain visualization technique. \
Has worked across GCP (GKE, PubSub, Cloud Functions), AWS (ECS, Lambda, SQS), \
and Azure. Comfortable with Terraform, Datadog (built dashboards + alerts, \
reduced costs by $8K/month), and CI/CD pipelines.

### Local LLM Infrastructure (deep, hands-on, empirical — self-directed, started 2026)
Operates a fleet of 13 base models (Qwen, DeepSeek families) configured into 35+ \
specialized personas on a 12GB VRAM budget. Understands quantization trade-offs \
(Q4_K_M: 75% size reduction, minimal quality loss), context window limits per \
model tier (8B safe at 32K, 14B at 16K), Flash Attention memory savings, and \
KV cache tuning.

Built an MCP bridge server (Python/FastMCP) that lets Claude Code delegate tasks \
to local Ollama models — with automatic persona routing, structured JSON output \
via grammar-constrained decoding, connection pooling, and cold-start management.

Key insight: prompt complexity has a hard ceiling per model tier (8B: ~400 output \
tokens, 14B: ~800). Beyond that, both timeout and logic errors co-occur. The fix \
is prompt decomposition, not retries or larger context windows.

### Go Backend Development (working proficiency, production-quality code)
Learned Go at InMarket to build an acceptance testing framework from scratch — \
catching a critical serialization bug before production; the framework was later \
adopted by the principal engineer for infrastructure validation. Continued with Go \
in the expense classifier project (Cobra CLI, 190+ unit tests, TDD).

### Python Tooling & Data Pipelines (Self-directed (early 2026), AI tooling focus only — not production engineering depth; primary professional language is Java.)
MCP server implementation, benchmark framework, persona management tools, \
extraction pipelines, overlay installer. Comfortable with async patterns (httpx), \
CLI tools, JSONL event logging, and structured output schemas.

### LLM/ML Techniques (applied practitioner, not researcher)
Structured output via grammar-constrained decoding, prompt decomposition \
(empirically validated 3-stage sweet spot), few-shot injection with keyword \
retrieval (47% token reduction measured), temperature tuning as a model-selection \
substitute, cascade patterns (local to frontier escalation). Collecting DPO \
training data passively through verdict-labeled inference logs.

Notably, arrived at LoRA's core concept independently from first principles — \
reasoning that "there must be a way to inject extra training into a model as a \
detachable layer, cheaper than text prompts, reusable across tasks" — before \
learning the formalism. Understands what fine-tuning can fix (mechanical patterns, \
persona compliance) vs. what it cannot (output budget ceiling, reasoning capacity).

## Engineering Philosophy
- Design-first: every major feature starts with a design document, not code
- Empirical over theoretical: benchmarks on real hardware, not spec-sheet claims
- Right tool for the right task: 8B for boilerplate, 14B for reasoning, frontier for judgment
- Process discipline: TDD non-negotiable, structured session handoffs, verdict protocol
- Local-first with frontier escalation: default is local, frontier for judgment
- Pragmatic constraints: 12GB VRAM drives every architecture decision

## Key Professional Achievements (by company — do NOT mix technologies between roles)

### InMarket (ad tech, 2025) — Tech: Java, Spring Boot, Apache Camel, Aerospike, GCP, Go
- Aerospike data pipeline — 350K+ writes/sec, 3.2B records/day, delivered in 4.5 months
- Pipeline: GCS file arrival → Cloud Function chunker → PubSub → Camel consumers → Protobuf → Aerospike
- NO Kafka at InMarket — messaging was GCP PubSub + Apache Camel
- Built Go acceptance testing framework (learned Go for this), caught critical serialization bug
- Reduced Datadog costs by $8K/month through configurable tag filtering

### BNP Paribas (fintech, 2021-2023) — Tech: Java, Spring Boot, Axon Framework, Oracle, ActiveMQ
- 89-96% test coverage (company record), <5 production bugs in first year
- Pioneered Event Modeling, implemented CQRS with Axon Framework

### Vivere Brasil (2017-2019) — Tech: Java, Kafka
- Kafka DLQ system eliminated message loss (5/week to 0)

### Unicred (fintech, 2024-2025) — Tech: Java, Spring Boot, Kafka, SQL Server
- API response from 100ms-5s to sub-150ms via parallel data consolidation

### Randstad/BV (banking, 2016) — Tech: Java, Azure
- Contributed to first Brazilian bank on public cloud (Azure)

## AI Infrastructure Projects
- MCP Bridge Server: Python/FastMCP server exposing Ollama models as Claude Code tools
- Persona System: 35+ specialized configs from 13 base models, registry-driven
- Benchmark Framework: multi-language validation (Go, Python, Shell, HTML/JS, Java)
- Expense Classifier: Go CLI with hybrid pattern-rules + LLM classification, 190+ tests
- Web Research Tool: local-model-powered extraction with DDD agent architecture
- Overlay System: portable scaffolding packages for cross-repo consistency
- Verdict Protocol: ACCEPTED/IMPROVED/REJECTED labels create DPO training data passively

## Scale and Scope
- 16+ years professional experience, 50+ AI-assisted development sessions
- 143 commits across 3 AI repositories
- 35+ model personas from 13 base models
- 190+ unit tests in the Go expense classifier
- 10-layer architectural plan — 5 layers complete, 5 planned

## What This Person Can Speak Deeply About
Professional: high-throughput pipelines (Aerospike, Kafka), event-driven architecture \
(CQRS, Event Sourcing, Axon, Event Modeling), Java ecosystem (Spring Boot, Cloud, \
Camel), cloud platforms (GCP, AWS), quality culture (TDD, mentoring), DDD.
AI: running LLMs on consumer hardware, frontier/local collaboration via MCP, persona \
engineering, QLoRA trade-offs, DPO data collection, prompt decomposition, benchmarking.

## What Would Require the Person Directly
- Team-scale AI workflow design (AI work is individual)
- Fine-tuning execution (planned, not yet implemented)
- Frontend development (backend-focused career)
"""

# ── Context loading from .memories/ files ─────────────────
CONTEXT_DIR = os.path.join(os.path.dirname(__file__), "context")


def _load_context_files(pattern: str) -> str:
    """Load markdown files matching a glob pattern from context/, sorted by name."""
    files = sorted(glob.glob(os.path.join(CONTEXT_DIR, pattern)))
    if not files:
        return ""
    sections = []
    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            with open(path) as f:
                content = f.read().strip()
            if content:
                sections.append(f"### {name}\n{content}")
        except OSError:
            continue
    if not sections:
        return ""
    return "\n\n---\n\n## Project Context (auto-loaded)\n\n" + "\n\n".join(sections)


# Always-inject tier: QUICK.md files from all repos (~5K tokens)
_PROJECT_CONTEXT = _load_context_files("*-quick.md")

# ── Phase 2: LLM-as-router for KNOWLEDGE.md sections ──────


@dataclass
class _Section:
    key: str
    source: str
    heading: str
    snippet: str   # first ~200 chars of body — used in routing index
    content: str   # full section text — injected when selected


def _build_section_index(directory: str | None = None) -> list[_Section]:
    """Parse all *-knowledge.md files into a flat list of sections."""
    directory = directory or CONTEXT_DIR
    sections = []
    for path in sorted(glob.glob(os.path.join(directory, "*-knowledge.md"))):
        source = os.path.splitext(os.path.basename(path))[0]
        try:
            with open(path) as f:
                content = f.read()
        except OSError:
            continue
        # Split on ## headings using lookahead to preserve the delimiter
        parts = re.split(r"\n(?=## )", content)
        for part in parts:
            lines = part.strip().split("\n")
            if not lines[0].startswith("## "):
                continue  # file-level header — skip
            heading = lines[0][3:].strip()
            body_lines = [l for l in lines[1:] if l.strip()]
            snippet = " ".join(body_lines[:2])[:200]
            sections.append(_Section(
                key=f"{source}:{heading}",
                source=source,
                heading=heading,
                snippet=snippet,
                content=part.strip(),
            ))
    return sections


def _format_routing_index(sections: list[_Section]) -> str:
    """Format the section list into a numbered index for the routing prompt."""
    return "\n".join(
        f"[{i}] {s.source} / {s.heading}: {s.snippet}"
        for i, s in enumerate(sections)
    )


_SECTION_INDEX: list[_Section] = _build_section_index()
_ROUTING_INDEX_STR: str = _format_routing_index(_SECTION_INDEX)

_ROUTING_SYSTEM = """\
You are a document retrieval assistant. Given a user question and an index of \
document sections, return the indices of the most relevant sections. \
Return ONLY a JSON array of integers, no explanation. Example: [0, 3, 7] \
Select at most 6 sections. If none are relevant, return []."""


def _parse_hf_error(exc: Exception) -> tuple[int, str, str]:
    """Extract (status_code, error_code, message) from an HfHubHTTPError.

    Returns (0, '', '') if exc has no .response or the body isn't parseable.
    """
    response = getattr(exc, "response", None)
    if response is None:
        return 0, "", ""
    status = getattr(response, "status_code", 0)
    try:
        body = response.json()
        # Groq (OpenAI-compatible) wraps errors: {"error": {"code": ..., "message": ...}}
        error_obj = body.get("error", body) if isinstance(body, dict) else {}
        return status, error_obj.get("code", ""), error_obj.get("message", "")
    except Exception as e:
        print(f"[parse_hf_error] json() failed: {e}", flush=True)
        return status, "", ""


def _retry_after(exc: Exception) -> float | None:
    """Return seconds to wait before retrying, or None if not retriable.

    Only retries on 429 rate_limit_exceeded with a short wait (<=60s).
    Daily/hourly quota exhaustion (long waits) returns None — not worth retrying.
    """
    status, code, msg = _parse_hf_error(exc)
    if status != 429 or code != "rate_limit_exceeded":
        return None
    m = re.search(r"try again in (?:(\d+)h)?(?:(\d+)m)?(\d+\.?\d*)s", msg)
    if not m:
        return None
    total = int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + float(m.group(3))
    return None if total > 60 else total + 1.0


def _format_wait(total_seconds: float) -> str:
    """Format a duration in seconds as a human-readable string."""
    minutes = math.ceil(total_seconds / 60)
    if minutes < 60:
        return f"about {minutes} minute{'s' if minutes != 1 else ''}"
    hours, mins = divmod(minutes, 60)
    base = f"about {hours} hour{'s' if hours != 1 else ''}"
    return base if mins == 0 else f"{base} {mins} minute{'s' if mins != 1 else ''}"


def _classify_error(exc: Exception) -> str:
    """Return a user-facing error message based on structured HTTP error data."""
    status, code, msg = _parse_hf_error(exc)
    if code == "rate_limit_exceeded":
        m = re.search(r"try again in (?:(\d+)h)?(?:(\d+)m)?(\d+\.?\d*)s", msg)
        if m:
            total = int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + float(m.group(3))
            if total > 60:
                return (f"Usage limit reached — please try again in {_format_wait(total)}, "
                        f"or switch to the Haiku model.")
        return "Rate limit reached. Please try again in a few minutes, or switch to the Haiku model."
    if status == 401:
        return "Authentication error — please check the API key configuration."
    if status == 413:
        return "Your message is too long for this model."
    if status in (500, 502, 503):
        return "The model service is temporarily down. Please try again in a moment."
    return "The model is temporarily unavailable. Please try again."


def _with_retry(fn):
    """Call fn(), retrying once on a retriable rate-limit error.

    fn is a zero-argument callable (typically a lambda wrapping an API call).
    On a retriable 429 (rate_limit_exceeded), sleeps the suggested wait time
    and retries once. Any other exception, or a second failure, is re-raised.
    """
    for attempt in range(2):
        try:
            return fn()
        except Exception as exc:
            wait = _retry_after(exc)
            if wait is not None and attempt == 0:
                print(f"[retry] rate limited, retrying in {wait:.1f}s…", flush=True)
                time.sleep(wait)
                continue
            raise


def _route_sections(question: str) -> list[_Section]:
    """Call the HF backend (non-streaming) to select relevant knowledge sections."""
    if not _SECTION_INDEX:
        print("[routing] index empty — skipping", flush=True)
        return []
    print(f"[routing] question: {question[:80]!r}", flush=True)
    try:
        resp = _with_retry(lambda: hf_client.chat_completion(
            messages=[
                {"role": "system", "content": _ROUTING_SYSTEM},
                {"role": "user", "content": f"Index:\n{_ROUTING_INDEX_STR}\n\nQuestion: {question}"},
            ],
            max_tokens=80,
            temperature=0.0,
            stream=False,
        ))
        raw = resp.choices[0].message.content.strip()
        print(f"[routing] raw response: {raw!r}", flush=True)
        indices = json.loads(raw)
        if not isinstance(indices, list):
            print(f"[routing] expected list, got {type(indices).__name__} — no sections selected", flush=True)
            return []
        selected = [
            _SECTION_INDEX[i] for i in indices[:3]
            if isinstance(i, int) and 0 <= i < len(_SECTION_INDEX)
        ]
        print(f"[routing] selected {len(selected)} section(s): {[s.key for s in selected]}", flush=True)
        return selected
    except Exception:
        traceback.print_exc()
        return []  # graceful degradation — fall back to quick-files-only


def _enrich_prompt(base_prompt: str, sections: list[_Section]) -> str:
    """Append selected knowledge sections to a system prompt."""
    if not sections:
        return base_prompt
    _MAX_SECTION_CHARS = 600
    parts = ["\n\n---\n\n## Retrieved Knowledge Sections\n"]
    for s in sections:
        body = s.content if len(s.content) <= _MAX_SECTION_CHARS else s.content[:_MAX_SECTION_CHARS] + "…"
        parts.append(f"### [{s.source}] {s.heading}\n{body}")
    return base_prompt + "\n\n".join(parts)


SYSTEM_PROMPT = _PREAMBLE + _HF_RULES + _PROFILE + _PROJECT_CONTEXT
CLAUDE_SYSTEM_PROMPT = _PREAMBLE + _CLAUDE_RULES + _PROFILE + _PROJECT_CONTEXT

EXAMPLES = [
    ["Tell me about the LLM projects he's working on"],
    ["Tell me about Leandro's practical knowledge on working with LLMs"],
    ["What local AI infrastructure has Leandro built, and why?"],
    ["How does Leandro decide when to use a local model vs. a frontier model?"],
    ["What surprised him most about running LLMs on consumer hardware?"],
    ["How does his backend background inform his AI infrastructure work?"],
    ["Tell me about the Aerospike pipeline at InMarket"],
    ["What's the DDD connection to agent architecture?"],
    ["What LLM techniques and tools does Leandro work with?"],
    ["Is this chat an example of Leandro's work?"],
    ["How does the MCP bridge server work?"],
    ["What's the evaluator framework and how does it relate to LLM observability?"],
    ["How does the expense classifier use local models?"],
    ["What are overlays and how could they help my AI workflow?"],
]

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks. Hides incomplete blocks mid-stream."""
    text = _THINK_RE.sub("", text)
    idx = text.find("<think>")
    if idx != -1:
        text = text[:idx]
    return text.lstrip("\n")


def respond_hf(message: str, history: list[dict]) -> Generator[str, Any, None]:
    """Stream response from HF Inference API."""
    selected = _route_sections(message)
    messages = [{"role": "system", "content": _enrich_prompt(SYSTEM_PROMPT, selected)}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    response = ""
    try:
        stream = _with_retry(lambda: hf_client.chat_completion(
            messages=messages,
            max_tokens=2048,
            temperature=0.7,
            stream=True,
        ))
        for chunk in stream:
            if not chunk.choices:
                continue
            token = chunk.choices[0].delta.content or ""
            response += token
            visible = _strip_thinking(response)
            if visible:
                yield visible
    except Exception as exc:
        traceback.print_exc()
        user_msg = _classify_error(exc)
        if response:
            yield response + f"\n\n*[{user_msg}]*"
        else:
            yield user_msg



def respond_claude(message: str, history: list[dict]) -> Generator[str, Any, None]:
    """Stream response from Claude API."""
    if not claude_client:
        yield "Claude backend is not configured."
        return

    # Simple session ID from first message in history
    session_id = str(hash(str(history[:1])))
    if _rate_limited(session_id):
        yield ("Rate limit reached for Claude backend. "
               "Please try again later, or switch to the open-source model.")
        return
    _claude_usage[session_id].append(time.time())

    # Claude doesn't need Groq for routing — skip _route_sections to avoid
    # burning Groq tokens (and failing when Groq's daily limit is hit)
    messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
    messages.append({"role": "user", "content": message})

    response = ""
    try:
        with claude_client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            temperature=0.7,
            system=CLAUDE_SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                response += text
                yield response
    except Exception as e:
        traceback.print_exc()
        if response:
            yield response + f"\n\n*[{_classify_error(e)}]*"
        else:
            yield _classify_error(e)


def respond(message: str, history: list[dict], backend: str = "") -> Generator[str, Any | None, None]:
    """Route to the selected backend."""
    if backend == "Claude (Haiku)" and claude_client:
        yield from respond_claude(message, history)
    else:
        yield from respond_hf(message, history)


PROFILE_PATH = os.path.join(os.path.dirname(__file__), "engineer-profile.md")
PORTFOLIO_PATH = os.path.join(os.path.dirname(__file__), "portfolio.md")


def read_file(path: str) -> str:
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return "*File not available.*"


def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter (---...---) for rendering."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].lstrip()
    return text


with gr.Blocks(title="Leandro R. — Engineer Profile") as demo:
    gr.Markdown("# Leandro R. — Engineer Profile")
    gr.Markdown(
        "Senior backend engineer (16+ years, Java) · Local AI infrastructure builder · "
        "[GitHub](https://github.com/leandror172)"
    )

    with gr.Tabs():
        with gr.TabItem("Chat"):
            gr.Markdown(
                "Ask me about Leandro's engineering background, projects, and technical approach. "
                "For complex questions (e.g., matching tools to your challenges), try the Claude backend for more precise answers. "
                "For a deeper conversation, download/copy the profile and portfolio docs from the tabs above, and add it to Claude, ChatGPT, "
                "or your preferred tool."
            )

            backend_choices = ["Open-source (Llama 3.3 70B)"]
            if claude_client:
                backend_choices.append("Claude (Haiku)")

            backend = gr.Radio(
                choices=backend_choices,
                value=backend_choices[0],
                label="Model",
                visible=len(backend_choices) > 1,
            )

            chat = gr.ChatInterface(
                fn=respond,
                additional_inputs=[backend],
                examples=EXAMPLES,
                cache_examples=False,
            )

        with gr.TabItem("Profile"):
            gr.Markdown("### AI-Readable Engineer Profile")
            gr.Markdown(
                "This document is designed to be fed to an AI model for a richer, "
                "more nuanced conversation about Leandro's background."
            )
            profile_content = read_file(PROFILE_PATH)
            with gr.Row():
                gr.File(
                    value=PROFILE_PATH if os.path.exists(PROFILE_PATH) else None,
                    label="Download",
                )
            gr.Markdown(
                strip_frontmatter(profile_content),
                buttons=["copy"],
            )

        with gr.TabItem("Portfolio"):
            gr.Markdown("### Project Portfolio")
            gr.Markdown(
                "Detailed overview of three interconnected repositories: "
                "AI platform, expense classifier, and web research tool."
            )
            portfolio_content = read_file(PORTFOLIO_PATH)
            with gr.Row():
                gr.File(
                    value=PORTFOLIO_PATH if os.path.exists(PORTFOLIO_PATH) else None,
                    label="Download",
                )
            gr.Markdown(
                portfolio_content,
                buttons=["copy"],
            )

if __name__ == "__main__":
    print("Launching Gradio app...")
    demo.launch()
