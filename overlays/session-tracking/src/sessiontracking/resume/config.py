"""Load and validate `resume.yaml` — the step list resume renders at session start.

Schema (R-D2, fixed vocabulary + a `run:` escape hatch):

    version: 1
    steps:
      - kind: text        lines: [...]                       # literal; {date} substituted
      - kind: region      role: <register-role>              # resolved via the register
                          ref_key: <ref:KEY>                 # ...or a raw key (see below)
      - kind: log_next    role: <register-role>              # newest session-log ### Next
      - kind: git_log     count: 5
      - kind: git_status
      - kind: run         command: "<shell>"                 # escape hatch

Shared options: title, head, filters (regexes; a line matching ANY is dropped),
fallback (printed when the step yields nothing), title_on_empty (default true),
omit_if_empty (skip the step entirely, title included), trailing_blank.

A step earns a FIXED kind when the overlay owns the invariant it depends on:
`log_next` parses session-log.md's structure (overlay-owned, already changed once);
`git_log` pins plain `git` because `rtk git log` silently drops merge commits.
`run:` is for what only the repo knows. It is executable code at the same trust level
as a Makefile — checked in, reviewed like source. That is the deliberate trade.

`role:` is preferred over `ref_key:`. A role resolves through the register, so renaming
or moving the block updates read and write together. A raw `ref_key:` shells out to the
ref-indexing overlay's `ref-lookup.sh` and loses that rename-safety.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment guard
    raise ImportError(
        "PyYAML is required for session-tracking. Install it with: pip install pyyaml"
    ) from exc

#: Bump only on a breaking change to the step schema. Same three-version-facts rule as
#: the register: this is the per-file contract, not the package version.
SUPPORTED_RESUME_SCHEMA = 1

STEP_KINDS = frozenset({"text", "region", "log_next", "git_log", "git_status", "run"})


class ResumeConfigError(Exception):
    """Raised for errors loading or validating resume.yaml."""


@dataclass(frozen=True)
class Step:
    kind: str
    title: Optional[str] = None
    title_on_empty: bool = True
    head: Optional[int] = None
    filters: tuple = ()
    fallback: Optional[str] = None
    omit_if_empty: bool = False
    trailing_blank: bool = False
    # kind-specific
    lines: tuple = ()
    role: Optional[str] = None
    ref_key: Optional[str] = None
    count: Optional[int] = None
    command: Optional[str] = None


@dataclass(frozen=True)
class ResumeConfig:
    steps: List[Step] = field(default_factory=list)


def _require_supported_schema(data: Dict[str, Any], path: Path) -> None:
    version = data.get("version", SUPPORTED_RESUME_SCHEMA)
    if version == SUPPORTED_RESUME_SCHEMA:
        return
    from sessiontracking import __version__ as pkg_version

    raise ResumeConfigError(
        f"{path}: resume config declares schema version {version!r}, but the installed "
        f"session-tracking {pkg_version} understands schema {SUPPORTED_RESUME_SCHEMA}."
    )


def _build_step(raw: Dict[str, Any], path: Path, index: int) -> Step:
    if not isinstance(raw, dict):
        raise ResumeConfigError(f"{path}: step {index} must be a mapping, got {type(raw)}")

    kind = raw.get("kind")
    if kind not in STEP_KINDS:
        raise ResumeConfigError(
            f"{path}: step {index} has unknown kind {kind!r}. "
            f"Known kinds: {', '.join(sorted(STEP_KINDS))}. "
            f"Use `kind: run` for anything the overlay does not model."
        )

    if kind == "region" and not (raw.get("role") or raw.get("ref_key")):
        raise ResumeConfigError(
            f"{path}: step {index} (region) needs `role:` (preferred — resolved through "
            f"the register) or `ref_key:` (raw key; loses rename-safety)."
        )
    if kind == "run" and not raw.get("command"):
        raise ResumeConfigError(f"{path}: step {index} (run) needs `command:`")

    return Step(
        kind=kind,
        title=raw.get("title"),
        title_on_empty=raw.get("title_on_empty", True),
        head=raw.get("head"),
        filters=tuple(raw.get("filters", ())),
        fallback=raw.get("fallback"),
        omit_if_empty=raw.get("omit_if_empty", False),
        trailing_blank=raw.get("trailing_blank", False),
        lines=tuple(raw.get("lines", ())),
        role=raw.get("role"),
        ref_key=raw.get("ref_key"),
        count=raw.get("count"),
        command=raw.get("command"),
    )


def load_resume_config(path: str | Path) -> ResumeConfig:
    """Load, validate, and build the step list from a resume.yaml.

    Raises:
        ResumeConfigError: missing file, invalid YAML, unsupported schema, unknown
            step kind, or a step missing its required key.
    """
    path = Path(path)
    if not path.exists():
        raise ResumeConfigError(f"File not found: {path}")

    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ResumeConfigError(f"Invalid YAML format in {path}") from exc

    if not isinstance(data, dict):
        raise ResumeConfigError(f"{path}: document must be a mapping, got {type(data)}")

    _require_supported_schema(data, path)

    steps = data.get("steps")
    if not isinstance(steps, list):
        raise ResumeConfigError(f"{path}: missing 'steps' key, or it is not a list")

    return ResumeConfig(steps=[_build_step(s, path, i) for i, s in enumerate(steps)])
