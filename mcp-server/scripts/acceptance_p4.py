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
RUBRIC = "oficina-edit"

sys.path.insert(0, str(REPO / "mcp-server" / "src"))

from ollama_mcp.oficina.drift import measure  # noqa: E402
from ollama_mcp.oficina.judge import judge_deliverable, load_rubric  # noqa: E402
from ollama_mcp.oficina.ledger import Ledger  # noqa: E402
from ollama_mcp.oficina.loop import _attempt_as_diff  # noqa: E402
from ollama_mcp.oficina.store import Store  # noqa: E402
from ollama_mcp.oficina.worker import Worker, default_judge  # noqa: E402

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
    verdict = judge_deliverable(rubric, objective, change, drift, default_judge(run_id))
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
        "objective": "Write a function area(w, h) that returns w * h. One line, with a docstring.",
        "deliverable": {"kind": "function", "target": str(root / "area.py"), "language": "python"},
        "workspace": "worktree",
        "acceptance": {
            "test_cmd": f"{python} -m pytest -q test_area.py",
            "test_files": ["test_area.py"],
            "rubric": RUBRIC,
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
        ok &= _check(
            "judge_verdict is a field distinct from auto_verdict",
            "judge_verdict" in judged and "auto_verdict" in iteration,
            f"judge_verdict={judged.get('judge_verdict')} auto_verdict={iteration.get('auto_verdict')}",
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

    rubric = load_rubric(RUBRIC)
    cuts = ", ".join(f"{c['name']}={c.get('passing_score')}" for c in rubric["criteria"])
    print(f"rubric {rubric['id']}  cuts: {cuts}\n")

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
