"""
ChainAware Example: Token Analyzer
=====================================
Agent: chainaware-token-analyzer
Source: .claude/agents/chainaware-token-analyzer.md

Deep-dives into a single token's community rank and top holders using ChainAware's
TokenRank system. Returns community rank, top holder profiles (wallet age, transactions,
total points, global rank), and a holder quality assessment.

Usage:
    python python/agents/token_analyzer.py <contract> <network> [due_diligence]

    contract        Token contract address (0x...)
    network         Blockchain network (ETH, BNB, BASE, SOLANA)
    due_diligence   Optional: pass "fraud" to also screen top holders for fraud risk

Examples:
    python python/agents/token_analyzer.py 0xdAC17F958D2ee523a2206206994597C13D831ec7 ETH
    python python/agents/token_analyzer.py 0xdAC17F958D2ee523a2206206994597C13D831ec7 ETH fraud

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

# USDT on ETH
DEMO_CONTRACT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
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


def analyze_token(contract: str, network: str, due_diligence: bool = False) -> str:
    """
    Deep-dive into a token's community rank and top holders.
    Behaviour is driven by the chainaware-token-analyzer.md agent definition.
    """
    log.info("Starting token analysis — contract=%s network=%s due_diligence=%s",
             contract, network, due_diligence)
    model, system_prompt = load_agent(AGENT_MD)

    body = f"Analyze the community rank and top holders of this token.\n\nContract: {contract}\nNetwork: {network}\n"
    if due_diligence:
        body += "Also run fraud screening on the top holders for due diligence.\n"
    body += f"API Key: {chainaware.api_key()}"

    log.info("Calling token analyzer (model=%s)", model)
    result = chainaware.run(body, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Token analysis complete — report length=%d chars", len(result))
    return result


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        contract      = sys.argv[1]
        network       = sys.argv[2].upper()
        due_diligence = len(sys.argv) > 3 and sys.argv[3].lower() == "fraud"
        log.info("=== Token Analyzer starting ===")
        print(f"Analyzing token: {contract}")
    else:
        contract      = DEMO_CONTRACT
        network       = DEMO_NETWORK
        due_diligence = False
        log.info("=== Token Analyzer starting (demo) ===")
        print(f"Analyzing token: {DEMO_CONTRACT} (USDT, demo)")

    print(f"Network:       {network}")
    if due_diligence:
        print("Mode:          analysis + holder fraud screening")
    print("=" * 60)

    report = analyze_token(contract, network, due_diligence=due_diligence)
    print(report)

    log.info("=== Token Analyzer done ===")
