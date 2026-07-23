"""Tests for oficina.intake — every deterministic rejection rule, both profiles.

Written in the executable-spec (DSL) style — `docs/patterns/test-authoring-executable-spec.md`
(`ref:test-executable-spec`). Intake is a PURE FUNCTION (spec -> verdict), so there is no temporal
`when_` to narrate: the given/when/then scaffold collapses to **spec-builder nouns**
(`a_function_spec` / `a_file_spec` / `an_answer_spec`) plus **verdict-asserter verbs**
(`accepts` / `rejects(with_rule=…)` / `rejects_with_triad`). Each test reads "this spec -> accepted"
or "this spec -> rejected with RULE_X". Exotic malformations (a deleted key, a bogus nested key) stay
inline data-prep — the earned vocabulary is the builders and the verbs, not a mutation mini-language.

Synchronous tests (plain ``def``), not async.
"""

from ollama_mcp.oficina.intake import (
    RULE_ACCEPTANCE_NOT_SUPPORTED,
    RULE_ACCEPTANCE_REQUIRED,
    RULE_ANSWER_WITH_TARGET,
    RULE_CONTEXT_FILE_MISSING,
    RULE_FILE_WITHOUT_TARGET,
    RULE_LANGUAGE_NOT_SUPPORTED,
    RULE_OBJECTIVE_MISSING,
    RULE_TARGET_NOT_GIT_REPO,
    RULE_UNKNOWN_KEY,
    RULE_UNKNOWN_KIND,
    RULE_UNSUPPORTED_LANGUAGE,
    RULE_WORKSPACE_UNSUPPORTED,
    RULE_WORKTREE_NOT_SUPPORTED,
    RULE_WORKTREE_REQUIRED,
    check_intake,
)


# --- vocabulary: spec builders (nouns) --------------------------------------


