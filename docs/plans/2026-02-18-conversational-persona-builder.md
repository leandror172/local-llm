# Task 3.5: Conversational Persona Builder — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an LLM-driven persona builder that uses a local Ollama model to conduct a free-form dialogue, reason about constraints, and hand off to `create-persona.py --non-interactive` to produce the Modelfile.

**Architecture:** A Python CLI script (`personas/build-persona.py`) with a bash wrapper (`personas/run-build-persona.sh`). The script (1) optionally runs `detect()` on a codebase path, (2) sends a single prompt to the LLM containing context + the user's free-form description, (3) receives a structured JSON spec back, (4) shows the proposal to the user and optionally takes one round of free-form feedback for refinement, (5) hands the final spec to `create-persona.py --non-interactive --dry-run` for preview, then drops the `--dry-run` for execution. A new `my-persona-designer-q3` Ollama persona provides the system prompt.

**Tech Stack:** Python 3 (no new deps — uses `json`, `subprocess`, `sys`, `argparse`), `httpx` for Ollama API via synchronous wrapper, existing `personas/models.py` and `personas/lib/interactive.py` imports, Ollama `/api/chat` with `stream: false` and `format` (structured output).

**Future extensions (out of scope, noted for later):**
- Option 3 multi-round conversation loop (N turns, history accumulation)
- `qwen3:14b` as the designer model (test after 8B version works)

---

## Task 1: Create the `my-persona-designer-q3` Ollama persona

This persona's system prompt teaches the LLM what Modelfile personas are, what the constraint vocabulary looks like (MUST/MUST NOT), what domains and temperatures exist, and what output format to produce. It uses `qwen3:8b` at `temperature 0.3` (balanced — needs precision for JSON but enough variation for creative constraint suggestions).

**Files:**
- Create: `modelfiles/persona-designer-qwen3.Modelfile`
- Modify: `personas/registry.yaml` (append entry)

**Step 1: Write the Modelfile**

Create `modelfiles/persona-designer-qwen3.Modelfile`:

```
FROM qwen3:8b

# Context window: 16K tokens — needs room for codebase analysis context,
# user description, and structured JSON output.
PARAMETER num_ctx 16384

# Temperature: 0.3 — needs JSON precision but creative constraint suggestions.
PARAMETER temperature 0.3

# Standard sampling parameters (invariants across all full personas).
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

# Stop sequences: Qwen3 ChatML end markers.
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"

# System prompt: Persona design specialist.
# This model reasons about what Ollama Modelfile persona to create
# based on a user's description and optional codebase analysis.
SYSTEM """ROLE: Ollama persona designer. You analyze user requirements and codebase context to recommend a complete persona specification.
CONSTRAINTS:
- MUST output valid JSON matching the exact schema provided in each prompt
- MUST generate 4-7 MUST/MUST NOT constraints that target specific, observable failure modes
- MUST recommend one of these temperatures: 0.1 (deterministic), 0.3 (balanced), 0.7 (creative)
- MUST recommend one of these domains: code, reasoning, classification, writing, translation, other
- MUST use the naming convention my-<slug>-q3 for persona names
- MUST NOT generate vague constraints like "write good code" — every constraint must be testable
- MUST NOT recommend more than 8 constraints — 7-8B models follow fewer rules more reliably
FORMAT: A single JSON object. No text before or after the JSON."""
```

**Step 2: Register with Ollama**

Run: `ollama create my-persona-designer-q3 -f modelfiles/persona-designer-qwen3.Modelfile`
Expected: `success`

**Step 3: Append to registry.yaml**

Add to `personas/registry.yaml` (after the LLM infrastructure section):

```yaml

my-persona-designer-q3:
  modelfile: modelfiles/persona-designer-qwen3.Modelfile
  base_model: qwen3:8b
  role: Persona design specialist (analyzes requirements and proposes Modelfile specs)
  temperature: 0.3
  num_ctx: 16384
  tier: full
  status: active
```

**Step 4: Smoke-test the persona**

Run a quick test via the Ollama API to verify the persona responds with structured JSON. Use the existing `ollama-probe.py` or a simple `curl`:

