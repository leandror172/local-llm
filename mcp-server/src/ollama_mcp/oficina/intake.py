"""Deterministic spec intake — validation + per-profile rejection rules (P1-D3).

Two profiles share ONE schema and differ only in intake rules:
- ``kind: file``   — requires ``deliverable.target`` (today's output_file semantics)
- ``kind: answer`` — forbids ``target`` (budget implicitly 1, workspace in_place)

Every rejection names its rule and carries the where/whose/what triad
(stage=intake, fault=payload). Intake RETURNS its verdict (accepted spec passed
through unchanged, or a named rejection) — it never raises; the worker turns a
rejection into an ``IntakeRejected`` event whose payload IS the rejection.

Pydantic models below are the schema of record (P1-D4); the set of allowed keys
at each level is derived from them so the fail-loud unknown-key check and the
schema can never drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

# --- Schema of record (P1-D4) -----------------------------------------------


class Deliverable(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Optional[str] = None
    target: Optional[str] = None


class Context(BaseModel):
    model_config = ConfigDict(extra="forbid")
    files: List[str] = Field(default_factory=list)
    refs: List[str] = Field(default_factory=list)


class RunSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deliverable: Deliverable
    objective: Optional[str] = None
    context: Context = Field(default_factory=Context)
    workspace: str = "in_place"
    model: str = "auto"
    timeout_s: int = 1800


# Allowed keys derived from the schema — single source of truth.
TOP_KEYS = set(RunSpec.model_fields)
DELIVERABLE_KEYS = set(Deliverable.model_fields)
CONTEXT_KEYS = set(Context.model_fields)

VALID_KINDS = {"file", "answer"}
SUPPORTED_WORKSPACE = "in_place"

# --- Rule identifiers (stable; tests assert on these) -----------------------

RULE_UNKNOWN_KEY = "unknown_key"
RULE_OBJECTIVE_MISSING = "objective_missing"
RULE_UNKNOWN_KIND = "unknown_kind"
RULE_FILE_WITHOUT_TARGET = "file_without_target"
RULE_ANSWER_WITH_TARGET = "answer_with_target"
RULE_WORKSPACE_UNSUPPORTED = "workspace_unsupported"
RULE_CONTEXT_FILE_MISSING = "context_file_missing"


@dataclass
class Rejection:
    """A named intake rejection carrying the where/whose/what triad."""

    rule: str
    detail: str
    stage: str = "intake"  # where
    fault: str = "payload"  # whose

    @property
    def payload(self) -> Dict[str, Any]:
        """The dict that becomes ``IntakeRejected.payload``."""
        return {
            "rule": self.rule,
            "stage": self.stage,
            "fault": self.fault,
            "detail": self.detail,
        }


@dataclass
class IntakeResult:
    """Verdict of intake: accepted (spec unchanged) or rejected (named)."""

    accepted: bool
    spec: Optional[Dict[str, Any]] = None
    rejection: Optional[Rejection] = None


def _check_unknown_keys(spec: Dict[str, Any]) -> Optional[Rejection]:
    """Reject any unknown top-level key (fail loud on typos)."""
    unknown = set(spec) - TOP_KEYS
    if unknown:
        return Rejection(RULE_UNKNOWN_KEY, f"unknown top-level key(s): {', '.join(sorted(unknown))}")
    return None


def _check_deliverable_unknown_keys(spec: Dict[str, Any]) -> Optional[Rejection]:
    """Reject any unknown key inside deliverable."""
    deliverable = spec.get("deliverable") or {}
    unknown = set(deliverable) - DELIVERABLE_KEYS
    if unknown:
        return Rejection(RULE_UNKNOWN_KEY, f"unknown deliverable key(s): {', '.join(sorted(unknown))}")
    return None


def _check_context_unknown_keys(spec: Dict[str, Any]) -> Optional[Rejection]:
    """Reject any unknown key inside context."""
    context = spec.get("context") or {}
    unknown = set(context) - CONTEXT_KEYS
    if unknown:
        return Rejection(RULE_UNKNOWN_KEY, f"unknown context key(s): {', '.join(sorted(unknown))}")
    return None


def _check_objective(spec: Dict[str, Any]) -> Optional[Rejection]:
    """Reject a missing or empty objective."""
    if not spec.get("objective"):
        return Rejection(RULE_OBJECTIVE_MISSING, "objective is missing or empty")
    return None


def _check_kind_and_target(spec: Dict[str, Any]) -> Optional[Rejection]:
    """Reject unknown kinds and per-profile kind/target violations."""
    deliverable = spec.get("deliverable") or {}
    kind = deliverable.get("kind")
    if kind not in VALID_KINDS:
        return Rejection(RULE_UNKNOWN_KIND, f"unknown deliverable.kind: {kind!r}")
    if kind == "file" and not deliverable.get("target"):
        return Rejection(RULE_FILE_WITHOUT_TARGET, "kind 'file' requires deliverable.target")
    if kind == "answer" and deliverable.get("target"):
        return Rejection(RULE_ANSWER_WITH_TARGET, "kind 'answer' forbids deliverable.target")
    return None


def _check_workspace(spec: Dict[str, Any]) -> Optional[Rejection]:
    """Reject any workspace other than the P1-supported in_place."""
    workspace = spec.get("workspace", SUPPORTED_WORKSPACE)
    if workspace != SUPPORTED_WORKSPACE:
        return Rejection(RULE_WORKSPACE_UNSUPPORTED, f"unsupported workspace: {workspace!r}")
    return None


def _check_context_files(spec: Dict[str, Any]) -> Optional[Rejection]:
    """Reject the first context.files entry that does not exist on disk."""
    context = spec.get("context") or {}
    for file_path in context.get("files", []):
        if not Path(file_path).exists():
            return Rejection(RULE_CONTEXT_FILE_MISSING, f"context file not found: {file_path}")
    return None


_CHECKS = (
    _check_unknown_keys,
    _check_deliverable_unknown_keys,
    _check_context_unknown_keys,
    _check_objective,
    _check_kind_and_target,
    _check_workspace,
    _check_context_files,
)


def check_intake(spec: Dict[str, Any]) -> IntakeResult:
    """Apply every deterministic rule; return accepted-unchanged or a rejection."""
    for check in _CHECKS:
        rejection = check(spec)
        if rejection:
            return IntakeResult(accepted=False, rejection=rejection)
    return IntakeResult(accepted=True, spec=spec)
