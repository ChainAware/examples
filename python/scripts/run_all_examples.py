"""
Run all ChainAware examples and display a summary table.

Always run from the project root:
    python python/scripts/run_all_examples.py
"""

import os
import subprocess
import sys
import time

# Demo values used for scripts that require CLI arguments
DEMO_WALLET   = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # vitalik.eth
DEMO_NETWORK  = "ETH"
DEMO_PLATFORM = "Aave"
DEMO_CSV      = "wallets.csv"

TIMEOUT = 120  # seconds per script

# (script_path, args, label)
EXAMPLES = [
    # ── agents: hardcoded demos (no args) ─────────────────────────────────
    ("python/agents/fraud_detector.py",        [],                                                          "fraud_detector"),
    ("python/agents/wallet_auditor.py",        [],                                                          "wallet_auditor"),
    ("python/agents/rug_pull_checker.py",      [],                                                          "rug_pull_checker"),
    ("python/agents/aml_scorer.py",            [],                                                          "aml_scorer"),
    ("python/agents/agent_screener.py",        [],                                                          "agent_screener"),
    ("python/agents/credit_scorer.py",         [],                                                          "credit_scorer"),
    ("python/agents/defi_advisor.py",          [],                                                          "defi_advisor"),
    ("python/agents/compliance_screener.py",   [],                                                          "compliance_screener"),
    ("python/agents/counterparty_screener.py", [],                                                          "counterparty_screener"),
    ("python/agents/token_analyzer.py",        [],                                                          "token_analyzer"),
    ("python/agents/token_ranker_list.py",     [],                                                          "token_ranker_list"),
    ("python/agents/token_ranker_single.py",   [],                                                          "token_ranker_single"),
    ("python/agents/token_launch_auditor.py",  [],                                                          "token_launch_auditor"),
    ("python/agents/portfolio_risk_advisor.py",[],                                                          "portfolio_risk_advisor"),
    ("python/agents/transaction_monitor.py",   [],                                                          "transaction_monitor"),
    # ── agents: single wallet ─────────────────────────────────────────────
    ("python/agents/onboarding_router.py",     [DEMO_WALLET, DEMO_NETWORK],                                "onboarding_router"),
    ("python/agents/platform_greeter.py",      [DEMO_WALLET, DEMO_NETWORK, DEMO_PLATFORM],                 "platform_greeter"),
    ("python/agents/governance_screener.py",   [DEMO_WALLET, DEMO_NETWORK, "token-weighted"],              "governance_screener"),
    ("python/agents/lead_scorer.py",           [DEMO_WALLET, DEMO_NETWORK, "DeFi lending", "acquisition"], "lead_scorer"),
    ("python/agents/lending_risk_assessor.py", [DEMO_WALLET, DEMO_NETWORK, "standard"],                    "lending_risk_assessor"),
    ("python/agents/marketing_director.py",    [DEMO_WALLET, DEMO_NETWORK, "DeFi lending platform"],       "marketing_director"),
    ("python/agents/reputation_scorer.py",     [DEMO_WALLET, DEMO_NETWORK],                                "reputation_scorer"),
    ("python/agents/rwa_investor_screener.py", [DEMO_WALLET, DEMO_NETWORK, "moderate"],                    "rwa_investor_screener"),
    ("python/agents/trust_scorer.py",          [DEMO_WALLET, DEMO_NETWORK],                                "trust_scorer"),
    ("python/agents/upsell_advisor.py",        [DEMO_WALLET, DEMO_NETWORK, "basic DEX swap", "revenue"],   "upsell_advisor"),
    ("python/agents/wallet_marketer.py",       [DEMO_WALLET, DEMO_NETWORK],                                "wallet_marketer"),
    ("python/agents/wallet_ranker.py",         [DEMO_WALLET, DEMO_NETWORK],                                "wallet_ranker"),
    ("python/agents/whale_detector.py",        [DEMO_WALLET, DEMO_NETWORK],                                "whale_detector"),
    # ── agents: CSV batch ─────────────────────────────────────────────────
    ("python/agents/airdrop_screener.py",      [DEMO_CSV, DEMO_NETWORK],                                   "airdrop_screener"),
    ("python/agents/cohort_analyzer.py",       [DEMO_CSV, DEMO_NETWORK, "retention"],                      "cohort_analyzer"),
    ("python/agents/ltv_estimator.py",         [DEMO_CSV, DEMO_NETWORK],                                   "ltv_estimator"),
    ("python/agents/sybil_detector.py",        [DEMO_CSV, DEMO_NETWORK, "Proposal #1"],                    "sybil_detector"),
    ("python/agents/gamefi_screener.py",       [DEMO_CSV, DEMO_NETWORK, "Demo Game", "100"],               "gamefi_screener"),
    ("python/agents/wallet_marketer_batch.py", [DEMO_CSV, DEMO_NETWORK, "/tmp/ca_marketer_out.csv"],       "wallet_marketer_batch"),
    # ── MCP direct ────────────────────────────────────────────────────────
    ("python/MCP/fraud_detector.py",           [],                                                          "MCP/fraud_detector"),
    ("python/MCP/rug_pull_checker.py",         [],                                                          "MCP/rug_pull_checker"),
    ("python/MCP/token_ranker.py",             [],                                                          "MCP/token_ranker"),
]


