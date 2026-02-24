"""Shared registry loader for personas/registry.yaml.

Provides a single load_registry() entry point used by benchmark.py and any
other tool that needs to read persona definitions. Keeps YAML-loading logic
in one place so callers don't re-implement it.

Note: the MCP server (mcp-server/src/ollama_mcp/registry.py) has its own
more complex registry module with caching and language-routing logic that
is specific to the server's startup lifecycle — it is not replaced by this
module.
"""

from pathlib import Path
from typing import Any

import yaml

# Default path: personas/registry.yaml, resolved relative to this file.
_DEFAULT_REGISTRY = Path(__file__).resolve().parent.parent / "registry.yaml"


def load_registry(
    path: "Path | str | None" = None,
    *,
    active_only: bool = True,
) -> dict[str, dict[str, Any]]:
    """Load personas/registry.yaml and return a dict of persona definitions.

    Args:
        path: Path to registry.yaml. Defaults to personas/registry.yaml
              (the canonical location relative to this file).
        active_only: When True (default), only personas with
                     ``status: active`` are returned.

    Returns:
        Dict mapping persona name to its attribute dict.

    Raises:
        FileNotFoundError: If the registry file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    registry_path = Path(path) if path is not None else _DEFAULT_REGISTRY
    with open(registry_path) as f:
        raw = yaml.safe_load(f) or {}

    entries = {k: v for k, v in raw.items() if isinstance(v, dict)}
    if active_only:
        entries = {k: v for k, v in entries.items() if v.get("status") == "active"}
    return entries
