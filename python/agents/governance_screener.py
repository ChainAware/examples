"""
ChainAware Example: Governance Screener
=========================================
Agent: chainaware-governance-screener
Source: .claude/agents/chainaware-governance-screener.md

Screens DAO voter lists for Sybil attacks and classifies wallets into
governance tiers (Core Contributor / Active Member / Participant / Observer /
Disqualified) with a recommended voting weight multiplier per wallet.

Reads addresses from a CSV file (batch mode) or accepts a single address
via command-line arguments.

Usage — batch:
    python python/agents/governance_screener.py <csv_file> <network> [governance_model] [voting_power_pool]

Usage — single:
    python python/agents/governance_screener.py <address> <network> [governance_model]

    csv_file           Path to a CSV file with wallet addresses
    address            A single wallet address (0x...)
    network            Blockchain network (ETH, BNB, BASE, HAQQ, SOLANA)
    governance_model   Optional: token-weighted | reputation-weighted | quadratic
    voting_power_pool  Optional: total voting power to distribute across eligible wallets

Examples:
    python python/agents/governance_screener.py wallets.csv ETH reputation-weighted 10000
    python python/agents/governance_screener.py 0xd8da6bf26964af9d7eed9e03e53415d37aa96045 ETH token-weighted

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-governance-screener.md"
)


def load_agent(path: str) -> tuple[str, str]:
    """Parse the agent .md file and return (model, system_prompt)."""
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-haiku-4-5-20251001"
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


def screen_governance(
    addresses: list[str],
    network: str,
    governance_model: str = None,
    voting_power_pool: str = None,
    proposal: str = None,
) -> str:
    """
    Screen one or more wallets for DAO governance participation quality.
    Behaviour is driven by the chainaware-governance-screener.md agent definition.
    """
    log.info(
        "Starting governance screen — %d address(es) network=%s model=%s",
        len(addresses), network, governance_model or "not specified",
    )

    model, system_prompt = load_agent(AGENT_MD)

    if len(addresses) == 1:
        body = f"Screen this wallet for DAO governance.\n\nAddress: {addresses[0]}\nNetwork: {network}\n"
    else:
        address_list = "\n".join(f"- {addr}" for addr in addresses)
        body = (
            f"Screen these wallets for our DAO governance vote.\n\n"
            f"Network: {network}\n"
            f"Wallet addresses ({len(addresses)} total):\n{address_list}\n"
        )

    if governance_model:
        body += f"Governance Model: {governance_model}\n"
    if voting_power_pool:
        body += f"Total Voting Power Pool: {voting_power_pool}\n"
    if proposal:
        body += f"Proposal / Vote: {proposal}\n"
    body += f"API Key: {chainaware.api_key()}"

    log.info("Calling governance screener (model=%s)", model)
    result = chainaware.run(body, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Governance screening complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python python/agents/governance_screener.py <csv_file|address> <network> [governance_model] [voting_power_pool]")
        sys.exit(1)

    target           = sys.argv[1]
    network          = sys.argv[2].upper()
    governance_model = sys.argv[3] if len(sys.argv) > 3 else None
    voting_power_pool = sys.argv[4] if len(sys.argv) > 4 else None

    # Determine if target is a CSV file or a single address
    if os.path.isfile(target):
        addresses = load_addresses_from_csv(target)
        log.info("=== Governance Screener starting (batch: %d wallets) ===", len(addresses))
        print(f"Screening voters from: {target}")
    else:
        addresses = [target]
        log.info("=== Governance Screener starting (single wallet) ===")
        print(f"Screening wallet: {target}")

    print(f"Network:          {network}")
    if governance_model:
        print(f"Governance model: {governance_model}")
    if voting_power_pool:
        print(f"Voting power pool: {voting_power_pool}")
    print("=" * 60)

    report = screen_governance(
        addresses, network,
        governance_model=governance_model,
        voting_power_pool=voting_power_pool,
    )
    print(report)

    log.info("=== Governance Screener done ===")
