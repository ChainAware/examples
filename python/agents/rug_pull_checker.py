"""
ChainAware Example: Rug Pull Checker
======================================
Agent: chainaware-rug-pull-detector
Source: .claude/agents/chainaware-rug-pull-detector.md

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-rug-pull-detector.md"
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


def check_rug_pull(contract_address: str, network: str) -> str:
    """
    Assess rug pull risk for a smart contract or liquidity pool address.
    Behaviour is driven by the chainaware-rug-pull-detector.md agent definition.
    """
    log.info("Starting rug pull check for contract=%s network=%s", contract_address, network)

    model, system_prompt = load_agent(AGENT_MD)

    user_message = (
        f"Check this contract for rug pull risk.\n\n"
        f"Contract: {contract_address}\n"
        f"Network:  {network}\n"
        f"API Key:  {chainaware.api_key()}"
    )

    log.info("Calling predictive_rug_pull via chainaware-rug-pull-detector agent (model=%s)", model)
    result = chainaware.run(user_message, system=system_prompt, model=model)

    if not result:
        log.warning("No result returned")
    else:
        log.info("Rug pull check complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    # Uniswap V2: USDC/ETH pair contract
    contract = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"
    network = "ETH"

    log.info("=== Rug Pull Checker starting ===")
    print(f"Checking contract: {contract} on {network}\n")
    print("=" * 60)

    report = check_rug_pull(contract, network)
    print(report)

    log.info("=== Rug Pull Checker done ===")
