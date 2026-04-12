"""
ChainAware Example: Platform Greeter
======================================
Agent: chainaware-platform-greeter
Source: .claude/agents/chainaware-platform-greeter.md

Generates a personalised welcome message for a wallet connecting to a specific
platform. The same wallet gets a completely different message on Aave vs 1inch
vs OpenSea — grounded in its real on-chain behaviour.

Usage — single:
    python python/agents/platform_greeter.py <address> <network> <platform> [tone] [feature]

    address   A single wallet address (0x...)
    network   Blockchain network (ETH, BNB, BASE, HAQQ, SOLANA)
    platform  Platform name (e.g. "Aave", "Uniswap", "OpenSea")
    tone      Optional: friendly | professional | bold  (default: friendly)
    feature   Optional: specific feature to highlight

Examples:
    python python/agents/platform_greeter.py 0xd8da6bf26964af9d7eed9e03e53415d37aa96045 ETH Aave
    python python/agents/platform_greeter.py 0xd8da6bf26964af9d7eed9e03e53415d37aa96045 ETH 1inch bold

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY="your-anthropic-key"
    export CHAINAWARE_API_KEY="your-chainaware-key"
"""

import logging
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import chainaware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

AGENT_MD = os.path.join(
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-platform-greeter.md"
)


def load_agent(path: str) -> tuple[str, str]:
    """Parse the agent .md file and return (model, system_prompt)."""
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-haiku-4-5-20251001"
    return model, body


def greet_wallet(
    address: str,
    network: str,
    platform: str,
    tone: str = None,
    feature: str = None,
) -> str:
    """
    Generate a personalised platform welcome message for a wallet.
    Behaviour is driven by the chainaware-platform-greeter.md agent definition.
    """
    log.info(
        "Generating platform greeting — wallet=%s network=%s platform=%s",
        address, network, platform,
    )

    model, system_prompt = load_agent(AGENT_MD)

    body = (
        f"Generate a personalised welcome message for this wallet.\n\n"
        f"Wallet:   {address}\n"
        f"Network:  {network}\n"
        f"Platform: {platform}\n"
    )
    if tone:
        body += f"Tone: {tone}\n"
    if feature:
        body += f"Feature to highlight: {feature}\n"
    body += f"API Key: {chainaware.api_key()}"

    log.info("Calling platform greeter (model=%s)", model)
    result = chainaware.run(body, system=system_prompt, model=model)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Platform greeting complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python python/agents/platform_greeter.py <address> <network> <platform> [tone] [feature]")
        sys.exit(1)

    address  = sys.argv[1]
    network  = sys.argv[2].upper()
    platform = sys.argv[3]
    tone     = sys.argv[4] if len(sys.argv) > 4 else None
    feature  = sys.argv[5] if len(sys.argv) > 5 else None

    log.info("=== Platform Greeter starting ===")
    print(f"Wallet:   {address}")
    print(f"Network:  {network}")
    print(f"Platform: {platform}")
    if tone:
        print(f"Tone:     {tone}")
    if feature:
        print(f"Feature:  {feature}")
    print("=" * 60)

    report = greet_wallet(address, network, platform, tone=tone, feature=feature)
    print(report)

    log.info("=== Platform Greeter done ===")
