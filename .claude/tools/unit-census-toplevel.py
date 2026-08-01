"""Census of top-level constructs in oficina's own modules.

Answers: if S3 addresses edits by SYMBOL, what fraction of a real module is
addressable, and what is left over?
"""
import ast
import pathlib
import collections

ROOT = pathlib.Path("/mnt/i/workspaces/llm")
FILES = [
    "mcp-server/src/ollama_mcp/oficina/parser.py",
    "mcp-server/src/ollama_mcp/oficina/intake.py",
    "mcp-server/src/ollama_mcp/oficina/loop.py",
    "mcp-server/src/ollama_mcp/oficina/evaluator.py",
    "mcp-server/src/ollama_mcp/oficina/judge.py",
    "mcp-server/src/ollama_mcp/oficina/drift.py",
    "mcp-server/src/ollama_mcp/oficina/prompt.py",
    "mcp-server/src/ollama_mcp/oficina/workspace.py",
    "mcp-server/src/ollama_mcp/oficina/transport.py",
    "mcp-server/src/ollama_mcp/oficina/report.py",
]

def describe(node):
    """Return (category, name-or-None) for a top-level statement."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return "function", node.name
    if isinstance(node, ast.ClassDef):
        return "class", node.name
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return "import", None
    if isinstance(node, ast.Assign):
        tgts = [t.id for t in node.targets if isinstance(t, ast.Name)]
        return "assign", tgts[0] if tgts else None
    if isinstance(node, ast.AnnAssign):
        return "assign", node.target.id if isinstance(node.target, ast.Name) else None
    if isinstance(node, ast.Expr):
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return "docstring", None
        return "bare_expr", None
    if isinstance(node, ast.If):
        return "if_block", None
    if isinstance(node, ast.Try):
        return "try_block", None
    return type(node).__name__, None


totals = collections.Counter()
lines_by_cat = collections.Counter()
print(f"{'file':<16} {'lines':>6}  top-level breakdown")
print("-" * 78)

for rel in FILES:
    p = ROOT / rel
    src = p.read_text(encoding="utf-8")
    tree = ast.parse(src)
    nlines = len(src.splitlines())
    per = collections.Counter()
    for node in tree.body:
        cat, name = describe(node)
        per[cat] += 1
        totals[cat] += 1
        span = (getattr(node, "end_lineno", node.lineno) or node.lineno) - node.lineno + 1
        lines_by_cat[cat] += span
    shown = ", ".join(f"{k}={v}" for k, v in sorted(per.items()))
    print(f"{p.name:<16} {nlines:>6}  {shown}")

print("\n=== totals across 10 modules ===")
named = totals["function"] + totals["class"] + totals["assign"]
unnamed = sum(v for k, v in totals.items() if k not in ("function", "class", "assign"))
for k, v in totals.most_common():
    print(f"  {k:<12} count={v:<4} lines={lines_by_cat[k]}")
print(f"\n  addressable by a NAME (function/class/assign): {named}")
print(f"  NOT name-addressable:                          {unnamed}")
tl = sum(totals.values())
print(f"  → {named}/{tl} = {100*named/tl:.1f}% of top-level statements carry a name")
code_lines = sum(v for k, v in lines_by_cat.items())
named_lines = lines_by_cat["function"] + lines_by_cat["class"] + lines_by_cat["assign"]
print(f"  → {named_lines}/{code_lines} = {100*named_lines/code_lines:.1f}% of top-level LINES sit under a name")

# Largest single unit — the granularity ceiling
print("\n=== largest named unit per file (the re-emit cost ceiling) ===")
for rel in FILES:
    p = ROOT / rel
    tree = ast.parse(p.read_text(encoding="utf-8"))
    biggest = None
    for node in tree.body:
        cat, name = describe(node)
        if cat in ("function", "class"):
            span = node.end_lineno - node.lineno + 1
            if biggest is None or span > biggest[1]:
                biggest = (name, span)
    total = len(p.read_text(encoding="utf-8").splitlines())
    if biggest:
        print(f"  {p.name:<16} {biggest[0]:<34} {biggest[1]:>4} lines "
              f"({100*biggest[1]/total:.0f}% of file)")
