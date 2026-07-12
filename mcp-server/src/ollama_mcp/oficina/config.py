"""oficina storage-root and retention configuration (P1-D2, P1-D7).

The storage root is machine-global (``~/.local/share/oficina/`` by default),
overridable via the ``OFICINA_ROOT`` env var (tests + acceptance point it at a
temp dir). Retention parameters live in ``~/.config/oficina/config.yaml`` (XDG);
a missing file is NOT an error — embedded defaults encode the P6-harvest
argument (``ledger: forever``, keep 20 runs of artifacts, 7-day workspace TTL).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

ROOT_ENV_VAR = "OFICINA_ROOT"


def default_root() -> Path:
    """Resolve the oficina storage root (env override or XDG data default)."""
    override = os.environ.get(ROOT_ENV_VAR)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".local" / "share" / "oficina"


def default_config_path() -> Path:
    """Resolve the XDG config path for oficina."""
    return Path.home() / ".config" / "oficina" / "config.yaml"


@dataclass
class RetentionConfig:
    """Retention policy parameters (P1-D2). Defaults encode the harvest argument."""

    ledger: str = "forever"
    workspaces_ttl_days: int = 7
    artifacts_keep_runs: int = 20


def load_retention_config(config_path: Optional[Path] = None) -> RetentionConfig:
    """Load retention config from YAML; a missing file yields embedded defaults."""
    path = config_path or default_config_path()
    if not path.exists():
        return RetentionConfig()
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    section = data.get("retention", {}) or {}
    defaults = RetentionConfig()
    return RetentionConfig(
        ledger=section.get("ledger", defaults.ledger),
        workspaces_ttl_days=section.get("workspaces_ttl_days", defaults.workspaces_ttl_days),
        artifacts_keep_runs=section.get("artifacts_keep_runs", defaults.artifacts_keep_runs),
    )
