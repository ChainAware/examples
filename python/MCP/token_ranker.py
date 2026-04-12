"""
ChainAware Example: Token Ranker
===================================
Tools: token_rank_list, token_rank_single

Ranks tokens by the strength of their holder community. Supports listing
and filtering tokens by network/category, or deep-diving into a single
token to see its rank and top holders.

Use cases:
  - "Which AI tokens are ranked highest on ETH?"
  - "What is the community rank of this token?"
  - "Who are the strongest holders of this contract?"

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY="your-anthropic-key"
    export CHAINAWARE_API_KEY="your-chainaware-key"

Register the MCP server (one-time):
    claude mcp add --transport sse chainaware-behavioral-prediction \\
      https://prediction.mcp.chainaware.ai/sse \\
      --header "X-API-Key: $CHAINAWARE_API_KEY"
"""

import logging
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import chainaware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def rank_tokens(network: str, category: str, limit: int = 10) -> str:
    """
    List and rank tokens by community strength for a given network and category.

    Uses token_rank_list to return:
      - Community rank and normalized rank per token
      - Token name, ticker, chain, category
      - Total holder count
    """
    log.info(
        "Fetching top %d tokens — network=%s category=%s", limit, network, category
    )

    prompt = (
        f"Use the token_rank_list tool to fetch the top {limit} tokens.\n\n"
        f"Network:  {network}\n"
        f"Category: {category}\n"
        f"Sort by communityRank descending.\n"
        f"Limit: {limit}, Offset: 0\n\n"
        f"Return a ranked table with: token name, ticker, community rank, "
        f"normalized rank, and total holders."
    )

    log.info("Calling token_rank_list via ChainAware MCP")
    result = chainaware.run(prompt)

    if not result:
        log.warning("No result returned from token_rank_list")
    else:
        log.info("Token list complete — report length=%d chars", len(result))

    return result


def rank_single_token(contract_address: str, network: str) -> str:
    """
    Get the community rank and top holders for a single token contract.

    Uses token_rank_single to return:
      - Token details: name, ticker, community rank, normalized rank, total holders
      - Top holders: wallet address, balance, wallet age, global rank
    """
    log.info(
        "Fetching single token rank for contract=%s network=%s", contract_address, network
    )

    prompt = (
        f"Use the token_rank_single tool to fetch rank and top holders for this token.\n\n"
        f"Contract: {contract_address}\n"
        f"Network:  {network}\n\n"
        f"Return: token name, ticker, community rank, normalized rank, total holders, "
        f"and a summary of the top holders including their wallet age and global rank."
    )

    log.info("Calling token_rank_single via ChainAware MCP")
    result = chainaware.run(prompt)

    if not result:
        log.warning("No result returned from token_rank_single")
    else:
        log.info("Single token rank complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    log.info("=== Token Ranker starting ===")

    # Example 1 — top AI tokens on ETH
    print("Top AI Tokens on ETH\n" + "=" * 60)
    report = rank_tokens(network="ETH", category="AI Token", limit=10)
    print(report)

    print()

    # Example 2 — single token deep dive (Chainlink on ETH)
    contract = "0x514910771AF9Ca656af840dff83E8264EcF986CA"
    network = "ETH"
    print(f"Single Token Rank: {contract} on {network}\n" + "=" * 60)
    report = rank_single_token(contract, network)
    print(report)

    log.info("=== Token Ranker done ===")
