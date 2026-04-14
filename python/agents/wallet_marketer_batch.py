"""
ChainAware Example: Wallet Marketer Batch
==========================================
Agent: chainaware-wallet-marketer
Source: .claude/agents/chainaware-wallet-marketer.md

Reads wallet addresses from a CSV file, generates a hyper-personalized
marketing message (max 20 words) for each wallet, and writes the results
to an output CSV with columns: address, message.

Each wallet is processed individually so results can be paired accurately.
Wallets flagged as high fraud risk are written with a "BLOCKED" message.

Usage:
    python python/agents/wallet_marketer_batch.py <csv_file> <network> [output_csv] [platform]

    csv_file    Path to a CSV file. Any column named 'address', 'wallet',
                'Address', or 'Wallet' is used. Falls back to first column.
    network     Blockchain network (ETH, BNB, BASE, HAQQ, SOLANA)
    output_csv  Output CSV path (default: wallet_marketer_output.csv)
    platform    Target platform name (e.g. Uniswap, Aave, OpenSea) — optional

Examples:
    python python/agents/wallet_marketer_batch.py wallets.csv ETH
    python python/agents/wallet_marketer_batch.py wallets.csv ETH results.csv Aave

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-wallet-marketer.md"
)


def load_agent(path: str) -> tuple[str, str]:
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-sonnet-4-6"
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
            log.warning(
                "No 'address'/'wallet' column found. Using first column: %s",
                header[0] if header else "(none)",
            )
            for row in raw_reader:
                if row and row[0].strip():
                    addresses.append(row[0].strip())
    return addresses


def extract_message(response_text: str) -> str:
    """
    Parse the agent's markdown response and return the 20-word marketing message.

    The agent formats the primary message as:
        ### 🎯 Your 20-Word Message
        > "The message here"

    Falls back to looking for any blockquote line if the heading is absent.
    Returns "BLOCKED" when the agent explicitly declines to market the wallet.
    """
    # Detect fraud-blocked responses
    if "⛔" in response_text and "Marketing Blocked" in response_text:
        m = re.search(r"[Ff]raud probability[:\s]*([\d.]+)", response_text)
        fraud_score = m.group(1) if m else "high"
        return f"BLOCKED — fraud risk {fraud_score}"

    # Primary: look for the line after the 20-Word Message heading
    heading_match = re.search(
        r"(?:🎯\s*)?(?:Your\s+)?20[- ]Word Message.*?\n+\s*>\s*[\"']?(.+?)[\"']?\s*$",
        response_text,
        re.MULTILINE | re.IGNORECASE,
    )
    if heading_match:
        return heading_match.group(1).strip().strip('"').strip("'")

    # Fallback: first blockquote line that looks like a sentence
    for line in response_text.splitlines():
        stripped = line.strip()
        if stripped.startswith(">"):
            candidate = stripped.lstrip(">").strip().strip('"').strip("'")
            if len(candidate) > 10:
                return candidate

    # Last resort: return a truncated version of the full response
    return response_text.strip()[:120]


def generate_message_for_wallet(
    address: str, network: str, system_prompt: str, model: str, platform: str = ""
) -> str:
    """Call the wallet marketer agent for a single wallet and return the message."""
    platform_line = f"Target platform: {platform}\n" if platform else ""
    user_message = (
        f"Generate a personalized marketing message for this wallet.\n\n"
        f"Address: {address}\n"
        f"Network: {network}\n"
        f"{platform_line}"
        f"API Key: {chainaware.api_key()}"
    )
    response_text = chainaware.run(
        user_message, system=system_prompt, model=model, max_tokens=2048
    )
    return extract_message(response_text)


def run_batch(
    csv_path: str, network: str, output_path: str, platform: str = ""
) -> list[dict]:
    """
    Process every wallet in csv_path and write results to output_path.
    Returns the list of result rows.
    """
    addresses = load_addresses_from_csv(csv_path)
    log.info("Loaded %d addresses from %s", len(addresses), csv_path)

    model, system_prompt = load_agent(AGENT_MD)
    log.info("Agent loaded — model=%s", model)

    results = []
    for i, address in enumerate(addresses, 1):
        log.info("[%d/%d] Processing %s", i, len(addresses), address)
        try:
            message = generate_message_for_wallet(
                address, network, system_prompt, model, platform
            )
        except Exception as exc:
            log.error("Error processing %s: %s", address, exc)
            message = f"ERROR — {exc}"
        results.append({"address": address, "message": message})
        log.info("[%d/%d] Done: %s", i, len(addresses), message[:60])

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["address", "message"])
        writer.writeheader()
        writer.writerows(results)

    log.info("Output written to %s", output_path)
    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python python/agents/wallet_marketer_batch.py "
            "<csv_file> <network> [output_csv] [platform]"
        )
        print(
            "Example: python python/agents/wallet_marketer_batch.py "
            "wallets.csv ETH results.csv Aave"
        )
        sys.exit(1)

    csv_file = sys.argv[1]
    network = sys.argv[2].upper()
    output_csv = sys.argv[3] if len(sys.argv) >= 4 else "wallet_marketer_output.csv"
    platform = sys.argv[4] if len(sys.argv) >= 5 else ""

    if not os.path.isfile(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        sys.exit(1)

    log.info("=== Wallet Marketer Batch starting ===")
    print(f"Input:   {csv_file}")
    print(f"Network: {network}")
    if platform:
        print(f"Platform: {platform}")
    print(f"Output:  {output_csv}")
    print("=" * 60)

    rows = run_batch(csv_file, network, output_csv, platform)

    print(f"\nDone — {len(rows)} wallet(s) processed.")
    print(f"Results written to: {output_csv}")
    print()

    # Print a summary table to stdout
    col_w = 44
    print(f"{'Address':<{col_w}}  Message")
    print("-" * (col_w + 2) + "-" * 40)
    for row in rows:
        addr_display = row["address"][:col_w]
        msg_display = row["message"][:60]
        print(f"{addr_display:<{col_w}}  {msg_display}")

    log.info("=== Wallet Marketer Batch done ===")
