"""
ChainAware shared helper — reused by all example scripts.

Sets up the Anthropic client with the ChainAware MCP server and
exposes a single `run(prompt)` function that calls Claude with
the MCP tools available.
"""

import os
import anthropic

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
CHAINAWARE_API_KEY = os.environ["CHAINAWARE_API_KEY"]

# The ChainAware MCP server — API key embedded in the URL for connection auth.
# Each tool also receives the API key explicitly in the prompt.
MCP_SERVER = {
    "type": "url",
    "url": f"https://prediction.mcp.chainaware.ai/sse?apiKey={CHAINAWARE_API_KEY}",
    "name": "chainaware-behavioral-prediction",
}

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def run(prompt: str, model: str = "claude-opus-4-6", max_tokens: int = 4096) -> str:
    """
    Send a prompt to Claude with the ChainAware MCP tools available.
    Claude will call the appropriate tools and return a final answer.
    """
    response = client.beta.messages.create(
        model=model,
        max_tokens=max_tokens,
        mcp_servers=[MCP_SERVER],
        messages=[{"role": "user", "content": prompt}],
        betas=["mcp-client-2025-04-04"],
    )
    result = ""
    for b in response.content:
        if b.type == "text":
            result = result + "\n\n" + b.text
    return result


def api_key() -> str:
    """Return the ChainAware API key for injecting into prompts."""
    return CHAINAWARE_API_KEY
