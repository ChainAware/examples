"""
ChainAware Example: Credit Scorer
===================================
Agent: chainaware-credit-scorer
Source: .claude/agents/chainaware-credit-scorer.md

Returns a crypto credit score (1–9) for a wallet using ChainAware's credit_score
tool, which combines fraud probability and social graph analysis to assess
borrower reliability.

Note: credit_score is currently only supported on ETH.

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-credit-scorer.md"
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


def score_credit(wallet: str, network: str) -> str:
    """
    Return a credit score (1–9) for a wallet.
    Behaviour is driven by the chainaware-credit-scorer.md agent definition.
    """
    log.info("Starting credit scoring — wallet=%s network=%s", wallet, network)

    model, system_prompt = load_agent(AGENT_MD)

    user_message = (
        f"Get the credit score for this wallet.\n\n"
        f"Wallet:  {wallet}\n"
        f"Network: {network}\n"
        f"API Key: {chainaware.api_key()}"
    )

    log.info("Calling credit scorer (model=%s)", model)
    result = chainaware.run(user_message, system=system_prompt, model=model)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Credit scoring complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    wallet  = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"  # vitalik.eth
    network = "ETH"

    log.info("=== Credit Scorer starting ===")
    print(f"Wallet:  {wallet}")
    print(f"Network: {network}\n")
    print("=" * 60)

    report = score_credit(wallet, network)
    print(report)

    log.info("=== Credit Scorer done ===")
