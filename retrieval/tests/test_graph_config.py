"""
Tests for retrieval/graph.py

Covers:
- load_graph_config(): reads a YAML config file and returns the contents of its top-level `graph:` section as a dict.
- load_graph_config(): raises FileNotFoundError if the file does not exist.
- load_graph_config(): raises KeyError if the file has no `graph:` section.
- load_graph_config(): raises KeyError if any required key is missing from the graph section.
"""

import pytest
import yaml
from pathlib import Path

from graph import load_graph_config


@pytest.fixture
def valid_graph_config_path(tmp_path) -> Path:
    config_content = """
graph:
  tau_floor: 0.70
  top_k: 10
  resolutions:
    coarse: 0.5
    fine: 1.5
  seed: 42
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)
    return config_file


def test_returns_graph_section_with_expected_keys(valid_graph_config_path):
    config = load_graph_config(valid_graph_config_path)
    assert set(config.keys()) == {"tau_floor", "top_k", "resolutions", "seed"}


def test_values_keep_yaml_types(valid_graph_config_path):
    config = load_graph_config(valid_graph_config_path)
    assert isinstance(config["tau_floor"], float)
    assert isinstance(config["top_k"], int)
    assert isinstance(config["resolutions"], dict)
    assert isinstance(config["resolutions"]["coarse"], float)
    assert isinstance(config["resolutions"]["fine"], float)
    assert isinstance(config["seed"], int)


def test_missing_file_raises_filenotfound(tmp_path):
    missing_file = tmp_path / "missing_config.yaml"
    with pytest.raises(FileNotFoundError, match=str(missing_file)):
        load_graph_config(missing_file)


def test_missing_graph_section_raises_keyerror(valid_graph_config_path):
    invalid_content = """
other_section:
  key: value
"""
    valid_graph_config_path.write_text(invalid_content)
    with pytest.raises(KeyError, match="graph"):
        load_graph_config(valid_graph_config_path)


def test_empty_config_file_raises_keyerror_not_typeerror(tmp_path):
    empty_file = tmp_path / "empty.yaml"
    empty_file.write_text("")
    with pytest.raises(KeyError, match="graph"):
        load_graph_config(empty_file)


def test_all_comments_config_file_raises_keyerror_not_typeerror(tmp_path):
    comments_only_file = tmp_path / "comments_only.yaml"
    comments_only_file.write_text("# just a comment\n# another comment\n")
    with pytest.raises(KeyError, match="graph"):
        load_graph_config(comments_only_file)


@pytest.mark.parametrize("missing_key", ["tau_floor", "top_k", "resolutions", "seed"])
def test_missing_required_key_raises_keyerror(tmp_path, missing_key):
    graph = {
        "tau_floor": 0.70,
        "top_k": 10,
        "resolutions": {"coarse": 0.5, "fine": 1.5},
        "seed": 42,
    }
    del graph[missing_key]
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.safe_dump({"graph": graph}))
    with pytest.raises(KeyError, match=missing_key):
        load_graph_config(config_file)