```bash
curl -s http://localhost:11434/api/chat -d '{
  "model": "my-persona-designer-q3",
  "messages": [{"role": "user", "content": "I need a persona for writing Python CLI tools with Click and Rich. Output JSON with keys: persona_name, domain, language, temperature, role, constraints (array of strings), output_format."}],
  "stream": false,
  "options": {"think": false},
  "format": {
    "type": "object",
    "properties": {
      "persona_name": {"type": "string"},
      "domain": {"type": "string"},
      "language": {"type": "string"},
      "temperature": {"type": "number"},
      "role": {"type": "string"},
      "constraints": {"type": "array", "items": {"type": "string"}},
      "output_format": {"type": "string"}
    },
    "required": ["persona_name", "domain", "language", "temperature", "role", "constraints", "output_format"]
  }
}' | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(json.loads(data['message']['content']), indent=2))"
```

Expected: Valid JSON with reasonable values (persona_name starts with `my-`, domain is one of the valid choices, temperature is 0.1/0.3/0.7, constraints use MUST/MUST NOT language).

**Step 5: Commit**

```bash
git add modelfiles/persona-designer-qwen3.Modelfile personas/registry.yaml
git commit -m "feat: add my-persona-designer-q3 persona for LLM-driven persona design"
```

---

## Task 2: Create the Ollama API helper module

