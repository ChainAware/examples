"""
ChainAware Example: Agent Trust Screener
=========================================
Agent: chainaware-agent-trust-screener
Source: .claude/agents/chainaware-agent-trust-screener.md

Vets ERC-8004 registered AI agents before allowing them to transact, receive
delegated funds, or be onboarded into an agent marketplace. Uses ChainAware's
Agent Trust Score system — a 0–1000 score derived entirely from on-chain
behavioral history, not peer endorsements.

Usage:
    python python/agents/agent_trust_screener.py                     # list top agents
    python python/agents/agent_trust_screener.py <agent_id> <chain_id>  # deep profile

    agent_id    Integer ID of the ERC-8004 registered agent
    chain_id    Chain ID (1=ETH, 56=BNB, 8453=Base, 137=Polygon, 42161=Arbitrum)

Examples:
    python python/agents/agent_trust_screener.py                # discover top agents
    python python/agents/agent_trust_screener.py 1 56           # deep profile: agent #1 on BNB
    python python/agents/agent_trust_screener.py 42 1           # deep profile: agent #42 on ETH

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-agent-trust-screener.md"
)


def load_agent(path: str) -> tuple[str, str, str]:
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-haiku-4-5-20251001"
    return model, body, frontmatter


def list_agents(limit: int = 10) -> str:
    """
    Discover and rank all ERC-8004 registered agents by trust score.
    Behaviour is driven by chainaware-agent-trust-screener.md.
    """
    log.info("Starting agent trust list — limit=%d", limit)
    model, system_prompt, frontmatter = load_agent(AGENT_MD)

    user_message = (
        f"List the top {limit} ERC-8004 registered AI agents sorted by trust score descending.\n\n"
        f"API Key: {chainaware.api_key()}"
    )

    log.info("Calling agent trust screener in list mode (model=%s)", model)
    result = chainaware.run(user_message, frontmatter=frontmatter, system=system_prompt, model=model)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Agent list complete — report length=%d chars", len(result))
    return result


def screen_agent(agent_id: int, chain_id: int) -> str:
    """
    Fetch the full trust profile for a specific ERC-8004 registered agent.
    Behaviour is driven by chainaware-agent-trust-screener.md.
    """
    log.info("Starting agent trust profile — agent_id=%d chain_id=%d", agent_id, chain_id)
    model, system_prompt, frontmatter = load_agent(AGENT_MD)

    user_message = (
        f"Get the full trust profile for this ERC-8004 agent.\n\n"
        f"agent_id:  {agent_id}\n"
        f"chain_id:  {chain_id}\n"
        f"API Key: {chainaware.api_key()}"
    )

    log.info("Calling agent trust screener in profile mode (model=%s)", model)
    result = chainaware.run(user_message, frontmatter=frontmatter, system=system_prompt, model=model)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Agent profile complete — report length=%d chars", len(result))
    return result


if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) >= 2:
        agent_id = int(args[0])
        chain_id = int(args[1])
        log.info("=== Agent Trust Screener starting (profile mode) ===")
        print(f"Agent ID:  {agent_id}")
        print(f"Chain ID:  {chain_id}")
        print("=" * 60)
        report = screen_agent(agent_id, chain_id)
    else:
        log.info("=== Agent Trust Screener starting (discovery mode) ===")
        print("Mode: Discover top ERC-8004 registered agents by trust score")
        print("=" * 60)
        report = list_agents()

    print(report)
    log.info("=== Agent Trust Screener done ===")
