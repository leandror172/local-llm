#!/usr/bin/env python3
"""evaluate.py — Score a single LLM output against a rubric.

Runs a two-phase evaluation:
  Phase 1: Automated checks (compilation, JSON schema validation, etc.)
  Phase 2: LLM judge — one call per criterion with structured output

Usage:
  python3 -u evaluator/lib/evaluate.py \\
    --prompt evaluator/prompts/go/01-http-handler.md \\
    --output /path/to/llm-output.txt \\
    --rubric evaluator/rubrics/code-go.yaml \\
    --judge-model my-codegen-q3 \\
    [--skip-phase1] [--skip-phase2] [--quiet]

Output: JSON to stdout.

Exit codes:
  0 = evaluation complete (check JSON for scores)
  1 = fatal error (missing files, Ollama unreachable, etc.)
"""

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# --- Path setup ---
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "personas" / "lib"))

from ollama_client import ollama_chat  # noqa: E402  (after sys.path setup)

# Load extract-code.py via importlib (hyphenated filename not importable directly)
_extract_code_path = REPO_ROOT / "benchmarks" / "lib" / "extract-code.py"
_spec = importlib.util.spec_from_file_location("extract_code", _extract_code_path)
_extract_code_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_extract_code_mod)

strip_thinking = _extract_code_mod.strip_thinking
extract_code = _extract_code_mod.extract_code
infer_language = _extract_code_mod.infer_language

VALIDATE_CODE_WRAPPER = REPO_ROOT / "benchmarks" / "lib" / "run-validate-code.sh"
VALIDATE_HTML_WRAPPER = REPO_ROOT / "benchmarks" / "lib" / "run-validate-html.sh"

DEFAULT_JUDGE_MODEL = "my-codegen-q3"
JUDGE_TEMPERATURE = 0.1
JUDGE_TIMEOUT = 120


# ---------------------------------------------------------------------------
# Rubric loading
# ---------------------------------------------------------------------------

def load_rubric(path: str) -> dict:
    """Load and do basic validation of a rubric YAML file."""
    with open(path) as f:
        rubric = yaml.safe_load(f)
    assert "id" in rubric, f"Rubric missing 'id': {path}"
    assert "criteria" in rubric, f"Rubric missing 'criteria': {path}"
    for c in rubric["criteria"]:
        assert "name" in c, "Criterion missing 'name'"
        assert "phase" in c, f"Criterion '{c.get('name')}' missing 'phase'"
        assert "weight" in c, f"Criterion '{c.get('name')}' missing 'weight'"
    return rubric


# ---------------------------------------------------------------------------
# Prompt file parsing
# ---------------------------------------------------------------------------

def parse_prompt_file(path: str) -> tuple[dict, str]:
    """Parse YAML frontmatter + markdown body.

    Returns (metadata_dict, body_text).
    """
    text = Path(path).read_text()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if m:
        meta = yaml.safe_load(m.group(1)) or {}
        body = m.group(2).strip()
    else:
        meta = {}
        body = text.strip()
    if "id" not in meta:
        # Derive id from filename
        meta["id"] = Path(path).stem
    return meta, body


# ---------------------------------------------------------------------------
# Code extraction from LLM output
# ---------------------------------------------------------------------------

def extract_code_from_text(output_text: str, domain: str) -> tuple[str | None, str | None]:
    """Extract code block from LLM output text.

    Returns (code_text, detected_language) or (None, None) if no code found.
    """
    cleaned = strip_thinking(output_text)
    preferred_lang, _ = infer_language(domain + "-x")  # e.g. "go-x" → "go"
    result = extract_code(cleaned, preferred_lang)
    if result:
        code_text, lang = result
        return code_text, lang
    return None, None


# ---------------------------------------------------------------------------
# Phase 1: Automated checks
# ---------------------------------------------------------------------------

