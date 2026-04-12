# ChainAware Examples — Claude Code Instructions

## Project Structure

```
python/MCP/        Direct MCP examples (call tools via user prompt)
python/agents/     Agent-based examples (load .md as system prompt)
python/chainaware.py  Shared helper — imported by all scripts
.claude/agents/    32 agent definitions pulled from behavioral-prediction-mcp repo
```

## Shared Helper

All scripts import `chainaware` from `python/chainaware.py`.
Scripts in `python/agents/` and `python/MCP/` must add this to their `sys.path`:

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
```

## Agent Example Pattern

When creating a new agent-based example in `python/agents/`:

1. Load the agent definition from `.claude/agents/<name>.md`
2. Parse frontmatter with `---` split to extract `model`
3. Use the body as the `system` prompt
4. Pass a minimal user message (wallet/contract/network only — no API key)
5. Call `chainaware.run(user_message, system=system_prompt, model=model)`

Standard `load_agent()` function to reuse across all agent scripts:

```python
AGENT_MD = os.path.join(
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "<agent-name>.md"
)

def load_agent(path: str) -> tuple[str, str]:
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-haiku-4-5-20251001"
    return model, body
```

## CSV Helper Pattern

Scripts that accept a CSV file use this standard loader:

```python
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
            next(raw_reader, None)
            for row in raw_reader:
                if row and row[0].strip():
                    addresses.append(row[0].strip())
    return addresses
```

## Single-or-CSV Pattern

Several scripts auto-detect whether their first argument is a CSV file or a single
address. Use `os.path.isfile(target)` to branch:

```python
if os.path.isfile(target):
    addresses = load_addresses_from_csv(target)
else:
    addresses = [target]
```

## Existing Agent Examples

### Single wallet / hardcoded input

| Script | Agent |
|--------|-------|
| `fraud_detector.py` | `chainaware-fraud-detector.md` |
| `wallet_auditor.py` | `chainaware-wallet-auditor.md` |
| `rug_pull_checker.py` | `chainaware-rug-pull-detector.md` |
| `aml_scorer.py` | `chainaware-aml-scorer.md` |
| `agent_screener.py` | `chainaware-agent-screener.md` |
| `credit_scorer.py` | `chainaware-credit-scorer.md` |
| `defi_advisor.py` | `chainaware-defi-advisor.md` |

### Single wallet or CSV (auto-detected)

| Script | Agent |
|--------|-------|
| `compliance_screener.py` | `chainaware-compliance-screener.md` |
| `counterparty_screener.py` | `chainaware-counterparty-screener.md` |
| `onboarding_router.py` | `chainaware-onboarding-router.md` |
| `platform_greeter.py` | `chainaware-platform-greeter.md` |
| `governance_screener.py` | `chainaware-governance-screener.md` |
| `lead_scorer.py` | `chainaware-lead-scorer.md` |
| `lending_risk_assessor.py` | `chainaware-lending-risk-assessor.md` |
| `marketing_director.py` | `chainaware-marketing-director.md` |
| `reputation_scorer.py` | `chainaware-reputation-scorer.md` |
| `rwa_investor_screener.py` | `chainaware-rwa-investor-screener.md` |
| `trust_scorer.py` | `chainaware-trust-scorer.md` |
| `upsell_advisor.py` | `chainaware-upsell-advisor.md` |
| `wallet_marketer.py` | `chainaware-wallet-marketer.md` |
| `wallet_ranker.py` | `chainaware-wallet-ranker.md` |
| `whale_detector.py` | `chainaware-whale-detector.md` |

### Unique input patterns

| Script | Agent |
|--------|-------|
| `token_analyzer.py` | `chainaware-token-analyzer.md` |
| `token_launch_auditor.py` | `chainaware-token-launch-auditor.md` |
| `token_ranker.py` | `chainaware-token-ranker.md` |
| `transaction_monitor.py` | `chainaware-transaction-monitor.md` |

### CSV batch only

| Script | Agent |
|--------|-------|
| `airdrop_screener.py` | `chainaware-airdrop-screener.md` |
| `cohort_analyzer.py` | `chainaware-cohort-analyzer.md` |
| `ltv_estimator.py` | `chainaware-ltv-estimator.md` |
| `sybil_detector.py` | `chainaware-sybil-detector.md` |
| `gamefi_screener.py` | `chainaware-gamefi-screener.md` |

## Agent Definitions

`.claude/agents/` files come from the upstream repo and **must not be hand-edited**.
To refresh all 32 agent definitions from GitHub:

```bash
gh api repos/ChainAware/behavioral-prediction-mcp/contents/.claude/agents | python3 -c "
import json, sys, base64, subprocess
for f in json.load(sys.stdin):
    data = json.loads(subprocess.run(['gh', 'api', f['url']], capture_output=True, text=True).stdout)
    open(f'.claude/agents/{f[\"name\"]}', 'w').write(base64.b64decode(data['content']).decode())
    print('Updated', f['name'])
