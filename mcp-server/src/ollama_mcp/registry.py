"""Persona registry: load, cache, query, and build language routes.

The persona registry (personas/registry.yaml) is the source of truth for all
Ollama personas. This module loads it once at server startup and provides:

- query_personas(): filter/search personas by language, domain, tier, or name
- get_language_routes(): mapping of programming language → best persona name,
  used by generate_code for automatic persona selection
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Module-level cache (populated by load_registry, read by everything else)
# ---------------------------------------------------------------------------

_registry: dict[str, dict[str, Any]] = {}
_language_routes: dict[str, str] = {}

# ---------------------------------------------------------------------------
# Language keywords to scan for in persona role strings
# ---------------------------------------------------------------------------

# Maps a keyword (found in role or persona name) to the canonical language
# name used as the routing key. Order doesn't matter — specialists win over
# generalists regardless of scan order.
_LANGUAGE_KEYWORDS: dict[str, str] = {
    "java": "java",
    "go ": "go",          # trailing space avoids matching "good", "google"
    "go-": "go",          # matches my-go-q3 style names
    "golang": "go",
    "python": "python",
    "rust": "rust",
    "react": "react",
    "angular": "angular",
    "html": "html",
    "canvas": "html",
    "svg": "html",
    "javascript": "javascript",
    "typescript": "typescript",
    "css": "css",
    "bash": "bash",
    "shell": "bash",
}

# Aliases: when someone asks for "js", route the same as "javascript"
_LANGUAGE_ALIASES: dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "golang": "go",
    "sh": "bash",
}


def load_registry(path: str | Path) -> dict[str, dict[str, Any]]:
    """Load the persona registry YAML and cache it.

    Called once during server startup (_lifespan). Populates both the
    _registry cache and the _language_routes cache.

    Args:
        path: Absolute path to registry.yaml.

    Returns:
        The parsed registry dict (persona_name → attributes).

    Raises:
        FileNotFoundError: If the registry file doesn't exist.
        yaml.YAMLError: If the file isn't valid YAML.
    """
    global _registry, _language_routes

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    # Filter out None/non-dict entries (comments-only sections parse as None)
    _registry = {
        k: v for k, v in (raw or {}).items()
        if isinstance(v, dict)
    }

    _language_routes = _build_language_routes(_registry)
    return _registry


def get_registry() -> dict[str, dict[str, Any]]:
    """Return the cached registry (empty dict if not loaded)."""
    return _registry


def get_language_routes() -> dict[str, str]:
    """Return the cached language → persona routing table."""
    return _language_routes


# ---------------------------------------------------------------------------
# Language route builder
# ---------------------------------------------------------------------------

def _build_language_routes(registry: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Scan active full-tier personas and build language → persona mapping.

    Algorithm:
    1. For each active, full-tier persona, scan its role string and name
       for language keywords.
    2. If multiple personas match the same language, prefer the one whose
       *name* contains the language (specialist) over one that only mentions
       it in the role (generalist/polyglot).

    Returns:
        Dict mapping canonical language name to persona name, e.g.
        {"java": "my-java-q3", "python": "my-python-q3", ...}
    """
    routes: dict[str, str] = {}
    # Track whether current winner is a "name match" (specialist) so we
    # know if a new candidate can override it.
    is_specialist: dict[str, bool] = {}

    for persona_name, attrs in registry.items():
        if attrs.get("status") != "active":
            continue
        if attrs.get("tier") != "full":
            continue

        role = (attrs.get("role") or "").lower()
        name_lower = persona_name.lower()

        for keyword, lang in _LANGUAGE_KEYWORDS.items():
            # Check if this persona matches this language keyword
            matched_in_role = keyword in role
            matched_in_name = keyword.strip(" -") in name_lower

            if not (matched_in_role or matched_in_name):
                continue

            candidate_is_specialist = matched_in_name

            if lang not in routes:
                # First match — take it
                routes[lang] = persona_name
                is_specialist[lang] = candidate_is_specialist
            elif candidate_is_specialist and not is_specialist[lang]:
                # New specialist beats existing generalist
                routes[lang] = persona_name
                is_specialist[lang] = True
            elif not is_specialist[lang] and not candidate_is_specialist:
                # Two generalists tie — prefer Qwen3 (-q3) over Qwen2.5
                if "-q3" in persona_name and "-q3" not in routes[lang]:
                    routes[lang] = persona_name
            # else: keep existing (specialist always wins)

    return routes


# ---------------------------------------------------------------------------
# Query function
# ---------------------------------------------------------------------------

def query_personas(
    *,
    language: str | None = None,
    domain: str | None = None,
    tier: str | None = None,
    name: str | None = None,
) -> list[dict[str, Any]]:
    """Filter personas from the cached registry.

    All parameters are optional. When multiple are provided, they are ANDed.

    Args:
        language: Filter by language keyword in role (e.g., "java", "python").
        domain: Filter by substring in role (e.g., "frontend", "review").
        tier: Filter by tier value (e.g., "full", "bare").
        name: Filter by substring in persona name (e.g., "architect").

    Returns:
        List of dicts, each with "persona_name" key plus all registry attrs.
    """
    results: list[dict[str, Any]] = []

    for persona_name, attrs in _registry.items():
        # Only include active personas by default
        if attrs.get("status") != "active":
            continue

        role_lower = (attrs.get("role") or "").lower()
        name_lower = persona_name.lower()

        # Apply filters (AND logic)
        if language and language.lower() not in role_lower and language.lower() not in name_lower:
            continue
        if domain and domain.lower() not in role_lower:
            continue
        if tier and attrs.get("tier") != tier:
            continue
        if name and name.lower() not in name_lower:
            continue

        results.append({"persona_name": persona_name, **attrs})

    return results
