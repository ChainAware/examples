"""
ChainAware Example: Whale Detector
=====================================
Agent: chainaware-whale-detector
Source: .claude/agents/chainaware-whale-detector.md

Classifies wallets into whale tiers (MEGA WHALE / WHALE / EMERGING WHALE / NOT A WHALE)
using behavioral signals. Also detects activity status (Active / Dormant) and domain
(DeFi Whale, Trading Whale, NFT Whale, etc.).

Usage — single:
    python python/agents/whale_detector.py <address> <network>

Usage — batch:
    python python/agents/whale_detector.py <csv_file> <network>

    address   A single wallet address (0x...)
    csv_file  Path to a CSV file with wallet addresses
    network   Blockchain network (ETH, BNB, BASE, HAQQ, SOLANA)

Examples:
    python python/agents/whale_detector.py 0xd8da6bf26964af9d7eed9e03e53415d37aa96045 ETH
    python python/agents/whale_detector.py wallets.csv ETH

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-whale-detector.md"
)

DEMO_ADDRESS = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"  # vitalik.eth
DEMO_NETWORK = "ETH"


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


def detect_whales(addresses: list[str], network: str) -> str:
    """
    Classify one or more wallets into whale tiers.
    Behaviour is driven by the chainaware-whale-detector.md agent definition.
    """
    log.info("Starting whale detection — %d address(es) network=%s", len(addresses), network)
    model, system_prompt = load_agent(AGENT_MD)

    if len(addresses) == 1:
        body = f"Classify this wallet's whale tier.\n\nAddress: {addresses[0]}\nNetwork: {network}\n"
    else:
        address_list = "\n".join(f"- {addr}" for addr in addresses)
        body = (
            f"Screen these wallets for whale tier classification.\n\n"
            f"Network: {network}\n"
            f"Wallet addresses ({len(addresses)} total):\n{address_list}\n"
        )
    body += f"API Key: {chainaware.api_key()}"

    log.info("Calling whale detector (model=%s)", model)
    result = chainaware.run(body, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Whale detection complete — report length=%d chars", len(result))
    return result


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        target  = sys.argv[1]
        network = sys.argv[2].upper()
        if os.path.isfile(target):
            addresses = load_addresses_from_csv(target)
            log.info("=== Whale Detector starting (batch: %d wallets) ===", len(addresses))
            print(f"Screening wallets from: {target}")
        else:
            addresses = [target]
            log.info("=== Whale Detector starting (single wallet) ===")
            print(f"Screening wallet: {target}")
    else:
        addresses = [DEMO_ADDRESS]
        network   = DEMO_NETWORK
        log.info("=== Whale Detector starting (demo) ===")
        print(f"Screening wallet: {DEMO_ADDRESS} (demo)")

    print(f"Network: {network}")
    print("=" * 60)

    report = detect_whales(addresses, network)
    print(report)

    log.info("=== Whale Detector done ===")
