#!/usr/bin/env python3
"""
create-persona.py — Conversational Ollama persona creator.

Walks you through the persona-template.md checklist interactively, then:
  1. Generates a Modelfile following the project's exact template
  2. Registers it with Ollama via `ollama create`
  3. Appends the entry to personas/registry.yaml

Usage (interactive):
  python3 personas/create-persona.py

Usage (non-interactive / scripting):
  python3 personas/create-persona.py --non-interactive \\
    --role "React 18+ TypeScript developer" \\
    --domain code --language react \\
    --name my-react-q3 [--dry-run]

Safer to invoke via the bash wrapper (whitelist-safe):
  personas/run-create-persona.sh [args]
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Import centralized model configuration (Task 3.4 refactoring)
from models import (
    MODEL_MATRIX,
    DOMAIN_CHOICES,
    TEMPERATURES,
    TEMPERATURE_MAP,
    TEMP_CATEGORY_TO_CHOICE,
    TEMP_DESCRIPTIONS,
    MODEL_TAG_TO_SUFFIX,
    MODEL_TAG_TO_Q_SUFFIX,
    get_model,
    get_temperature_value,
    get_temperature_description,
    get_modelfile_suffix,
    get_persona_name_suffix,
)

# Import reusable interactive helpers (Task 3.4 refactoring)
from lib.interactive import ask, ask_choice, ask_multiline, ask_confirm

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────

# Resolve REPO_ROOT relative to this script's location (personas/)
REPO_ROOT = Path(__file__).resolve().parent.parent
MODELFILES_DIR = REPO_ROOT / "modelfiles"
REGISTRY_PATH = REPO_ROOT / "personas" / "registry.yaml"

# ──────────────────────────────────────────────────────────────────────────────
# Domain defaults
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_CONSTRAINTS = {
    "code": [
        "MUST output complete, runnable code — never pseudocode or TODOs",
        "MUST follow idiomatic style and best-practice conventions",
        "MUST include error handling for all failure paths",
        "MUST NOT add explanatory text unless the user explicitly asks",
        "MUST NOT invent import paths or library names that do not exist",
    ],
    "reasoning": [
        "MUST show reasoning steps before conclusions",
        "MUST cite trade-offs for each option",
        "MUST flag assumptions explicitly",
        "MUST NOT recommend without explaining why",
    ],
    "classification": [
        "MUST select exactly one category from the provided list",
        "MUST provide a confidence score between 0.0 and 1.0",
        "MUST output valid JSON matching the requested schema",
        "MUST NOT output any text before or after the JSON object",
        "MUST NOT invent categories not in the provided list",
    ],
    "writing": [
        "MUST use active voice and direct language",
        "MUST use short paragraphs (3-4 sentences max)",
        "MUST NOT use filler phrases (e.g., 'It is important to note')",
        "MUST NOT use marketing language (e.g., 'powerful', 'seamless', 'robust')",
    ],
    "translation": [
        "MUST output only the translated text — no preamble or notes",
        "MUST use idiomatic expressions in the target language",
        "MUST maintain the original formatting",
        "MUST NOT translate proper nouns unless standard translations exist",
        "MUST NOT add translator notes or explanations",
    ],
    "other": [
        "MUST respond only within the defined role scope",
        "MUST be concise and direct",
        "MUST NOT add unrequested information",
    ],
}

DEFAULT_FORMATS = {
    "code":           "One fenced code block per file with language tag. If multiple files, label each with its path.",
    "reasoning":      "Structured analysis: problem statement → options → trade-offs → recommendation.",
    "classification": "A single JSON object with keys: category, confidence, reasoning.",
    "writing":        "GitHub-flavored Markdown with headers and code fences where appropriate.",
    "translation":    "Plain translated text only, preserving the original structure.",
    "other":          "Plain text output.",
}

# ──────────────────────────────────────────────────────────────────────────────
# Input helpers
# ──────────────────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────────────────
# Business logic
# ──────────────────────────────────────────────────────────────────────────────

def select_model(domain: str) -> tuple[str, str, int]:
    """Return (display_name, ollama_tag, num_ctx) for a domain."""
    display, tag, ctx, _ = MODEL_MATRIX[domain]
    return display, tag, ctx


def persona_name_to_filename(persona_name: str, base_tag: str) -> str:
    """
    Convert a persona name to its Modelfile filename (without .Modelfile extension).
    my-java-q3  + qwen3:8b  → java-qwen3
    my-go-q3    + qwen3:8b  → go-qwen3
    my-writer   + llama3.1  → writer-llama31
    """
    # Strip leading "my-"
    slug = persona_name.removeprefix("my-")
    # Strip trailing q-suffix (-q3, etc.)
    for q in ("-q3", "-q4", "-q8"):
        if slug.endswith(q):
            slug = slug[: -len(q)]
            break
    suffix = MODEL_TAG_TO_SUFFIX.get(base_tag, "qwen3")
    return f"{slug}-{suffix}"


def suggest_persona_name(role: str, domain: str, language: str | None, base_tag: str) -> str:
    """
    Derive a suggested persona name from role + model family.
    Priority: explicit language arg > first meaningful words of role.
    """
    if language:
        slug = language.lower().strip()
    else:
        words = re.findall(r"[a-zA-Z]+", role)
        fillers = {"developer", "specialist", "assistant", "generator", "expert",
                   "engineer", "backend", "frontend", "senior", "junior", "the", "a", "an"}
        words = [w.lower() for w in words if w.lower() not in fillers]
        slug = "-".join(words[:2]) if words else "custom"

    slug = re.sub(r"[^a-z0-9-]", "-", slug).strip("-")
    slug = re.sub(r"-+", "-", slug)
    q_suffix = MODEL_TAG_TO_Q_SUFFIX.get(base_tag, "-q3")
    return f"my-{slug}{q_suffix}"


def validate_persona_name(name: str, registry_path: Path) -> tuple[bool, str]:
    """
    Check that name matches pattern and is not already registered.
    Returns (is_valid, error_message).
    """
    if not re.fullmatch(r"my-[a-z0-9][a-z0-9-]*", name):
        return False, f"Name '{name}' must match pattern: my-[a-z0-9-]+"
    # Grep-style check — avoids YAML parse (which strips comments)
    if registry_path.exists():
        content = registry_path.read_text()
        # Look for the name as a top-level YAML key (starts at column 0, followed by colon)
        if re.search(rf"^{re.escape(name)}:", content, re.MULTILINE):
            return False, f"Persona '{name}' already exists in registry.yaml"
    return True, ""


# ──────────────────────────────────────────────────────────────────────────────
# Modelfile generation
# ──────────────────────────────────────────────────────────────────────────────

def _ctx_comment(num_ctx: int) -> str:
    if num_ctx == 16384:
        return "16K tokens — fits full files with room for response."
    return "4K tokens — reduced for 14B model VRAM budget (RTX 3060 12GB)."


def _temp_comment(temperature: float) -> str:
    """Get human-readable temperature comment from consolidated TEMPERATURES config."""
    # Find temperature by value
    for temp_name, temp_data in TEMPERATURES.items():
        if temp_data["value"] == temperature:
            # Return descriptive comment (extracted from description)
            desc = temp_data["description"]
            # Remove the numeric prefix (e.g., "0.1 — ") to get the comment part
            return desc.split(" — ", 1)[1] if " — " in desc else desc
    # Fallback
    return f"Temperature {temperature}"


def _normalize_constraint(c: str) -> str:
    """Ensure constraint starts with MUST or MUST NOT."""
    c = c.strip().lstrip("- ").strip()
    if not c.upper().startswith("MUST"):
        c = "MUST " + c
    return c


def build_system_prompt(role: str, constraints: list[str], output_format: str) -> str:
    """Assemble ROLE / CONSTRAINTS / FORMAT system prompt."""
    parts = [f"ROLE: {role}."]
    parts.append("CONSTRAINTS:")
    for c in constraints:
        parts.append(f"- {_normalize_constraint(c)}")
    parts.append(f"FORMAT: {output_format}")
    return "\n".join(parts)


def generate_modelfile(
    base_tag: str,
    num_ctx: int,
    temperature: float,
    role: str,
    constraints: list[str],
    output_format: str,
    tier: str,
) -> str:
    """Render the Modelfile following the project's exact template pattern."""
    ctx_cmt = _ctx_comment(num_ctx)
    temp_cmt = _temp_comment(temperature)

    if tier == "bare":
        # Bare personas: no SYSTEM, minimal params (like aider-qwen25.Modelfile)
        role_short = role.split(".")[0][:60]
        return (
            f"# Lightweight persona — parameters only, NO system prompt.\n"
            f"# The host tool injects its own system prompt; a Modelfile SYSTEM would conflict.\n"
            f"FROM {base_tag}\n"
            f"PARAMETER temperature {temperature}\n"
            f"PARAMETER num_ctx {num_ctx}\n"
            f'PARAMETER stop "<|endoftext|>"\n'
        )

    # Full persona (like java-qwen3.Modelfile)
    system_prompt = build_system_prompt(role, constraints, output_format)
    role_short = role.split(".")[0][:60]

    lines = [
        f"FROM {base_tag}",
        "",
        f"# Context window: {ctx_cmt}",
        f"PARAMETER num_ctx {num_ctx}",
        "",
        f"# Temperature: {temperature} — {temp_cmt}",
        f"PARAMETER temperature {temperature}",
        "",
        "# Standard sampling parameters (invariants across all full personas).",
        "PARAMETER top_p 0.9",
        "PARAMETER repeat_penalty 1.1",
        "",
        "# Stop sequences: Qwen3 ChatML end markers.",
        'PARAMETER stop "<|im_end|>"',
        'PARAMETER stop "<|endoftext|>"',
        "",
        f"# System prompt: {role_short}.",
        "# Constraints target observed failure modes for this domain.",
        f'SYSTEM """{system_prompt}"""',
    ]
    return "\n".join(lines) + "\n"


