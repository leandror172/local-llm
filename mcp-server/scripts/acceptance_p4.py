"""Live acceptance for the P4 judge gate — real model calls, real rubric, real pinned runs.

Run it with `./run-acceptance-p4.sh` (or `make accept-p4`). Requires Ollama up with the judge
persona; it makes real GPU calls and takes roughly a minute.

**Why this is a script and not a test.** The suite covers these claims with fakes, which is
correct for CI — but a fake `chat` never reads the prompt, so the suite is structurally blind to
anything about what the judge is actually asked. These three cases are the ones whose whole point
is that a real model, given real artifacts, reaches a particular verdict. They were run ad hoc in
sessions 131 and 132 and reconstructed from scratch both times; this file is the third time being
the last.

| case | claim |
|------|-------|
| A1 | the real T-119 leak is caught — `scope_adherence` low, gate withheld |
| A2 | a real in-scope edit passes — the signal discriminates rather than firing on size |
| A5 | S17 has something to gate on: a live run's ledger event and its `calls.jsonl` record
       join by `call_id`, and `judge_verdict` is a field distinct from `auto_verdict` |

A1/A2 are REPLAYS: both runs' bytes survive only because `refs/oficina/<run_id>` pins a run's
commits before its branch is deleted (T-118 R-D2). Each case reads the base commit from its own
`AssemblyDone` event and the delivered/best content from the pinned ref, so nothing here is
synthetic — which is the entire point, since a synthetic leak is exactly what P4-T9 could not
have trusted.

A3/A4/A6 are NOT here: event folding, report survival past a prune and the failure path are
deterministic, need no model, and are covered by the suite.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RUNS = Path.home() / ".local/share/oficina/runs"
CALLS = Path.home() / ".local/share/ollama-bridge/calls.jsonl"
# One rubric per run mode (T-130). A1/A2 replay real EDIT runs; A5 drives a real GREENFIELD
# one, and judging that with the edit rubric is what made its verdict meaningless — every rung
# of that ladder presupposes a prior state. The run mode is not a parameter here, it is a
# property of each case.
EDIT_RUBRIC = "oficina-edit"
GREENFIELD_RUBRIC = "oficina-greenfield"
AN_EDIT_RUN = "edit"

sys.path.insert(0, str(REPO / "mcp-server" / "src"))

from ollama_mcp.oficina.drift import measure  # noqa: E402
from ollama_mcp.oficina.judge import default_judge, judge_deliverable, load_rubric  # noqa: E402
from ollama_mcp.oficina.ledger import Ledger  # noqa: E402
from ollama_mcp.oficina.loop import _attempt_as_diff  # noqa: E402
from ollama_mcp.oficina.store import Store  # noqa: E402
from ollama_mcp.oficina.worker import Worker  # noqa: E402

REPLAYS = [
    {
        "case": "A1",
        "what": "the real T-119 leak",
        "run_id": "dy-Bi1nMo5LIqnpzrtXRTw",
        "target": "mcp-server/src/ollama_mcp/oficina/prompt.py",
        "tests": ["mcp-server/tests/oficina/test_prompt.py"],
        "expect_passed": False,
    },
    {
        "case": "A2",
        "what": "a real in-scope edit (the negative control)",
        "run_id": "r5qHxH2CghKQ1TWhbdYzXQ",
        "target": "mcp-server/src/ollama_mcp/oficina/loop.py",
        "tests": ["mcp-server/tests/oficina/test_loop.py"],
        "expect_passed": True,
    },
]


def _git_show(rev, path):
    return subprocess.run(
        ["git", "-C", str(REPO), "show", f"{rev}:{path}"],
        capture_output=True, text=True, check=True,
    ).stdout


def _base_commit(run_id):
    for line in (RUNS / run_id / "events.jsonl").read_text().splitlines():
        event = json.loads(line)
        if event["event"] == "AssemblyDone":
            return event["payload"]["base_commit"]
    raise SystemExit(f"{run_id}: no AssemblyDone — cannot replay")


def _check(label, ok, detail=""):
    print(f"    {'PASS' if ok else 'FAIL'}  {label}{'  ' + detail if detail else ''}")
    return ok


def run_replay(case, rubric):
    """A1/A2 — judge a pinned run's real change and require the recorded verdict."""
    run_id = case["run_id"]
    if not (RUNS / run_id).exists():
        print(f"    SKIP  run dir {run_id} is gone — retention pruned the evidence")
        return False

    base, pinned = _base_commit(run_id), f"refs/oficina/{run_id}"
    baseline = _git_show(base, case["target"])
    delivered = _git_show(pinned, case["target"])
    drift = measure(baseline, delivered, [_git_show(pinned, t) for t in case["tests"]])
    change = _attempt_as_diff(baseline, delivered)

    print(f"    drift +{drift['lines_added']}/-{drift['lines_removed']}  "
          f"hunks={len(drift['hunks'])}  verbatim_vs_tests={drift['max_verbatim_run_vs_tests']}  "
          f"diff~{len(change) // 4} tok")

    objective = json.loads((RUNS / run_id / "spec.json").read_text()).get("objective", "")
    started = time.monotonic()
    verdict = judge_deliverable(
        rubric, objective, change, drift, default_judge(run_id), AN_EDIT_RUN
    )
    elapsed = time.monotonic() - started

    for crit in verdict["criteria"]:
        print(f"      {crit['name']:18} {crit['score']} (cut {crit['passing_score']})  "
              f"{str(crit['reasoning'])[:96]}")
    return _check(
        f"passed={verdict['passed']} judge_verdict={verdict['judge_verdict']}",
        verdict["passed"] is case["expect_passed"],
        f"expected passed={case['expect_passed']}  [{elapsed:.1f}s]",
    )


