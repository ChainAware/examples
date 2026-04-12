"""
ChainAware Example: Airdrop Screener
======================================
Agent: chainaware-airdrop-screener
Source: .claude/agents/chainaware-airdrop-screener.md

Reads wallet addresses from a CSV file and screens them for airdrop
eligibility. Filters bots, fraud, and sybil wallets, then ranks the
remaining eligible wallets by reputation score.

Usage:
    python python/agents/airdrop_screener.py <csv_file> <network>

    csv_file   Path to a CSV file. Any column named 'address', 'wallet',
               or 'Address' is used. If no such column exists the first
               column is used.
    network    Blockchain network (ETH, BNB, BASE, POLYGON, TON, TRON, HAQQ, SOLANA)

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-airdrop-screener.md"
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
    Looks for a column named 'address', 'wallet', or 'Address'.
    Falls back to the first column if none of those exist.
    Deduplication is handled by the agent, but we strip blank rows here.
    """
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        # Pick the address column
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
            # No recognised header — restart and use the first column
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


def screen_airdrop(csv_path: str, network: str) -> str:
    """
    Screen all wallet addresses in a CSV file for airdrop eligibility.
    Behaviour is driven by the chainaware-airdrop-screener.md agent definition.
    """
    log.info("Loading addresses from %s", csv_path)
    addresses = load_addresses_from_csv(csv_path)
    log.info("Loaded %d addresses for network=%s", len(addresses), network)

    model, system_prompt = load_agent(AGENT_MD)

    address_list = "\n".join(f"- {addr}" for addr in addresses)
    user_message = (
        f"Screen these wallets for our airdrop.\n\n"
        f"Network: {network}\n"
        f"API Key: {chainaware.api_key()}\n\n"
        f"Wallet addresses ({len(addresses)} total):\n"
        f"{address_list}"
    )

    log.info(
        "Calling airdrop screener agent (model=%s) with %d wallets on %s",
        model, len(addresses), network,
    )
    result = chainaware.run(user_message, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Airdrop screening complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python python/agents/airdrop_screener.py <csv_file> <network>")
        print("Example: python python/agents/airdrop_screener.py wallets.csv ETH")
        sys.exit(1)

    csv_file = sys.argv[1]
    network = sys.argv[2].upper()

    if not os.path.isfile(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        sys.exit(1)

    log.info("=== Airdrop Screener starting ===")
    print(f"Screening wallets from: {csv_file}")
    print(f"Network: {network}")
    print("=" * 60)

    report = screen_airdrop(csv_file, network)
    print(report)

    log.info("=== Airdrop Screener done ===")
