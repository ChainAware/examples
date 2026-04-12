"""
ChainAware Example: Marketing Director
========================================
Agent: chainaware-marketing-director
Source: .claude/agents/chainaware-marketing-director.md

Full-cycle marketing campaign orchestrator. Takes a wallet list (CSV) or single
address, a platform description, and a campaign goal — then orchestrates multiple
specialist agents to produce a complete Marketing Campaign Brief: segmented
audience, hot leads, whale roster, per-cohort message playbook, upsell
opportunities, and onboarding routes.

Note: this agent uses claude-sonnet-4-6 and calls multiple specialist sub-agents
internally. Expect longer run times than single-tool agents.

Usage — batch:
    python python/agents/marketing_director.py <csv_file> <network> <platform_description> [campaign_goal] [current_product]

Usage — single:
    python python/agents/marketing_director.py <address> <network> <platform_description> [campaign_goal] [current_product]

    csv_file              Path to a CSV file with wallet addresses
    address               A single wallet address (0x...)
    network               Blockchain network (ETH, BNB, BASE, HAQQ, SOLANA)
    platform_description  Free-text description of the platform (quote it if it contains spaces)
    campaign_goal         Optional: acquisition | retention | monetization | re-engagement
    current_product       Optional: current product/tier wallets are on (enables upsell targeting)

Examples:
    python python/agents/marketing_director.py wallets.csv ETH \\
        "A DeFi yield aggregator that auto-compounds staking rewards across Lido and Convex" \\
        retention

    python python/agents/marketing_director.py 0xd8da6bf26964af9d7eed9e03e53415d37aa96045 ETH \\
        "A cross-chain DEX aggregator with intent-based routing for best swap prices" \\
        acquisition

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY="your-anthropic-key"
    export CHAINAWARE_API_KEY="your-chainaware-key"
"""

import csv
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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-marketing-director.md"
)


def load_agent(path: str) -> tuple[str, str]:
    """Parse the agent .md file and return (model, system_prompt)."""
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-sonnet-4-6"
    return model, body


def load_addresses_from_csv(csv_path: str) -> list[str]:
    """
    Read wallet addresses from a CSV file.
    Looks for a column named 'address', 'wallet', 'Address', or 'Wallet'.
    Falls back to the first column if none of those exist.
    """
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        address_col = None
        for candidate in ("address", "wallet", "Address", "Wallet"):
            if candidate in fieldnames:
                address_col = candidate
                break

        addresses = []
        if address_col:
            for row in reader:
                val = row[address_col].strip()
                if val:
                    addresses.append(val)
        else:
            f.seek(0)
            raw_reader = csv.reader(f)
            header = next(raw_reader, None)
            log.warning(
                "No 'address'/'wallet' column found. Using first column: %s",
                header[0] if header else "(none)",
            )
            for row in raw_reader:
                if row and row[0].strip():
                    addresses.append(row[0].strip())

    return addresses


def run_campaign(
    addresses: list[str],
    network: str,
    platform_description: str,
    campaign_goal: str = None,
    current_product: str = None,
) -> str:
    """
    Produce a full Marketing Campaign Brief for a wallet list, or a single
    Wallet Marketing Profile for one address.
    Behaviour is driven by the chainaware-marketing-director.md agent definition.
    """
    log.info(
        "Starting marketing director — %d address(es) network=%s goal=%s",
        len(addresses), network, campaign_goal or "balanced",
    )

    model, system_prompt = load_agent(AGENT_MD)

    if len(addresses) == 1:
        body = f"Create a wallet marketing profile for this address.\n\nAddress: {addresses[0]}\nNetwork: {network}\n"
    else:
        address_list = "\n".join(f"- {addr}" for addr in addresses)
        body = (
            f"Plan a marketing campaign for these wallets.\n\n"
            f"Network: {network}\n"
            f"Wallet addresses ({len(addresses)} total):\n{address_list}\n"
        )

    body += f"\nPlatform description:\n{platform_description}\n"

    if campaign_goal:
        body += f"Campaign goal: {campaign_goal}\n"
    if current_product:
        body += f"Current product / tier: {current_product}\n"
    body += f"API Key: {chainaware.api_key()}"

    log.info("Calling marketing director (model=%s) — this may take a while", model)
    result = chainaware.run(body, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Campaign brief complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python python/agents/marketing_director.py <csv_file|address> <network> <platform_description> [campaign_goal] [current_product]")
        sys.exit(1)

    target               = sys.argv[1]
    network              = sys.argv[2].upper()
    platform_description = sys.argv[3]
    campaign_goal        = sys.argv[4] if len(sys.argv) > 4 else None
    current_product      = sys.argv[5] if len(sys.argv) > 5 else None

    if os.path.isfile(target):
        addresses = load_addresses_from_csv(target)
        log.info("=== Marketing Director starting (batch: %d wallets) ===", len(addresses))
        print(f"Building campaign for: {target}")
    else:
        addresses = [target]
        log.info("=== Marketing Director starting (single wallet) ===")
        print(f"Building wallet profile for: {target}")

    print(f"Network:     {network}")
    print(f"Platform:    {platform_description}")
    if campaign_goal:
        print(f"Goal:        {campaign_goal}")
    if current_product:
        print(f"Product:     {current_product}")
    print("=" * 60)

    brief = run_campaign(
        addresses, network,
        platform_description=platform_description,
        campaign_goal=campaign_goal,
        current_product=current_product,
    )
    print(brief)

    log.info("=== Marketing Director done ===")
