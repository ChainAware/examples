"""
ChainAware Example: Compliance Screener — Transaction Check
=============================================================
Agent: chainaware-compliance-screener
Source: .claude/agents/chainaware-compliance-screener.md

MiCA-aligned compliance screening for a transaction: checks sender and receiver
for fraud/AML risk, scores the counterparty, and produces a PASS / EDD / REJECT
verdict with a Travel Rule threshold assessment.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY="your-anthropic-key"
    export CHAINAWARE_API_KEY="your-chainaware-key"
"""

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-compliance-screener.md"
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


def screen_transaction(
    sender: str,
    receiver: str,
    network: str,
    value: str = None,
    tx_type: str = None,
    receiver_type: str = None,
) -> str:
    """
    Run a transaction compliance check against sender and receiver wallets.
    Behaviour is driven by the chainaware-compliance-screener.md agent definition.

    receiver_type: "wallet" — EOA, uses fraud check
                   "contract" — smart contract, uses rug pull check
                   None (default) — inferred from tx_type by the agent
    """
    log.info(
        "Starting transaction compliance check — sender=%s receiver=%s (%s) network=%s",
        sender, receiver, receiver_type or "inferred", network,
    )

    model, system_prompt = load_agent(AGENT_MD)

    lines = [
        "Run a transaction compliance check.\n",
        f"Sender:   {sender}",
        f"Receiver: {receiver}",
        f"Network:  {network}",
    ]
    if value:
        lines.append(f"Transaction Value: {value}")
    if tx_type:
        lines.append(f"Transaction Type: {tx_type}")
    if receiver_type:
        lines.append(f"Receiver Type: {receiver_type}")
    lines.append(f"API Key: {chainaware.api_key()}")

    user_message = "\n".join(lines)

    log.info("Calling compliance screener (model=%s)", model)
    result = chainaware.run(user_message, system=system_prompt, model=model)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Compliance check complete — report length=%d chars", len(result))

    return result


if __name__ == "__main__":
    # Usage: compliance_screener.py [sender receiver network [value [tx_type [receiver_type]]]]
    # receiver_type: "wallet" or "contract" — omit to let agent infer from tx_type
    args = sys.argv[1:]
    if len(args) >= 3:
        sender        = args[0]
        receiver      = args[1]
        network       = args[2]
        value         = args[3] if len(args) >= 4 else None
        tx_type       = args[4] if len(args) >= 5 else None
        receiver_type = args[5] if len(args) >= 6 else None
    else:
        # Hardcoded defaults: transfer between two wallets, above Travel Rule threshold
        sender        = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"  # vitalik.eth
        receiver      = "0x388c818ca8b9251b393131c08a736a67ccb19297"  # Lido operator
        network       = "ETH"
        value         = "$5,000"
        tx_type       = "transfer"
        receiver_type = None  # agent will infer "wallet" from tx_type=transfer

    log.info("=== Compliance Screener (transaction) starting ===")
    print(f"Sender:        {sender}")
    print(f"Receiver:      {receiver}")
    print(f"Receiver type: {receiver_type or '(infer from tx_type)'}")
    print(f"Network:       {network}")
    print(f"Value:         {value or '(not specified)'}")
    print(f"Type:          {tx_type or '(not specified)'}\n")
    print("=" * 60)

    report = screen_transaction(sender, receiver, network, value=value, tx_type=tx_type, receiver_type=receiver_type)
    print(report)

    log.info("=== Compliance Screener done ===")
