"""
ChainAware Example: Lead Scorer
=================================
Agent: chainaware-lead-scorer
Source: .claude/agents/chainaware-lead-scorer.md

Scores wallets as sales leads (0–100) and classifies them into tiers
(Hot / Warm / Cold / Dead) with a conversion probability and recommended
outreach angle. Accepts a single address or a CSV file for batch scoring.

Usage — batch:
    python python/agents/lead_scorer.py <csv_file> <network> [product_context] [outreach_goal]

Usage — single:
    python python/agents/lead_scorer.py <address> <network> [product_context] [outreach_goal]

    csv_file        Path to a CSV file with wallet addresses
    address         A single wallet address (0x...)
    network         Blockchain network (ETH, BNB, BASE, HAQQ, SOLANA)
    product_context Optional: what you are selling (e.g. "DeFi lending platform")
    outreach_goal   Optional: acquisition | upsell | reactivation

Examples:
    python python/agents/lead_scorer.py wallets.csv ETH "DeFi lending platform" acquisition
    python python/agents/lead_scorer.py 0xd8da6bf26964af9d7eed9e03e53415d37aa96045 ETH "staking product"

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-lead-scorer.md"
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


def score_leads(
    addresses: list[str],
    network: str,
    product_context: str = None,
    outreach_goal: str = None,
) -> str:
    """
    Score one or more wallets as sales leads.
    Behaviour is driven by the chainaware-lead-scorer.md agent definition.
    """
    log.info(
        "Starting lead scoring — %d address(es) network=%s product=%s goal=%s",
        len(addresses), network,
        product_context or "not specified",
        outreach_goal or "not specified",
    )

    model, system_prompt = load_agent(AGENT_MD)

    if len(addresses) == 1:
        body = f"Score this wallet as a sales lead.\n\nAddress: {addresses[0]}\nNetwork: {network}\n"
    else:
        address_list = "\n".join(f"- {addr}" for addr in addresses)
        body = (
            f"Score these wallets as sales leads.\n\n"
            f"Network: {network}\n"
            f"Wallet addresses ({len(addresses)} total):\n{address_list}\n"
        )

    if product_context:
        body += f"Product context: {product_context}\n"
    if outreach_goal:
        body += f"Outreach goal: {outreach_goal}\n"
    body += f"API Key: {chainaware.api_key()}"

    log.info("Calling lead scorer (model=%s)", model)
    result = chainaware.run(body, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Lead scoring complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python python/agents/lead_scorer.py <csv_file|address> <network> [product_context] [outreach_goal]")
        sys.exit(1)

    target          = sys.argv[1]
    network         = sys.argv[2].upper()
    product_context = sys.argv[3] if len(sys.argv) > 3 else None
    outreach_goal   = sys.argv[4] if len(sys.argv) > 4 else None

    if os.path.isfile(target):
        addresses = load_addresses_from_csv(target)
        log.info("=== Lead Scorer starting (batch: %d wallets) ===", len(addresses))
        print(f"Scoring leads from: {target}")
    else:
        addresses = [target]
        log.info("=== Lead Scorer starting (single wallet) ===")
        print(f"Scoring wallet: {target}")

    print(f"Network:         {network}")
    if product_context:
        print(f"Product context: {product_context}")
    if outreach_goal:
        print(f"Outreach goal:   {outreach_goal}")
    print("=" * 60)

    report = score_leads(addresses, network, product_context=product_context, outreach_goal=outreach_goal)
    print(report)

    log.info("=== Lead Scorer done ===")