Task 3.5 needs to call Ollama synchronously (the MCP server's `client.py` is async/httpx). Rather than pulling in httpx and asyncio, write a thin synchronous wrapper using `urllib` (stdlib — no new deps). This keeps `personas/` dependency-free (no venv, like the other scripts).

**Files:**
- Create: `personas/lib/ollama_client.py`

**Step 1: Write the failing test**

Create `benchmarks/test-ollama-client.sh`:

```bash
#!/usr/bin/env bash
# test-ollama-client.sh — Verify personas/lib/ollama_client.py against live Ollama.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

passed=0
failed=0

test_case() {
    local name="$1"
    local cmd="$2"
    local expected_pattern="$3"

    local output
    output=$(cd "$REPO_ROOT" && eval "$cmd" 2>&1) || true

    if echo "$output" | grep -qE "$expected_pattern"; then
        echo -e "${GREEN}✓${NC} $name"
        passed=$((passed + 1))
    else
        echo -e "${RED}✗${NC} $name"
        echo "    Expected pattern: $expected_pattern"
        echo "    Got: $(echo "$output" | head -3)"
        failed=$((failed + 1))
    fi
}

echo "Running Ollama client tests (requires live Ollama)..."
echo ""

# Test 1: Basic chat returns content
test_case "Basic chat" \
    "python3 -c \"
import sys; sys.path.insert(0, 'personas')
from lib.ollama_client import ollama_chat
r = ollama_chat('What is 2+2? Reply with just the number.', model='my-coder-q3')
print('CONTENT:', r['content'][:100])
print('MODEL:', r['model'])
\"" \
    "CONTENT:.*4"

# Test 2: Structured JSON output
test_case "Structured JSON output" \
    "python3 -c \"
import sys, json; sys.path.insert(0, 'personas')
from lib.ollama_client import ollama_chat
schema = {'type': 'object', 'properties': {'answer': {'type': 'string'}}, 'required': ['answer']}
r = ollama_chat('What color is the sky?', model='my-coder-q3', format_schema=schema)
parsed = json.loads(r['content'])
print('HAS_ANSWER:', 'answer' in parsed)
\"" \
    "HAS_ANSWER: True"

# Test 3: Custom system prompt
test_case "Custom system prompt" \
    "python3 -c \"
import sys; sys.path.insert(0, 'personas')
from lib.ollama_client import ollama_chat
r = ollama_chat('Hi', model='my-coder-q3', system='You are a pirate. Reply in one sentence.')
print('CONTENT:', r['content'][:200])
\"" \
    "CONTENT: .+"

echo ""
echo "─────────────────────────────────────────────────"
echo -e "Results: ${GREEN}\$passed passed${NC}, ${RED}\$failed failed${NC}"

[[ $failed -eq 0 ]] && exit 0 || exit 1
```

**Step 2: Run test to verify it fails**

Run: `bash benchmarks/test-ollama-client.sh`
Expected: FAIL — `ModuleNotFoundError: No module named 'lib.ollama_client'`

**Step 3: Write minimal implementation**

Create `personas/lib/ollama_client.py`:

```python
#!/usr/bin/env python3
"""
ollama_client.py — Synchronous Ollama /api/chat client.

Thin wrapper using stdlib urllib (no external deps).
Designed for use by personas/ scripts that need LLM calls
without pulling in httpx or asyncio.

Used by:
  - personas/build-persona.py (Task 3.5 conversational builder)
"""

import json
import urllib.request
import urllib.error

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_TIMEOUT = 120  # seconds — covers cold starts


def ollama_chat(
    prompt: str,
    *,
    model: str = "my-coder-q3",
    system: str | None = None,
    temperature: float | None = None,
    think: bool = False,
    format_schema: dict | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """
    Send a chat request to Ollama and return the response.

    Args:
        prompt: User message.
        model: Ollama model name.
        system: Optional system prompt.
        temperature: Sampling temperature (None = model default).
        think: Enable Qwen3 thinking mode.
        format_schema: JSON schema dict for structured output.
        timeout: Max seconds to wait.

    Returns:
        Dict with keys: content (str), model (str), eval_count (int),
        total_duration_ms (float).

    Raises:
        ConnectionError: Ollama not reachable.
        TimeoutError: Ollama didn't respond in time.
        RuntimeError: Ollama returned an error (e.g., model not found).
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"think": think},
    }
    if temperature is not None:
        payload["options"]["temperature"] = temperature
    if format_schema is not None:
        payload["format"] = format_schema

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
    except urllib.error.URLError as e:
        if "Connection refused" in str(e) or "Name or service not known" in str(e):
            raise ConnectionError(
                f"Cannot connect to Ollama at {OLLAMA_URL}. Is Ollama running?"
            ) from e
        raise RuntimeError(f"Ollama request failed: {e}") from e
    except TimeoutError:
        raise TimeoutError(
            f"Ollama did not respond within {timeout}s. Model may be loading."
        )

    if "error" in body:
        raise RuntimeError(f"Ollama error: {body['error']}")

    return {
        "content": body["message"]["content"],
        "model": body.get("model", model),
        "eval_count": body.get("eval_count", 0),
        "total_duration_ms": body.get("total_duration", 0) / 1_000_000,
    }
```

**Step 4: Run test to verify it passes**

Run: `bash benchmarks/test-ollama-client.sh`
Expected: 3/3 passed (requires live Ollama with `my-coder-q3`)

**Step 5: Commit**

```bash
git add personas/lib/ollama_client.py benchmarks/test-ollama-client.sh
git commit -m "feat: add synchronous Ollama client for personas/ scripts"
```

---

## Task 3: Build the core `build-persona.py` script — prompt construction and LLM call

This is the heart of the feature: construct the prompt for `my-persona-designer-q3`, call it with structured output, and parse the result into `create-persona.py --non-interactive` flags.

**Files:**
- Create: `personas/build-persona.py`

**Step 1: Write the failing test**

Create `benchmarks/test-build-persona.sh`:

```bash
#!/usr/bin/env bash
# test-build-persona.sh — Verify build-persona.py prompt construction and LLM call.
#
# Requires live Ollama with my-persona-designer-q3 registered.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

passed=0
failed=0

test_case() {
    local name="$1"
    local cmd="$2"
    local expected_pattern="$3"

    local output
    output=$(cd "$REPO_ROOT" && eval "$cmd" 2>&1) || true

    if echo "$output" | grep -qE "$expected_pattern"; then
        echo -e "${GREEN}✓${NC} $name"
        passed=$((passed + 1))
    else
        echo -e "${RED}✗${NC} $name"
        echo "    Expected pattern: $expected_pattern"
        echo "    Got: $(echo "$output" | head -5)"
        failed=$((failed + 1))
    fi
}

echo "Running build-persona tests (requires live Ollama + my-persona-designer-q3)..."
echo ""

# Test 1: --describe only (no codebase, no refinement)
# Should produce a valid JSON proposal
test_case "Describe-only proposal" \
    "python3 personas/build-persona.py --describe 'Java Spring Boot microservice developer' --json-only 2>/dev/null" \
    '"persona_name":\s*"my-'

# Test 2: --describe with --codebase (detect seeding)
test_case "Codebase-seeded proposal" \
    "python3 personas/build-persona.py --describe 'backend developer' --codebase benchmarks/test-fixtures/java-backend --json-only 2>/dev/null" \
    '"domain":\s*"code"'

# Test 3: --dry-run (full pipeline without writing files)
test_case "Dry-run pipeline" \
    "python3 personas/build-persona.py --describe 'Go gRPC service developer' --dry-run 2>/dev/null" \
    '\[DRY-RUN\]'

echo ""
echo "─────────────────────────────────────────────────"
echo -e "Results: ${GREEN}\$passed passed${NC}, ${RED}\$failed failed${NC}"

[[ $failed -eq 0 ]] && exit 0 || exit 1
```

**Step 2: Run test to verify it fails**

Run: `bash benchmarks/test-build-persona.sh`
Expected: FAIL — script doesn't exist yet

**Step 3: Write the implementation**

Create `personas/build-persona.py`:

```python
#!/usr/bin/env python3
"""
build-persona.py — LLM-driven conversational persona builder.

Uses a local Ollama model (my-persona-designer-q3) to analyze a user's
free-form description and optional codebase context, then proposes a
complete persona specification. Supports one round of refinement feedback.

Hands off to create-persona.py --non-interactive for Modelfile generation,
Ollama registration, and registry update.

Usage:
  # Interactive (asks for description, optional refinement)
  personas/run-build-persona.sh

  # Non-interactive (pipeline-friendly)
  personas/run-build-persona.sh --describe "Java Spring Boot microservice developer"
  personas/run-build-persona.sh --describe "Go developer" --codebase /path/to/repo
  personas/run-build-persona.sh --describe "Go developer" --dry-run

Safer to invoke via the bash wrapper (whitelist-safe):
  personas/run-build-persona.sh [args]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Resolve paths relative to this script's location (personas/)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

# Add personas/ to path for imports
sys.path.insert(0, str(SCRIPT_DIR))

from lib.ollama_client import ollama_chat
from lib.interactive import ask, ask_confirm
from models import DOMAIN_CHOICES, TEMPERATURES, MODEL_MATRIX

# Import detect function
from detect_persona import detect

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

DESIGNER_MODEL = "my-persona-designer-q3"

# JSON schema for structured output from the designer model
PERSONA_SPEC_SCHEMA = {
    "type": "object",
    "properties": {
        "persona_name": {"type": "string"},
        "domain": {"type": "string", "enum": DOMAIN_CHOICES},
        "language": {"type": "string"},
        "temperature": {"type": "number", "enum": [0.1, 0.3, 0.7]},
        "role": {"type": "string"},
        "constraints": {"type": "array", "items": {"type": "string"}},
        "output_format": {"type": "string"},
        "tier": {"type": "string", "enum": ["full", "bare"]},
    },
    "required": [
        "persona_name", "domain", "language", "temperature",
        "role", "constraints", "output_format", "tier",
    ],
}

# Temperature name lookup (reverse of TEMPERATURES)
TEMP_VALUE_TO_NAME = {
    data["value"]: name for name, data in TEMPERATURES.items()
}


# ──────────────────────────────────────────────────────────────────────────────
# Prompt construction
# ──────────────────────────────────────────────────────────────────────────────

def build_initial_prompt(description: str, detect_results: list | None = None) -> str:
    """
    Construct the prompt for the designer model's first pass.

    Args:
        description: User's free-form description of what they want.
        detect_results: Optional output from detect() (list of dicts).

    Returns:
        Prompt string for the LLM.
    """
    parts = []

    parts.append("You are designing an Ollama Modelfile persona. Analyze the requirements below and output a complete persona specification as JSON.\n")

    # Inject codebase context if available
    if detect_results:
        top = detect_results[0]
        parts.append("CODEBASE ANALYSIS (from file-based detection):")
        parts.append(f"  Top match: {top['persona_name']} (confidence: {top['confidence']})")
        parts.append(f"  Reason: {top['reason']}")
        if len(detect_results) > 1:
            alts = ", ".join(f"{r['persona_name']} ({r['confidence']})" for r in detect_results[1:])
            parts.append(f"  Alternatives: {alts}")
        parts.append("")

    parts.append(f"USER REQUEST: {description}")
    parts.append("")

    # Provide available options as context
    parts.append("AVAILABLE OPTIONS:")
    parts.append(f"  Domains: {', '.join(DOMAIN_CHOICES)}")
    parts.append(f"  Temperatures: 0.1 (deterministic), 0.3 (balanced), 0.7 (creative)")
    parts.append(f"  Tiers: full (standalone with SYSTEM prompt), bare (for external tools)")
    parts.append(f"  Name pattern: my-<slug>-q3 (e.g., my-java-q3, my-fastapi-q3)")
    parts.append("")

    parts.append("CONSTRAINT GUIDELINES:")
    parts.append("  - Each constraint MUST start with 'MUST' or 'MUST NOT'")
    parts.append("  - Target specific, observable failure modes (not vague goals)")
    parts.append("  - 4-7 constraints total (7-8B models follow fewer rules more reliably)")
    parts.append("  - Example good: 'MUST use jakarta.* namespace, NOT javax.*'")
    parts.append("  - Example bad: 'MUST write good code'")
    parts.append("")

    parts.append("Output a JSON object with these exact keys: persona_name, domain, language, temperature, role, constraints, output_format, tier.")

    return "\n".join(parts)


def build_refinement_prompt(original_spec: dict, feedback: str) -> str:
    """
    Construct the prompt for the refinement pass.

    Args:
        original_spec: The JSON spec from the first pass.
        feedback: User's free-form feedback on what to change.

    Returns:
        Prompt string for the LLM.
    """
    parts = []

    parts.append("You previously proposed this persona specification:")
    parts.append(json.dumps(original_spec, indent=2))
    parts.append("")
    parts.append(f"The user wants these changes: {feedback}")
    parts.append("")
    parts.append("Output the REVISED JSON specification with the same keys. Apply the requested changes while keeping everything else intact.")

    return "\n".join(parts)


# ──────────────────────────────────────────────────────────────────────────────
# LLM interaction
# ──────────────────────────────────────────────────────────────────────────────

def call_designer(prompt: str) -> dict:
    """
    Call my-persona-designer-q3 with structured output.

    Args:
        prompt: The constructed prompt.

    Returns:
        Parsed JSON dict from the LLM.

    Raises:
        RuntimeError: If LLM returns invalid JSON or connection fails.
    """
    try:
        response = ollama_chat(
            prompt,
            model=DESIGNER_MODEL,
            format_schema=PERSONA_SPEC_SCHEMA,
        )
    except (ConnectionError, TimeoutError, RuntimeError) as e:
        raise RuntimeError(f"LLM call failed: {e}") from e

    try:
        spec = json.loads(response["content"])
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"LLM returned invalid JSON: {e}\nRaw content: {response['content'][:500]}"
        ) from e

    return spec


# ──────────────────────────────────────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────────────────────────────────────

def validate_spec(spec: dict) -> list[str]:
    """
    Check that the LLM's proposed spec has valid values.

    Returns:
        List of error strings (empty = valid).
    """
    errors = []

    # Check required keys
    required = ["persona_name", "domain", "language", "temperature", "role", "constraints", "output_format", "tier"]
    for key in required:
        if key not in spec:
            errors.append(f"Missing key: {key}")

    if errors:
        return errors  # Can't validate further without keys

    # Domain
    if spec["domain"] not in DOMAIN_CHOICES:
        errors.append(f"Invalid domain '{spec['domain']}'. Must be one of: {', '.join(DOMAIN_CHOICES)}")

    # Temperature
    if spec["temperature"] not in (0.1, 0.3, 0.7):
        errors.append(f"Invalid temperature {spec['temperature']}. Must be 0.1, 0.3, or 0.7")

    # Name pattern
    name = spec.get("persona_name", "")
    if not name.startswith("my-"):
        errors.append(f"Persona name '{name}' must start with 'my-'")

    # Constraints
    constraints = spec.get("constraints", [])
    if not isinstance(constraints, list):
        errors.append("constraints must be an array")
    elif len(constraints) == 0:
        errors.append("Must have at least one constraint")
    elif len(constraints) > 8:
        errors.append(f"Too many constraints ({len(constraints)}). Max 8 for 7-8B reliability.")

    # Tier
    if spec.get("tier") not in ("full", "bare"):
        errors.append(f"Invalid tier '{spec.get('tier')}'. Must be 'full' or 'bare'")

    return errors


# ──────────────────────────────────────────────────────────────────────────────
# Display
# ──────────────────────────────────────────────────────────────────────────────

def display_proposal(spec: dict) -> None:
    """Pretty-print the proposed persona spec for user review."""
    print("\n━━━ Proposed Persona ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Name:        {spec.get('persona_name', '?')}")
    print(f"  Domain:      {spec.get('domain', '?')}")
    print(f"  Language:    {spec.get('language', '?')}")
    temp = spec.get('temperature', '?')
    temp_name = TEMP_VALUE_TO_NAME.get(temp, '?')
    print(f"  Temperature: {temp} ({temp_name})")
    print(f"  Tier:        {spec.get('tier', '?')}")
    print(f"  Role:        {spec.get('role', '?')}")
    print(f"  Format:      {spec.get('output_format', '?')}")
    print("  Constraints:")
    for i, c in enumerate(spec.get("constraints", []), 1):
        print(f"    {i}. {c}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


# ──────────────────────────────────────────────────────────────────────────────
# Handoff to create-persona.py
# ──────────────────────────────────────────────────────────────────────────────

def build_creator_command(spec: dict, dry_run: bool = False) -> list[str]:
    """
    Convert the LLM's spec dict into create-persona.py --non-interactive flags.

    Args:
        spec: Validated persona specification dict.
        dry_run: If True, add --dry-run flag.

    Returns:
        List of command arguments.
    """
    creator = str(SCRIPT_DIR / "run-create-persona.sh")

    temp_name = TEMP_VALUE_TO_NAME.get(spec["temperature"], "balanced")

    cmd = [
        creator,
        "--non-interactive",
        "--role", spec["role"],
        "--domain", spec["domain"],
        "--name", spec["persona_name"],
        "--temperature", temp_name,
        "--tier", spec.get("tier", "full"),
        "--output-format", spec["output_format"],
        "--constraints", ",".join(spec["constraints"]),
    ]

    if spec.get("language"):
        cmd.extend(["--language", spec["language"]])

    if dry_run:
        cmd.append("--dry-run")

    return cmd


def handoff_to_creator(spec: dict, dry_run: bool = False) -> int:
    """
    Run create-persona.py --non-interactive with the spec.

    Returns:
        Exit code from the creator script.
    """
    cmd = build_creator_command(spec, dry_run=dry_run)
    print(f"\n[HANDOFF] {' '.join(cmd[:4])} ...")
    result = subprocess.run(cmd)
    return result.returncode


# ──────────────────────────────────────────────────────────────────────────────
# Main flow
# ──────────────────────────────────────────────────────────────────────────────

def run(description: str, codebase_path: str | None = None,
        dry_run: bool = False, json_only: bool = False,
        skip_refinement: bool = False) -> int:
    """
    Main entry point for the conversational builder flow.

    Args:
        description: User's free-form persona description.
        codebase_path: Optional path to scan with detect().
        dry_run: If True, don't write files (preview only).
        json_only: If True, output raw JSON and exit (for testing).
        skip_refinement: If True, skip the refinement pass.

    Returns:
        Exit code (0 = success).
    """
    # Step 1: Codebase detection (optional)
    detect_results = None
    if codebase_path:
        print(f"[DETECT] Scanning {codebase_path}...")
        try:
            detect_results = detect(codebase_path)
            top = detect_results[0]
            print(f"[DETECT] Top match: {top['persona_name']} (confidence: {top['confidence']})")
        except Exception as e:
            print(f"[DETECT] Warning: detection failed ({e}), continuing without codebase context")
            detect_results = None

    # Step 2: Initial LLM call
    print("[LLM] Generating persona proposal...")
    prompt = build_initial_prompt(description, detect_results)

    try:
        spec = call_designer(prompt)
    except RuntimeError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    # Step 3: Validate
    errors = validate_spec(spec)
    if errors:
        print("[WARN] LLM produced spec with issues:")
        for err in errors:
            print(f"  - {err}")
        print("[WARN] Proceeding with best-effort values.")

    # json_only mode: output and exit (for testing)
    if json_only:
        print(json.dumps(spec, indent=2))
        return 0

    # Step 4: Display proposal
    display_proposal(spec)

    # Step 5: Refinement pass (optional)
    if not skip_refinement:
        wants_changes = ask_confirm("\nWant to refine this proposal?", default=False)
        if wants_changes:
            feedback = ask("What would you like to change?")
            print("[LLM] Refining proposal...")
            refine_prompt = build_refinement_prompt(spec, feedback)
            try:
                spec = call_designer(refine_prompt)
            except RuntimeError as e:
                print(f"[ERROR] Refinement failed: {e}", file=sys.stderr)
                print("        Using original proposal.")

            errors = validate_spec(spec)
            if errors:
                print("[WARN] Refined spec has issues:")
                for err in errors:
                    print(f"  - {err}")

            display_proposal(spec)

    # Step 6: Confirm and hand off
    if not dry_run:
        proceed = ask_confirm("\nCreate this persona?", default=True)
        if not proceed:
            print("Aborted.")
            return 0

    return handoff_to_creator(spec, dry_run=dry_run)


def parse_args():
    p = argparse.ArgumentParser(
        description="LLM-driven persona builder. Uses AI to propose a complete persona from your description.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  personas/run-build-persona.sh --describe 'Java Spring Boot microservice dev'\n"
               "  personas/run-build-persona.sh --describe 'Go developer' --codebase /path/to/repo\n"
               "  personas/run-build-persona.sh --describe 'Python FastAPI dev' --dry-run\n"
               "  personas/run-build-persona.sh  # interactive (asks for description)\n",
    )
    p.add_argument("--describe", metavar="TEXT",
                   help="Free-form description of the persona you want.")
    p.add_argument("--codebase", metavar="PATH",
                   help="Path to a codebase to analyze for language/framework hints.")
    p.add_argument("--dry-run", action="store_true",
                   help="Preview the generated persona without writing files.")
    p.add_argument("--json-only", action="store_true",
                   help="Output raw JSON proposal and exit (for testing/piping).")
    p.add_argument("--skip-refinement", action="store_true",
                   help="Skip the refinement feedback step.")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # Interactive mode: ask for description if not provided
    description = args.describe
    if not description:
        print("\n━━━ Persona Builder ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("Describe the persona you want in plain language.")
        print("Examples:")
        print("  'Java Spring Boot microservice developer with strict Jakarta EE'")
        print("  'Python data scientist for pandas and sklearn workflows'")
        print("  'Go gRPC service developer for Kubernetes'")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        description = ask("Describe the persona you want")

    return run(
        description=description,
        codebase_path=args.codebase,
        dry_run=args.dry_run,
        json_only=args.json_only,
        skip_refinement=args.skip_refinement,
    )


if __name__ == "__main__":
    sys.exit(main())
```

**Step 4: Run test to verify it passes**

Run: `bash benchmarks/test-build-persona.sh`
Expected: 3/3 passed (requires live Ollama + `my-persona-designer-q3`)

Note: If the LLM's JSON is structurally valid but has unexpected values (e.g., a creative persona name), the test may still pass because we check for patterns, not exact values. This is intentional — the LLM has creative latitude within the schema constraints.

**Step 5: Commit**

```bash
git add personas/build-persona.py benchmarks/test-build-persona.sh
git commit -m "feat: add LLM-driven persona builder (build-persona.py)"
```

---

## Task 4: Create the bash wrapper and wire up the full pipeline

**Files:**
- Create: `personas/run-build-persona.sh`

**Step 1: Write the wrapper**

Create `personas/run-build-persona.sh`:

```bash
#!/usr/bin/env bash
# run-build-persona.sh — LLM-driven persona builder.
#
# Security rationale: This wrapper is safe to whitelist in Claude Code's
# "don't ask again" prompts. Whitelisting the bare `python3` command would
# grant permission for ALL Python scripts; this wrapper limits scope.
#
# Usage:
#   personas/run-build-persona.sh --describe "Java Spring Boot developer"
#   personas/run-build-persona.sh --describe "Go dev" --codebase /path/to/repo
#   personas/run-build-persona.sh --dry-run --describe "Python FastAPI dev"
#   personas/run-build-persona.sh  # interactive mode

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Non-interactive WSL shells (spawned by Claude Desktop, cron, etc.) do not
# source ~/.bashrc, so ~/.local/bin (uv, etc.) won't be on PATH.
export PATH="$HOME/.local/bin:$PATH"

exec python3 "$SCRIPT_DIR/build-persona.py" "$@"
```

**Step 2: Make it executable**

Run: `chmod +x personas/run-build-persona.sh`

**Step 3: End-to-end dry-run test**

Run the full pipeline in dry-run mode:

```bash
personas/run-build-persona.sh --describe "Rust systems programmer for async Tokio services" --dry-run --skip-refinement
```

Expected output pattern:
```
[LLM] Generating persona proposal...
━━━ Proposed Persona ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Name:        my-rust-q3
  Domain:      code
  ...
[HANDOFF] personas/run-create-persona.sh --non-interactive ...
[DRY-RUN] Would write: ...
[DRY-RUN] Would register: my-rust-q3
```

**Step 4: End-to-end dry-run with codebase detection**

```bash
personas/run-build-persona.sh --describe "backend developer for this project" --codebase benchmarks/test-fixtures/java-backend --dry-run --skip-refinement
```

Expected: The `[DETECT]` line shows `my-java-q3`, and the proposal reflects Java/Spring Boot.

**Step 5: Commit**

```bash
git add personas/run-build-persona.sh
git commit -m "feat: add bash wrapper for LLM-driven persona builder"
```

---

## Task 5: Integration verification and documentation

**Files:**
- Modify: `personas/DETECT-PERSONA.md` (or create `personas/BUILD-PERSONA.md`)
- Modify: `.claude/tasks.md` (mark 3.5 complete)
- Modify: `.claude/session-context.md` (update status)

**Step 1: Run the full test suite**

Run all tests to ensure nothing broke:

```bash
bash benchmarks/test-detect.sh && echo "--- detect: OK ---"
bash benchmarks/test-ollama-client.sh && echo "--- ollama-client: OK ---"
bash benchmarks/test-build-persona.sh && echo "--- build-persona: OK ---"
```

Expected: All tests pass.

**Step 2: End-to-end live test (actually creates a persona)**

Pick a persona that doesn't exist yet (e.g., a Rust persona) and run the builder for real:

```bash
personas/run-build-persona.sh --describe "Rust async systems programmer using Tokio and Axum" --skip-refinement
```

Expected: Creates the Modelfile, registers with Ollama, appends to registry.yaml.

Verify:
```bash
ollama list | grep rust
grep "my-rust" personas/registry.yaml
```

**Step 3: Test the refinement flow**

Run interactively (or with --describe but without --skip-refinement) and exercise the refinement:

```bash
personas/run-build-persona.sh --describe "generic backend developer" --dry-run
# When prompted "Want to refine?" → yes
# Type: "Make it specific to Node.js Express with TypeScript"
# Verify the refined proposal reflects Express/TypeScript
```

**Step 4: Write documentation**

Create `personas/BUILD-PERSONA.md`:

Contents should cover:
- What the builder does (LLM-driven vs the form-filling `create-persona.py`)
- Usage examples (interactive, non-interactive, with codebase, dry-run)
- Architecture diagram: user → build-persona.py → [detect() + LLM] → create-persona.py
- How the designer model works (system prompt, structured output schema)
- Known limitations (8B quality ceiling, no multi-round yet)
- Future: multi-round option 3, qwen3:14b testing

**Step 5: Clean up the test persona**

If a test persona was created (e.g., `my-rust-q3`), either keep it or remove it:

```bash
# To remove:
ollama rm my-rust-q3
# And remove the last entry from personas/registry.yaml
```

**Step 6: Update tracking files**

Update `.claude/tasks.md`: Mark Task 3.5 as complete.
Update `.claude/session-context.md`: Update Layer 3 status.

**Step 7: Commit**

```bash
git add personas/BUILD-PERSONA.md .claude/tasks.md .claude/session-context.md
git commit -m "docs: add BUILD-PERSONA.md and mark Task 3.5 complete"
```

---

## Summary

| Task | What | Files | Commit |
|------|------|-------|--------|
| 1 | Designer persona | `modelfiles/persona-designer-qwen3.Modelfile`, `registry.yaml` | `feat: add my-persona-designer-q3` |
| 2 | Sync Ollama client | `personas/lib/ollama_client.py`, test | `feat: add synchronous Ollama client` |
| 3 | Core builder script | `personas/build-persona.py`, test | `feat: add LLM-driven persona builder` |
| 4 | Bash wrapper + e2e | `personas/run-build-persona.sh` | `feat: add bash wrapper` |
| 5 | Verification + docs | `BUILD-PERSONA.md`, tracking files | `docs: mark Task 3.5 complete` |

**Estimated total: 5 tasks, each with clear test-before-implement steps.**