# ──────────────────────────────────────────────────────────────────────────────
# Registry operations
# ──────────────────────────────────────────────────────────────────────────────

def generate_registry_entry(
    persona_name: str,
    modelfile_filename: str,
    base_tag: str,
    role: str,
    temperature: float,
    num_ctx: int,
    tier: str,
) -> str:
    """Return raw YAML text block for the new registry entry."""
    lines = [
        "",
        f"{persona_name}:",
        f"  modelfile: modelfiles/{modelfile_filename}.Modelfile",
        f"  base_model: {base_tag}",
        f"  role: {role}",
        f"  temperature: {temperature}",
        f"  num_ctx: {num_ctx}",
        f"  tier: {tier}",
        "  status: active",
    ]
    return "\n".join(lines) + "\n"


def append_registry(registry_path: Path, entry_text: str) -> None:
    """Append raw YAML entry to the registry file, preserving all comments."""
    with registry_path.open("a") as f:
        f.write(entry_text)


# ──────────────────────────────────────────────────────────────────────────────
# Ollama registration
# ──────────────────────────────────────────────────────────────────────────────

def register_with_ollama(persona_name: str, modelfile_path: Path) -> bool:
    """
    Run: ollama create <persona_name> -f <modelfile_path>
    Streams stdout/stderr to terminal for progress visibility.
    Returns True on success.
    """
    cmd = ["ollama", "create", persona_name, "-f", str(modelfile_path)]
    print(f"\n[RUN] {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode == 0


# ──────────────────────────────────────────────────────────────────────────────
# Interactive flow
# ──────────────────────────────────────────────────────────────────────────────

def collect_interactive() -> dict:
    """8-step Q&A flow. Returns a config dict."""
    print("\n━━━ Persona Creator ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Walks through persona-template.md to create a new Ollama persona.")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    # Q1: Role
    print("Step 1/8 — Role")
    role = ask("What is this persona's role?  (e.g., 'Go 1.22+ backend developer')")

    # Q2: Domain → model selection
    print("\nStep 2/8 — Domain")
    domain = ask_choice("What domain best describes this persona?", DOMAIN_CHOICES, default="code")

    _, base_tag, num_ctx = select_model(domain)
    display_name = MODEL_MATRIX[domain][0]
    print(f"  → Selected model: {display_name} ({base_tag}), {num_ctx} ctx tokens")

    # Q3: Language/framework (code domain only)
    language = None
    if domain == "code":
        print("\nStep 3/8 — Language / framework")
        raw = ask("Language or framework?  (e.g., react, java, go, python — leave blank to skip)", default="")
        language = raw if raw else None
    else:
        print("\nStep 3/8 — Language / framework  [skipped — not code domain]")

    # Q4: Temperature
    print("\nStep 4/8 — Temperature")
    suggested = TEMP_CATEGORY_TO_CHOICE[MODEL_MATRIX[domain][3]]
    temp_choices = list(TEMPERATURE_MAP.keys())
    print("  Options:")
    for tc in temp_choices:
        print(f"    {tc}: {TEMP_DESCRIPTIONS[tc]}")
    temp_choice = ask_choice(
        f"Temperature preference?  (suggested for '{domain}': {suggested})",
        temp_choices,
        default=suggested,
    )
    temperature = TEMPERATURE_MAP[temp_choice]

    # Q5: Persona name
    print("\nStep 5/8 — Persona name")
    suggestion = suggest_persona_name(role, domain, language, base_tag)
    while True:
        persona_name = ask("Persona name?", default=suggestion)
        valid, error = validate_persona_name(persona_name, REGISTRY_PATH)
        if valid:
            break
        print(f"  [!] {error}")

    modelfile_filename = persona_name_to_filename(persona_name, base_tag)
    print(f"  → Modelfile will be: modelfiles/{modelfile_filename}.Modelfile")

    # Q6: Constraints
    print("\nStep 6/8 — Constraints")
    defaults = DEFAULT_CONSTRAINTS.get(domain, DEFAULT_CONSTRAINTS["other"])
    # Substitute {language} placeholder if applicable
    if language:
        defaults = [c.replace("{language}", language) for c in defaults]
    print("  Default constraints for this domain:")
    for i, c in enumerate(defaults, 1):
        print(f"    {i}. {c}")
    use_defaults = ask_confirm("\n  Use these defaults?", default=True)
    constraints = list(defaults) if use_defaults else []

    extra = ask_multiline("\n  Add extra constraints? (MUST / MUST NOT rules)")
    constraints.extend(extra)

    if len(constraints) > 8:
        print(f"  [!] {len(constraints)} constraints — recommend ≤8 for 7-8B model reliability.")

    # Q7: Output format
    print("\nStep 7/8 — Output format")
    default_fmt = DEFAULT_FORMATS.get(domain, "Plain text output.")
    output_format = ask("What should the persona output?", default=default_fmt)

    # Q8: Tier
    print("\nStep 8/8 — Tier")
    print("  full: standalone persona with SYSTEM prompt (most common)")
    print("  bare: minimal config for external tools (Aider, OpenCode) that inject their own prompt")
    tier = ask_choice("Tier?", ["full", "bare"], default="full")

    return {
        "role":              role,
        "domain":            domain,
        "language":          language,
        "temp_choice":       temp_choice,
        "temperature":       temperature,
        "persona_name":      persona_name,
        "modelfile_filename": modelfile_filename,
        "base_tag":          base_tag,
        "num_ctx":           num_ctx,
        "constraints":       constraints,
        "output_format":     output_format,
        "tier":              tier,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Non-interactive mode
# ──────────────────────────────────────────────────────────────────────────────

def collect_from_flags(args) -> dict:
    """Build and validate config dict from CLI flags."""
    errors = []

    if not args.role:
        errors.append("--role is required in non-interactive mode")

    domain = args.domain or "code"
    if domain not in DOMAIN_CHOICES:
        errors.append(f"--domain must be one of: {', '.join(DOMAIN_CHOICES)}")

    temp_choice = args.temperature
    if temp_choice and temp_choice not in TEMPERATURE_MAP:
        errors.append(f"--temperature must be one of: {', '.join(TEMPERATURE_MAP)}")

    if errors:
        for e in errors:
            print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(2)

    _, base_tag, num_ctx = select_model(domain)
    language = args.language or None

    if not temp_choice:
        temp_choice = TEMP_CATEGORY_TO_CHOICE[MODEL_MATRIX[domain][3]]
    temperature = TEMPERATURE_MAP[temp_choice]

    # Name
    if args.name:
        persona_name = args.name
    else:
        persona_name = suggest_persona_name(args.role, domain, language, base_tag)

    valid, error = validate_persona_name(persona_name, REGISTRY_PATH)
    if not valid:
        print(f"[ERROR] {error}", file=sys.stderr)
        sys.exit(2)

    modelfile_filename = persona_name_to_filename(persona_name, base_tag)

    # Constraints
    defaults = DEFAULT_CONSTRAINTS.get(domain, DEFAULT_CONSTRAINTS["other"])
    if language:
        defaults = [c.replace("{language}", language) for c in defaults]
    if args.constraints:
        constraints = [c.strip() for c in args.constraints.split(",") if c.strip()]
    else:
        constraints = list(defaults)

    output_format = args.output_format or DEFAULT_FORMATS.get(domain, "Plain text output.")
    tier = args.tier or "full"

    return {
        "role":               args.role,
        "domain":             domain,
        "language":           language,
        "temp_choice":        temp_choice,
        "temperature":        temperature,
        "persona_name":       persona_name,
        "modelfile_filename": modelfile_filename,
        "base_tag":           base_tag,
        "num_ctx":            num_ctx,
        "constraints":        constraints,
        "output_format":      output_format,
        "tier":               tier,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Preview and execution
# ──────────────────────────────────────────────────────────────────────────────

def preview_and_confirm(config: dict, modelfile_content: str, registry_entry: str) -> bool:
    """Print generated Modelfile and registry entry, ask for confirmation."""
    print("\n━━━ Generated Modelfile ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(modelfile_content)
    print("━━━ Registry Entry ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(registry_entry)
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    return ask_confirm("\nProceed? (write Modelfile → ollama create → update registry)", default=True)


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Interactively create a new Ollama Modelfile persona.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--non-interactive", action="store_true",
                   help="Skip interactive prompts; use flags below.")
    p.add_argument("--role", metavar="TEXT",
                   help="One-line role description (required in non-interactive mode).")
    p.add_argument("--domain", choices=DOMAIN_CHOICES, metavar="DOMAIN",
                   help=f"Domain: {', '.join(DOMAIN_CHOICES)}.")
    p.add_argument("--language", metavar="TEXT",
                   help="Language or framework (for code domain; drives naming).")
    p.add_argument("--temperature", choices=list(TEMPERATURE_MAP), metavar="CHOICE",
                   help="deterministic | balanced | creative.")
    p.add_argument("--name", metavar="TEXT",
                   help="Persona name (e.g., my-react-q3). Auto-suggested if omitted.")
    p.add_argument("--constraints", metavar="TEXT",
                   help="Comma-separated constraint list. Defaults to domain defaults if omitted.")
    p.add_argument("--output-format", metavar="TEXT",
                   help="FORMAT line for the SYSTEM prompt.")
    p.add_argument("--tier", choices=["full", "bare"],
                   help="full (default) or bare (no SYSTEM prompt).")
    p.add_argument("--dry-run", action="store_true",
                   help="Print Modelfile + registry entry without writing any files.")
    p.add_argument("--force", action="store_true",
                   help="Overwrite existing Modelfile if it already exists.")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # Verify ollama is available
    probe = subprocess.run(["ollama", "--version"], capture_output=True)
    if probe.returncode != 0:
        print("[ERROR] 'ollama' not found. Is Ollama running?", file=sys.stderr)
        return 1

    # Collect config
    if args.non_interactive:
        config = collect_from_flags(args)
    else:
        config = collect_interactive()

    persona_name      = config["persona_name"]
    modelfile_filename = config["modelfile_filename"]
    base_tag          = config["base_tag"]
    num_ctx           = config["num_ctx"]
    temperature       = config["temperature"]
    tier              = config["tier"]

    modelfile_path = MODELFILES_DIR / f"{modelfile_filename}.Modelfile"

    # Generate content
    modelfile_content = generate_modelfile(
        base_tag=base_tag,
        num_ctx=num_ctx,
        temperature=temperature,
        role=config["role"],
        constraints=config["constraints"],
        output_format=config["output_format"],
        tier=tier,
    )
    registry_entry = generate_registry_entry(
        persona_name=persona_name,
        modelfile_filename=modelfile_filename,
        base_tag=base_tag,
        role=config["role"],
        temperature=temperature,
        num_ctx=num_ctx,
        tier=tier,
    )

    # Dry-run: print and exit
    if args.dry_run:
        print(f"\n[DRY-RUN] Would write: {modelfile_path}")
        print(f"[DRY-RUN] Would register: {persona_name}")
        print(f"[DRY-RUN] Would append to: {REGISTRY_PATH}\n")
        print("━━━ Modelfile ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(modelfile_content)
        print("━━━ Registry Entry ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(registry_entry)
        return 0

    # Interactive: show preview and confirm
    if not args.non_interactive:
        if not preview_and_confirm(config, modelfile_content, registry_entry):
            print("Aborted.")
            return 0

    # Safety check: don't overwrite existing Modelfile
    if modelfile_path.exists() and not args.force:
        print(f"[ERROR] Modelfile already exists: {modelfile_path}")
        print("        Use --force to overwrite, or choose a different name.")
        return 1

    # Write Modelfile
    modelfile_path.write_text(modelfile_content)
    print(f"[OK] Modelfile written: {modelfile_path}")

    # Register with Ollama
    success = register_with_ollama(persona_name, modelfile_path)
    if not success:
        print(f"\n[ERROR] 'ollama create' failed. Modelfile kept at: {modelfile_path}")
        print("        Registry NOT updated. Fix the Modelfile and re-run:")
        print(f"        ollama create {persona_name} -f {modelfile_path}")
        return 1

    # Append to registry
    if not REGISTRY_PATH.exists():
        print(f"[ERROR] Registry not found: {REGISTRY_PATH}")
        print("        Modelfile registered with Ollama.")
        print("        Add this entry manually to personas/registry.yaml:")
        print(registry_entry)
        return 1

    append_registry(REGISTRY_PATH, registry_entry)
    print(f"[OK] Registry updated: {REGISTRY_PATH}")

    print(f"\n✓ Persona ready: {persona_name}")
    print(f"  Test with: ollama run {persona_name} \"<your prompt>\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
