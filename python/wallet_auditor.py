"""
ChainAware Example: Wallet Auditor
====================================
Agent: chainaware-wallet-auditor

Full due diligence on a wallet — combines fraud detection, behavioural
analysis, and rug-pull risk into a single comprehensive report.

Use cases:
  - "Audit this wallet before we onboard them"
  - "Is this address safe to do business with?"
  - "Give me a full due diligence report on this wallet"

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY="your-anthropic-key"
    export CHAINAWARE_API_KEY="your-chainaware-key"

Register the MCP server (one-time):
    claude mcp add --transport sse chainaware-behavioral-prediction \\
      https://prediction.mcp.chainaware.ai/sse \\
      --header "X-API-Key: $CHAINAWARE_API_KEY"
"""

import os
import logging
import anthropic

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

CHAINAWARE_API_KEY = os.environ["CHAINAWARE_API_KEY"]

MCP_SERVER = {
    "type": "url",
    "url": f"https://prediction.mcp.chainaware.ai/sse?apiKey={CHAINAWARE_API_KEY}",
    "name": "chainaware-behavioral-prediction",
}


def audit_wallet(wallet_address: str, network: str) -> str:
    """
    Run a full due diligence audit on a wallet address.

    The chainaware-wallet-auditor agent orchestrates:
      1. predictive_fraud    — fraud probability + AML forensics
      2. predictive_behaviour — risk profile, intentions, experience
      3. predictive_rug_pull  — contract/LP safety (if applicable)

    Returns a structured report with an overall verdict.
    """
    log.info("Starting audit for wallet=%s network=%s", wallet_address, network)
    log.info("Calling ChainAware MCP — fraud, behaviour, rug-pull checks")

    response = client.beta.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        mcp_servers=[MCP_SERVER],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Use the chainaware-wallet-auditor agent to run a full due diligence "
                    f"audit on this wallet.\n\n"
                    f"Wallet:  {wallet_address}\n"
                    f"Network: {network}\n"
                    f"API Key: {CHAINAWARE_API_KEY}\n\n"
                    f"Include: fraud status, AML flags, behavioural profile, "
                    f"DeFi intentions, experience level, and an overall verdict."
                ),
            }
        ],
        betas=["mcp-client-2025-04-04"],
    )

    log.info(
        "Response received — stop_reason=%s input_tokens=%d output_tokens=%d",
        response.stop_reason,
        response.usage.input_tokens,
        response.usage.output_tokens,
    )

    result = next((b.text for b in response.content if b.type == "text"), "")
    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Audit complete — report length=%d chars", len(result))
    return result


if __name__ == "__main__":
    wallet = "0x77D1D1638d6770de23125F6298D2814A6ecebccC"  # vitalik.eth
    network = "ETH"

    log.info("=== Wallet Auditor starting ===")
    print(f"Auditing wallet: {wallet} on {network}\n")
    print("=" * 60)

    report = audit_wallet(wallet, network)
    print(report)
    log.info("=== Wallet Auditor done ===")
