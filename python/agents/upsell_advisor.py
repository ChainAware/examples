"""
ChainAware Example: Upsell Advisor
=====================================
Agent: chainaware-upsell-advisor
Source: .claude/agents/chainaware-upsell-advisor.md

Identifies the best upsell opportunity for an existing user based on their current
product tier and on-chain behaviour. Returns the specific next product to offer,
an upgrade readiness score, conversion probability, optimal trigger event, and a
ready-to-use upsell message.

Usage — single:
    python python/agents/upsell_advisor.py <address> <network> <current_product> [goal] [catalogue]

Usage — batch:
    python python/agents/upsell_advisor.py <csv_file> <network> <current_product> [goal] [catalogue]

    address          A single wallet address (0x...)
    csv_file         Path to a CSV file with wallet addresses
    network          Blockchain network (ETH, BNB, BASE, HAQQ, SOLANA)
    current_product  The product/tier the wallet is currently on (required)
    goal             Optional: revenue | engagement | retention
    catalogue        Optional: comma-separated list of available next-tier products

Examples:
    python python/agents/upsell_advisor.py 0xd8da6bf26964af9d7eed9e03e53415d37aa96045 ETH "basic DEX swap"
    python python/agents/upsell_advisor.py 0xd8da6bf26964af9d7eed9e03e53415d37aa96045 ETH "single-asset staking" revenue
    python python/agents/upsell_advisor.py wallets.csv ETH "basic swap" retention "yield vault,lending,LP provision"

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-upsell-advisor.md"
)

DEMO_ADDRESS        = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"  # vitalik.eth
DEMO_NETWORK        = "ETH"
DEMO_CURRENT_PRODUCT = "basic DEX swap"


def load_agent(path: str) -> tuple[str, str]:
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-haiku-4-5-20251001"
    return model, body


def load_addresses_from_csv(csv_path: str) -> list[str]:
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
            log.warning("No 'address'/'wallet' column found. Using first column: %s",
                        header[0] if header else "(none)")
            for row in raw_reader:
                if row and row[0].strip():
                    addresses.append(row[0].strip())
    return addresses


def advise_upsell(
    addresses: list[str],
    network: str,
    current_product: str,
    goal: str = None,
    catalogue: str = None,
) -> str:
    """
    Identify upsell opportunities for one or more wallets.
    Behaviour is driven by the chainaware-upsell-advisor.md agent definition.
    """
    log.info(
        "Starting upsell advisory — %d address(es) network=%s product=%s",
        len(addresses), network, current_product,
    )
    model, system_prompt = load_agent(AGENT_MD)

    if len(addresses) == 1:
        body = (
            f"Identify the best upsell opportunity for this wallet.\n\n"
            f"Address: {addresses[0]}\n"
            f"Network: {network}\n"
            f"Current product: {current_product}\n"
        )
    else:
        address_list = "\n".join(f"- {addr}" for addr in addresses)
        body = (
            f"Identify upsell opportunities across these wallets.\n\n"
            f"Network: {network}\n"
            f"Current product: {current_product}\n"
            f"Wallet addresses ({len(addresses)} total):\n{address_list}\n"
        )

    if goal:
        body += f"Upsell goal: {goal}\n"
    if catalogue:
        body += f"Available next products: {catalogue}\n"
    body += f"API Key: {chainaware.api_key()}"

    log.info("Calling upsell advisor (model=%s)", model)
    result = chainaware.run(body, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Upsell advisory complete — report length=%d chars", len(result))
    return result


if __name__ == "__main__":
    if len(sys.argv) >= 4:
        target          = sys.argv[1]
        network         = sys.argv[2].upper()
        current_product = sys.argv[3]
        goal            = sys.argv[4] if len(sys.argv) > 4 else None
        catalogue       = sys.argv[5] if len(sys.argv) > 5 else None

        if os.path.isfile(target):
            addresses = load_addresses_from_csv(target)
            log.info("=== Upsell Advisor starting (batch: %d wallets) ===", len(addresses))
            print(f"Advising upsell for: {target}")
        else:
            addresses = [target]
            log.info("=== Upsell Advisor starting (single wallet) ===")
            print(f"Advising upsell for: {target}")
    else:
        addresses       = [DEMO_ADDRESS]
        network         = DEMO_NETWORK
        current_product = DEMO_CURRENT_PRODUCT
        goal            = None
        catalogue       = None
        log.info("=== Upsell Advisor starting (demo) ===")
        print(f"Advising upsell for: {DEMO_ADDRESS} (demo)")

    print(f"Network:         {network}")
    print(f"Current product: {current_product}")
    if goal:
        print(f"Goal:            {goal}")
    if catalogue:
        print(f"Catalogue:       {catalogue}")
    print("=" * 60)

    report = advise_upsell(addresses, network, current_product, goal=goal, catalogue=catalogue)
    print(report)

    log.info("=== Upsell Advisor done ===")
