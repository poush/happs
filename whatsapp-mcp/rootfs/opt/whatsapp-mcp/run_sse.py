#!/usr/bin/env python3
"""
Runs the WhatsApp MCP server with SSE transport instead of the upstream's
hardcoded stdio transport.

Strategy: monkey-patch FastMCP.run() before importing main.py so that
when main.py calls `mcp.run(transport='stdio')` it actually starts an
SSE/HTTP server on 0.0.0.0:MCP_PORT.
"""
import os
import sys

sys.path.insert(0, "/opt/whatsapp-mcp-server")

from mcp.server.fastmcp import FastMCP  # noqa: E402 — must come before main import

_original_run = FastMCP.run


def _sse_run(self, transport=None, **kwargs):  # noqa: ANN001
    port = int(os.environ.get("MCP_PORT", "8000"))
    return _original_run(self, transport="sse", host="0.0.0.0", port=port, **kwargs)


FastMCP.run = _sse_run

# Execute main.py as __main__ so `if __name__ == "__main__":` blocks fire.
# The FastMCP class object is shared across modules, so the patch above
# is already in effect when main.py calls mcp.run().
import runpy  # noqa: E402

runpy.run_path("/opt/whatsapp-mcp-server/main.py", run_name="__main__")
