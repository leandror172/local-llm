"""Loads the session-handoff register's roles mapping from a YAML file.

Layering rule: this is the ONLY module in the primitive allowed to import PyYAML.
`locator` — the handoff's safety core — stays stdlib-only.
"""

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment guard
    raise ImportError(
        "PyYAML is required for the session-handoff pipeline. "
        "Install it with: pip install pyyaml"
    ) from exc
from pathlib import Path
from typing import Dict, Any

#: The register schema this package understands. Bump only on a breaking change to
#: the `roles:` shape. See "three version facts" in docs/plans/resume-config-steps.md:
#: the installed package is machine-global, this schema is the per-file contract, and
#: the CLAUDE.md `<!-- overlay:session-tracking vN -->` marker is the per-repo config
#: generation. They answer different questions; do not conflate them.
SUPPORTED_REGISTER_SCHEMA = 1


class RegistryError(Exception):
    """Raised for errors loading or parsing the registry."""

    def __init__(self, message, *, kind="internal"):
        super().__init__(message)
        self.kind = kind


def _require_supported_schema(data: Dict[str, Any], path: Path) -> None:
    """Refuse to run against a register this package cannot read.

    An absent `version:` is treated as schema 1 — the only schema that has ever
    existed, so absence cannot prove incompatibility. A *present* version we do not
    recognise is a hard stop: the repo's config and the installed package disagree,
    and silently guessing is how config drift becomes data loss.
    """
    version = data.get("version", SUPPORTED_REGISTER_SCHEMA)
    if version == SUPPORTED_REGISTER_SCHEMA:
        return
    from sessiontracking import __version__ as pkg_version

    raise RegistryError(
        f"{path}: register declares schema version {version!r}, but the installed "
        f"session-tracking {pkg_version} understands schema "
        f"{SUPPORTED_REGISTER_SCHEMA}. These are different version facts: the package "
        f"is machine-global, the schema is this file's contract. Install a "
        f"session-tracking release that supports schema {version!r}, or migrate the "
        f"register."
    )


def load_register(path: str | Path) -> Dict[str, Dict[str, Any]]:
    """Load and parse a YAML file containing a session-handoff register.

    Args:
        path: A string or Path object pointing to the YAML file.

    Returns:
        The roles mapping from the YAML document.

    Raises:
        RegistryError: If the file does not exist, is invalid, declares an
            unsupported schema version, or lacks required structure.
    """
    path = Path(path)

    if not path.exists():
        raise RegistryError(f"File not found: {path}")

    try:
        with open(path, "r") as file:
            data = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise RegistryError(f"Invalid YAML format in {path}") from exc

    if not isinstance(data, dict):
        raise RegistryError(f"Document must be a mapping, got {type(data)}")

    _require_supported_schema(data, path)

    if "roles" not in data or not isinstance(data["roles"], dict):
        raise RegistryError("Missing 'roles' key or it is not a mapping")

    return data["roles"]
