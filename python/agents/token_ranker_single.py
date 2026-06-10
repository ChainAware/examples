"""
ChainAware Example: Token Ranker Single
=========================================
Agent: chainaware-token-analyzer
Source: .claude/agents/chainaware-token-analyzer.md

Deep-dives into a single token's community rank and top holders using ChainAware's
TokenRank system. Returns community rank, top holder profiles (wallet age, transactions,
total points, global rank), and a holder quality assessment.

Usage:
    python python/agents/token_ranker_single.py <contract> <network>

    contract   Token contract address (0x... or Solana mint)
    network    Blockchain network (ETH, BNB, BASE, SOLANA)

Examples:
    python python/agents/token_ranker_single.py 0xa0820613976b441e2c6a90e4877e2fb5f7d72552 BASE
    python python/agents/token_ranker_single.py 0xdAC17F958D2ee523a2206206994597C13D831ec7 ETH

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-token-analyzer.md"
)

# Polter (POLTER) on BASE
DEMO_CONTRACT = "0xa0820613976b441e2c6a90e4877e2fb5f7d72552"
DEMO_NETWORK  = "BASE"


def load_agent(path: str) -> tuple[str, str]:
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-haiku-4-5-20251001"
    return model, body


def rank_single_token(contract: str, network: str) -> str:
    """
    Get community rank and top holders for a single token.
    Behaviour is driven by the chainaware-token-analyzer.md agent definition.
    """
    log.info("Starting single token rank — contract=%s network=%s", contract, network)
    model, system_prompt = load_agent(AGENT_MD)

    body = (
        f"Get the community rank and top holders for this token.\n\n"
        f"Contract: {contract}\n"
        f"Network: {network}\n"
        f"API Key: {chainaware.api_key()}"
    )

    log.info("Calling token analyzer (model=%s)", model)
    result = chainaware.run(body, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Single token rank complete — report length=%d chars", len(result))
    return result


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        contract = sys.argv[1]
        network  = sys.argv[2].upper()
        log.info("=== Token Ranker Single starting ===")
    else:
        contract = DEMO_CONTRACT
        network  = DEMO_NETWORK
        log.info("=== Token Ranker Single starting (demo) ===")

    print(f"Contract: {contract}")
    print(f"Network:  {network}")
    print("=" * 60)

    report = rank_single_token(contract, network)
    print(report)

    log.info("=== Token Ranker Single done ===")