def a_function_spec(tmp_path, *, git=True):
    """A minimal VALID kind:function loop spec: target + acceptance.test_cmd + worktree + git repo.

    Creates the target's directory, optionally with a ``.git`` marker so the worktree/git-repo rule
    is satisfied. Callers mutate the returned dict to exercise individual rejections.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    if git:
        (repo / ".git").mkdir()
    return {
        "deliverable": {"kind": "function", "target": str(repo / "area.py")},
        "objective": "implement area(w, h)",
        "acceptance": {"test_cmd": "pytest -q", "test_files": ["tests/test_area.py"]},
        "workspace": "worktree",
    }


def a_file_spec(tmp_path):
    """A minimal VALID kind:file spec targeting a path under tmp_path."""
    return {
        "deliverable": {"kind": "file", "target": str(tmp_path / "out.py")},
        "objective": "write a function",
    }


def an_answer_spec():
    """A minimal VALID kind:answer spec."""
    return {"deliverable": {"kind": "answer"}, "objective": "answer the question"}


# --- vocabulary: verdict asserters (verbs) ----------------------------------


def accepts(spec):
    """The verdict: intake accepts the spec. Returns the result for further assertions."""
    result = check_intake(spec)
    assert result.accepted is True
    return result


def rejects(spec, *, with_rule):
    """The verdict: intake rejects the spec, naming ``with_rule``. Returns the result."""
    result = check_intake(spec)
    assert not result.accepted and result.rejection.rule == with_rule
    return result


def rejects_with_triad(spec, *, with_rule):
    """rejects(with_rule) AND the rejection payload names the where/whose/what triad (+ rule) —
    the unified spelling the Failed event uses (P2 retired intake's stage/fault/detail)."""
    result = rejects(spec, with_rule=with_rule)
    payload = result.rejection.payload
    assert payload["where"] == "intake" and payload["whose"] == "payload" and "what" in payload
    assert payload["rule"] == with_rule
    return result


# --- Accepted specs pass through unchanged ----------------------------------


def test_valid_file_spec_accepted(tmp_path):
    """A well-formed kind:file spec is accepted."""
    accepts(a_file_spec(tmp_path))


def test_valid_answer_spec_accepted():
    """A well-formed kind:answer spec is accepted."""
    accepts(an_answer_spec())


def test_accepted_spec_passes_through_unchanged(tmp_path):
    """The accepted result's spec is the exact same content as the input."""
    spec = a_file_spec(tmp_path)
    assert accepts(spec).spec == spec


def test_accepted_result_has_no_rejection():
    """An accepted result carries no rejection."""
    assert accepts(an_answer_spec()).rejection is None


# --- Objective rule ---------------------------------------------------------


def test_missing_objective_rejected():
    """A spec with no objective is rejected with the objective rule."""
    spec = an_answer_spec()
    del spec["objective"]
    rejects(spec, with_rule=RULE_OBJECTIVE_MISSING)


def test_empty_objective_rejected():
    """An empty-string objective is rejected with the objective rule."""
    spec = an_answer_spec()
    spec["objective"] = ""
    rejects(spec, with_rule=RULE_OBJECTIVE_MISSING)


# --- kind / target cross-rules (per profile) --------------------------------


def test_unknown_kind_rejected():
    """A deliverable.kind outside {file, answer, function} is rejected."""
    rejects({"deliverable": {"kind": "banana"}, "objective": "x"}, with_rule=RULE_UNKNOWN_KIND)


def test_missing_kind_rejected():
    """A deliverable with no kind is rejected as unknown_kind."""
    rejects({"deliverable": {}, "objective": "x"}, with_rule=RULE_UNKNOWN_KIND)


def test_file_without_target_rejected():
    """kind:file with no target is rejected with the file_without_target rule."""
    rejects({"deliverable": {"kind": "file"}, "objective": "x"}, with_rule=RULE_FILE_WITHOUT_TARGET)


def test_answer_with_target_rejected(tmp_path):
    """kind:answer that carries a target is rejected with the answer_with_target rule."""
    spec = {"deliverable": {"kind": "answer", "target": str(tmp_path / "x")}, "objective": "x"}
    rejects(spec, with_rule=RULE_ANSWER_WITH_TARGET)


# --- Unknown-key fail-loud --------------------------------------------------


def test_unknown_top_level_key_rejected(tmp_path):
    """A typo'd top-level key (e.g. 'contxt') fails loud, not silently ignored."""
    spec = a_file_spec(tmp_path)
    spec["contxt"] = {}
    rejects(spec, with_rule=RULE_UNKNOWN_KEY)


def test_unknown_deliverable_key_rejected(tmp_path):
    """An unknown key inside deliverable fails loud."""
    spec = a_file_spec(tmp_path)
    spec["deliverable"]["bogus"] = 1
    rejects(spec, with_rule=RULE_UNKNOWN_KEY)


# --- Workspace rule ---------------------------------------------------------


def test_unsupported_workspace_rejected():
    """A workspace value outside the supported set (in_place, worktree) is rejected."""
    spec = an_answer_spec()
    spec["workspace"] = "container"
    rejects(spec, with_rule=RULE_WORKSPACE_UNSUPPORTED)


def test_in_place_workspace_accepted():
    """An explicit workspace: in_place is accepted."""
    spec = an_answer_spec()
    spec["workspace"] = "in_place"
    accepts(spec)


# --- Context-file existence -------------------------------------------------


def test_nonexistent_context_file_rejected():
    """A context.files entry pointing at a missing path is rejected."""
    spec = an_answer_spec()
    spec["context"] = {"files": ["/definitely/not/here/nope.txt"]}
    rejects(spec, with_rule=RULE_CONTEXT_FILE_MISSING)


def test_existing_context_file_accepted(tmp_path):
    """A context.files entry that exists on disk is accepted."""
    f = tmp_path / "ctx.txt"
    f.write_text("hi")
    spec = an_answer_spec()
    spec["context"] = {"files": [str(f)]}
    accepts(spec)


# --- Rejection payload shape (where/whose/what triad) -----------------------


def test_rejection_payload_carries_triad():
    """Every rejection's payload names the where/whose/what triad plus the rule —
    the same spelling the Failed event uses (P2 unified stage/fault/detail → where/whose/what)."""
    spec = an_answer_spec()
    del spec["objective"]
    rejects_with_triad(spec, with_rule=RULE_OBJECTIVE_MISSING)


# --- P2 acceptance schema + loop rejections (P2-D13) ------------------------


def test_valid_function_spec_accepted(tmp_path):
    """A well-formed kind:function spec is accepted and passes through unchanged."""
    spec = a_function_spec(tmp_path)
    assert accepts(spec).spec == spec


def test_function_without_target_rejected(tmp_path):
    """kind 'function' requires a target, like 'file' — missing target is rejected."""
    spec = a_function_spec(tmp_path)
    del spec["deliverable"]["target"]
    rejects(spec, with_rule=RULE_FILE_WITHOUT_TARGET)


def test_function_without_acceptance_rejected(tmp_path):
    """A function deliverable with no acceptance block is rejected (the loop needs a gate)."""
    spec = a_function_spec(tmp_path)
    del spec["acceptance"]
    rejects(spec, with_rule=RULE_ACCEPTANCE_REQUIRED)


def test_function_acceptance_without_test_cmd_rejected(tmp_path):
    """A function whose acceptance omits test_cmd is rejected — test_cmd is the every-iteration gate."""
    spec = a_function_spec(tmp_path)
    spec["acceptance"] = {"test_files": ["tests/test_area.py"]}
    rejects(spec, with_rule=RULE_ACCEPTANCE_REQUIRED)


def test_test_cmd_with_in_place_rejected(tmp_path):
    """acceptance.test_cmd combined with workspace in_place is rejected — tests need isolation."""
    spec = a_function_spec(tmp_path)
    spec["workspace"] = "in_place"
    rejects(spec, with_rule=RULE_WORKTREE_REQUIRED)


def test_test_cmd_defaults_to_in_place_rejected(tmp_path):
    """A test_cmd spec that omits workspace (defaulting to in_place) is rejected worktree-required."""
    spec = a_function_spec(tmp_path)
    del spec["workspace"]
    rejects(spec, with_rule=RULE_WORKTREE_REQUIRED)


def test_worktree_non_git_target_rejected(tmp_path):
    """workspace worktree whose target is NOT inside a git repo is rejected."""
    rejects(a_function_spec(tmp_path, git=False), with_rule=RULE_TARGET_NOT_GIT_REPO)


def test_worktree_git_target_accepted(tmp_path):
    """workspace worktree whose target lives in a git repo (has a .git marker) is accepted."""
    accepts(a_function_spec(tmp_path, git=True))


def test_unknown_acceptance_key_rejected(tmp_path):
    """A bogus key inside acceptance is rejected as an unknown key (schema is fail-loud)."""
    spec = a_function_spec(tmp_path)
    spec["acceptance"]["bogus"] = 1
    rejects(spec, with_rule=RULE_UNKNOWN_KEY)


def test_acceptance_rubric_key_rejected(tmp_path):
    """acceptance.rubric is a P4 (Phase-2 judge) field, NOT in P2 — it is rejected as unknown,
    which is how the schema keeps P4 scope out of P2."""
    spec = a_function_spec(tmp_path)
    spec["acceptance"]["rubric"] = "x"
    rejects(spec, with_rule=RULE_UNKNOWN_KEY)


def test_p2_rejection_carries_triad(tmp_path):
    """A P2 loop rejection (worktree-required) carries the where/whose/what triad."""
    spec = a_function_spec(tmp_path)
    spec["workspace"] = "in_place"
    rejects_with_triad(spec, with_rule=RULE_WORKTREE_REQUIRED)


# --- P2 fix regressions: budget keys + kind-scoped worktree/acceptance ------


def test_unknown_budgets_key_rejected(tmp_path):
    """A mistyped budgets key (e.g. 'iteration' for 'iterations') is rejected, not silently
    dropped to the loop default — the fail-loud contract must hold at the budgets level too."""
    spec = a_function_spec(tmp_path)
    spec["budgets"] = {"iteration": 10}
    rejects(spec, with_rule=RULE_UNKNOWN_KEY)


def test_budgets_num_predict_is_accepted(tmp_path):
    """budgets.num_predict is a real field (T-91) — a spec declaring it passes intake."""
    spec = a_function_spec(tmp_path)
    spec["budgets"] = {"num_predict": 4096}
    accepts(spec)


def test_file_kind_with_test_cmd_rejected(tmp_path):
    """A kind:file spec carrying acceptance.test_cmd is rejected: the single-shot path would
    ignore the acceptance gate and write in place, so accepting it would silently drop the gate."""
    spec = a_file_spec(tmp_path)
    spec["acceptance"] = {"test_cmd": "pytest -q"}
    spec["workspace"] = "worktree"
    rejects(spec, with_rule=RULE_ACCEPTANCE_NOT_SUPPORTED)


def test_file_kind_with_worktree_rejected(tmp_path):
    """workspace:'worktree' on a non-loop kind is rejected — the single-shot path ignores
    workspace and writes in place, so accepting worktree would deny the requested isolation."""
    spec = a_file_spec(tmp_path)
    spec["workspace"] = "worktree"
    rejects(spec, with_rule=RULE_WORKTREE_NOT_SUPPORTED)


def test_answer_kind_with_worktree_rejected():
    """workspace:'worktree' on kind:answer is rejected (no target → the git-repo check would
    otherwise fall back to the worker's nondeterministic cwd)."""
    spec = an_answer_spec()
    spec["workspace"] = "worktree"
    rejects(spec, with_rule=RULE_WORKTREE_NOT_SUPPORTED)


# --- Language: declared-or-inferred, loop-kind-scoped (Axis A widening, R1) -------
#
# R1 (declared, infer-from-extension as default): a loop kind resolves a language from
# deliverable.language if present, else from the target's extension. The resolved language
# must be supported. `language` on a non-loop kind is rejected (silent no-op → drops the
# caller's intent, same reasoning as acceptance/worktree kind-scoping).


def test_function_declared_language_accepted(tmp_path):
    """A kind:function spec that declares a supported language is accepted."""
    spec = a_function_spec(tmp_path)
    spec["deliverable"]["language"] = "python"
    accepts(spec)


def test_function_declared_go_accepted(tmp_path):
    """Declared language 'go' passes intake — intake is language-LIST-gated, not
    implementation-gated; the loop's Go support need not exist yet for intake to accept it."""
    spec = a_function_spec(tmp_path)
    spec["deliverable"]["language"] = "go"
    accepts(spec)


def test_function_infers_python_from_py_extension(tmp_path):
    """With no declared language, a .py target infers python and is accepted (the a_function_spec
    default target is area.py). Inference is the default; declaration is the override."""
    spec = a_function_spec(tmp_path)
    assert "language" not in spec["deliverable"]
    accepts(spec)


def test_function_infers_unsupported_extension_rejected(tmp_path):
    """A target extension with no supported language (.rs) is rejected — proving inference RAN
    (an accepted result here would mean the extension was never inspected)."""
    spec = a_function_spec(tmp_path)
    spec["deliverable"]["target"] = str(tmp_path / "repo" / "area.rs")
    rejects(spec, with_rule=RULE_UNSUPPORTED_LANGUAGE)


def test_function_declared_unsupported_language_rejected(tmp_path):
    """A declared language outside the supported set is rejected, even with a .py target —
    declaration overrides inference, so the unsupported declaration wins the rejection."""
    spec = a_function_spec(tmp_path)
    spec["deliverable"]["language"] = "rust"
    rejects(spec, with_rule=RULE_UNSUPPORTED_LANGUAGE)


def test_function_unresolvable_language_rejected(tmp_path):
    """A target with no extension and no declared language cannot resolve a language → rejected
    (not silently defaulted to python)."""
    spec = a_function_spec(tmp_path)
    spec["deliverable"]["target"] = str(tmp_path / "repo" / "Makefile")
    rejects(spec, with_rule=RULE_UNSUPPORTED_LANGUAGE)


def test_file_kind_with_language_rejected(tmp_path):
    """A declared language on kind:file is rejected — the single-shot path ignores language,
    so accepting it would silently drop the caller's intent (same shape as acceptance/worktree)."""
    spec = a_file_spec(tmp_path)
    spec["deliverable"]["language"] = "python"
    rejects(spec, with_rule=RULE_LANGUAGE_NOT_SUPPORTED)


def test_answer_kind_with_language_rejected():
    """A declared language on kind:answer is rejected for the same reason."""
    spec = an_answer_spec()
    spec["deliverable"]["language"] = "go"
    rejects(spec, with_rule=RULE_LANGUAGE_NOT_SUPPORTED)


def test_unsupported_language_rejection_carries_triad(tmp_path):
    """The language rejection carries the where/whose/what triad like every other rejection."""
    spec = a_function_spec(tmp_path)
    spec["deliverable"]["language"] = "rust"
    rejects_with_triad(spec, with_rule=RULE_UNSUPPORTED_LANGUAGE)


# --- edit mode (T-110): intake accepts function + already-existing target ----
# The formerly-DANGEROUS case (T-104): a function spec pointed at an existing file. Edit mode
# (E-D2) makes it safe; intake must accept it because target-presence is an ASSEMBLY concern
# (committed-at-HEAD), never an intake rule — intake does not touch the filesystem for the target.


def test_function_with_already_existing_target_accepted(tmp_path):
    """Intake accepts a kind:function spec whose target file already exists on disk —
    target presence is an assembly-time concern (E-D2), not an intake rule."""
    from pathlib import Path
    spec = a_function_spec(tmp_path)
    target_path = Path(spec["deliverable"]["target"])
    target_path.write_text("existing content")
    assert accepts(spec)
