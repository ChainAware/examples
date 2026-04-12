"""
ChainAware Example: GameFi Screener — Batch Mode
==================================================
Agent: chainaware-gamefi-screener
Source: .claude/agents/chainaware-gamefi-screener.md

Reads wallet addresses from a CSV file and screens them for bot farms,
multi-account cheaters, and reward abusers. Classifies legitimate players
into experience tiers (Casual / Active / Veteran / Pro) and calculates
P2E reward eligibility and multiplier for each wallet.

Usage:
    python python/agents/gamefi_screener.py <csv_file> <network> [game_name] [reward_cap]

    csv_file     Path to a CSV file. Any column named 'address', 'wallet',
                 'Address', or 'Wallet' is used. Falls back to the first column.
    network      Blockchain network (ETH, BNB, BASE, POLYGON, TON, TRON, HAQQ, SOLANA)
    game_name    Optional: name or type of the game/platform for context
    reward_cap   Optional: maximum P2E token reward per eligibility period (number)

Examples:
    python python/agents/gamefi_screener.py wallets.csv ETH
    python python/agents/gamefi_screener.py players.csv BNB "MyP2EGame" 500

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-gamefi-screener.md"
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


def screen_players(
    csv_path: str,
    network: str,
    game_name: str = None,
    reward_cap: str = None,
) -> str:
    """
    Batch screen wallet addresses from a CSV for bot detection, player tier
    classification, and P2E reward eligibility.
    Behaviour is driven by the chainaware-gamefi-screener.md agent definition.
    """
    log.info("Loading addresses from %s", csv_path)
    addresses = load_addresses_from_csv(csv_path)
    log.info("Loaded %d addresses for network=%s", len(addresses), network)

    model, system_prompt = load_agent(AGENT_MD)

    address_list = "\n".join(f"- {addr}" for addr in addresses)
    lines = [
        f"Screen these wallets for our Web3 game.\n",
        f"Network: {network}",
    ]
    if game_name:
        lines.append(f"Game / Platform: {game_name}")
    if reward_cap:
        lines.append(f"P2E Reward Cap: {reward_cap} tokens per eligibility period")
    lines.append(f"API Key: {chainaware.api_key()}")
    lines.append(f"\nWallet addresses ({len(addresses)} total):\n{address_list}")

    user_message = "\n".join(lines)

    log.info(
        "Calling GameFi screener (model=%s) with %d wallets on %s",
        model, len(addresses), network,
    )
    result = chainaware.run(user_message, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("GameFi screening complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python python/agents/gamefi_screener.py <csv_file> <network> [game_name] [reward_cap]")
        print("Example: python python/agents/gamefi_screener.py wallets.csv ETH \"MyP2EGame\" 500")
        sys.exit(1)

    csv_file   = sys.argv[1]
    network    = sys.argv[2].upper()
    game_name  = sys.argv[3] if len(sys.argv) > 3 else None
    reward_cap = sys.argv[4] if len(sys.argv) > 4 else None

    if not os.path.isfile(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        sys.exit(1)

    log.info("=== GameFi Screener starting ===")
    print(f"Screening players from: {csv_file}")
    print(f"Network:    {network}")
    if game_name:
        print(f"Game:       {game_name}")
    if reward_cap:
        print(f"Reward cap: {reward_cap} tokens")
    print("=" * 60)

    report = screen_players(csv_file, network, game_name=game_name, reward_cap=reward_cap)
    print(report)

    log.info("=== GameFi Screener done ===")
