# ChainAware Examples

Python examples showing how to use the [ChainAware Behavioral Prediction MCP](https://github.com/ChainAware/behavioral-prediction-mcp) with Claude.

---

## Prerequisites

```bash
pip install anthropic
```

### API Keys

**Anthropic API key** — used to call Claude models.
Get one at [console.anthropic.com](https://console.anthropic.com).

**ChainAware API key** — used to call the Behavioral Prediction MCP tools.
Get one at [chainaware.ai/pricing](https://chainaware.ai/pricing).

**Etherscan API key** *(optional)* — used by `chainaware.is_contract()` to auto-detect
whether an address is a smart contract or an EOA wallet. Required only by
`agent_screener.py` and `compliance_screener.py` when you want automatic
contract/wallet detection instead of passing `agent_type`, `feeder_type`, or
`receiver_type` manually.
Get one at [etherscan.io/myapikey](https://etherscan.io/myapikey).

**Option A — `.env` file (recommended):**

```bash
cp .env.example .env
# then edit .env and fill in your keys
```

The `.env.example` file is included in the repo as a template. `.env` is already
listed in `.gitignore` so your keys will not be committed. Scripts do not
auto-load `.env` — use a tool like [python-dotenv](https://pypi.org/project/python-dotenv/)
or source it manually:

```bash
export $(grep -v '^#' .env | xargs)
```

**Option B — export directly in your shell:**

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export CHAINAWARE_API_KEY="your-chainaware-key"
export ETHERSCAN_API_KEY="your-etherscan-key"   # optional
```

On Windows (PowerShell):

```powershell
$env:ANTHROPIC_API_KEY="sk-ant-..."
$env:CHAINAWARE_API_KEY="your-chainaware-key"
$env:ETHERSCAN_API_KEY="your-etherscan-key"     # optional
```

---

## Examples

### `python/agents/` — Agent-based examples

These scripts load a `.claude/agents/*.md` definition as the system prompt, keeping
tool instructions and output format in the agent file rather than in code.

#### Single wallet / hardcoded input

| Script | Agent | What it does |
|--------|-------|-------------|
| `fraud_detector.py` | `chainaware-fraud-detector.md` | Fraud probability + AML forensics on a wallet |
| `wallet_auditor.py` | `chainaware-wallet-auditor.md` | Full behavioral profile + personalized recommendations |
| `rug_pull_checker.py` | `chainaware-rug-pull-detector.md` | Rug pull risk on a smart contract or LP |
| `aml_scorer.py` | `chainaware-aml-scorer.md` | AML compliance score (0–100) with full forensic flag breakdown |
| `agent_screener.py` | `chainaware-agent-screener.md` | Trust score (0–10) for an AI agent — checks operational wallet + feeder wallet. Accepts optional `agent_type` and `feeder_type` (`wallet`/`contract`) to route fraud vs rug pull check. Requires `ETHERSCAN_API_KEY` for automatic contract detection. |
| `credit_scorer.py` | `chainaware-credit-scorer.md` | Crypto credit score (1–9) combining fraud probability and social graph analysis |
| `defi_advisor.py` | `chainaware-defi-advisor.md` | Personalized DeFi product recommendations calibrated to experience and risk appetite |

```bash
python python/agents/fraud_detector.py
python python/agents/wallet_auditor.py
python python/agents/rug_pull_checker.py
python python/agents/aml_scorer.py
python python/agents/agent_screener.py                                          # hardcoded defaults (both EOA wallets)
python python/agents/agent_screener.py 0xAGENT... 0xFEEDER... ETH              # both wallets (EOA)
python python/agents/agent_screener.py 0xAGENT... 0xCONTRACT... ETH wallet contract  # feeder is a contract
python python/agents/agent_screener.py 0xCONTRACT... 0xFEEDER... ETH contract  # agent is a contract
python python/agents/agent_screener.py 0xCONTRACT... 0xCONTRACT... ETH contract contract  # both contracts
python python/agents/credit_scorer.py
python python/agents/defi_advisor.py
```

#### Single wallet or CSV (auto-detected)

| Script | Agent | Input | What it does |
|--------|-------|-------|-------------|
| `compliance_screener.py` | `chainaware-compliance-screener.md` | sender + receiver + network | MiCA-aligned transaction compliance check with Travel Rule assessment. Accepts optional `receiver_type` (`wallet`/`contract`) to route fraud vs rug pull check on receiver. Requires `ETHERSCAN_API_KEY` for automatic contract detection. |
| `counterparty_screener.py` | `chainaware-counterparty-screener.md` | address + network | Pre-transaction go/no-go safety check (Safe / Caution / Block) |
| `onboarding_router.py` | `chainaware-onboarding-router.md` | address or CSV + network | Routes wallets to Beginner / Intermediate / Skip Onboarding flow |
| `platform_greeter.py` | `chainaware-platform-greeter.md` | address + network + platform | Personalised welcome message for a wallet connecting to a specific platform |
| `governance_screener.py` | `chainaware-governance-screener.md` | address or CSV + network | Sybil screening + voting weight multiplier for DAO governance |
| `lead_scorer.py` | `chainaware-lead-scorer.md` | address or CSV + network | Lead score (0–100) + tier (Hot/Warm/Cold/Dead) + outreach angle |
| `lending_risk_assessor.py` | `chainaware-lending-risk-assessor.md` | address or CSV + network | Borrower risk grade (A–F) + collateral ratio + interest rate tier |
| `marketing_director.py` | `chainaware-marketing-director.md` | address or CSV + network + platform description | Full marketing campaign brief — segments, hot leads, whales, message playbook |
| `reputation_scorer.py` | `chainaware-reputation-scorer.md` | address or CSV + network | Reputation score (0–4000) using the ChainAware formula: experience × risk × (1 - fraud) |
| `rwa_investor_screener.py` | `chainaware-rwa-investor-screener.md` | address or CSV + network | RWA investor suitability tier (QUALIFIED / CONDITIONAL / REFER_TO_KYC / DISQUALIFIED) + investment cap |
| `trust_scorer.py` | `chainaware-trust-scorer.md` | address or CSV + network | Trust score (0.00–1.00) = 1 - fraud_probability |
| `upsell_advisor.py` | `chainaware-upsell-advisor.md` | address or CSV + network + current product | Best next product, upgrade readiness score, conversion probability, trigger event |
| `wallet_marketer.py` | `chainaware-wallet-marketer.md` | address or CSV + network | Hyper-personalized 20-word marketing message derived from on-chain behavior |
| `wallet_ranker.py` | `chainaware-wallet-ranker.md` | address or CSV + network | Global wallet rank — experience, total points, wallet age, behavioral segments |
| `whale_detector.py` | `chainaware-whale-detector.md` | address or CSV + network | Whale tier (MEGA WHALE / WHALE / EMERGING WHALE / NOT A WHALE) + domain + status |

```bash
# single wallet
python python/agents/compliance_screener.py                                                    # hardcoded defaults
python python/agents/compliance_screener.py 0xSENDER... 0xRECEIVER... ETH '$500' transfer     # wallet-to-wallet
python python/agents/compliance_screener.py 0xSENDER... 0xCONTRACT... ETH '$2,500' swap contract  # swap into contract
python python/agents/counterparty_screener.py
python python/agents/onboarding_router.py 0xABC... ETH
python python/agents/platform_greeter.py 0xABC... ETH Aave
python python/agents/governance_screener.py 0xABC... ETH token-weighted
python python/agents/lead_scorer.py 0xABC... ETH "DeFi lending platform" acquisition
python python/agents/lending_risk_assessor.py 0xABC... ETH standard '$10,000' '6%'
python python/agents/marketing_director.py 0xABC... ETH "Your platform description"
python python/agents/reputation_scorer.py 0xABC... ETH
python python/agents/rwa_investor_screener.py 0xABC... ETH moderate
python python/agents/trust_scorer.py 0xABC... ETH
python python/agents/upsell_advisor.py 0xABC... ETH "basic DEX swap" revenue
python python/agents/wallet_marketer.py 0xABC... ETH
python python/agents/wallet_ranker.py 0xABC... ETH
python python/agents/whale_detector.py 0xABC... ETH

# CSV batch
python python/agents/onboarding_router.py wallets.csv ETH "A DeFi lending platform"
python python/agents/governance_screener.py wallets.csv ETH reputation-weighted 10000
python python/agents/lead_scorer.py wallets.csv ETH "DeFi lending platform" acquisition
python python/agents/lending_risk_assessor.py wallets.csv ETH conservative
python python/agents/marketing_director.py wallets.csv ETH "Your platform description" retention
python python/agents/reputation_scorer.py wallets.csv ETH
python python/agents/rwa_investor_screener.py wallets.csv ETH moderate '$50,000'
python python/agents/trust_scorer.py wallets.csv ETH
python python/agents/upsell_advisor.py wallets.csv ETH "basic DEX swap" retention
python python/agents/wallet_marketer.py wallets.csv ETH
python python/agents/wallet_ranker.py wallets.csv ETH
python python/agents/whale_detector.py wallets.csv ETH
```

#### Unique input patterns

| Script | Agent | Input | What it does |
|--------|-------|-------|-------------|
| `token_analyzer.py` | `chainaware-token-analyzer.md` | contract + network | Community rank + top holder profiles + holder quality assessment |
| `token_launch_auditor.py` | `chainaware-token-launch-auditor.md` | contract + deployer + network | Launch Safety Score + APPROVED/CONDITIONAL/REJECTED verdict + safety badge |
| `token_ranker.py` | `chainaware-token-ranker.md` | network + category | Top tokens ranked by holder community strength |
| `transaction_monitor.py` | `chainaware-transaction-monitor.md` | sender + receiver + network | Real-time risk signal: ALLOW / FLAG / HOLD / BLOCK |

```bash
python python/agents/token_analyzer.py 0xCONTRACT... ETH
python python/agents/token_analyzer.py 0xCONTRACT... ETH fraud        # also screen top holders
python python/agents/token_launch_auditor.py 0xCONTRACT... 0xDEPLOYER... ETH
python python/agents/token_ranker.py ETH "DeFi Token" 10
python python/agents/token_ranker.py SOLANA "AI Token" 5
python python/agents/transaction_monitor.py 0xSENDER... 0xRECEIVER... ETH
python python/agents/transaction_monitor.py 0xSENDER... 0xRECEIVER... ETH "" "2.5 ETH" swap
```

#### CSV batch only

| Script | Agent | Input | What it does |
|--------|-------|-------|-------------|
| `airdrop_screener.py` | `chainaware-airdrop-screener.md` | CSV + network | Filters bots/fraud, ranks eligible wallets by reputation for airdrop allocation |
| `cohort_analyzer.py` | `chainaware-cohort-analyzer.md` | CSV + network + goal | Segments wallets into behavioral cohorts with per-cohort engagement strategies |
| `ltv_estimator.py` | `chainaware-ltv-estimator.md` | CSV + network | Estimates 12-month revenue potential per wallet. Optional `platform_share` (default 0.15) and `fee_rate` (default 0.001) calibrate the estimate to your platform. |
| `sybil_detector.py` | `chainaware-sybil-detector.md` | CSV + network + proposal | Screens DAO voter list for Sybil attacks, classifies ELIGIBLE / REVIEW / EXCLUDE |
| `gamefi_screener.py` | `chainaware-gamefi-screener.md` | CSV + network | Detects bots/farm wallets, classifies players into tiers, calculates P2E reward eligibility |
| `portfolio_risk_advisor.py` | `chainaware-portfolio-risk-advisor.md` | CSV + risk_tolerance | Rug pull scan across all portfolio tokens, portfolio-weighted risk grade (A–F), rebalancing plan |
| `wallet_marketer_batch.py` | `chainaware-wallet-marketer.md` | CSV + network + output CSV | Generates a personalized 20-word marketing message per wallet and writes results to a CSV |

```bash
python python/agents/airdrop_screener.py wallets.csv ETH
python python/agents/cohort_analyzer.py wallets.csv ETH retention
python python/agents/ltv_estimator.py wallets.csv ETH                    # default platform_share=0.15, fee_rate=0.001
python python/agents/ltv_estimator.py wallets.csv ETH 0.30               # lending protocol (30% share)
python python/agents/ltv_estimator.py wallets.csv ETH 0.10 0.003         # DEX (10% share, 0.3% swap fee)
python python/agents/sybil_detector.py voters.csv ETH "Proposal #42"
python python/agents/gamefi_screener.py players.csv ETH "MyGame" 500
python python/agents/portfolio_risk_advisor.py portfolio.csv             # default: standard risk tolerance
python python/agents/portfolio_risk_advisor.py portfolio.csv conservative
python python/agents/wallet_marketer_batch.py wallets.csv ETH results.csv
python python/agents/wallet_marketer_batch.py wallets.csv ETH results.csv Aave
```

---

### `python/MCP/` — Direct MCP examples

These scripts call the ChainAware MCP tools directly via a user prompt.

| Script | Tool(s) | What it does |
|--------|---------|-------------|
| `fraud_detector.py` | `predictive_fraud` | Fraud probability + AML forensics on a wallet |
| `rug_pull_checker.py` | `predictive_rug_pull` | Rug pull risk on a smart contract or LP |
| `token_ranker.py` | `token_rank_list`, `token_rank_single` | Rank tokens by holder community strength |

```bash
python python/MCP/fraud_detector.py
python python/MCP/rug_pull_checker.py
python python/MCP/token_ranker.py
```

---

## Shared Helper

`python/chainaware.py` is imported by all scripts. It configures the Anthropic
client with the ChainAware MCP server and exposes:

- `run(prompt, system, model)` — calls Claude with MCP tools available
- `api_key()` — returns the ChainAware API key for injecting into prompts
- `is_contract(address, chain)` — async; detects contract vs EOA via Etherscan V2 API.
  Used by `agent_screener.py` and `compliance_screener.py` for automatic
  `agent_type` / `feeder_type` / `receiver_type` detection.
  Requires `ETHERSCAN_API_KEY`. Supported chains: ETH, BNB, BASE, POLYGON, ARB, HAQQ.

---

## Agent Definitions

`.claude/agents/` contains 32 ready-made agent definitions pulled from the
[behavioral-prediction-mcp](https://github.com/ChainAware/behavioral-prediction-mcp/tree/main/.claude/agents)
repo. To refresh them:

```bash
gh api repos/ChainAware/behavioral-prediction-mcp/contents/.claude/agents | python3 -c "
import json, sys, base64, subprocess
for f in json.load(sys.stdin):
    data = json.loads(subprocess.run(['gh', 'api', f['url']], capture_output=True, text=True).stdout)
    open(f'.claude/agents/{f[\"name\"]}', 'w').write(base64.b64decode(data['content']).decode())
    print('Updated', f['name'])
"
```

---

## Supported Networks

`ETH` · `BNB` · `POLYGON` · `BASE` · `TRON` · `TON` · `HAQQ` · `SOLANA`
