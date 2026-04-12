"""
ChainAware Example: DeFi Advisor
==================================
Agent: chainaware-defi-advisor
Source: .claude/agents/chainaware-defi-advisor.md

Returns personalized DeFi product recommendations calibrated to a wallet's
experience level and risk willingness. Higher experience + higher risk appetite
maps to more complex, higher-yield products; lower experience + lower risk maps
to simpler, protected products.

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-defi-advisor.md"
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


def advise_defi(wallet: str, network: str) -> str:
    """
    Return personalized DeFi product recommendations for a wallet.
    Behaviour is driven by the chainaware-defi-advisor.md agent definition.
    """
    log.info("Starting DeFi advisor — wallet=%s network=%s", wallet, network)

    model, system_prompt = load_agent(AGENT_MD)

    user_message = (
        f"Recommend DeFi products for this wallet.\n\n"
        f"Wallet:  {wallet}\n"
        f"Network: {network}\n"
        f"API Key: {chainaware.api_key()}"
    )

    log.info("Calling DeFi advisor (model=%s)", model)
    result = chainaware.run(user_message, system=system_prompt, model=model)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("DeFi advice complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    wallet  = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"  # vitalik.eth
    network = "ETH"

    log.info("=== DeFi Advisor starting ===")
    print(f"Wallet:  {wallet}")
    print(f"Network: {network}\n")
    print("=" * 60)

    report = advise_defi(wallet, network)
    print(report)

    log.info("=== DeFi Advisor done ===")