def _seed_repo(root: Path) -> dict:
    """A minimal committed git repo: one acceptance test, target absent at C0."""
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "test_area.py").write_text(
        "from area import area\n\n\ndef test_area():\n    assert area(3, 4) == 12\n",
        encoding="utf-8",
    )
    for args in (["add", "-A"], ["-c", "user.email=a@b", "-c", "user.name=t", "commit", "-qm", "c0"]):
        subprocess.run(["git", "-C", str(root)] + args, check=True)
    python = REPO / "mcp-server" / ".venv" / "bin" / "python"
    return {
        # "One line, with a docstring" until s133 — two requirements that cannot both hold, so
        # `objective_met` could never reach its cut of 4 and the judge said so verbatim ("does
        # not meet the one-line requirement"). Latent since A5 was written, because the old
        # assertion only checked that a verdict FIELD was present. A fixture whose objective is
        # unsatisfiable measures the fixture, not the gate.
        "objective": "Write a function area(w, h) that returns w * h, with a docstring.",
        "deliverable": {"kind": "function", "target": str(root / "area.py"), "language": "python"},
        "workspace": "worktree",
        "acceptance": {
            "test_cmd": f"{python} -m pytest -q test_area.py",
            "test_files": ["test_area.py"],
            "rubric": GREENFIELD_RUBRIC,
        },
    }


def run_a5():
    """A5 — drive a REAL run and require the ledger↔calls.jsonl join to hold by identity."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        spec = _seed_repo(tmp / "repo")
        store = Store(tmp / "store")
        worker = Worker(tmp / "store")

        run_id = store.create_run(spec)
        Ledger(store.events_path(run_id)).run_submitted({"queue_position": 1})
        worker.fifo.push(run_id)
        started = time.monotonic()
        worker.process_run(run_id)
        elapsed = time.monotonic() - started

        events = Ledger(store.events_path(run_id)).read()
        names = [e["event"] for e in events]
        payload = {e["event"]: (e.get("payload") or {}) for e in events}
        print(f"    events: {' -> '.join(names)}  [{elapsed:.1f}s]")

        ok = _check("Delivered", "Delivered" in names)
        ok &= _check("Judged emitted", "Judged" in names)

        iteration = payload.get("IterationEvaluated", {})
        judged = payload.get("Judged", {})
        # A5's store lives in a tempdir that is gone by the time anyone reads a failure, so
        # unlike A1/A2 — which replay pinned refs and can always be re-examined — whatever this
        # case does not print is unrecoverable. The reasoning is what says whether a low score
        # is the judge disagreeing or the fixture being unanswerable.
        for crit in judged.get("criteria", []):
            print(f"      {crit['name']:18} {crit['score']} (cut {crit['passing_score']})  "
                  f"{str(crit['reasoning'])[:96]}")
        ok &= _check(
            "judge_verdict is a field distinct from auto_verdict",
            "judge_verdict" in judged and "auto_verdict" in iteration,
            f"judge_verdict={judged.get('judge_verdict')} auto_verdict={iteration.get('auto_verdict')}",
        )
        # T-130: the check above passes on ANY number, which is how it stayed green while this
        # very run returned 5 and then 1 an hour apart on identical code. A rubric that fits the
        # run's mode makes the verdict mean something, so it can now be asserted rather than
        # merely counted — the deliverable is a correct one-line `area()` with a docstring.
        ok &= _check(
            "the greenfield verdict is a PASS, not just a present field",
            judged.get("passed") is True,
            f"rubric={judged.get('rubric')} judge_verdict={judged.get('judge_verdict')} "
            f"criteria={[(c['name'], c['score']) for c in judged.get('criteria', [])]}",
        )

        call_id = iteration.get("call_id")
        logged = {json.loads(line).get("call_id") for line in CALLS.read_text().splitlines()[-400:]}
        ok &= _check(
            "the iteration's call_id names a real calls.jsonl record",
            bool(call_id) and call_id in logged,
            f"call_id={call_id}",
        )
        judge_calls = [
            json.loads(line) for line in CALLS.read_text().splitlines()[-400:]
            if json.loads(line).get("run_id") == run_id
        ]
        ok &= _check(
            "both the coder's and the judge's calls are attributable to the run",
            len(judge_calls) >= 2,
            f"{len(judge_calls)} records carry run_id={run_id}",
        )
        return ok


def main():
    wanted = set(sys.argv[1:]) or {"A1", "A2", "A5"}
    if not os.environ.get("OFICINA_RUBRICS") and not (REPO / "evaluator" / "rubrics").exists():
        raise SystemExit("cannot find evaluator/rubrics — set OFICINA_RUBRICS")

    for rubric_id in (EDIT_RUBRIC, GREENFIELD_RUBRIC):
        loaded = load_rubric(rubric_id)
        cuts = ", ".join(f"{c['name']}={c.get('passing_score')}" for c in loaded["criteria"])
        print(f"rubric {loaded['id']:20} applies_to={loaded.get('applies_to')}  cuts: {cuts}")
    print()
    rubric = load_rubric(EDIT_RUBRIC)

    ok = True
    for case in REPLAYS:
        if case["case"] in wanted:
            print(f"--- {case['case']} — {case['what']} ({case['run_id']}) ---")
            ok &= run_replay(case, rubric)
            print()
    if "A5" in wanted:
        print("--- A5 — S17 has something to gate on (live run) ---")
        ok &= run_a5()
        print()

    print("ACCEPTANCE: ALL EXPECTATIONS MET" if ok else "ACCEPTANCE: FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
