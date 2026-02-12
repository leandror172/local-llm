"""Entry point for `python -m ollama_mcp`.

When you run `python -m some_package`, Python looks for __main__.py inside
that package and executes it. This file is intentionally thin — all logic
lives in server.py. The only job here is to import the configured server
and start it with stdio transport.

stdio transport means the server reads JSON-RPC messages from stdin and
writes responses to stdout. This is how Claude Code communicates with MCP
servers — it spawns them as subprocesses and pipes data through stdin/stdout.
"""

from ollama_mcp.server import mcp

mcp.run(transport="stdio")
