#!/usr/bin/env python3
"""
Runs the WhatsApp MCP server with SSE transport instead of the upstream's
hardcoded stdio transport.

FastMCP reads host/port from its Pydantic Settings object, which is populated
from env vars (FASTMCP_HOST / FASTMCP_PORT) at instantiation time.
We set those before importing main.py so they're baked in when FastMCP("whatsapp")
is called. We also monkey-patch run() to force transport="sse" since main.py
hardcodes transport='stdio'.
"""
import os
import sys

sys.path.insert(0, "/opt/whatsapp-mcp-server")

_port = int(os.environ.get("MCP_PORT", "8000"))

# Set BEFORE FastMCP is imported/instantiated — Pydantic BaseSettings
# reads env vars at __init__ time, not at run() time.
os.environ["FASTMCP_HOST"] = "0.0.0.0"
os.environ["FASTMCP_PORT"] = str(_port)

from mcp.server.fastmcp import FastMCP  # noqa: E402

_original_run = FastMCP.run


def _sse_run(self, transport=None, **kwargs):  # noqa: ANN001
    # Also set via settings object in case it was already instantiated
    if hasattr(self, "settings"):
        self.settings.host = "0.0.0.0"
        self.settings.port = _port
    # Strip any kwargs the current mcp version doesn't accept
    return _original_run(self, transport="sse")


FastMCP.run = _sse_run

import runpy  # noqa: E402

runpy.run_path("/opt/whatsapp-mcp-server/main.py", run_name="__main__")
