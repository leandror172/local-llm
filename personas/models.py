#!/usr/bin/env python3
"""
models.py — Centralized model selection and configuration.

Loads all model data from models.yaml (single source of truth).
Provides lookup functions and derived constants for:
  - personas/create-persona.py (interactive persona creator)
  - personas/build-persona.py (LLM-driven persona builder)

To add a new base model: edit models.yaml, no code changes needed.
"""

from pathlib import Path

import yaml

# ──────────────────────────────────────────────────────────────────────────────
# Load configuration from YAML
# ──────────────────────────────────────────────────────────────────────────────

_CONFIG_PATH = Path(__file__).resolve().parent / "models.yaml"

with open(_CONFIG_PATH) as f:
    _config = yaml.safe_load(f)

# ──────────────────────────────────────────────────────────────────────────────
# Models: tag → metadata
# ──────────────────────────────────────────────────────────────────────────────

_MODELS = _config["models"]

# Model-tag → Modelfile filename suffix
MODEL_TAG_TO_SUFFIX = {tag: m["file_suffix"] for tag, m in _MODELS.items()}

# Model-tag → persona name q-suffix (appended to "my-<slug>")
MODEL_TAG_TO_Q_SUFFIX = {tag: m["name_suffix"] for tag, m in _MODELS.items()}


def get_modelfile_suffix(model_tag: str) -> str:
    """Get Modelfile filename suffix for a model tag."""
    return MODEL_TAG_TO_SUFFIX.get(model_tag, "custom")


def get_persona_name_suffix(model_tag: str) -> str:
    """Get persona name q-suffix for a model tag (appended to 'my-<slug>')."""
    return MODEL_TAG_TO_Q_SUFFIX.get(model_tag, "")


def get_model_defaults(model_tag: str) -> dict | None:
    """Get full model defaults (num_ctx, default_temp, display_name) for a tag."""
    return _MODELS.get(model_tag)


# ──────────────────────────────────────────────────────────────────────────────
# Domains: abstract task type → recommended base model
# ──────────────────────────────────────────────────────────────────────────────

_DOMAINS = _config["domains"]

# Build MODEL_MATRIX in the legacy format for backward compatibility:
# domain → (display_name, ollama_tag, num_ctx, default_temp_category)
MODEL_MATRIX = {}
for domain_key, domain_info in _DOMAINS.items():
    model_tag = domain_info["model"]
    model_meta = _MODELS[model_tag]
    MODEL_MATRIX[domain_key] = (
        model_meta["display_name"],
        model_tag,
        model_meta["num_ctx"],
        model_meta["default_temp"],
    )

DOMAIN_CHOICES = list(_DOMAINS.keys())


def get_model(domain: str) -> tuple:
    """
    Get model recommendation for a domain.

    Args:
        domain: One of DOMAIN_CHOICES

    Returns:
        Tuple of (display_name, ollama_tag, num_ctx, default_temp_category)
    """
    if domain not in MODEL_MATRIX:
        domain = "other"
    return MODEL_MATRIX[domain]


# ──────────────────────────────────────────────────────────────────────────────
# Temperatures
# ──────────────────────────────────────────────────────────────────────────────

TEMPERATURES = _config["temperatures"]

TEMP_CATEGORY_TO_CHOICE = _config["temp_categories"]

# Derived mappings (backward compatibility)
TEMPERATURE_MAP = {name: data["value"] for name, data in TEMPERATURES.items()}
TEMP_DESCRIPTIONS = {name: data["description"] for name, data in TEMPERATURES.items()}


def get_temperature_value(name: str) -> float:
    """Get temperature float value by name."""
    return TEMPERATURES.get(name, TEMPERATURES["balanced"])["value"]


def get_temperature_description(name: str) -> str:
    """Get human-readable temperature description by name."""
    return TEMPERATURES.get(name, TEMPERATURES["balanced"])["description"]


# ──────────────────────────────────────────────────────────────────────────────
# Temperature input resolver (named preset OR raw numeric)
# ──────────────────────────────────────────────────────────────────────────────

TEMP_MIN, TEMP_MAX = 0.0, 2.0


def parse_temperature_input(raw: str) -> float:
    """
    Resolve a temperature input string to a float value.

    Accepts:
      - Named preset: "deterministic" | "balanced" | "creative"
      - Raw numeric: any float in [TEMP_MIN, TEMP_MAX] (e.g. "0.5", "1.25")
      - Leading/trailing whitespace is stripped.

    Returns:
        float temperature value.

    Raises:
        ValueError: if the input is not a valid preset name or a number in
            [TEMP_MIN, TEMP_MAX].  The error message lists named options and
            the valid numeric range.
    """
    stripped = raw.strip()
    if stripped in TEMPERATURE_MAP:
        return TEMPERATURE_MAP[stripped]

    named = ", ".join(TEMPERATURE_MAP.keys())
    try:
        value = float(stripped)
    except (ValueError, TypeError):
        raise ValueError(
            f"--temperature '{stripped}' is not a valid preset ({named}) "
            f"or a number in [{TEMP_MIN}, {TEMP_MAX}]."
        )
    if not (TEMP_MIN <= value <= TEMP_MAX):
        raise ValueError(
            f"--temperature {value} out of range [{TEMP_MIN}, {TEMP_MAX}]. "
            f"Named presets: {named}."
        )
    return value


# ──────────────────────────────────────────────────────────────────────────────
# Quick verification
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Available domains:", DOMAIN_CHOICES)
    print("Available temperatures:", list(TEMPERATURES.keys()))
    print(f"Models registered: {len(_MODELS)}")
    print(f"\nExample: code domain → {get_model('code')}")
    print(f"Example: balanced temp → {get_temperature_value('balanced')}")
    print(f"Example: qwen3.5:9b suffix → {get_modelfile_suffix('qwen3.5:9b')}")
    print(f"Example: qwen3.5:9b name → my-python{get_persona_name_suffix('qwen3.5:9b')}")
