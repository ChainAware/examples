# ChainAware Python Examples

Python examples for the ChainAware Behavioural Prediction MCP — 32 AI agents grouped by use case.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-anthropic-key"
export CHAINAWARE_API_KEY="your-chainaware-key"
```

Get a ChainAware API key at https://chainaware.ai/pricing

## MCP Server

All examples connect to:
```
https://prediction.mcp.chainaware.ai/sse
```

Register it once in Claude Code CLI:
```bash
claude mcp add --transport sse chainaware-behavioral-prediction \
  https://prediction.mcp.chainaware.ai/sse \
  --header "X-API-Key: $CHAINAWARE_API_KEY"
```

## Use Case Groups

| Folder | Agents | What it does |
|--------|--------|--------------|
| `01_security/` | fraud-detector, rug-pull-detector, aml-scorer, compliance-screener, counterparty-screener, transaction-monitor | Detect fraud, rug pulls, AML violations |
| `02_wallet_intelligence/` | wallet-auditor, credit-scorer, trust-scorer, reputation-scorer, wallet-ranker, whale-detector, ltv-estimator | Deep wallet profiling and scoring |
| `03_defi_lending/` | defi-advisor, lending-risk-assessor, portfolio-risk-advisor | DeFi product recommendations and lending risk |
| `04_token/` | token-ranker, token-analyzer, token-launch-auditor | Token ranking and launch safety audits |
| `05_marketing/` | lead-scorer, cohort-analyzer, wallet-marketer, upsell-advisor, platform-greeter, marketing-director | Growth, personalization, campaigns |
| `06_onboarding/` | onboarding-router | Route wallets to the right onboarding flow |
| `07_governance/` | governance-screener, sybil-detector | DAO voter screening and Sybil detection |
| `08_specialized/` | airdrop-screener, gamefi-screener, rwa-investor-screener, agent-screener | Specialized vertical use cases |

## Underlying MCP Tools

All agents are built on top of 6 core tools:

- `predictive_fraud` — Fraud probability + AML forensics (~98% accuracy)
- `predictive_behaviour` — Next-action prediction, risk profile, DeFi intentions
- `predictive_rug_pull` — Rug-pull risk for contracts and liquidity pools
- `credit_score` — Crypto credit/trust score (1–9) for lending
- `token_rank_list` — Ranked list of tokens by holder community strength
- `token_rank_single` — Single token rank + top holders
