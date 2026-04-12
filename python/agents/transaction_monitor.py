"""
ChainAware Example: Transaction Monitor
=========================================
Agent: chainaware-transaction-monitor
Source: .claude/agents/chainaware-transaction-monitor.md

Real-time transaction risk scoring for autonomous AI agents and automated pipelines.
Screens sender, receiver, and contract — returns a composite risk score and a
machine-actionable pipeline signal: ALLOW / FLAG / HOLD / BLOCK.

Usage:
    python python/agents/transaction_monitor.py \\
        <sender> <receiver> <network> [contract] [value] [action_type]

    sender       Sender wallet address (0x...)
    receiver     Receiver wallet address (0x...)
    network      Blockchain network (ETH, BNB, POLYGON, TON, BASE, TRON, HAQQ)
    contract     Optional: contract address involved in the transaction
    value        Optional: transaction value (e.g. '5.0 ETH', '$10,000')
    action_type  Optional: transfer | swap | stake | bridge | mint | approve | liquidity

Examples:
    python python/agents/transaction_monitor.py \\
        0xd8da6bf26964af9d7eed9e03e53415d37aa96045 \\
        0xE592427A0AEce92De3Edee1F18E0157C05861564 \\
        ETH

    python python/agents/transaction_monitor.py \\
        0xd8da6bf26964af9d7eed9e03e53415d37aa96045 \\
        0xE592427A0AEce92De3Edee1F18E0157C05861564 \\
        ETH "" "2.5 ETH" swap

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
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "chainaware-transaction-monitor.md"
)

# Demo: vitalik.eth sending to Uniswap v3 router
DEMO_SENDER   = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"  # vitalik.eth
DEMO_RECEIVER = "0xE592427A0AEce92De3Edee1F18E0157C05861564"  # Uniswap v3 SwapRouter
DEMO_NETWORK  = "ETH"
DEMO_ACTION   = "swap"


def load_agent(path: str) -> tuple[str, str]:
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-haiku-4-5-20251001"
    return model, body


def monitor_transaction(
    sender: str,
    receiver: str,
    network: str,
    contract: str = None,
    value: str = None,
    action_type: str = None,
) -> str:
    """
    Evaluate transaction risk and return a pipeline action signal.
    Behaviour is driven by the chainaware-transaction-monitor.md agent definition.
    """
    log.info(
        "Evaluating transaction — sender=%s receiver=%s network=%s action=%s",
        sender, receiver, network, action_type or "unspecified",
    )
    model, system_prompt = load_agent(AGENT_MD)

    body = (
        f"Evaluate this transaction and return a risk signal.\n\n"
        f"Sender:   {sender}\n"
        f"Receiver: {receiver}\n"
        f"Network:  {network}\n"
    )
    if contract:
        body += f"Contract: {contract}\n"
    if value:
        body += f"Value: {value}\n"
    if action_type:
        body += f"Action type: {action_type}\n"
    body += f"API Key: {chainaware.api_key()}"

    log.info("Calling transaction monitor (model=%s)", model)
    result = chainaware.run(body, system=system_prompt, model=model, max_tokens=4096)

    if not result:
        log.warning("No text block found in response content")
    else:
        log.info("Transaction evaluation complete — report length=%d chars", len(result))
    return result


if __name__ == "__main__":
    if len(sys.argv) >= 4:
        sender      = sys.argv[1]
        receiver    = sys.argv[2]
        network     = sys.argv[3].upper()
        contract    = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else None
        value       = sys.argv[5] if len(sys.argv) > 5 and sys.argv[5] else None
        action_type = sys.argv[6] if len(sys.argv) > 6 else None
        log.info("=== Transaction Monitor starting ===")
    else:
        sender      = DEMO_SENDER
        receiver    = DEMO_RECEIVER
        network     = DEMO_NETWORK
        contract    = None
        value       = None
        action_type = DEMO_ACTION
        log.info("=== Transaction Monitor starting (demo) ===")
        print("Note: demo — vitalik.eth → Uniswap v3 SwapRouter, ETH, swap")

    print(f"Sender:   {sender}")
    print(f"Receiver: {receiver}")
    print(f"Network:  {network}")
    if contract:
        print(f"Contract: {contract}")
    if value:
        print(f"Value:    {value}")
    if action_type:
        print(f"Action:   {action_type}")
    print("=" * 60)

    report = monitor_transaction(sender, receiver, network,
                                  contract=contract, value=value, action_type=action_type)
    print(report)

    log.info("=== Transaction Monitor done ===")
