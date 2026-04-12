"""
ChainAware Example: AML Scorer
================================
Agent: chainaware-aml-scorer
Source: .claude/agents/chainaware-aml-scorer.md

Uses the agent definition .md file as the system prompt so that AML scoring
logic, forensic flag detection, and output format live in the .md — not in code.

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-aml-scorer.md"
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


def score_aml(wallet_address: str, network: str) -> str:
    """
    Run an AML compliance score on a wallet address.
    Behaviour is driven by the chainaware-aml-scorer.md agent definition.
    """
    log.info("Starting AML scoring for wallet=%s network=%s", wallet_address, network)

    model, system_prompt = load_agent(AGENT_MD)

    user_message = (
        f"Run an AML compliance check on this wallet.\n\n"
        f"Wallet:  {wallet_address}\n"
        f"Network: {network}\n"
        f"API Key: {chainaware.api_key()}"
    )

    log.info("Calling predictive_fraud via chainaware-aml-scorer agent (model=%s)", model)
    result = chainaware.run(user_message, system=system_prompt, model=model)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("AML scoring complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    wallet = "vitalik.eth"
    network = "ETH"

    log.info("=== AML Scorer starting ===")
    print(f"Checking wallet: {wallet} on {network}\n")
    print("=" * 60)

    report = score_aml(wallet, network)
    print(report)

    log.info("=== AML Scorer done ===")