def run_example(script: str, args: list) -> dict:
    for arg in args:
        if arg.endswith(".csv") and not arg.startswith("/tmp") and not os.path.isfile(arg):
            return {"status": "SKIP", "duration": 0.0, "tokens": 0, "note": f"missing input file: {arg}"}

    cmd = [sys.executable, script] + args
    start = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
        duration = time.time() - start
        tokens = _parse_tokens(proc.stderr + proc.stdout)
        if proc.returncode == 0:
            return {"status": "PASS", "duration": duration, "tokens": tokens, "note": _first_output_line(proc.stdout)}
        else:
            return {"status": "FAIL", "duration": duration, "tokens": tokens, "note": _first_output_line(proc.stderr or proc.stdout)}
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "duration": time.time() - start, "tokens": 0, "note": f"exceeded {TIMEOUT}s"}
    except Exception as e:
        return {"status": "ERROR", "duration": time.time() - start, "tokens": 0, "note": str(e)[:80]}


def _parse_tokens(text: str) -> int:
    import re
    total = 0
    for m in re.finditer(r"input_tokens=(\d+)\s+output_tokens=(\d+)", text):
        total += int(m.group(1)) + int(m.group(2))
    return total


def _first_output_line(text: str) -> str:
    lines = text.splitlines()
    # First pass: look for the actual exception line (last non-empty line of a traceback)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("Traceback (most recent call last)"):
            # Return the last non-empty line of the traceback block
            for candidate in reversed(lines[i:]):
                c = candidate.strip()
                if c and not c.startswith("File ") and not c.startswith("Traceback"):
                    return c[:80]
    # Second pass: first meaningful non-log line
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "[INFO]" in line or "[WARNING]" in line:
            continue
        if "[ERROR]" in line or "[CRITICAL]" in line:
            return line.split("]", 1)[-1].strip()[:80]
        return line[:80]
    return ""


def print_summary(results: list) -> None:
    STATUS_ICON = {"PASS": "✓", "FAIL": "✗", "SKIP": "—", "TIMEOUT": "⏱", "ERROR": "✗"}

    col_label  = max(len(r[0]) for r in results) + 2
    col_status = 10
    col_dur    = 9
    col_tokens = 10
    col_note   = 45
    width      = col_label + col_status + col_dur + col_tokens + col_note

    sep = "─" * width
    print(f"\n{sep}")
    print(f"{'Script':<{col_label}} {'Status':<{col_status}} {'Time':<{col_dur}} {'Tokens':<{col_tokens}} Note")
    print(sep)

    passed = failed = skipped = timed_out = 0
    total_tokens = 0
    for label, res in results:
        icon   = STATUS_ICON.get(res["status"], "?")
        status = f"{icon} {res['status']}"
        dur    = f"{res['duration']:.1f}s" if res["duration"] else "—"
        tokens = f"{res['tokens']:,}" if res.get("tokens") else "—"
        note   = res["note"][:col_note]
        print(f"{label:<{col_label}} {status:<{col_status}} {dur:<{col_dur}} {tokens:<{col_tokens}} {note}")
        total_tokens += res.get("tokens", 0)
        if   res["status"] == "PASS":    passed    += 1
        elif res["status"] == "SKIP":    skipped   += 1
        elif res["status"] == "TIMEOUT": timed_out += 1
        else:                            failed    += 1

    print(sep)
    total = len(results)
    print(f"\n  {passed}/{total} passed  ·  {failed} failed  ·  {timed_out} timed out  ·  {skipped} skipped")
    print(f"  Total tokens consumed: {total_tokens:,}\n")


if __name__ == "__main__":
    total = len(EXAMPLES)
    print(f"\nChainAware Examples — running {total} scripts\n")

    results = []
    for i, (script, args, label) in enumerate(EXAMPLES, 1):
        print(f"  [{i:2d}/{total}] {label} ...", end="", flush=True)
        res = run_example(script, args)
        icon = STATUS_ICON = {"PASS": "✓", "FAIL": "✗", "SKIP": "—", "TIMEOUT": "⏱", "ERROR": "✗"}.get(res["status"], "?")
        dur  = f"  {res['duration']:.1f}s" if res["duration"] else ""
        print(f"  {icon}{dur}")
        results.append((label, res))
        if i < total:
            pause = 30 if res["status"] == "TIMEOUT" else 3
            time.sleep(pause)

    print_summary(results)
