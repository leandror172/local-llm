# locator.py

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass(frozen=True)
class Region:
    kind: str
    mode: str
    start: int
    end: int
    interior: str = ""
    # Optional metadata for diagnostic messages — populated by orchestrator._collect_edits
    role: str = ""
    target: str = ""   # ref-key, task-id, or field label
    file: str = ""     # repo-relative file path

class LocatorError(Exception):
    def __init__(self, message, *, kind="payload"):
        super().__init__(message)
        self.kind = kind

def locate(role: Dict[str, Any], text: str, *, task_id: Optional[str] = None) -> Region:
    locator_type = role["locator"]["type"]
    mode = role["write_mode"]

    if locator_type == "ref_block":
        return _locate_ref_block(role, text)
    elif locator_type == "field":
        return _locate_field(role, text)
    elif locator_type == "structural":
        return _locate_structural(role, text)
    elif locator_type == "checklist":
        return _locate_checklist(role, text, task_id=task_id)
    else:
        raise ValueError(f"Unknown locator type: {locator_type}")

def _locate_ref_block(role: Dict[str, Any], text: str) -> Region:
    key = role["locator"]["key"]
    open_marker = f"<!-- ref:{key} -->"
    close_marker = f"<!-- /ref:{key} -->"

    start_index = text.find(open_marker)
    end_index = text.find(close_marker)

    if start_index == -1 or end_index == -1:
        file_path = role.get('file', '<file>')
        raise LocatorError(
            f"ref block <!-- ref:{key} --> not found in {file_path} "
            f"(open found={start_index != -1}, close found={end_index != -1}). "
            f"Check the marker exists and is spelled exactly.",
            kind="payload")

    if text.count(open_marker) > 1 or text.count(close_marker) > 1:
        file_path = role.get('file', '<file>')
        raise LocatorError(
            f"ref block <!-- ref:{key} --> duplicated in {file_path}: "
            f"found {text.count(open_marker)} open markers and {text.count(close_marker)} close markers. "
            f"Each key should appear exactly once.",
            kind="payload")

    interior_start = text.index("\n", start_index) + 1
    interior_end = end_index

    return Region(
        kind="ref_block",
        mode=role["write_mode"],
        start=interior_start,
        end=interior_end,
        interior=text[interior_start:interior_end]
    )

def _locate_field(role: Dict[str, Any], text: str) -> Region:
    label = role["locator"]["label"]
    pattern = re.compile(rf"^\*\*{re.escape(label)}:\*\*\s*(.*)$", re.MULTILINE)

    matches = list(pattern.finditer(text))

    if len(matches) != 1:
        file_path = role.get('file', '<file>')
        raise LocatorError(
            f"field **{label}:** not found or duplicated in {file_path} "
            f"(found {len(matches)} matches, need exactly 1). "
            f"Check the field name is exact.",
            kind="payload")

    match = matches[0]
    start, end = match.span(1)
    return Region(
        kind="field",
        mode=role["write_mode"],
        start=start,
        end=end,
        interior=text[start:end]
    )

def _locate_structural(role: Dict[str, Any], text: str) -> Region:
    pattern = role["locator"]["pattern"]
    occurrence = role["locator"]["occurrence"] - 1
    position = role["locator"]["position"]

    lines = text.splitlines()
    matches = [i for i, line in enumerate(lines) if re.match(pattern, line)]

    if len(matches) < occurrence + 1:
        file_path = role.get('file', '<file>')
        raise LocatorError(
            f"pattern occurrence {occurrence + 1} not found in {file_path} "
            f"(pattern: {pattern!r}, found {len(matches)} total matches, need at least {occurrence + 1}). "
            f"Verify the pattern and occurrence number.",
            kind="payload")

    match_index = matches[occurrence]
    line_start = sum(len(line) + 1 for line in lines[:match_index])
    line_end = line_start + len(lines[match_index])

    if position == "after":
        return Region(
            kind="structural",
            mode=role["write_mode"],
            start=line_end + 1,
            end=line_end + 1
        )
    elif position == "before":
        return Region(
            kind="structural",
            mode=role["write_mode"],
            start=line_start,
            end=line_start
        )
    else:
        raise ValueError(f"Unknown position: {position}")

def _locate_checklist(role: Dict[str, Any], text: str, *, task_id: Optional[str] = None) -> Region:
    if not task_id:
        raise ValueError("task_id is required for checklist locator")

    id_boundary = re.compile(
        rf'(?<![A-Za-z0-9.]){re.escape(task_id)}(?![A-Za-z0-9.])'
    )
    # Search only within the first 40 chars of each candidate line: task IDs
    # always appear immediately after '- [ ]'; description text that happens
    # to mention another ID is never within that prefix.
    matches = [
        m for m in re.finditer(r'^- \[ \].*$', text, re.MULTILINE)
        if id_boundary.search(m.group()[:40])
    ]

    if len(matches) != 1:
        file_path = role.get('file', '<file>')
        raise LocatorError(
            f"task id {task_id} matched {len(matches)} checklist items in {file_path} (need exactly 1). "
            f"If 0: the task isn't an unchecked '- [ ]' line. If >1: the id is ambiguous.",
            kind="payload")

    start, end = matches[0].span()
    return Region(
        kind="checklist",
        mode=role["write_mode"],
        start=start,
        end=end,
        interior=text[start:end]
    )
