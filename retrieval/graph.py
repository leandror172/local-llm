"""LTG Phase 4 — graph assembly.

Loads graph-build configuration from the retrieval config.yaml `graph:` section.
"""

from pathlib import Path
import yaml

REQUIRED_KEYS = ("tau_floor", "top_k", "resolutions", "seed")
RESOLUTIONS_KEYS = ("coarse", "fine")

def load_graph_config(path: Path | str) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file {path} does not exist")
    
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    
    if "graph" not in raw:
        raise KeyError("Missing 'graph' section in config file")
    
    graph_config = raw["graph"]
    
    missing_keys = [key for key in REQUIRED_KEYS if key not in graph_config]
    if missing_keys:
        raise KeyError(f"Missing required key(s) in 'graph' section: {', '.join(missing_keys)}")
    
    resolutions = graph_config.get("resolutions", {})
    missing_resolutions_keys = [key for key in RESOLUTIONS_KEYS if key not in resolutions]
    if missing_resolutions_keys:
        raise KeyError(f"Missing required resolution key(s) in 'graph' section: {', '.join(missing_resolutions_keys)}")
    
    return graph_config
