"""
ChainAware Example: Agent Screener
====================================
Agent: chainaware-agent-screener
Source: .claude/agents/chainaware-agent-screener.md

Screens an AI agent's trustworthiness by checking both its operational wallet
and its feeder wallet (the wallet that funds it). Returns a normalized Agent
Trust Score from 0 to 10.

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-agent-screener.md"
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


def screen_agent(agent_wallet: str, feeder_wallet: str, network: str) -> str:
    """
    Screen an AI agent's trustworthiness by checking its operational and feeder wallets.
    Behaviour is driven by the chainaware-agent-screener.md agent definition.
    """
    log.info(
        "Starting agent screening — agent=%s feeder=%s network=%s",
        agent_wallet, feeder_wallet, network,
    )

    model, system_prompt = load_agent(AGENT_MD)

    user_message = (
        f"Screen this agent.\n\n"
        f"Agent Wallet:  {agent_wallet}\n"
        f"Feeder Wallet: {feeder_wallet}\n"
        f"Network:       {network}\n"
        f"API Key: {chainaware.api_key()}"
    )

    log.info("Calling agent screener (model=%s)", model)
    result = chainaware.run(user_message, system=system_prompt, model=model)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Agent screening complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    # Example: screen a well-known wallet as the agent, funded by a second wallet
    agent_wallet  = "0x388c818ca8b9251b393131c08a736a67ccb19297"  # Lido operator
    feeder_wallet = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"  # vitalik.eth
    network       = "ETH"

    log.info("=== Agent Screener starting ===")
    print(f"Agent wallet:  {agent_wallet}")
    print(f"Feeder wallet: {feeder_wallet}")
    print(f"Network:       {network}\n")
    print("=" * 60)

    report = screen_agent(agent_wallet, feeder_wallet, network)
    print(report)

    log.info("=== Agent Screener done ===")