def _score_from_validator_output(validator_results: list[dict], criterion: dict) -> dict:
    """Map validator JSON output to a 1/3/5 score for a single criterion."""
    name = criterion["name"]
    # Aggregate error/warning counts across all files
    total_errors = sum(r.get("error_count", 0) for r in validator_results)
    total_warnings = sum(r.get("warning_count", 0) for r in validator_results)

    # Count specifically vet warnings (error type contains 'vet')
    vet_warnings = sum(
        1 for r in validator_results
        for e in r.get("errors", [])
        if "vet" in e.get("type", "").lower()
    )

    if name == "compiles":
        compile_errors = sum(
            1 for r in validator_results
            for e in r.get("errors", [])
            if "vet" not in e.get("type", "").lower()
        )
        if compile_errors == 0 and total_warnings == 0:
            score, reason = 5, f"0 errors, 0 warnings"
        elif compile_errors == 0:
            score, reason = 3, f"0 errors, {total_warnings} warning(s)"
        else:
            score, reason = 1, f"{compile_errors} compile error(s)"

    elif name == "vet_clean":
        if vet_warnings == 0:
            score, reason = 5, "0 vet warnings"
        elif vet_warnings <= 2:
            score, reason = 3, f"{vet_warnings} vet warning(s)"
        else:
            score, reason = 1, f"{vet_warnings} vet warnings (3+)"

    elif name == "shellcheck_clean":
        if total_errors == 0 and total_warnings == 0:
            score, reason = 5, "0 shellcheck errors or warnings"
        elif total_errors == 0:
            score, reason = 3, f"0 errors, {total_warnings} info/style issue(s)"
        else:
            score, reason = 1, f"{total_errors} shellcheck error(s)/warning(s)"

    elif name == "syntax_valid":
        if total_errors == 0:
            score, reason = 5, "0 syntax errors"
        else:
            score, reason = 1, f"{total_errors} syntax error(s)"

    else:
        # Unknown auto criterion — skip
        return {"name": name, "score": None, "max": 5,
                "weight": criterion["weight"], "reason": "unknown auto_source mapping"}

    return {"name": name, "score": score, "max": 5,
            "weight": criterion["weight"], "reason": reason}


def _validate_json_schema(output_text: str, validator_spec: dict) -> dict:
    """Validate that output_text is JSON matching expected fields and types."""
    required = validator_spec.get("required_fields", [])
    field_types = validator_spec.get("field_types", {})
    try:
        data = json.loads(output_text.strip())
    except json.JSONDecodeError as e:
        return {"valid": False, "reason": f"Invalid JSON: {e}"}

    missing = [f for f in required if f not in data]
    if missing:
        return {"valid": False, "reason": f"Missing fields: {missing}"}

    type_map = {"string": str, "number": (int, float), "boolean": bool, "array": list, "object": dict}
    for field, expected_type_name in field_types.items():
        if field in data:
            expected = type_map.get(expected_type_name)
            if expected and not isinstance(data[field], expected):
                return {"valid": False, "reason": f"Field '{field}' expected {expected_type_name}, got {type(data[field]).__name__}"}

    # Check confidence range if present
    if "confidence" in data:
        conf = data["confidence"]
        if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
            return {"valid": False, "reason": f"confidence={conf} out of [0.0, 1.0]"}

    return {"valid": True, "reason": "All fields present and correctly typed", "data": data}


def _invoke_code_validator(code_text: str, ext: str) -> list[dict]:
    """Write code to a temp file, run the validate-code wrapper, return results.

    Returns a list of validator result dicts (one per file checked). An empty
    stdout from the wrapper is treated as a clean result (no errors).

    Raises:
        RuntimeError: If the subprocess times out, returns invalid JSON, or the
                      wrapper script cannot be found.
    """
    with tempfile.NamedTemporaryFile(suffix=ext, mode="w", delete=False) as f:
        f.write(code_text)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [str(VALIDATE_CODE_WRAPPER), "--quiet", tmp_path],
            capture_output=True, text=True, timeout=60,
        )
        if result.stdout.strip():
            return json.loads(result.stdout)
        return [{"error_count": 0, "warning_count": 0, "errors": []}]
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        raise RuntimeError(f"validator error: {e}") from e
    finally:
        os.unlink(tmp_path)


def _validate_json(output_text: str, phase1_criteria: list[Any], scores: list[Any], validators: list[Any]):
    json_validators = [v for v in validators if v["type"] == "json_schema"]
    if json_validators:
        json_result = _validate_json_schema(output_text, json_validators[0])
        for c in phase1_criteria:
            name = c["name"]
            if name == "json_valid":
                score = 5 if json_result["valid"] else 1
                scores.append({"name": name, "score": score, "max": 5,
                               "weight": c["weight"], "reason": json_result["reason"]})
            elif name == "confidence_range":
                # confidence validity is part of _validate_json_schema
                score = 5 if json_result["valid"] else 1
                scores.append({"name": name, "score": score, "max": 5,
                               "weight": c["weight"], "reason": json_result["reason"]})


