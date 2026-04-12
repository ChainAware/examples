"""
ChainAware Example: Counterparty Screener
==========================================
Agent: chainaware-counterparty-screener
Source: .claude/agents/chainaware-counterparty-screener.md

Real-time pre-transaction safety check on a counterparty wallet. Returns a fast
go/no-go verdict (Safe / Caution / Block) before a trade, transfer, or contract
interaction is signed.

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-counterparty-screener.md"
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


def screen_counterparty(
    address: str,
    network: str,
    tx_type: str = None,
) -> str:
    """
    Run a pre-transaction counterparty safety check on a wallet address.
    Behaviour is driven by the chainaware-counterparty-screener.md agent definition.
    """
    log.info(
        "Starting counterparty screen — address=%s network=%s tx_type=%s",
        address, network, tx_type,
    )

    model, system_prompt = load_agent(AGENT_MD)

    lines = [
        "Screen this counterparty before I transact.\n",
        f"Address: {address}",
        f"Network: {network}",
    ]
    if tx_type:
        lines.append(f"Transaction Type: {tx_type}")
    lines.append(f"API Key: {chainaware.api_key()}")

    user_message = "\n".join(lines)

    log.info("Calling counterparty screener (model=%s)", model)
    result = chainaware.run(user_message, system=system_prompt, model=model)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Counterparty screen complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    address = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"  # vitalik.eth
    network = "ETH"
    tx_type = "transfer"

    log.info("=== Counterparty Screener starting ===")
    print(f"Address: {address}")
    print(f"Network: {network}")
    print(f"Type:    {tx_type}\n")
    print("=" * 60)

    report = screen_counterparty(address, network, tx_type=tx_type)
    print(report)

    log.info("=== Counterparty Screener done ===")
