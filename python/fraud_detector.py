"""
ChainAware Example: Fraud Detector
====================================
Tool: predictive_fraud

Predicts the likelihood of fraudulent activity on a wallet address *before*
it happens (~98% accuracy), and surfaces AML/forensic indicators and
sanction data.

Use cases:
  - "Is this address safe to transact with?"
  - "Run an AML check on this wallet"
  - "What is the fraud risk for this address?"

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


def detect_fraud(wallet_address: str, network: str) -> str:
    """
    Run a fraud detection and AML check on a wallet address.

    Uses the predictive_fraud tool to return:
      - Fraud probability score (0.00–1.00)
      - Classification: Fraud / Not Fraud / New Address
      - Forensic indicators (cybercrime, money laundering, phishing, mixer, etc.)
      - Sanction exposure data
    """
    log.info("Starting fraud detection for wallet=%s network=%s", wallet_address, network)
    log.info("Calling predictive_fraud via ChainAware MCP")

    response = client.beta.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        mcp_servers=[MCP_SERVER],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Use the predictive_fraud tool to assess this wallet.\n\n"
                    f"Wallet:  {wallet_address}\n"
                    f"Network: {network}\n"
                    f"API Key: {CHAINAWARE_API_KEY}\n\n"
                    f"Return: fraud status, probability score, key forensic indicators "
                    f"that are flagged, sanction exposure, and a plain-English risk summary."
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

    result = ""
    for b in response.content:
        if b.type == "text":
            result = result + "\n\n" + b.text

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Fraud detection complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    wallet = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # vitalik.eth
    network = "ETH"

    log.info("=== Fraud Detector starting ===")
    print(f"Checking wallet: {wallet} on {network}\n")
    print("=" * 60)

    report = detect_fraud(wallet, network)
    print(report)

    log.info("=== Fraud Detector done ===")
