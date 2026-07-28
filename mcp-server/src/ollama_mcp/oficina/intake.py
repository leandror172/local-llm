"""Deterministic spec intake — validation + per-profile rejection rules (P1-D3, P2-D13).

Profiles share ONE schema and differ only in intake rules:
- ``kind: file``     — requires ``deliverable.target`` (today's output_file semantics)
- ``kind: function`` — the evaluated-loop deliverable (greenfield OR edit): requires ``target``
  AND an ``acceptance`` spec (``test_cmd`` is the every-iteration gate), tests run in an isolated
  ``worktree``. Greenfield vs edit is NOT an intake concern — intake accepts a ``function`` spec
  whether the target is new or already exists on disk; the mode is decided at assembly by whether
  the target is committed at HEAD (E-D2), so intake never touches the filesystem for the target.
- ``kind: answer``   — forbids ``target`` (budget implicitly 1, workspace in_place)

Every rejection names its rule and carries the **where/whose/what** triad — the single
spelling shared with the ``Failed`` event payload (P2 unified the P1 ``stage/fault/detail``
divergence). Intake RETURNS its verdict (accepted spec passed through unchanged, or a named
rejection) — it never raises; the worker turns a rejection into an ``IntakeRejected`` event
whose payload IS the rejection.

Pydantic models below are the schema of record (P1-D4); the set of allowed keys at each
level is derived from them so the fail-loud unknown-key check and the schema can never drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

# --- Schema of record (P1-D4, extended in P2-D13) ---------------------------


class Deliverable(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Optional[str] = None
    target: Optional[str] = None
    language: Optional[str] = None  # loop kinds only; declared or inferred from target ext (R1)


class Context(BaseModel):
    model_config = ConfigDict(extra="forbid")
    files: List[str] = Field(default_factory=list)
    refs: List[str] = Field(default_factory=list)
    callers: List[str] = Field(default_factory=list)


class Acceptance(BaseModel):
    """The evaluated-loop acceptance spec (P2), plus the P4 judge gate.

    ``rubric`` names an evaluator rubric by id (e.g. ``code-python``); its phase-2 criteria
    are judged ONCE at packaging (P4-D1). Omitted means no judge runs — the gate is opt-in,
    and a run without one is delivered exactly as it was before P4.
    """

    model_config = ConfigDict(extra="forbid")
    test_cmd: Optional[str] = None
    test_files: List[str] = Field(default_factory=list)
    validators: List[str] = Field(default_factory=list)
    structural: Optional[str] = None
    rubric: Optional[str] = None


class Budgets(BaseModel):
    """Loop budgets (P2-D10). Iterations steers; the rest are safety nets (enforced in the loop)."""

    model_config = ConfigDict(extra="forbid")
    # T-114: None → the loop resolves the default by mode post-assembly (edit 1, greenfield 3);
    # an explicit value always wins. Mirrors num_predict's None-means-mode-resolved contract (E-D9).
    iterations: Optional[int] = None
    fresh_starts: int = 1
    wall_clock_s: Optional[int] = 900  # 0/None disables the whole-run wall-clock net
    tokens: Optional[int] = None
    num_predict: Optional[int] = None  # T-91: floored/capped generation length; None → loop default


class RunSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deliverable: Deliverable
    objective: Optional[str] = None
    context: Context = Field(default_factory=Context)
    acceptance: Optional[Acceptance] = None
    budgets: Budgets = Field(default_factory=Budgets)
    workspace: str = "in_place"
    model: str = "auto"
    timeout_s: int = 1800


# Allowed keys derived from the schema — single source of truth.
TOP_KEYS = set(RunSpec.model_fields)
DELIVERABLE_KEYS = set(Deliverable.model_fields)
CONTEXT_KEYS = set(Context.model_fields)
ACCEPTANCE_KEYS = set(Acceptance.model_fields)
BUDGETS_KEYS = set(Budgets.model_fields)

VALID_KINDS = {"file", "answer", "function"}
KINDS_REQUIRING_TARGET = {"file", "function"}
LOOP_KINDS = {"function"}  # kinds that run through the evaluated loop (need acceptance)
# Language: single source of truth for both resolve_language and the rejection rule (R1).
# Intake is language-LIST-gated, not implementation-gated — 'go' is accepted here before the
# loop's Go support exists (that gates at the loop, not intake).
SUPPORTED_LANGUAGES = {"python", "go"}
EXTENSION_TO_LANGUAGE = {".py": "python", ".go": "go"}
DEFAULT_WORKSPACE = "in_place"
WORKTREE_WORKSPACE = "worktree"
SUPPORTED_WORKSPACES = {"in_place", "worktree"}

# --- Rule identifiers (stable; tests assert on these) -----------------------

RULE_UNKNOWN_KEY = "unknown_key"
RULE_OBJECTIVE_MISSING = "objective_missing"
RULE_UNKNOWN_KIND = "unknown_kind"
RULE_FILE_WITHOUT_TARGET = "file_without_target"
RULE_ANSWER_WITH_TARGET = "answer_with_target"
RULE_WORKSPACE_UNSUPPORTED = "workspace_unsupported"
RULE_CONTEXT_FILE_MISSING = "context_file_missing"
# P2 additions (P2-D13)
RULE_ACCEPTANCE_REQUIRED = "acceptance_required"
RULE_WORKTREE_REQUIRED = "worktree_required"
RULE_TARGET_NOT_GIT_REPO = "target_not_git_repo"
RULE_ACCEPTANCE_NOT_SUPPORTED = "acceptance_not_supported"
RULE_WORKTREE_NOT_SUPPORTED = "worktree_not_supported"
# Language rules (Axis A widening, R1) — mirror the acceptance _supported/_required pair.
RULE_LANGUAGE_NOT_SUPPORTED = "language_not_supported"
RULE_UNSUPPORTED_LANGUAGE = "unsupported_language"


@dataclass
class Rejection:
    """A named intake rejection carrying the where/whose/what triad.

    ``what`` is the human-readable detail; ``where``/``whose`` default to the intake
    stage and a payload-fault attribution. These three keys are the SAME triad the
    ``Failed`` event emits (unified in P2).
    """

    rule: str
    what: str
    where: str = "intake"
    whose: str = "payload"

    @property
    def payload(self) -> Dict[str, Any]:
        """The dict that becomes ``IntakeRejected.payload``."""
        return {
            "rule": self.rule,
            "where": self.where,
            "whose": self.whose,
            "what": self.what,
        }


@dataclass
class IntakeResult:
    """Verdict of intake: accepted (spec unchanged) or rejected (named)."""

    accepted: bool
    spec: Optional[Dict[str, Any]] = None
    rejection: Optional[Rejection] = None


def _git_root(start: Path) -> Optional[Path]:
    """Walk up from ``start`` returning the first dir containing a ``.git`` entry, or None."""
    resolved = start.resolve()
    for directory in (resolved, *resolved.parents):
        if (directory / ".git").exists():
            return directory
    return None


def resolve_language(deliverable: Dict[str, Any]) -> Optional[str]:
    """Resolve a deliverable's language: declared wins, else inferred from the target extension (R1).

    Returns the declared ``language`` verbatim — even an unsupported value like ``"rust"``; the
    resolver resolves, the rule judges — else the extension-mapped language, else None (no
    declaration and an absent/unknown extension).
    """
    language = deliverable.get("language")
    if language:
        return language
    target = deliverable.get("target")
    if target:
        return EXTENSION_TO_LANGUAGE.get(Path(target).suffix)
    return None


# Every schema level the unknown-key rule covers: (section key, allowed keys, label);
# None = the spec's top level. A new nested model gets one row here — the single checker
# below then covers it, so a section cannot be added without typo protection.
_KEYED_SECTIONS = (
    (None, TOP_KEYS, "top-level"),
    ("deliverable", DELIVERABLE_KEYS, "deliverable"),
    ("context", CONTEXT_KEYS, "context"),
    ("acceptance", ACCEPTANCE_KEYS, "acceptance"),
    ("budgets", BUDGETS_KEYS, "budgets"),
)


def _check_unknown_keys(spec: Dict[str, Any]) -> Optional[Rejection]:
    """Reject any unknown key at any schema level (fail loud on typos like 'iteration').

    check_intake never instantiates the pydantic models, so their ``extra='forbid'``
    does not run on this path — this check is what keeps a mistyped key from silently
    falling back to a default instead of the value the user meant.
    """
    for section, allowed, label in _KEYED_SECTIONS:
        data = spec if section is None else (spec.get(section) or {})
        unknown = set(data) - allowed
        if unknown:
            return Rejection(
                RULE_UNKNOWN_KEY, f"unknown {label} key(s): {', '.join(sorted(unknown))}"
            )
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
    if kind in KINDS_REQUIRING_TARGET and not deliverable.get("target"):
        return Rejection(RULE_FILE_WITHOUT_TARGET, f"kind {kind!r} requires deliverable.target")
    if kind == "answer" and deliverable.get("target"):
        return Rejection(RULE_ANSWER_WITH_TARGET, "kind 'answer' forbids deliverable.target")
    return None


def _check_workspace(spec: Dict[str, Any]) -> Optional[Rejection]:
    """Reject any workspace value outside the supported set."""
    workspace = spec.get("workspace", DEFAULT_WORKSPACE)
    if workspace not in SUPPORTED_WORKSPACES:
        return Rejection(RULE_WORKSPACE_UNSUPPORTED, f"unsupported workspace: {workspace!r}")
    return None


def _check_acceptance_supported(spec: Dict[str, Any]) -> Optional[Rejection]:
    """acceptance.test_cmd is only wired for loop kinds; reject it on file/answer.

    Without this a ``kind: file`` spec carrying a test_cmd passes intake but takes the P1
    single-shot path, which writes the target in place and never runs the declared tests —
    the acceptance gate is silently ignored. Widen when a non-function kind gains the loop.
    """
    kind = (spec.get("deliverable") or {}).get("kind")
    acceptance = spec.get("acceptance") or {}
    if acceptance.get("test_cmd") and kind not in LOOP_KINDS:
        return Rejection(
            RULE_ACCEPTANCE_NOT_SUPPORTED,
            f"acceptance.test_cmd is only supported for loop kinds {sorted(LOOP_KINDS)}, not {kind!r}",
        )
    return None


def _check_worktree_supported(spec: Dict[str, Any]) -> Optional[Rejection]:
    """workspace 'worktree' is only wired for loop kinds; reject it on file/answer.

    The single-shot path ignores ``workspace`` and writes in place, so accepting worktree
    for a non-loop kind silently denies the isolation the caller asked for. (Also removes the
    answer+worktree case whose git-repo check falls back to the worker's nondeterministic cwd.)
    """
    kind = (spec.get("deliverable") or {}).get("kind")
    workspace = spec.get("workspace", DEFAULT_WORKSPACE)
    if workspace == WORKTREE_WORKSPACE and kind not in LOOP_KINDS:
        return Rejection(
            RULE_WORKTREE_NOT_SUPPORTED,
            f"workspace 'worktree' is only supported for loop kinds {sorted(LOOP_KINDS)}, not {kind!r}",
        )
    return None


def _check_language_supported(spec: Dict[str, Any]) -> Optional[Rejection]:
    """A declared language is only wired for loop kinds; reject it on file/answer.

    Mirrors _check_acceptance_supported: the single-shot path ignores language, so accepting a
    declared language on a non-loop kind silently drops the caller's intent.
    """
    deliverable = spec.get("deliverable") or {}
    kind = deliverable.get("kind")
    if deliverable.get("language") and kind not in LOOP_KINDS:
        return Rejection(
            RULE_LANGUAGE_NOT_SUPPORTED,
            f"deliverable.language is only supported for loop kinds {sorted(LOOP_KINDS)}, not {kind!r}",
        )
    return None


def _check_language_resolvable(spec: Dict[str, Any]) -> Optional[Rejection]:
    """A loop kind must resolve to a supported language — declared or inferred from the target ext (R1).

    Mirrors _check_acceptance_required (a loop-kind requirement). ``None`` (unresolvable) and an
    unsupported value both fail the single ``not in`` membership test.
    """
    deliverable = spec.get("deliverable") or {}
    if deliverable.get("kind") not in LOOP_KINDS:
        return None
    language = resolve_language(deliverable)
    if language not in SUPPORTED_LANGUAGES:
        return Rejection(
            RULE_UNSUPPORTED_LANGUAGE,
            f"unsupported or unresolvable language {language!r}; supported: {sorted(SUPPORTED_LANGUAGES)}",
        )
    return None


def _check_acceptance_required(spec: Dict[str, Any]) -> Optional[Rejection]:
    """A loop kind (function) needs an acceptance.test_cmd — the every-iteration gate (P2-D13)."""
    kind = (spec.get("deliverable") or {}).get("kind")
    if kind not in LOOP_KINDS:
        return None
    acceptance = spec.get("acceptance") or {}
    if not acceptance.get("test_cmd"):
        return Rejection(
            RULE_ACCEPTANCE_REQUIRED,
            f"kind {kind!r} requires acceptance.test_cmd (the loop's every-iteration gate)",
        )
    return None


def _check_worktree_required(spec: Dict[str, Any]) -> Optional[Rejection]:
    """A spec with a test_cmd must run in a worktree — tests need isolation (P2-D5)."""
    acceptance = spec.get("acceptance") or {}
    workspace = spec.get("workspace", DEFAULT_WORKSPACE)
    if acceptance.get("test_cmd") and workspace != WORKTREE_WORKSPACE:
        return Rejection(
            RULE_WORKTREE_REQUIRED,
            "acceptance.test_cmd requires workspace 'worktree' (tests need isolation)",
        )
    return None


def _check_target_git_repo(spec: Dict[str, Any]) -> Optional[Rejection]:
    """A worktree workspace requires the target to live in a git repo (P2-D13).

    The worktree is a linked working tree of the target's repository; without a repo
    there is nothing to ``git worktree add``.
    """
    workspace = spec.get("workspace", DEFAULT_WORKSPACE)
    if workspace != WORKTREE_WORKSPACE:
        return None
    target = (spec.get("deliverable") or {}).get("target")
    base = Path(target).parent if target else Path.cwd()
    if _git_root(base) is None:
        return Rejection(
            RULE_TARGET_NOT_GIT_REPO,
            f"workspace 'worktree' requires the target to live in a git repo: {target!r}",
        )
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
    _check_objective,
    _check_kind_and_target,
    _check_workspace,
    _check_acceptance_supported,
    _check_worktree_supported,
    _check_language_supported,
    _check_acceptance_required,
    _check_worktree_required,
    _check_language_resolvable,
    _check_target_git_repo,
    _check_context_files,
)


def check_intake(spec: Dict[str, Any]) -> IntakeResult:
    """Apply every deterministic rule; return accepted-unchanged or a rejection."""
    for check in _CHECKS:
        rejection = check(spec)
        if rejection:
            return IntakeResult(accepted=False, rejection=rejection)
    return IntakeResult(accepted=True, spec=spec)
