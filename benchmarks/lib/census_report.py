"""Report the criterion-5b census cuts from a saved census run.

s139 computed its published table ad hoc and it was not reproducible without re-deriving the
cuts by hand. The cuts ARE the measurement -- the headline moves by 2x between them -- so they
belong in a file that can be re-run against a new census and diffed against the old one.

Adds the ADDED-vs-CHANGED split of the module-constant slice (s140), which s139 could not make:
its `bare_added` is a set difference over unparsed strings, so `X = 1` -> `X = 2` and a new
`X = 2` are the same value. Only the CHANGED half is convertible by giving the resolver a
`Constant` kind; the ADDED half needs `insert_top_level`, exactly as an import does.
"""
import json
import sys

from unaddressable_census import classify, bound_names

# (label, path substring or None, max churn or None) -- s139's published cuts, verbatim, so a
# re-run is checkable against the table in docs/plans/oficina-p3-context-assembly.md.
CUTS = [
    ("all edits", None, None),
    ("<=10 lines", None, 10),
    ("<=40 lines", None, 40),
    ("mcp-server/src/ <=10 lines", "mcp-server/src/", 10),
    ("mcp-server/src/ <=40 lines", "mcp-server/src/", 40),
    # NOT the substring "oficina/": that also matches mcp-server/tests/oficina/, which adds 45
    # test-file edits to a 69-edit cut and moves the constant share 30.4% -> 21.1%. s139's
    # published row is oficina's own SOURCE ("30.4% ... in oficina's own source").
    ("oficina/ src <=40 lines", "src/ollama_mcp/oficina/", 40),
]


def rows_for(rows: list[dict], path_sub: str | None, max_churn: int | None) -> list[dict]:
    out = rows
    if path_sub is not None:
        out = [r for r in out if path_sub in r["path"]]
    if max_churn is not None:
        out = [r for r in out if r["churn"] <= max_churn]
    return out


def tally(rows: list[dict]) -> dict:
    """Per-edit booleans summed over a cut. `before_bound` is absent from a pre-s140 census
    file, and defaults to empty -- which reports every constant as ADDED. That is the honest
    reading of an older run (it recorded nothing about the before-names), never a zero."""
    n = len(rows)
    if not n:
        return {}
    keys = ("unaddressable", "import", "other_bare", "module_docstring", "new_unit",
            "other_bare_changed", "other_bare_added")
    acc = dict.fromkeys(keys + ("constant_convertible",), 0)
    for r in rows:
        c = classify(r["bare_added"], r["units_added"], set(r.get("before_bound", ())))
        for k in keys:
            acc[k] += bool(c[k])
        # THE decision-relevant quantity. An edit whose constant work is ENTIRELY changes is
        # converted outright by giving the resolver a `Constant` kind. An edit that ALSO adds
        # one still needs `insert_top_level`, so it is not converted -- which is why this is
        # an AND-NOT and not the `other_bare_changed` column.
        acc["constant_convertible"] += bool(c["other_bare_changed"] and not c["other_bare_added"])
    return {"n": n, **{k: 100.0 * v / n for k, v in acc.items()}}


def main(path: str) -> None:
    rows = json.load(open(path))["rows"]
    hdr = (f"{'population':30} {'n':>5} {'unaddr':>8} {'import':>8} {'const':>8} "
           f"{'ADDED':>8} {'CHANGED':>8} {'CONVERT':>8} {'docstr':>8} {'newunit':>8}")
    print(hdr)
    print("-" * len(hdr))
    for label, sub, churn in CUTS:
        t = tally(rows_for(rows, sub, churn))
        if not t:
            print(f"{label:30} {'-':>5}")
            continue
        print(f"{label:30} {t['n']:>5} {t['unaddressable']:>7.1f}% {t['import']:>7.1f}% "
              f"{t['other_bare']:>7.1f}% {t['other_bare_added']:>7.1f}% "
              f"{t['other_bare_changed']:>7.1f}% {t['constant_convertible']:>7.1f}% "
              f"{t['module_docstring']:>7.1f}% {t['new_unit']:>7.1f}%")
    print()
    print("const    = the s139 'constant' column, UNCHANGED -- the published 5b figure.")
    print("ADDED/CHANGED overlap: one edit can do both, so they need not sum to `const`.")
    print("CONVERT  = changed AND NOT added. THE number: the share a `Constant` kind converts")
    print("           outright. An edit that also ADDS a constant still needs insert_top_level.")


if __name__ == "__main__":
    main(sys.argv[1])
