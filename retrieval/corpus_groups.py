"""Shared corpus group-matching (ref:ltg-corpus, T-65).

The provenance-group rules in corpus.yaml are an ordered list of
`{match: <glob>, tag: <group>}` entries; first match wins. Both the corpus
manifest builder (freeze step) and store.py (row-level source_group derivation)
resolve a path → group through this single matcher, so the glob semantics —
notably `**/` matching zero leading dirs — live in exactly one place.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

DEFAULT_CONFIG = Path(__file__).parent / "corpus.yaml"
UNGROUPED = "ungrouped"


def glob_to_regex(pattern: str) -> re.Pattern:
    """Compile a glob to an anchored regex.

    `**` matches any chars including `/` (recursive); `**/` matches any number
    of leading dirs INCLUDING zero (so `**/foo` matches `foo` at the root too);
    `*` matches any chars except `/`; `?` matches one non-`/`.
    """
    out: list[str] = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            if pattern[i + 1 : i + 2] == "*":
                if pattern[i + 2 : i + 3] == "/":
                    out.append("(?:.*/)?")
                    i += 3
                else:
                    out.append(".*")
                    i += 2
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def assign_group(path: str, groups: list[dict], default: str = UNGROUPED) -> str:
    """First matching rule wins (order in corpus.yaml is significant)."""
    for rule in groups:
        if glob_to_regex(rule["match"]).match(path):
            return rule["tag"]
    return default


def load_group_rules(config_path: Path = DEFAULT_CONFIG) -> list[dict]:
    with Path(config_path).open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("groups", [])
