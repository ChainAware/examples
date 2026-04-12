"""
ChainAware Example: Token Ranker
===================================
Agent: chainaware-token-ranker
Source: .claude/agents/chainaware-token-ranker.md

Discovers and ranks tokens by the strength of their holder community using ChainAware's
TokenRank system. Rankings are based on holder wallet quality — not price or market cap.

Usage:
    python python/agents/token_ranker.py <network> [category] [limit]

    network   Blockchain network (ETH, BNB, BASE, SOLANA)
    category  Optional: AI Token | RWA Token | DeFi Token | DeFAI Token | DePIN Token
              Use "all" or omit for all categories.
    limit     Optional: number of results (default: 10)

Examples:
    python python/agents/token_ranker.py ETH
    python python/agents/token_ranker.py ETH "DeFi Token" 10
    python python/agents/token_ranker.py SOLANA "AI Token" 5

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-token-ranker.md"
)

DEMO_NETWORK   = "ETH"
DEMO_CATEGORY  = "DeFi Token"
DEMO_LIMIT     = 10


def load_agent(path: str) -> tuple[str, str]:
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-haiku-4-5-20251001"
    return model, body


def rank_tokens(network: str, category: str = "", limit: int = 10) -> str:
    """
    Rank tokens by community strength on a given network.
    Behaviour is driven by the chainaware-token-ranker.md agent definition.
    """
    log.info("Starting token ranking — network=%s category=%s limit=%d",
             network, category or "all", limit)
    model, system_prompt = load_agent(AGENT_MD)

    if category and category.lower() != "all":
        body = f"Rank the top {limit} {category} tokens on {network} by community strength.\n\n"
    else:
        body = f"Rank the top {limit} tokens on {network} by community strength (all categories).\n\n"
    body += f"Network: {network}\n"
    if category and category.lower() != "all":
        body += f"Category: {category}\n"
    body += f"Limit: {limit}\n"
    body += f"API Key: {chainaware.api_key()}"

    log.info("Calling token ranker (model=%s)", model)
    result = chainaware.run(body, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Token ranking complete — report length=%d chars", len(result))
    return result


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        network  = sys.argv[1].upper()
        category = sys.argv[2] if len(sys.argv) > 2 else ""
        limit    = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        log.info("=== Token Ranker starting ===")
    else:
        network  = DEMO_NETWORK
        category = DEMO_CATEGORY
        limit    = DEMO_LIMIT
        log.info("=== Token Ranker starting (demo) ===")

    print(f"Network:  {network}")
    print(f"Category: {category or 'all'}")
    print(f"Limit:    {limit}")
    print("=" * 60)

    report = rank_tokens(network, category=category, limit=limit)
    print(report)

    log.info("=== Token Ranker done ===")
