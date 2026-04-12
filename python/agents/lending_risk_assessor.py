"""
ChainAware Example: Lending Risk Assessor
==========================================
Agent: chainaware-lending-risk-assessor
Source: .claude/agents/chainaware-lending-risk-assessor.md

Assesses borrower risk for DeFi lending. Combines fraud probability, credit
score, on-chain experience, and risk appetite into a Borrower Risk Grade
(A–F) with a recommended collateral ratio and interest rate tier.

Accepts a single address or a CSV file for batch screening.

Usage — single:
    python python/agents/lending_risk_assessor.py <address> <network> [policy_mode] [loan_amount] [base_rate]

Usage — batch:
    python python/agents/lending_risk_assessor.py <csv_file> <network> [policy_mode]

    address      A single wallet address (0x...)
    csv_file     Path to a CSV file with wallet addresses
    network      Blockchain network (ETH, BNB, BASE, HAQQ, SOLANA)
    policy_mode  Optional: conservative | standard | aggressive  (default: standard)
    loan_amount  Optional: e.g. "$10,000" — used to calculate recommended terms
    base_rate    Optional: e.g. "6%" — protocol base rate to calculate borrower rate

Examples:
    python python/agents/lending_risk_assessor.py 0xd8da6bf26964af9d7eed9e03e53415d37aa96045 ETH standard "$10,000" "6%"
    python python/agents/lending_risk_assessor.py wallets.csv ETH conservative

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-lending-risk-assessor.md"
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


def assess_lending_risk(
    addresses: list[str],
    network: str,
    policy_mode: str = None,
    loan_amount: str = None,
    base_rate: str = None,
) -> str:
    """
    Assess borrower risk for one or more wallets.
    Behaviour is driven by the chainaware-lending-risk-assessor.md agent definition.
    """
    log.info(
        "Starting lending risk assessment — %d address(es) network=%s policy=%s",
        len(addresses), network, policy_mode or "standard",
    )

    model, system_prompt = load_agent(AGENT_MD)

    if len(addresses) == 1:
        body = f"Assess borrower risk for this wallet.\n\nAddress: {addresses[0]}\nNetwork: {network}\n"
    else:
        address_list = "\n".join(f"- {addr}" for addr in addresses)
        body = (
            f"Assess borrower risk for these wallets.\n\n"
            f"Network: {network}\n"
            f"Wallet addresses ({len(addresses)} total):\n{address_list}\n"
        )

    if policy_mode:
        body += f"Policy Mode: {policy_mode}\n"
    if loan_amount:
        body += f"Loan Amount: {loan_amount}\n"
    if base_rate:
        body += f"Base Rate: {base_rate}\n"
    body += f"API Key: {chainaware.api_key()}"

    log.info("Calling lending risk assessor (model=%s)", model)
    result = chainaware.run(body, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Lending risk assessment complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python python/agents/lending_risk_assessor.py <csv_file|address> <network> [policy_mode] [loan_amount] [base_rate]")
        sys.exit(1)

    target      = sys.argv[1]
    network     = sys.argv[2].upper()
    policy_mode = sys.argv[3] if len(sys.argv) > 3 else "standard"
    loan_amount = sys.argv[4] if len(sys.argv) > 4 else None
    base_rate   = sys.argv[5] if len(sys.argv) > 5 else None

    if os.path.isfile(target):
        addresses = load_addresses_from_csv(target)
        log.info("=== Lending Risk Assessor starting (batch: %d wallets) ===", len(addresses))
        print(f"Assessing borrowers from: {target}")
    else:
        addresses = [target]
        log.info("=== Lending Risk Assessor starting (single wallet) ===")
        print(f"Assessing wallet: {target}")

    print(f"Network:     {network}")
    print(f"Policy mode: {policy_mode}")
    if loan_amount:
        print(f"Loan amount: {loan_amount}")
    if base_rate:
        print(f"Base rate:   {base_rate}")
    print("=" * 60)

    report = assess_lending_risk(
        addresses, network,
        policy_mode=policy_mode,
        loan_amount=loan_amount,
        base_rate=base_rate,
    )
    print(report)

    log.info("=== Lending Risk Assessor done ===")
