"""Lightweight structural test for retrieval/run-rebuild-all.sh (T-71).

We can't exercise this wrapper end-to-end in CI: anchors.py's rebuild path
makes a real embedding call (Ollama), and running it would rewrite/require a
live index. Instead, this parses the script text and asserts the invariants
that matter for the T-71 backup-chain design:

- the authoritative --backup-only backup runs before any derivation stage
- store/anchors/communities are invoked with --no-backup (graph is not,
  since graph.py takes no backup at all)
- stages run in the documented order: store -> anchors -> graph -> communities
"""

from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent / "run-rebuild-all.sh"


def _script_text() -> str:
    return SCRIPT_PATH.read_text()


def test_script_exists_and_executable():
    assert SCRIPT_PATH.exists()
    assert SCRIPT_PATH.stat().st_mode & 0o111, "run-rebuild-all.sh must be executable"


def test_backup_only_runs_before_any_stage_invocation():
    text = _script_text()
    backup_only_pos = text.index("--backup-only")

    stage_pos = {
        "store": text.index('"$SCRIPT_DIR/store.py" \\\n  --input'),
        "anchors": text.index('"$SCRIPT_DIR/anchors.py"'),
        "graph": text.index('"$SCRIPT_DIR/graph.py"'),
        "communities": text.index('"$SCRIPT_DIR/communities.py"'),
    }

    for stage, pos in stage_pos.items():
        assert backup_only_pos < pos, f"--backup-only must precede the {stage} stage invocation"


def test_stages_run_in_documented_order():
    text = _script_text()
    store_pos = text.index('--input "$EMBEDDINGS"')
    anchors_pos = text.index('"$SCRIPT_DIR/anchors.py"')
    graph_pos = text.index('"$SCRIPT_DIR/graph.py"')
    communities_pos = text.index('"$SCRIPT_DIR/communities.py"')

    assert store_pos < anchors_pos < graph_pos < communities_pos


def test_store_anchors_communities_pass_no_backup():
    text = _script_text()

    # Isolate each stage's invocation block (from its script name to the next
    # blank-line-separated "echo ==" stage marker, or EOF).
    markers = ['"$SCRIPT_DIR/store.py" \\\n  --input', '"$SCRIPT_DIR/anchors.py"',
               '"$SCRIPT_DIR/graph.py"', '"$SCRIPT_DIR/communities.py"']
    starts = [text.index(m) for m in markers]
    ends = starts[1:] + [len(text)]

    store_block = text[starts[0]:ends[0]]
    anchors_block = text[starts[1]:ends[1]]
    graph_block = text[starts[2]:ends[2]]
    communities_block = text[starts[3]:ends[3]]

    assert "--no-backup" in store_block
    assert "--no-backup" in anchors_block
    assert "--no-backup" in communities_block
    # graph.py takes no backup at all — it must not be passed a flag it lacks.
    assert "--no-backup" not in graph_block


def test_embeddings_flag_required():
    text = _script_text()
    assert "--embeddings" in text
    assert "is required" in text
