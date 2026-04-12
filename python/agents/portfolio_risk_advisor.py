"""
ChainAware Example: Portfolio Risk Advisor
==========================================
Agent: chainaware-portfolio-risk-advisor
Source: .claude/agents/chainaware-portfolio-risk-advisor.md

Scans every token in a portfolio through predictive_rug_pull, enriches with
community rank data where available, calculates a portfolio-weighted risk score,
assigns a grade (A–F), flags dangerous concentrations, and produces a prioritized
rebalancing plan.

Note: this agent uses claude-sonnet-4-6 and scans every token sequentially.
Expect longer run times for large portfolios.

Usage — CSV:
    python python/agents/portfolio_risk_advisor.py <csv_file> [risk_tolerance]

    csv_file        CSV with columns: contract, network, position_usd (optional)
    risk_tolerance  Optional: conservative | standard | aggressive  (default: standard)

Usage — hardcoded demo (no arguments):
    python python/agents/portfolio_risk_advisor.py

CSV format example:
    contract,network,position_usd
    0xdAC17F958D2ee523a2206206994597C13D831ec7,ETH,5000
    0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599,ETH,3000
    0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c,BNB,2000

Networks supported for rug pull scan: ETH · BNB · BASE · HAQQ
Networks supported for community rank: ETH · BNB · BASE · SOLANA

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-portfolio-risk-advisor.md"
)

# Demo portfolio used when no CSV is provided
DEMO_PORTFOLIO = [
    {"contract": "0xdAC17F958D2ee523a2206206994597C13D831ec7", "network": "ETH", "position_usd": "8000"},   # USDT
    {"contract": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", "network": "ETH", "position_usd": "6000"},   # WBTC
    {"contract": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "network": "ETH", "position_usd": "5000"},   # WETH
    {"contract": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c", "network": "BNB", "position_usd": "3000"},   # WBNB
    {"contract": "0x4200000000000000000000000000000000000006", "network": "BASE", "position_usd": "3000"},   # WETH on BASE
]


def load_agent(path: str) -> tuple[str, str]:
    """Parse the agent .md file and return (model, system_prompt)."""
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-sonnet-4-6"
    return model, body


def load_portfolio_from_csv(csv_path: str) -> list[dict]:
    """
    Read token portfolio from a CSV file.
    Expected columns: contract, network, position_usd (optional).
    Falls back to first two columns if headers are not recognised.
    """
    portfolio = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = [f.lower() for f in (reader.fieldnames or [])]

        has_contract = "contract" in fieldnames
        has_network  = "network" in fieldnames
        has_position = "position_usd" in fieldnames

        if has_contract and has_network:
            for row in reader:
                # normalise keys to lowercase
                row_lower = {k.lower(): v for k, v in row.items()}
                entry = {
                    "contract": row_lower["contract"].strip(),
                    "network":  row_lower["network"].strip().upper(),
                }
                if has_position and row_lower.get("position_usd", "").strip():
                    entry["position_usd"] = row_lower["position_usd"].strip()
                if entry["contract"]:
                    portfolio.append(entry)
        else:
            # No recognised headers — try raw first two columns
            f.seek(0)
            raw_reader = csv.reader(f)
            next(raw_reader, None)  # skip header row
            log.warning("Expected columns 'contract' and 'network' not found — using first two columns")
            for row in raw_reader:
                if len(row) >= 2 and row[0].strip():
                    entry = {"contract": row[0].strip(), "network": row[1].strip().upper()}
                    if len(row) >= 3 and row[2].strip():
                        entry["position_usd"] = row[2].strip()
                    portfolio.append(entry)

    return portfolio


def assess_portfolio(portfolio: list[dict], risk_tolerance: str = "standard") -> str:
    """
    Assess rug pull risk across a token portfolio.
    Behaviour is driven by the chainaware-portfolio-risk-advisor.md agent definition.
    """
    log.info(
        "Starting portfolio risk assessment — %d token(s) risk_tolerance=%s",
        len(portfolio), risk_tolerance,
    )

    model, system_prompt = load_agent(AGENT_MD)

    has_positions = any("position_usd" in t for t in portfolio)

    token_lines = []
    for t in portfolio:
        line = f"- Contract: {t['contract']}  Network: {t['network']}"
        if "position_usd" in t:
            line += f"  Position: ${t['position_usd']}"
        token_lines.append(line)

    body = (
        f"Assess the rug pull risk of my token portfolio.\n\n"
        f"Risk Tolerance: {risk_tolerance}\n"
    )
    if not has_positions:
        body += "Position sizes: not provided — use equal weighting\n"
    body += f"\nTokens ({len(portfolio)} total):\n" + "\n".join(token_lines)
    body += f"\n\nAPI Key: {chainaware.api_key()}"

    log.info("Calling portfolio risk advisor (model=%s) — scanning %d token(s)", model, len(portfolio))
    result = chainaware.run(body, system=system_prompt, model=model, max_tokens=8192)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Portfolio risk assessment complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    risk_tolerance = "standard"

    if len(sys.argv) >= 2 and os.path.isfile(sys.argv[1]):
        portfolio = load_portfolio_from_csv(sys.argv[1])
        if len(sys.argv) >= 3:
            risk_tolerance = sys.argv[2].lower()
        log.info("=== Portfolio Risk Advisor starting (CSV: %d tokens) ===", len(portfolio))
        print(f"Portfolio from: {sys.argv[1]}")
    elif len(sys.argv) >= 2 and sys.argv[1] in ("conservative", "standard", "aggressive"):
        portfolio = DEMO_PORTFOLIO
        risk_tolerance = sys.argv[1].lower()
        log.info("=== Portfolio Risk Advisor starting (demo portfolio) ===")
        print("Portfolio: demo (hardcoded)")
    else:
        portfolio = DEMO_PORTFOLIO
        if len(sys.argv) >= 2:
            risk_tolerance = sys.argv[1].lower()
        log.info("=== Portfolio Risk Advisor starting (demo portfolio) ===")
        print("Portfolio: demo (hardcoded)")

    print(f"Risk tolerance: {risk_tolerance}")
    print(f"Tokens: {len(portfolio)}")
    print("=" * 60)
    for t in portfolio:
        pos = f"  ${t['position_usd']}" if "position_usd" in t else ""
        print(f"  {t['contract']}  [{t['network']}]{pos}")
    print("=" * 60)

    report = assess_portfolio(portfolio, risk_tolerance=risk_tolerance)
    print(report)

    log.info("=== Portfolio Risk Advisor done ===")
