"""
ChainAware Example: LTV Estimator
======================================
Agent: chainaware-ltv-estimator
Source: .claude/agents/chainaware-ltv-estimator.md

Reads wallet addresses from a CSV file, estimates the 12-month revenue
potential (Lifetime Value) for each wallet, and prints a ranked summary
with the total portfolio LTV.

Usage:
    python python/agents/ltv_estimator.py <csv_file> <network> [platform_share [fee_rate]]

    csv_file        Path to a CSV file. Any column named 'address', 'wallet',
                    or 'Address' is used. If no such column exists the first
                    column is used.
    network         Blockchain network (ETH, BNB, BASE, POLYGON, TON, TRON, HAQQ, SOLANA)
    platform_share  Optional. Fraction of wallet balance expected to be deployed on
                    your platform (0.01–1.00). Defaults to 0.15 (15%) if not provided.
                    Examples: 0.30 for a primary lending protocol, 0.10 for a DEX.
    fee_rate        Optional. Platform revenue rate per transaction as a fraction of
                    avg_tx_value (0.0001–1.00). Defaults to 0.001 (0.1%) if not provided.
                    Examples: 0.003 for a 0.3% swap fee, 0.01 for a 1% lending spread.

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-ltv-estimator.md"
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


def estimate_ltv(
    csv_path: str,
    network: str,
    platform_share: float = None,
    fee_rate: float = None,
) -> str:
    """
    Estimate 12-month LTV for all wallet addresses in a CSV file.
    The agent processes each wallet individually, then returns a ranked
    batch summary with per-wallet LTV ranges and a total portfolio sum.

    platform_share: fraction of wallet balance deployed on your platform (0.01–1.00).
                    Defaults to 0.15 (15%) inside the agent if not provided.
    fee_rate:       platform revenue rate per transaction as a fraction of avg_tx_value.
                    Defaults to 0.001 (0.1%) inside the agent if not provided.
    """
    log.info("Loading addresses from %s", csv_path)
    addresses = load_addresses_from_csv(csv_path)
    log.info(
        "Loaded %d addresses for network=%s platform_share=%s fee_rate=%s",
        len(addresses), network,
        platform_share or "(default 0.15)",
        fee_rate or "(default 0.001)",
    )

    model, system_prompt = load_agent(AGENT_MD)

    address_list = "\n".join(f"- {addr}" for addr in addresses)
    lines = [
        "Estimate 12-month LTV for these wallets.\n",
        f"Network: {network}",
        f"API Key: {chainaware.api_key()}",
    ]
    if platform_share is not None:
        lines.append(f"Platform Share: {platform_share}")
    if fee_rate is not None:
        lines.append(f"Fee Rate: {fee_rate}")
    lines += [
        f"\nWallet addresses ({len(addresses)} total):",
        address_list,
    ]
    user_message = "\n".join(lines)

    log.info(
        "Calling LTV estimator agent (model=%s) with %d wallets on %s",
        model, len(addresses), network,
    )
    result = chainaware.run(user_message, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("LTV estimation complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python python/agents/ltv_estimator.py <csv_file> <network> [platform_share [fee_rate]]")
        print("Example: python python/agents/ltv_estimator.py wallets.csv ETH")
        print("Example: python python/agents/ltv_estimator.py wallets.csv ETH 0.30")
        print("Example: python python/agents/ltv_estimator.py wallets.csv ETH 0.30 0.003")
        sys.exit(1)

    csv_file = sys.argv[1]
    network = sys.argv[2].upper()
    platform_share = float(sys.argv[3]) if len(sys.argv) >= 4 else None
    fee_rate = float(sys.argv[4]) if len(sys.argv) >= 5 else None

    if not os.path.isfile(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        sys.exit(1)

    log.info("=== LTV Estimator starting ===")
    print(f"Estimating LTV for wallets from: {csv_file}")
    print(f"Network:        {network}")
    print(f"Platform share: {platform_share or '(default 0.15)'}")
    print(f"Fee rate:       {fee_rate or '(default 0.001)'}")
    print("=" * 60)

    report = estimate_ltv(csv_file, network, platform_share, fee_rate)
    print(report)

    log.info("=== LTV Estimator done ===")
