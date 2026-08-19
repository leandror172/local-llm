"""Criterion 5b — what share of REAL edits need a statement replace_unit cannot express?

Unit of measurement: one (commit, file) pair, because that is oficina's unit of work — one
run edits one file. Not a commit (may span files), not a hunk (finer than any run).

Structural, never textual. A diff line `+import math` may be a FUNCTION-LOCAL import, which is
not a top-level statement at all; and a reordered import is not a new one. So both revisions
are parsed and their top-level sets compared.

TWO classes are counted separately, because they need different remedies:
  (i)  bare statement added  — import / module constant / any top-level non-def-non-class.
       No dotted address exists, by construction. This is P3-D1 item 6's bound.
  (ii) new unit added        — a top-level def/class that did not exist before. It HAS a name,
       but `replace_unit` replaces; it cannot create. A different missing operation.
Conflating them would overstate item 6 and hide the second gap entirely.
"""
import ast
import json
import subprocess
import sys
from collections import Counter

EXCLUDE = ("test-fixtures/", "/__pycache__/", "benchmarks/results/")


def sh(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          errors="replace").stdout


def top_sets(src: str):
    """(bare top-level statements, top-level def/class names). None if it does not parse."""
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError):
        return None
    bare, names = set(), set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        else:
            try:
                bare.add(ast.unparse(n))
            except Exception:
                bare.add(ast.dump(n))
    return bare, names


# A bare string STATEMENT is a docstring. Match on any opening quote, not on triples:
# `ast.unparse` renders a module docstring as an ordinary single-quoted literal, so a
# triple-quote prefix test silently matches nothing and empties the category (s139).
_QUOTES = ("'", '"')


def classify(bare_added: list[str], units_added: list[str]) -> dict:
    """What kind of unaddressable change is this edit, given its top-level deltas?

    `bare_added` is the set difference after-minus-before over unparsed top-level
    non-def/non-class statements, so it holds statements that were ADDED *or CHANGED*. Both
    belong here: `replace_unit` addresses units by dotted path, and a module constant has no
    path whether you are adding it or editing it.

    `units_added` is kept as a SEPARATE class deliberately. A new top-level def/class has a
    name; it simply does not exist yet, so `replace_unit` cannot create it either. Folding the
    two together would overstate P3-D1 item 6's bound (which is about statements with no name
    at all) and would hide the second missing operation entirely.
    """
    imports = [x for x in bare_added if x.startswith(("import ", "from "))]
    docstrings = [x for x in bare_added if x.startswith(_QUOTES)]
    others = [x for x in bare_added if x not in imports and x not in docstrings]
    return {
        "unaddressable": bool(bare_added),
        "import": bool(imports),
        "module_docstring": bool(docstrings),
        "other_bare": bool(others),
        "new_unit": bool(units_added),
    }


def main(out_path: str) -> None:
    rows = []
    skipped = Counter()
    commits = sh("log", "--no-merges", "--format=%H", "--", "*.py").split()
    for i, c in enumerate(commits):
        # Only MODIFIED files. A created file trivially "adds" imports and is not an edit.
        out = sh("diff-tree", "--no-commit-id", "--name-status", "-r", "--diff-filter=M", c, "--", "*.py")
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            path = parts[1]
            if any(x in path for x in EXCLUDE):
                skipped["excluded path"] += 1
                continue
            before, after = sh("show", f"{c}~1:{path}"), sh("show", f"{c}:{path}")
            if not before or not after:
                skipped["revision unreadable"] += 1
                continue
            tb, ta = top_sets(before), top_sets(after)
            if tb is None or ta is None:
                skipped["does not parse"] += 1
                continue
            stat = sh("diff", "--numstat", f"{c}~1", c, "--", path).split()
            try:
                churn = int(stat[0]) + int(stat[1])
            except (IndexError, ValueError):
                churn = 0
            if churn == 0:
                skipped["no line change"] += 1
                continue
            rows.append({
                "commit": c[:8], "path": path, "churn": churn,
                "bare_added": sorted(ta[0] - tb[0]),
                "units_added": sorted(ta[1] - tb[1]),
            })
        if i % 50 == 0:
            print(f"  ...{i}/{len(commits)} commits", file=sys.stderr)

    json.dump({"rows": rows, "skipped": dict(skipped)},
                  open(out_path, "w"), indent=1)
    print(f"edits measured: {len(rows)}   skipped: {dict(skipped)}")


if __name__ == "__main__":
    main(sys.argv[1])
