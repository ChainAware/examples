"""
ChainAware shared helper — reused by all example scripts.

Sets up the Anthropic client with the ChainAware MCP server and
exposes a single `run(prompt)` function that calls Claude with
the MCP tools available.
"""

import os
import logging
import httpx
import anthropic

log = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
CHAINAWARE_API_KEY = os.environ["CHAINAWARE_API_KEY"]
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY", "")

# Etherscan V2 — one base URL, differentiated by chainid.
EXPLORERS: dict[str, dict] = {
    "ETH":     {"chainid": 1,      "url": "https://api.etherscan.io/v2/api"},
    "BNB":     {"chainid": 56,     "url": "https://api.etherscan.io/v2/api"},
    "BASE":    {"chainid": 8453,   "url": "https://api.etherscan.io/v2/api"},
    "POLYGON": {"chainid": 137,    "url": "https://api.etherscan.io/v2/api"},
    "ARB":     {"chainid": 42161,  "url": "https://api.etherscan.io/v2/api"},
    "HAQQ":    {"chainid": 11235,  "url": "https://api.etherscan.io/v2/api"},
}

# The ChainAware MCP server — API key embedded in the URL for connection auth.
# Each tool also receives the API key explicitly in the prompt.
MCP_SERVER = {
    "type": "url",
    "url": f"https://prediction.mcpbeta.chainaware.ai/sse?apiKey={CHAINAWARE_API_KEY}",
    "name": "chainaware-behavioral-prediction",
}

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def run(prompt: str, system: str = None, model: str = "claude-opus-4-6", max_tokens: int = 4096) -> str:
    """
    Send a prompt to Claude with the ChainAware MCP tools available.
    Claude will call the appropriate tools and return a final answer.
    Pass system to override the default behaviour with an agent definition.
    """
    kwargs = {"system": system} if system else {}
    response = client.beta.messages.create(
        model=model,
        max_tokens=max_tokens,
        mcp_servers=[MCP_SERVER],
        messages=[{"role": "user", "content": prompt}],
        betas=["mcp-client-2025-04-04"],
        **kwargs,
    )
    log.info(
        "Response received — stop_reason=%s input_tokens=%d output_tokens=%d",
        response.stop_reason,
        response.usage.input_tokens,
        response.usage.output_tokens,
    )
    result = ""
    for b in response.content:
        if b.type == "text":
            result = result + "\n\n" + b.text
    return result


def api_key() -> str:
    """Return the ChainAware API key for injecting into prompts."""
    return CHAINAWARE_API_KEY


async def is_contract(address: str, chain: str) -> dict:
    """
    Return whether *address* is a smart contract or an EOA wallet on *chain*.

    Uses the Etherscan V2 API (eth_getCode).  A non-empty bytecode response
    means the address is a contract; "0x" means it is a plain wallet.

    Requires ETHERSCAN_API_KEY in the environment.
    Supported chains: ETH, BNB, BASE, POLYGON, ARB, HAQQ.
    """
    chain = chain.upper()

    if chain not in EXPLORERS:
        raise ValueError(f"Unsupported chain: {chain}. Supported: {list(EXPLORERS.keys())}")

    explorer = EXPLORERS[chain]

    params = {
        "chainid": explorer["chainid"],
        "module": "proxy",
        "action": "eth_getCode",
        "address": address,
        "tag": "latest",
        "apikey": ETHERSCAN_API_KEY,
    }

    async with httpx.AsyncClient() as http:
        response = await http.get(explorer["url"], params=params)
        data = response.json()

    bytecode = data.get("result", "0x")
    is_ctr = bytecode not in ("0x", "0x0", None, "")

    return {
        "address": address,
        "chain": chain,
        "is_contract": is_ctr,
        "type": "contract" if is_ctr else "wallet",
    }
