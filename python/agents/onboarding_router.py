"""
ChainAware Example: Onboarding Router
=======================================
Agent: chainaware-onboarding-router
Source: .claude/agents/chainaware-onboarding-router.md

Determines the correct onboarding flow for a wallet based on its real on-chain
experience — Beginner Tutorial / Intermediate Guide / Skip Onboarding.
Accepts a single address or a CSV file for batch routing.

Usage — single:
    python python/agents/onboarding_router.py <address> <network> [platform_description]

Usage — batch:
    python python/agents/onboarding_router.py <csv_file> <network> [platform_description]

    address               A single wallet address (0x...)
    csv_file              Path to a CSV file with wallet addresses
    network               Blockchain network (ETH, BNB, BASE, HAQQ, SOLANA)
    platform_description  Optional: what your platform does — enables platform-aware routing

Examples:
    python python/agents/onboarding_router.py 0xd8da6bf26964af9d7eed9e03e53415d37aa96045 ETH
    python python/agents/onboarding_router.py wallets.csv ETH "A DeFi lending platform on Ethereum"

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-onboarding-router.md"
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


def route_onboarding(
    addresses: list[str],
    network: str,
    platform_description: str = None,
) -> str:
    """
    Route one or more wallets to the correct onboarding flow.
    Behaviour is driven by the chainaware-onboarding-router.md agent definition.
    """
    log.info(
        "Starting onboarding routing — %d address(es) network=%s",
        len(addresses), network,
    )

    model, system_prompt = load_agent(AGENT_MD)

    if len(addresses) == 1:
        body = f"Route this wallet to the correct onboarding flow.\n\nAddress: {addresses[0]}\nNetwork: {network}\n"
    else:
        address_list = "\n".join(f"- {addr}" for addr in addresses)
        body = (
            f"Route these wallets to the correct onboarding flows.\n\n"
            f"Network: {network}\n"
            f"Wallet addresses ({len(addresses)} total):\n{address_list}\n"
        )

    if platform_description:
        body += f"Platform: {platform_description}\n"
    body += f"API Key: {chainaware.api_key()}"

    log.info("Calling onboarding router (model=%s)", model)
    result = chainaware.run(body, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Onboarding routing complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python python/agents/onboarding_router.py <csv_file|address> <network> [platform_description]")
        sys.exit(1)

    target               = sys.argv[1]
    network              = sys.argv[2].upper()
    platform_description = sys.argv[3] if len(sys.argv) > 3 else None

    if os.path.isfile(target):
        addresses = load_addresses_from_csv(target)
        log.info("=== Onboarding Router starting (batch: %d wallets) ===", len(addresses))
        print(f"Routing wallets from: {target}")
    else:
        addresses = [target]
        log.info("=== Onboarding Router starting (single wallet) ===")
        print(f"Routing wallet: {target}")

    print(f"Network:  {network}")
    if platform_description:
        print(f"Platform: {platform_description}")
    print("=" * 60)

    report = route_onboarding(addresses, network, platform_description=platform_description)
    print(report)

    log.info("=== Onboarding Router done ===")
