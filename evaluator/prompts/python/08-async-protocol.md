---
id: python-08-async-protocol
domain: python
difficulty: hard
timeout: 420
description: Custom asyncio protocol for a line-delimited text server
---

Implement a custom asyncio protocol for a line-delimited text server (stdlib only).

1. `LineProtocol(asyncio.Protocol)`: buffers bytes, splits on `\n`, calls `line_received(line: str)`

2. `EchoServerProtocol(LineProtocol)`:
   - `PING\n` → `PONG\n`
   - `QUIT\n` → close gracefully
   - Everything else → `ECHO: {line}\n`

3. `CommandClientProtocol(LineProtocol)`:
   - `line_received` → `asyncio.Queue`
   - `send(line: str)`, `async def read_response(timeout=5.0) -> str`

4. `serve(host, port) -> asyncio.AbstractServer`

5. Async `main()` integration test: start server, connect client, send PING/hello/QUIT

Requirements: stdlib `asyncio` only, full type hints, `logging` for connection events
