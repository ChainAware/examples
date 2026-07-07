import os
import re

# ---------------------------------------------------------------------------
# One-time registry: connection details for every MCP server used by ANY agent.
# Keyed by the server "name" exactly as it appears in tools: mcp__<name>__<tool>
# ---------------------------------------------------------------------------
MCP_SERVER_REGISTRY = {
    "chainaware-behavioral-prediction": {
        "type": "url",
        "url": os.environ.get("CHAINAWARE_MCP_URL", "https://prediction.mcp.chainaware.ai/sse"),
        "name": "chainaware-behavioral-prediction",
        "authorization_token": os.environ["CHAINAWARE_API_KEY"],
    },
    # add other MCP servers here as you wire up more agents
    # "some-other-server": {"type": "url", "url": "...", "name": "some-other-server", "authorization_token": "..."},
}

# Native (non-MCP) Anthropic tools an agent.md might list under `tools:`
NATIVE_TOOL_DEFS = {
    "WebSearch": {"type": "web_search_20250305", "name": "web_search"},
    "WebFetch": {"type": "web_fetch_20250910", "name": "web_fetch"},
}

MCP_TOOL_RE = re.compile(r"^mcp__([^_].*?)__([^_].*)$")


def parse_tool_names(frontmatter: str) -> list[str]:
    """Extract the comma-separated `tools:` list from agent frontmatter."""
    m = re.search(r"^tools:\s*(.+)$", frontmatter, re.MULTILINE)
    if not m:
        return []
    return [t.strip() for t in m.group(1).split(",") if t.strip()]


def build_mcp_and_tools(frontmatter: str) -> tuple[list[dict], list[dict]]:
    """
    Given an agent's frontmatter, return (mcp_servers, tools) ready to pass
    straight into client.beta.messages.create(..., betas=["mcp-client-2025-11-20"]).

    - Groups mcp__<server>__<tool> entries by server, builds one mcp_toolset
      per server with only the referenced tools enabled (denylist-by-default).
    - Maps bare native tool names (WebSearch, WebFetch, ...) to their real
      Anthropic tool definitions.
    - Raises if an agent references an MCP server not in MCP_SERVER_REGISTRY,
      so a missing registration fails loudly instead of silently granting
      zero or unrestricted tools.
    """
    tool_names = parse_tool_names(frontmatter)

    servers_needed: dict[str, list[str]] = {}
    native_tools: list[dict] = []

    for raw in tool_names:
        match = MCP_TOOL_RE.match(raw)
        if match:
            server_name, tool_name = match.group(1), match.group(2)
            servers_needed.setdefault(server_name, []).append(tool_name)
        elif raw in NATIVE_TOOL_DEFS:
            native_tools.append(NATIVE_TOOL_DEFS[raw])
        else:
            raise ValueError(
                f"Unrecognized tool entry '{raw}' in agent frontmatter — "
                f"add it to NATIVE_TOOL_DEFS if it's a native tool, or check spelling."
            )

    mcp_servers = []
    mcp_toolsets = []
    for server_name, tools_for_server in servers_needed.items():
        if server_name not in MCP_SERVER_REGISTRY:
            raise ValueError(
                f"Agent references MCP server '{server_name}' which is not in "
                f"MCP_SERVER_REGISTRY — add its connection details there first."
            )
        mcp_servers.append(MCP_SERVER_REGISTRY[server_name])
        mcp_toolsets.append({
            "type": "mcp_toolset",
            "mcp_server_name": server_name,
            "default_config": {"enabled": False},
            "configs": {t: {"enabled": True} for t in tools_for_server},
        })

    return mcp_servers, mcp_toolsets + native_tools