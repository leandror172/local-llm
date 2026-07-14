import subprocess
import json
import os
import sys
from pathlib import Path
import tempfile

def _run_scan(store_root: str) -> tuple[int, str]:
    scan_path = Path(os.environ.get("SCAN_PATH", Path(__file__).parent.parent / "oficina-runs-scan.py"))
    if not scan_path.exists():
        raise FileNotFoundError(f"Scan script not found at {scan_path}")
    
    env = os.environ.copy()
    env["OFICINA_ROOT"] = store_root
    result = subprocess.run(
        [sys.executable, str(scan_path)],
        input="",
        capture_output=True,
        text=True,
        check=False,
        env=env
    )
    return result.returncode, result.stdout

def _make_run(store_root: str, run_id: str, events: list[dict]) -> None:
    store_dir = Path(store_root)
    run_dir = store_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    events_jsonl = [json.dumps(event) for event in events]
    events_jsonl.append("")  # Add an empty line to simulate a torn last line (optional)
    
    with open(run_dir / "events.jsonl", "w") as f:
        f.write("\n".join(events_jsonl))

def _submitted(run_id_origin: str = "/mnt/i/workspaces/llm") -> dict:
    return {
        "offset": 0,
        "ts": "t",
        "event": "RunSubmitted",
        "payload": {"queue_position": 1, "submitted_from": run_id_origin}
    }

def _delivered() -> dict:
    return {
        "offset": 3,
        "ts": "t",
        "event": "Delivered",
        "payload": {"report": {}, "deliverable": {"kind": "answer", "answer": "x"}}
    }

def test_terminal_unmarked_run_is_surfaced_with_origin() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        store_root = tmpdir
        run_id = "R1"
        
        _make_run(store_root, run_id, [_submitted(), _delivered()])
        
        returncode, stdout = _run_scan(store_root)
        assert returncode == 0
        assert run_id in stdout
        assert "/mnt/i/workspaces/llm" in stdout
        
        run_dir = Path(store_root) / "runs" / run_id
        surfaced_marker = run_dir / "surfaced"
        assert surfaced_marker.exists()

def test_second_scan_emits_nothing() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        store_root = tmpdir
        run_id = "R1"
        
        _make_run(store_root, run_id, [_submitted(), _delivered()])
        
        returncode, stdout = _run_scan(store_root)
        assert returncode == 0
        assert run_id in stdout  # first scan surfaces the run

        # Second scan should not emit anything (surfaced marker written)
        returncode, stdout = _run_scan(store_root)
        assert returncode == 0
        assert stdout.strip() == ""

def test_non_terminal_run_not_surfaced() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        store_root = tmpdir
        run_id = "R1"
        
        _make_run(store_root, run_id, [_submitted()])
        
        returncode, stdout = _run_scan(store_root)
        assert returncode == 0
        assert stdout.strip() == ""
        
        run_dir = Path(store_root) / "runs" / run_id
        surfaced_marker = run_dir / "surfaced"
        assert not surfaced_marker.exists()

def test_failed_run_is_surfaced() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        store_root = tmpdir
        run_id = "R1"
        
        _make_run(store_root, run_id, [
            _submitted(),
            {"offset": 1, "ts": "t", "event": "Failed", "payload": {"where": "generation", "whose": "model", "what": "boom"}}
        ])
        
        returncode, stdout = _run_scan(store_root)
        assert returncode == 0
        assert run_id in stdout

def test_missing_store_prints_nothing() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent_path = Path(tmpdir) / "nonexistent"
        
        returncode, stdout = _run_scan(str(non_existent_path))
        assert returncode == 0
        assert stdout.strip() == ""

def test_torn_last_line_tolerated() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        store_root = tmpdir
        run_id = "R1"
        
        _make_run(store_root, run_id, [_submitted(), _delivered()])
        events_path = Path(store_root) / "runs" / run_id / "events.jsonl"
        with open(events_path, "a") as f:
            f.write('{"offset": 4, "ev')  # genuinely torn: invalid JSON fragment

        returncode, stdout = _run_scan(store_root)
        assert returncode == 0
        assert run_id in stdout  # Delivered is still the last VALID event

if __name__ == "__main__":
    test_functions = [
        test_terminal_unmarked_run_is_surfaced_with_origin,
        test_second_scan_emits_nothing,
        test_non_terminal_run_not_surfaced,
        test_failed_run_is_surfaced,
        test_missing_store_prints_nothing,
        test_torn_last_line_tolerated
    ]
    failed = False
    for test_func in test_functions:
        try:
            test_func()
            print(f"PASS {test_func.__name__}")
        except AssertionError as exc:
            print(f"FAIL {test_func.__name__}: {exc}")
            failed = True
    sys.exit(1 if failed else 0)
