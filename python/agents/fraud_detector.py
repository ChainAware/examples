"""
ChainAware Example: Fraud Detector
====================================
Agent: chainaware-fraud-detector
Source: .claude/agents/chainaware-fraud-detector.md

Uses the agent definition .md file as the system prompt so that tool
instructions, output format, and risk thresholds live in the .md —
not in code.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY="your-anthropic-key"
    export CHAINAWARE_API_KEY="your-chainaware-key"
"""

import logging
import os
import re
import sys

# Resolve chainaware.py from python/MCP relative to this file
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "MCP"))
import chainaware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

AGENT_MD = os.path.join(
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-fraud-detector.md"
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


def detect_fraud(wallet_address: str, network: str) -> str:
    """
    Run a fraud detection and AML check on a wallet address.
    Behaviour is driven by the chainaware-fraud-detector.md agent definition.
    """
    log.info("Starting fraud detection for wallet=%s network=%s", wallet_address, network)

    model, system_prompt = load_agent(AGENT_MD)

    user_message = (
        f"Check this wallet for fraud.\n\n"
        f"Wallet:  {wallet_address}\n"
        f"Network: {network}\n"
        f"API Key: {chainaware.api_key()}"
    )

    log.info("Calling predictive_fraud via chainaware-fraud-detector agent (model=%s)", model)
    result = chainaware.run(user_message, system=system_prompt, model=model)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Fraud detection complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    wallet = "0x77D1D1638d6770de23125F6298D2814A6ecebccC"
    network = "ETH"

    log.info("=== Fraud Detector starting ===")
    print(f"Checking wallet: {wallet} on {network}\n")
    print("=" * 60)

    report = detect_fraud(wallet, network)
    print(report)

    log.info("=== Fraud Detector done ===")
