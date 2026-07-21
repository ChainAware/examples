"""
ChainAware SSE helper — persistent MCP connection.

One SSE connection is opened when this module is first imported and reused
across every run() call in the same process. Works with local (localhost)
and remote MCP endpoints; does NOT delegate to Anthropic's managed MCP beta.

Requires:  pip install mcp
"""

import os
import asyncio
import threading
import logging

import anthropic
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

from scripts.agent_tools import parse_tool_names, MCP_TOOL_RE, NATIVE_TOOL_DEFS

log = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
CHAINAWARE_API_KEY = os.environ["CHAINAWARE_API_KEY"]
CHAINAWARE_MCP_URL = os.environ.get(
    "CHAINAWARE_MCP_URL", "https://prediction.mcp.chainaware.ai/sse"
)
MCP_URL = f"{CHAINAWARE_MCP_URL}?apiKey={CHAINAWARE_API_KEY}"

_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

# ── Persistent event loop ────────────────────────────────────────────────────
# One event loop lives in a daemon thread for the lifetime of the process.
# asyncio.run() would create and destroy a loop on every run() call — this
# avoids that by keeping one loop warm and submitting coroutines to it.
_loop = asyncio.new_event_loop()
threading.Thread(target=_loop.run_forever, daemon=True, name="mcp-loop").start()

# ── Persistent MCP session ───────────────────────────────────────────────────
_sess: ClientSession | None = None
_ready = threading.Event()  # set once the session is initialised


async def _open_session() -> None:
    """
    Opens the SSE connection and MCP session, then blocks on an unresolved
    Future to hold both context managers open for the process lifetime.
    Runs permanently in the background event loop.
    """
    global _sess
    log.info("MCP connecting to %s", CHAINAWARE_MCP_URL)
    async with sse_client(MCP_URL) as (read, write):
        async with ClientSession(read, write) as sess:
            await sess.initialize()
            _sess = sess
            _ready.set()
            log.info("MCP persistent session ready")
            await asyncio.Future()  # hold context managers open until process exits


# Start immediately — connection is established before the first run() call
asyncio.run_coroutine_threadsafe(_open_session(), _loop)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _to_anthropic_tool(mcp_tool) -> dict:
    return {
        "name": mcp_tool.name,
        "description": mcp_tool.description or "",
        "input_schema": mcp_tool.inputSchema,
    }


def _tool_content(mcp_resp) -> str:
    parts = [item.text for item in mcp_resp.content if hasattr(item, "text")]
    return "\n".join(parts) if parts else ""


# ── Core async loop ──────────────────────────────────────────────────────────

async def _run(
    prompt: str,
    system: str | None,
    model: str,
    allowed_mcp: set[str] | None,
    native_tools: list[dict],
    max_tokens: int,
) -> str:
    sess = _sess  # persistent session shared across all run() calls
    if sess is None:
        raise RuntimeError("MCP session unavailable")

    listed = await sess.list_tools()
    mcp_tools = [
        _to_anthropic_tool(t)
        for t in listed.tools
        if allowed_mcp is None or t.name in allowed_mcp
    ]
    log.info("MCP tools: %s", [t["name"] for t in mcp_tools])

    all_tools = mcp_tools + native_tools
    messages = [{"role": "user", "content": prompt}]
    extra = {"system": system} if system else {}

    while True:
        response = await _client.messages.create(
            model=model,
            max_tokens=max_tokens,
            tools=all_tools,
            messages=messages,
            **extra,
        )
        log.info(
            "Claude — stop_reason=%s input_tokens=%d output_tokens=%d",
            response.stop_reason,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )

        if response.stop_reason == "end_turn":
            return "\n\n".join(b.text for b in response.content if b.type == "text")

        if response.stop_reason != "tool_use":
            log.warning("Unexpected stop_reason: %s", response.stop_reason)
            return "\n\n".join(b.text for b in response.content if b.type == "text")

        messages.append({"role": "assistant", "content": response.content})

        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            log.info("Calling MCP tool: %s  args=%s", block.name, block.input)
            try:
                mcp_resp = await sess.call_tool(block.name, block.input)
                content = _tool_content(mcp_resp)
                is_error = bool(getattr(mcp_resp, "isError", False))
            except Exception as exc:
                content = f"Tool error: {exc}"
                is_error = True
                log.error("MCP tool %s failed: %s", block.name, exc)

            entry = {"type": "tool_result", "tool_use_id": block.id, "content": content}
            if is_error:
                entry["is_error"] = True
            results.append(entry)

        messages.append({"role": "user", "content": results})


# ── Public API ───────────────────────────────────────────────────────────────

def run(
    prompt: str,
    frontmatter: str = "",
    system: str = None,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 4096,
) -> str:
    """
    Send a prompt to Claude with ChainAware MCP tools available.
    Reuses the persistent SSE session opened at module import time.
    Drop-in replacement for chainaware.run().
    """
    # Wait for the session to be ready (blocks the calling thread, not the loop)
    if not _ready.wait(timeout=30):
        raise RuntimeError("MCP session did not connect within 30s")

    tool_names = parse_tool_names(frontmatter)
    allowed_mcp: set[str] = set()
    native_tools: list[dict] = []
    for raw in tool_names:
        m = MCP_TOOL_RE.match(raw)
        if m:
            allowed_mcp.add(m.group(2))
        elif raw in NATIVE_TOOL_DEFS:
            native_tools.append(NATIVE_TOOL_DEFS[raw])

    future = asyncio.run_coroutine_threadsafe(
        _run(prompt, system, model, allowed_mcp or None, native_tools, max_tokens),
        _loop,
    )
    return future.result(timeout=300)


def run_direct(
    prompt: str,
    system: str = None,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 4096,
) -> str:
    """
    Like run() but with no tool filtering — all MCP tools are available.
    Drop-in replacement for chainaware.run_direct() used by python/MCP/ scripts.
    """
    if not _ready.wait(timeout=30):
        raise RuntimeError("MCP session did not connect within 30s")

    future = asyncio.run_coroutine_threadsafe(
        _run(prompt, system, model, allowed_mcp=None, native_tools=[], max_tokens=max_tokens),
        _loop,
    )
    return future.result(timeout=300)


def api_key() -> str:
    return CHAINAWARE_API_KEY
