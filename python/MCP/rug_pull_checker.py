"""
ChainAware Example: Rug Pull Checker
======================================
Tool: predictive_rug_pull

AI-powered engine that forecasts whether a liquidity pool or smart contract
is likely to perform a rug pull — before you deposit.

Use cases:
  - "Is this DeFi pool safe to stake in?"
  - "Check this contract for rug pull risk"
  - "Monitor my LP position for potential exploits"

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
import chainaware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def check_rug_pull(contract_address: str, network: str) -> str:
    """
    Assess rug pull risk for a smart contract or liquidity pool address.

    Uses the predictive_rug_pull tool to return:
      - Risk score and status (Low / Medium / High Risk)
      - Fraud probability (0.00–1.00)
      - Risk indicators: honeypot, mintable, hidden owner, tax rates, liquidity lock, etc.
      - Liquidity event history with fraud scores per participant
      - Forensic details: selfdestruct, proxy, approval abuse, etc.
    """
    log.info("Starting rug pull check for contract=%s network=%s", contract_address, network)

    prompt = (
        f"Use the predictive_rug_pull tool to assess this contract.\n\n"
        f"Contract: {contract_address}\n"
        f"Network:  {network}\n"
        f"API Key:  {chainaware.api_key()}\n\n"
        f"Return: risk status, risk score, fraud probability, key risk indicators "
        f"that are flagged (honeypot, mintable, hidden owner, taxes, liquidity lock), "
        f"any suspicious liquidity events, and a plain-English safety verdict."
    )

    log.info("Calling predictive_rug_pull via ChainAware MCP")
    result = chainaware.run(prompt)

    if not result:
        log.warning("No result returned from predictive_rug_pull")
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