def run_phase1(output_text: str, rubric: dict, domain: str) -> list[dict]:
    """Run Phase 1 automated checks.

    Returns list of scored criterion dicts.
    """
    phase1_criteria = [c for c in rubric["criteria"] if c["phase"] == 1]
    if not phase1_criteria:
        return []

    validators = rubric.get("validators", [])
    scores = []

    # --- Code validator (Go, shell, etc.) ---
    code_validators = [v for v in validators if v["type"] == "code"]

    if code_validators:
        code_text, _ = extract_code_from_text(output_text, domain)
        if code_text is None:
            # No code found — all Phase 1 criteria score None
            for c in phase1_criteria:
                scores.append({"name": c["name"], "score": None, "max": 5,
                               "weight": c["weight"], "reason": "no code block found in output"})
            return scores

        ext = code_validators[0]["extensions"][0]
        try:
            validator_results = _invoke_code_validator(code_text, ext)
        except RuntimeError as e:
            for c in phase1_criteria:
                scores.append({"name": c["name"], "score": None, "max": 5,
                               "weight": c["weight"], "reason": str(e)})
            return scores

        for c in phase1_criteria:
            if c.get("auto_source") == "validator":
                scores.append(_score_from_validator_output(validator_results, c))

    # --- JSON schema validator ---
    _validate_json(output_text, phase1_criteria, scores, validators)

    # Fill any unevaluated Phase 1 criteria
    scored_names = {s["name"] for s in scores}
    for c in phase1_criteria:
        if c["name"] not in scored_names:
            scores.append({"name": c["name"], "score": None, "max": 5,
                           "weight": c["weight"], "reason": "no matching validator"})

    return scores


# ---------------------------------------------------------------------------
# Phase 2: LLM judge
# ---------------------------------------------------------------------------

def _build_judge_system_prompt(criterion: dict) -> str:
    scoring = criterion.get("scoring", {})
    scale_lines = "\n".join(f"  {k}: {v}" for k, v in sorted(scoring.items(), reverse=True))
    return (
        f"You are an impartial code evaluation judge. "
        f"Score an LLM output on exactly ONE criterion.\n\n"
        f"Criterion: {criterion['name']}\n"
        f"Description: {criterion['description']}\n\n"
        f"Scoring scale (1-5):\n{scale_lines}\n\n"
        f"Respond ONLY with a JSON object: "
        f'{{\"score\": <integer 1-5>, \"reasoning\": \"<one concise sentence>\"}}'
    )


def _build_judge_user_prompt(prompt_text: str, output_text: str,
                              code_text: str | None, criterion: dict) -> str:
    code_section = (
        f"## Extracted Code\n```\n{code_text}\n```\n\n"
        if code_text else ""
    )
    return (
        f"## Original Prompt\n{prompt_text}\n\n"
        f"## Model Output\n{output_text}\n\n"
        f"{code_section}"
        f"Score the output on the criterion: **{criterion['name']}**"
    )


def run_phase2(
    prompt_text: str,
    output_text: str,
    code_text: str | None,
    rubric: dict,
    judge_model: str,
    quiet: bool = False,
) -> tuple[list[dict], int, float]:
    """Run Phase 2 LLM-judge evaluation.

    Returns (scores, total_eval_count, total_duration_ms).
    """
    phase2_criteria = [c for c in rubric["criteria"] if c["phase"] == 2]
    scores = []
    total_eval_count = 0
    total_duration_ms = 0.0

    schema = {
        "type": "object",
        "properties": {
            "score": {"type": "integer", "minimum": 1, "maximum": 5},
            "reasoning": {"type": "string"},
        },
        "required": ["score", "reasoning"],
    }

    for criterion in phase2_criteria:
        if not quiet:
            print(f"  [phase2] judging: {criterion['name']} ...", file=sys.stderr)

        system_prompt = _build_judge_system_prompt(criterion)
        user_prompt = _build_judge_user_prompt(prompt_text, output_text, code_text, criterion)

        result = None
        try:
            result = ollama_chat(
                prompt=user_prompt,
                model=judge_model,
                system=system_prompt,
                temperature=JUDGE_TEMPERATURE,
                think=False,
                format_schema=schema,
                timeout=JUDGE_TIMEOUT,
            )
            parsed = json.loads(result["content"])
            score = int(parsed["score"])
            reasoning = str(parsed.get("reasoning", ""))
        except Exception as e:
            score = None
            reasoning = f"judge error: {e}"

        scores.append({
            "name": criterion["name"],
            "score": score,
            "max": 5,
            "weight": criterion["weight"],
            "reason": reasoning,
        })
        if result is not None:
            total_eval_count += result.get("eval_count", 0)
            total_duration_ms += result.get("total_duration_ms", 0.0)

    return scores, total_eval_count, total_duration_ms


