"""
ChainAware Example: Token Audit Analyst
=========================================
Agent: chainaware-token-audit-analyst
Source: .claude/agents/chainaware-token-audit-analyst.md

Deep contract-level due diligence for token smart contracts — ownership control,
liquidity health, supply/mint risk, transfer integrity, approve/permit safety,
reentrancy, and honeypot detection — before a listing, swap, or deposit.
Returns a 0–100 aggregate risk score with a module-by-module breakdown.

Uses an async get-or-create audit pipeline: run_token_audit first (returns
immediately if cached, otherwise queues a job), then polls get_token_audit_result
until the audit is complete.

Usage:
    python python/agents/token_audit_analyst.py                        # demo contract
    python python/agents/token_audit_analyst.py <contract> <network>   # specific contract

    contract    Token contract address (0x...)
    network     Network in any case — normalised to lowercase automatically
                Supported: eth, bsc, base, arbitrum, avalanche, optimism, polygon

Examples:
    python python/agents/token_audit_analyst.py
    python python/agents/token_audit_analyst.py 0x... eth
    python python/agents/token_audit_analyst.py 0x... BSC
    python python/agents/token_audit_analyst.py 0x... base

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
import chainaware_sse as chainaware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

AGENT_MD = os.path.join(
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-token-audit-analyst.md"
)

# PEPE token on Ethereum — a high-profile memecoin; demonstrates ownership + supply analysis
DEMO_CONTRACT = "0x6982508145454ce325ddbe47a25d4ec3d2311933"
DEMO_NETWORK  = "eth"


def load_agent(path: str) -> tuple[str, str, str]:
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-haiku-4-5-20251001"
    return model, body, frontmatter


def audit_token(contract: str, network: str) -> str:
    """
    Run a deep contract audit on a token smart contract.
    Network is normalised to lowercase; the audit tools require lowercase values.
    Behaviour is driven by chainaware-token-audit-analyst.md.
    """
    network = network.lower()
    log.info("Starting token audit — contract=%s network=%s", contract, network)
    model, system_prompt, frontmatter = load_agent(AGENT_MD)

    user_message = (
        f"Run a full contract audit on this token.\n\n"
        f"Contract: {contract}\n"
        f"Network:  {network}\n"
        f"API Key: {chainaware.api_key()}"
    )

    log.info("Calling token audit analyst (model=%s)", model)
    result = chainaware.run(user_message, frontmatter=frontmatter, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Token audit complete — report length=%d chars", len(result))
    return result


if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) >= 2:
        contract = args[0]
        network  = args[1]
        log.info("=== Token Audit Analyst starting ===")
        print(f"Contract: {contract}")
    else:
        contract = DEMO_CONTRACT
        network  = DEMO_NETWORK
        log.info("=== Token Audit Analyst starting (demo) ===")
        print(f"Contract: {DEMO_CONTRACT} (PEPE, demo)")

    print(f"Network:  {network.lower()}")
    print("=" * 60)

    report = audit_token(contract, network)
    print(report)

    log.info("=== Token Audit Analyst done ===")
