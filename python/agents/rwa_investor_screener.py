"""
ChainAware Example: RWA Investor Screener
==========================================
Agent: chainaware-rwa-investor-screener
Source: .claude/agents/chainaware-rwa-investor-screener.md

Screens wallets seeking to invest in tokenized Real World Assets (RWA). Assesses
AML compliance, fraud risk, on-chain experience, and risk profile alignment against
the RWA's risk tier — then returns a Suitability Tier (QUALIFIED / CONDITIONAL /
REFER_TO_KYC / DISQUALIFIED) and a recommended investment cap.

Usage — single:
    python python/agents/rwa_investor_screener.py <address> <network> [rwa_risk_tier] [investment_cap] [policy]

Usage — batch:
    python python/agents/rwa_investor_screener.py <csv_file> <network> [rwa_risk_tier] [investment_cap] [policy]

    address         A single wallet address (0x...)
    csv_file        Path to a CSV file with wallet addresses
    network         Blockchain network (ETH, BNB, BASE, HAQQ, SOLANA)
    rwa_risk_tier   Optional: conservative | moderate | aggressive  (default: moderate)
    investment_cap  Optional: platform investment cap (e.g. '$50,000')
    policy          Optional: conservative | standard | aggressive  (issuer policy mode)

Examples:
    python python/agents/rwa_investor_screener.py 0xd8da6bf26964af9d7eed9e03e53415d37aa96045 ETH moderate
    python python/agents/rwa_investor_screener.py 0xd8da6bf26964af9d7eed9e03e53415d37aa96045 ETH aggressive '$25,000'
    python python/agents/rwa_investor_screener.py wallets.csv ETH moderate '$50,000' conservative

Networks supported for fraud screening:    ETH · BNB · POLYGON · TON · BASE · TRON · HAQQ
Networks supported for behaviour data:     ETH · BNB · BASE · HAQQ · SOLANA

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-rwa-investor-screener.md"
)

# Demo address used when no argument is provided
DEMO_ADDRESS = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"  # vitalik.eth
DEMO_NETWORK = "ETH"


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


def screen_rwa_investors(
    addresses: list[str],
    network: str,
    rwa_risk_tier: str = None,
    investment_cap: str = None,
    policy: str = None,
) -> str:
    """
    Screen one or more wallets for RWA investor suitability.
    Behaviour is driven by the chainaware-rwa-investor-screener.md agent definition.
    """
    log.info(
        "Starting RWA investor screening — %d address(es) network=%s rwa_risk_tier=%s",
        len(addresses), network, rwa_risk_tier or "moderate (default)",
    )

    model, system_prompt = load_agent(AGENT_MD)

    if len(addresses) == 1:
        body = (
            f"Screen this wallet for RWA investor suitability.\n\n"
            f"Address: {addresses[0]}\n"
            f"Network: {network}\n"
        )
    else:
        address_list = "\n".join(f"- {addr}" for addr in addresses)
        body = (
            f"Batch screen these wallets for RWA investor suitability.\n\n"
            f"Network: {network}\n"
            f"Wallet addresses ({len(addresses)} total):\n{address_list}\n"
        )

    if rwa_risk_tier:
        body += f"RWA Risk Tier: {rwa_risk_tier}\n"
    if investment_cap:
        body += f"Platform Investment Cap: {investment_cap}\n"
    if policy:
        body += f"Issuer Policy Mode: {policy}\n"
    body += f"API Key: {chainaware.api_key()}"

    log.info("Calling RWA investor screener (model=%s)", model)
    result = chainaware.run(body, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("RWA screening complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        target         = sys.argv[1]
        network        = sys.argv[2].upper()
        rwa_risk_tier  = sys.argv[3] if len(sys.argv) > 3 else None
        investment_cap = sys.argv[4] if len(sys.argv) > 4 else None
        policy         = sys.argv[5] if len(sys.argv) > 5 else None

        if os.path.isfile(target):
            addresses = load_addresses_from_csv(target)
            log.info("=== RWA Investor Screener starting (batch: %d wallets) ===", len(addresses))
            print(f"Screening wallets from: {target}")
        else:
            addresses = [target]
            log.info("=== RWA Investor Screener starting (single wallet) ===")
            print(f"Screening wallet: {target}")
    else:
        addresses      = [DEMO_ADDRESS]
        network        = DEMO_NETWORK
        rwa_risk_tier  = "moderate"
        investment_cap = None
        policy         = None
        log.info("=== RWA Investor Screener starting (demo) ===")
        print(f"Screening wallet: {DEMO_ADDRESS} (demo)")

    print(f"Network:       {network}")
    print(f"RWA Risk Tier: {rwa_risk_tier or 'moderate (default)'}")
    if investment_cap:
        print(f"Platform Cap:  {investment_cap}")
    if policy:
        print(f"Policy Mode:   {policy}")
    print("=" * 60)

    report = screen_rwa_investors(
        addresses, network,
        rwa_risk_tier=rwa_risk_tier,
        investment_cap=investment_cap,
        policy=policy,
    )
    print(report)

    log.info("=== RWA Investor Screener done ===")
