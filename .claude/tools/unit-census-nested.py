"""Second pass: does DOTTED (nested) addressing fix the granularity ceiling?

Top-level addressing makes `EvaluatedLoop` (438 lines) the unit for any change
inside loop.py. Measure the ceiling again allowing `Class.method` addresses.
"""
import ast
import pathlib

ROOT = pathlib.Path("/mnt/i/workspaces/llm")
FILES = [
    "mcp-server/src/ollama_mcp/oficina/parser.py",
    "mcp-server/src/ollama_mcp/oficina/intake.py",
    "mcp-server/src/ollama_mcp/oficina/loop.py",
    "mcp-server/src/ollama_mcp/oficina/evaluator.py",
    "mcp-server/src/ollama_mcp/oficina/judge.py",
    "mcp-server/src/ollama_mcp/oficina/workspace.py",
    "mcp-server/src/ollama_mcp/oficina/transport.py",
]
FN = (ast.FunctionDef, ast.AsyncFunctionDef)


def addressable(tree):
    """Yield (dotted_name, line_span) for every nested-addressable unit."""
    for node in tree.body:
        if isinstance(node, FN):
            yield node.name, node.end_lineno - node.lineno + 1
        elif isinstance(node, ast.ClassDef):
            members = [m for m in node.body if isinstance(m, FN)]
            for m in members:
                yield f"{node.name}.{m.name}", m.end_lineno - m.lineno + 1
            # class-level attribute block: the class body minus its methods
            if not members:
                yield node.name, node.end_lineno - node.lineno + 1


print(f"{'file':<16} {'file':>5} {'top-lvl':>8} {'dotted':>7}   largest dotted unit")
print(f"{'':<16} {'lines':>5} {'ceiling':>8} {'ceiling':>7}")
print("-" * 82)

for rel in FILES:
    p = ROOT / rel
    src = p.read_text(encoding="utf-8")
    tree = ast.parse(src)
    nlines = len(src.splitlines())

    top = max(
        (n.end_lineno - n.lineno + 1
         for n in tree.body if isinstance(n, FN + (ast.ClassDef,))),
        default=0,
    )
    units = list(addressable(tree))
    name, span = max(units, key=lambda u: u[1]) if units else ("-", 0)
    print(f"{p.name:<16} {nlines:>5} {top:>7}  {span:>6}   {name} ({100*span/nlines:.0f}% of file)")

print("\n=== the two files where it matters most ===")
for rel in ["mcp-server/src/ollama_mcp/oficina/loop.py",
            "mcp-server/src/ollama_mcp/oficina/workspace.py"]:
    p = ROOT / rel
    src = p.read_text(encoding="utf-8")
    tree = ast.parse(src)
    nlines = len(src.splitlines())
    units = sorted(addressable(tree), key=lambda u: -u[1])
    print(f"\n{p.name} — {nlines} lines, {len(units)} addressable units")
    print(f"  median unit: {sorted(u[1] for u in units)[len(units)//2]} lines")
    print(f"  top 5 by size:")
    for n, s in units[:5]:
        print(f"    {n:<38} {s:>4} lines  ({100*s/nlines:>2.0f}% of file)")
