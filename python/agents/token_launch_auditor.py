"""
ChainAware Example: Token Launch Auditor
==========================================
Agent: chainaware-token-launch-auditor
Source: .claude/agents/chainaware-token-launch-auditor.md

Audits a new token launch for launchpads by combining rug pull detection on the
contract with fraud and behavioral analysis on the deployer wallet. Returns a
Launch Safety Score (0–100), a listing verdict (APPROVED / CONDITIONAL / REJECTED),
a public safety badge, and required listing conditions.

Usage:
    python python/agents/token_launch_auditor.py <contract> <deployer> <network>

    contract  Token contract address (0x...)
    deployer  Deployer wallet address (0x...)
    network   Blockchain network (ETH, BNB, BASE, HAQQ)

    Note: rug pull scoring is supported on ETH, BNB, BASE, HAQQ only.
          Deployer fraud/behaviour checks also cover POLYGON, TON, TRON.

Examples:
    python python/agents/token_launch_auditor.py \\
        0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 \\
        0xd8da6bf26964af9d7eed9e03e53415d37aa96045 \\
        ETH

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-token-launch-auditor.md"
)

# Demo: WETH contract + vitalik.eth as deployer (illustrative only)
DEMO_CONTRACT = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"   # WETH on ETH
DEMO_DEPLOYER = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"   # vitalik.eth
DEMO_NETWORK  = "ETH"


def load_agent(path: str) -> tuple[str, str]:
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-haiku-4-5-20251001"
    return model, body


def audit_launch(contract: str, deployer: str, network: str) -> str:
    """
    Audit a token launch: rug pull check on contract + fraud/behaviour check on deployer.
    Behaviour is driven by the chainaware-token-launch-auditor.md agent definition.
    """
    log.info("Starting token launch audit — contract=%s deployer=%s network=%s",
             contract, deployer, network)
    model, system_prompt = load_agent(AGENT_MD)

    body = (
        f"Audit this token launch and return a listing verdict.\n\n"
        f"Contract: {contract}\n"
        f"Deployer: {deployer}\n"
        f"Network:  {network}\n"
        f"API Key: {chainaware.api_key()}"
    )

    log.info("Calling token launch auditor (model=%s)", model)
    result = chainaware.run(body, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Token launch audit complete — report length=%d chars", len(result))
    return result


if __name__ == "__main__":
    if len(sys.argv) >= 4:
        contract = sys.argv[1]
        deployer = sys.argv[2]
        network  = sys.argv[3].upper()
        log.info("=== Token Launch Auditor starting ===")
    else:
        contract = DEMO_CONTRACT
        deployer = DEMO_DEPLOYER
        network  = DEMO_NETWORK
        log.info("=== Token Launch Auditor starting (demo) ===")
        print("Note: demo uses WETH contract + vitalik.eth as deployer (illustrative)")

    print(f"Contract: {contract}")
    print(f"Deployer: {deployer}")
    print(f"Network:  {network}")
    print("=" * 60)

    report = audit_launch(contract, deployer, network)
    print(report)

    log.info("=== Token Launch Auditor done ===")