# ---------------------------------------------------------------------------
# Score aggregation
# ---------------------------------------------------------------------------

def weighted_average(scores: list[dict]) -> float | None:
    """Compute weighted average, ignoring criteria where score is None."""
    valid = [(s["score"], s["weight"]) for s in scores if s["score"] is not None]
    if not valid:
        return None
    total_weight = sum(w for _, w in valid)
    if total_weight == 0:
        return None
    return sum(score * w for score, w in valid) / total_weight


def aggregate_scores(
    phase1: list[dict],
    phase2: list[dict],
    p2_eval_count: int,
    p2_duration_ms: float,
) -> dict:
    """Build the full evaluation result dict."""
    p1_score = weighted_average(phase1)
    p2_score = weighted_average(phase2)

    all_scores = phase1 + phase2
    overall = weighted_average(all_scores)
    pct = round(overall / 5.0 * 100, 1) if overall is not None else None

    return {
        "phase1": {
            "criteria": phase1,
            "weighted_score": round(p1_score, 3) if p1_score is not None else None,
        },
        "phase2": {
            "criteria": phase2,
            "weighted_score": round(p2_score, 3) if p2_score is not None else None,
            "judge_eval_count": p2_eval_count,
            "judge_duration_ms": round(p2_duration_ms, 1),
        },
        "overall": {
            "weighted_score": round(overall, 3) if overall is not None else None,
            "percentage": pct,
        },
    }


# ---------------------------------------------------------------------------
# Main helpers
# ---------------------------------------------------------------------------

def _extract_output_text(raw: str) -> str:
    """Return the model output text from a raw file.

    If raw is an Ollama API JSON response, unwrap message.content;
    otherwise treat the whole string as plain text.
    """
    try:
        api_resp = json.loads(raw)
        if "message" in api_resp and "content" in api_resp["message"]:
            return api_resp["message"]["content"]
    except json.JSONDecodeError:
        pass
    return raw


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a single LLM output against a rubric.")
    parser.add_argument("--prompt", required=True, help="Path to prompt file (YAML frontmatter + markdown)")
    parser.add_argument("--output", required=True, help="Path to LLM output file (raw text or Ollama JSON)")
    parser.add_argument("--rubric", required=True, help="Path to rubric YAML file")
    parser.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL, help="Ollama model for Phase 2 judging")
    parser.add_argument("--skip-phase1", action="store_true", help="Skip Phase 1 automated checks")
    parser.add_argument("--skip-phase2", action="store_true", help="Skip Phase 2 LLM judge")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output (stderr)")
    args = parser.parse_args()

    # Load inputs
    try:
        rubric = load_rubric(args.rubric)
        prompt_meta, prompt_text = parse_prompt_file(args.prompt)
        raw = Path(args.output).read_text()
    except (FileNotFoundError, AssertionError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Detect if output file is Ollama API JSON
    output_text = _extract_output_text(raw)

    domain = rubric.get("domain", prompt_meta.get("domain", "general"))
    prompt_id = prompt_meta.get("id", Path(args.prompt).stem)

    # Extract code once (reused by both phases)
    code_text, _ = extract_code_from_text(output_text, domain)

    if not args.quiet:
        print(f"[evaluate] prompt={prompt_id} rubric={rubric['id']} judge={args.judge_model}", file=sys.stderr)

    # Phase 1
    phase1_scores = []
    if not args.skip_phase1:
        if not args.quiet:
            print(f"  [phase1] running automated checks ...", file=sys.stderr)
        phase1_scores = run_phase1(output_text, rubric, domain)

    # Phase 2
    phase2_scores = []
    p2_eval_count = 0
    p2_duration_ms = 0.0
    if not args.skip_phase2:
        phase2_scores, p2_eval_count, p2_duration_ms = run_phase2(
            prompt_text, output_text, code_text, rubric, args.judge_model, args.quiet
        )

    result = {
        "prompt_id": prompt_id,
        "rubric_id": rubric["id"],
        "judge_model": args.judge_model,
        **aggregate_scores(phase1_scores, phase2_scores, p2_eval_count, p2_duration_ms),
        "evaluated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