"
```

## Running Examples

Always run from the project root:

```bash
# hardcoded single wallet
python python/agents/fraud_detector.py
python python/agents/wallet_auditor.py
python python/agents/rug_pull_checker.py
python python/agents/aml_scorer.py
python python/agents/agent_screener.py
python python/agents/credit_scorer.py
python python/agents/defi_advisor.py

# single wallet (pass address on CLI)
python python/agents/onboarding_router.py 0xABC... ETH
python python/agents/platform_greeter.py 0xABC... ETH Aave
python python/agents/governance_screener.py 0xABC... ETH token-weighted
python python/agents/lead_scorer.py 0xABC... ETH "DeFi lending" acquisition
python python/agents/lending_risk_assessor.py 0xABC... ETH standard '$10,000' '6%'
python python/agents/marketing_director.py 0xABC... ETH "Platform description"
python python/agents/reputation_scorer.py 0xABC... ETH
python python/agents/rwa_investor_screener.py 0xABC... ETH moderate
python python/agents/trust_scorer.py 0xABC... ETH
python python/agents/upsell_advisor.py 0xABC... ETH "basic DEX swap" revenue
python python/agents/wallet_marketer.py 0xABC... ETH
python python/agents/wallet_ranker.py 0xABC... ETH
python python/agents/whale_detector.py 0xABC... ETH

# CSV batch
python python/agents/airdrop_screener.py wallets.csv ETH
python python/agents/cohort_analyzer.py wallets.csv ETH retention
python python/agents/ltv_estimator.py wallets.csv ETH
python python/agents/sybil_detector.py voters.csv ETH "Proposal #42"
python python/agents/gamefi_screener.py players.csv ETH "MyGame" 500
python python/agents/governance_screener.py wallets.csv ETH reputation-weighted 10000
python python/agents/lead_scorer.py wallets.csv ETH "DeFi lending" acquisition
python python/agents/lending_risk_assessor.py wallets.csv ETH conservative
python python/agents/marketing_director.py wallets.csv ETH "Platform description" retention
python python/agents/reputation_scorer.py wallets.csv ETH
python python/agents/rwa_investor_screener.py wallets.csv ETH moderate '$50,000'
python python/agents/trust_scorer.py wallets.csv ETH
python python/agents/upsell_advisor.py wallets.csv ETH "basic DEX swap" retention
python python/agents/wallet_marketer.py wallets.csv ETH
python python/agents/wallet_ranker.py wallets.csv ETH
python python/agents/whale_detector.py wallets.csv ETH

# unique input patterns
python python/agents/token_analyzer.py 0xCONTRACT... ETH
python python/agents/token_launch_auditor.py 0xCONTRACT... 0xDEPLOYER... ETH
python python/agents/token_ranker.py ETH "DeFi Token" 10
python python/agents/transaction_monitor.py 0xSENDER... 0xRECEIVER... ETH

# MCP direct
python python/MCP/fraud_detector.py
python python/MCP/rug_pull_checker.py
python python/MCP/token_ranker.py
```

## Environment Variables

```bash
export ANTHROPIC_API_KEY="..."
export CHAINAWARE_API_KEY="..."
```

Copy `.env.example` to `.env` and fill in your keys. `.env` is in `.gitignore`.

Never pass `API Key` in the user message — the key is already embedded in the
MCP server URL inside `chainaware.py`.
