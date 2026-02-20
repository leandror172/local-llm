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

# Import detect function from detect-persona.py (hyphenated filename → importlib)
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("detect_persona", SCRIPT_DIR / "detect-persona.py")
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
detect = _mod.detect

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

def call_designer(prompt: str, model: str = DESIGNER_MODEL, verbose: bool = False) -> dict:
    """
    Call the designer model with structured output.

    Args:
        prompt: The constructed prompt.
        model: Ollama model name to use (default: DESIGNER_MODEL).
        verbose: If True, print prompt and raw response to stderr.

    Returns:
        Parsed JSON dict from the LLM.

    Raises:
        RuntimeError: If LLM returns invalid JSON or connection fails.
    """
    if verbose:
        print(f"\n[VERBOSE] Prompt ({len(prompt)} chars):\n{prompt}\n", file=sys.stderr)

    try:
        response = ollama_chat(
            prompt,
            model=model,
            format_schema=PERSONA_SPEC_SCHEMA,
        )
    except (ConnectionError, TimeoutError, RuntimeError) as e:
        raise RuntimeError(f"LLM call failed: {e}") from e

    if verbose:
        print(f"[VERBOSE] Raw response:\n{response['content']}\n", file=sys.stderr)

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
        "--constraints", ",".join(c.replace(",", ";") for c in spec["constraints"]),
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
        skip_refinement: bool = False, designer_model: str = DESIGNER_MODEL,
        verbose: bool = False) -> int:
    """
    Main entry point for the conversational builder flow.

    Args:
        description: User's free-form persona description.
        codebase_path: Optional path to scan with detect().
        dry_run: If True, don't write files (preview only).
        json_only: If True, output raw JSON and exit (for testing).
        skip_refinement: If True, skip the refinement feedback step.
        designer_model: Ollama model to use as the persona designer.
        verbose: If True, print prompts and raw responses to stderr.

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
    print(f"[LLM] Generating persona proposal (model: {designer_model})...")
    prompt = build_initial_prompt(description, detect_results)

    try:
        spec = call_designer(prompt, model=designer_model, verbose=verbose)
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
                spec = call_designer(refine_prompt, model=designer_model, verbose=verbose)
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
    p.add_argument("--designer-model", metavar="MODEL", default=DESIGNER_MODEL,
                   help=f"Ollama model to use as persona designer (default: {DESIGNER_MODEL}).")
    p.add_argument("--verbose", action="store_true",
                   help="Print prompts and raw LLM responses to stderr (useful for debugging).")
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
        designer_model=args.designer_model,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    sys.exit(main())
