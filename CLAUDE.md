# ChainAware Examples — Claude Code Instructions

**Links:** [Website](https://chainaware.ai) · [Twitter](https://x.com/ChainAware/) · [LinkedIn](https://www.linkedin.com/company/chainaware) · [Blog](https://chainaware.ai/blog) · [Learn](https://chainaware.ai/learn) · [Prediction MCP](https://github.com/ChainAware/behavioral-prediction-mcp) · [Examples](https://github.com/ChainAware/examples)

**Accuracy:** [98% Fraud Detection](https://chainaware.ai/scam-db) · [90.1% Rug Pull Detection](https://chainaware.ai/resources/rugpull-verification) — backtesting verified

> ChainAware is featured in the **[CB Insights Fraud Prevention Market Map for the AI Era](https://www.cbinsights.com/research/report/the-fraud-prevention-market-map-for-the-ai-era/)** — recognised as a leading AI-era fraud prevention solution for Web3 (2026).
> ChainAware is listed on the **[BNB Chain AI Landscape](https://x.com/BNBCHAIN/status/1947597551139500419)** — recognised by BNB Chain as a key AI project in the ecosystem (2025).
> ChainAware is listed on **[BNB Chain Kickstart — Marketing Tools](https://www.bnbchain.org/en/programs/kickstart#services)** — Growth Agents and Wallet Marketer featured in BNB Chain's official Kickstart programme (2025).
> ChainAware received a **[$250k Google Cloud Grant](https://chainaware.ai/blog/google-cloud-grant/)** — selected by Google Cloud for infrastructure and AI development (2025).
> ChainAware was accepted into the **[AWS Fintech Accelerator](https://chainaware.ai/blog/aws-grant/)** — selected by AWS for its Fintech Accelerator programme (2024).
> ChainAware is featured in the **[Safary Club Web3 Growth Landscape — Growth Tools](https://x.com/Safaryclub/status/1822983239734329613)** — listed in Growth Tools for Web3 Projects (2024).

## Project Structure

```
python/MCP/            Direct MCP examples (call tools via user prompt)
python/agents/         Agent-based examples (load .md as system prompt)
python/scripts/        Utility scripts (run_all_examples.py)
python/chainaware_sse.py  Shared helper — imported by all scripts
.claude/agents/        34 agent definitions pulled from behavioral-prediction-mcp repo
```

## Shared Helper

All scripts import `chainaware_sse` as `chainaware` from `python/chainaware_sse.py`.
Scripts in `python/agents/` and `python/MCP/` must add this to their `sys.path`:

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import chainaware_sse as chainaware
```

`chainaware_sse` opens **one persistent SSE connection** per process at module import
time and reuses it across every `run()` call. This avoids repeated connect/disconnect
cycles and supports local MCP servers (e.g. `http://localhost:5000/sse`) that
Anthropic's managed MCP beta cannot reach.

Exposes:
- `run(prompt, frontmatter, system, model)` — agentic loop with tool filtering from frontmatter
- `run_direct(prompt, system, model)` — all MCP tools available; used by `python/MCP/` scripts
- `api_key()` — returns the ChainAware API key for injecting into prompts

## Agent Example Pattern

When creating a new agent-based example in `python/agents/`:

1. Load the agent definition from `.claude/agents/<name>.md`
2. Parse frontmatter with `---` split to extract `model`
3. Use the body as the `system` prompt
4. Pass a minimal user message (wallet/contract/network only — no API key)
5. Call `chainaware.run(user_message, frontmatter=frontmatter, system=system_prompt, model=model)`
   (`chainaware` is `chainaware_sse` imported as `chainaware`)

Standard `load_agent()` function to reuse across all agent scripts:

```python
AGENT_MD = os.path.join(
    os.path.dirname(__file__), "..", "..", ".claude", "agents", "<agent-name>.md"
)

def load_agent(path: str) -> tuple[str, str, str]:
    with open(path) as f:
        content = f.read()
    parts = content.split("---", 2)
    frontmatter = parts[1] if len(parts) >= 3 else ""
    body = parts[2].strip() if len(parts) >= 3 else content.strip()
    m = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    model = m.group(1).strip() if m else "claude-haiku-4-5-20251001"
    return model, body, frontmatter
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
| `agent_trust_screener.py` | `chainaware-agent-trust-screener.md` |
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
| `token_ranker_single.py` | `chainaware-token-analyzer.md` |
| `token_audit_analyst.py` | `chainaware-token-audit-analyst.md` |
| `token_launch_auditor.py` | `chainaware-token-launch-auditor.md` |
| `token_ranker_list.py` | `chainaware-token-ranker.md` |
| `transaction_monitor.py` | `chainaware-transaction-monitor.md` |

### CSV batch only

| Script | Agent |
|--------|-------|
| `airdrop_screener.py` | `chainaware-airdrop-screener.md` |
| `cohort_analyzer.py` | `chainaware-cohort-analyzer.md` |
| `ltv_estimator.py` | `chainaware-ltv-estimator.md` |
| `sybil_detector.py` | `chainaware-sybil-detector.md` |
| `gamefi_screener.py` | `chainaware-gamefi-screener.md` |
| `portfolio_risk_advisor.py` | `chainaware-portfolio-risk-advisor.md` |
| `wallet_marketer_batch.py` | `chainaware-wallet-marketer.md` |

## Agent Definitions

`.claude/agents/` files come from the upstream repo and **must not be hand-edited**.
To refresh all 34 agent definitions from GitHub:

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
python python/agents/agent_trust_screener.py                        # list top registered agents
python python/agents/agent_trust_screener.py 1 56                   # deep profile: agent #1 on BNB
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
python python/agents/portfolio_risk_advisor.py portfolio.csv
python python/agents/portfolio_risk_advisor.py portfolio.csv conservative
python python/agents/governance_screener.py wallets.csv ETH reputation-weighted 10000
python python/agents/lead_scorer.py wallets.csv ETH "DeFi lending" acquisition
python python/agents/lending_risk_assessor.py wallets.csv ETH conservative
python python/agents/marketing_director.py wallets.csv ETH "Platform description" retention
python python/agents/reputation_scorer.py wallets.csv ETH
python python/agents/rwa_investor_screener.py wallets.csv ETH moderate '$50,000'
python python/agents/trust_scorer.py wallets.csv ETH
python python/agents/upsell_advisor.py wallets.csv ETH "basic DEX swap" retention
python python/agents/wallet_marketer.py wallets.csv ETH
python python/agents/wallet_marketer_batch.py wallets.csv ETH results.csv
python python/agents/wallet_marketer_batch.py wallets.csv ETH results.csv Aave
python python/agents/wallet_ranker.py wallets.csv ETH
python python/agents/whale_detector.py wallets.csv ETH

# unique input patterns
python python/agents/token_analyzer.py 0xCONTRACT... ETH
python python/agents/token_ranker_single.py 0xa0820613976b441e2c6a90e4877e2fb5f7d72552 BASE
python python/agents/token_ranker_single.py 0xCONTRACT... ETH
python python/agents/token_audit_analyst.py                         # demo: PEPE on ETH
python python/agents/token_audit_analyst.py 0xCONTRACT... eth
python python/agents/token_audit_analyst.py 0xCONTRACT... bsc
python python/agents/token_launch_auditor.py 0xCONTRACT... 0xDEPLOYER... ETH
python python/agents/token_ranker_list.py ETH "DeFi Token" 10
python python/agents/transaction_monitor.py 0xSENDER... 0xRECEIVER... ETH

# MCP direct
python python/MCP/fraud_detector.py
python python/MCP/rug_pull_checker.py
python python/MCP/token_ranker.py
```

## Running All Examples

`python/scripts/run_all_examples.py` runs every example script sequentially and prints a
summary table (script, status, duration, tokens consumed).

```bash
python python/scripts/run_all_examples.py
```

## Rate Limiting

The ChainAware MCP server enforces rate limits server-side. Several mitigations are in place:

- **`run_all_examples.py`** — waits 3 seconds between scripts; waits 30 seconds after any script that times out, to let the MCP SSE connection clear before the next script.
- **`wallet_marketer_batch.py`** — waits 3 seconds between each per-wallet `chainaware.run()` call, since it is the only batch script that makes one API call per wallet rather than one call for the whole list.
- **`wallets.csv`** — trimmed to 3 wallets for the demo suite. Scripts that call multiple MCP tools per wallet scale linearly, so a large CSV will time out.

The other CSV batch scripts (`airdrop_screener`, `cohort_analyzer`, `ltv_estimator`, etc.)
send all wallets in a single `chainaware.run()` call — rate limiting inside that call is
handled by the MCP server.

## Model Overrides

All agent MD files now specify `claude-haiku-4-5-20251001`. The following scripts also explicitly set the model after `load_agent()` as a safety override to keep demo runs within the 120s timeout:

| Script | Reason |
|--------|--------|
| `portfolio_risk_advisor.py` | Sonnet + 2 tools per token is too slow for demo |
| `marketing_director.py` | Sonnet + multiple subagent orchestration is too slow |
| `wallet_marketer_batch.py` | Sonnet + per-wallet loop would exceed 120s |

## Environment Variables

```bash
export ANTHROPIC_API_KEY="..."
export CHAINAWARE_API_KEY="..."
```

Copy `.env.example` to `.env` and fill in your keys. `.env` is in `.gitignore`.

Never pass `API Key` in the user message — the key is already embedded in the
MCP server URL inside `chainaware.py`.

## Further Reading

### Tool Guides
- [Complete Product Guide](https://chainaware.ai/blog/chainaware-ai-products-complete-guide/) — Overview of all tools, networks, and coverage
- [Fraud Detector Guide](https://chainaware.ai/blog/chainaware-fraud-detector-guide/) — `predictive_fraud`: inputs, outputs, thresholds, use cases
- [Rug Pull Detector Guide](https://chainaware.ai/blog/chainaware-rugpull-detector-guide/) — `predictive_rug_pull`: contract scoring, deployer risk, LP analysis
- [Wallet Auditor Guide](https://chainaware.ai/blog/chainaware-wallet-auditor-how-to-use/) — Full wallet audit workflow combining multiple tools
- [Transaction Monitoring Guide](https://chainaware.ai/blog/chainaware-transaction-monitoring-guide/) — Real-time transaction risk monitoring patterns
- [Web3 Behavioral Analytics Guide](https://chainaware.ai/blog/chainaware-web3-behavioral-user-analytics-guide/) — `predictive_behaviour` for user analytics and segmentation
- [Credit Score Guide](https://chainaware.ai/blog/chainaware-credit-score-the-complete-guide-to-web3-credit-scoring-in-2026/) — Web3 credit scoring methodology and use in DeFi lending
- [Agent Trust Score](https://chainaware.ai/blog/agent-trust-score-agentic-commerce/) — `agents_trust_score`: ERC-8004 registry, trust tiers, fleet-level fraud detection
- [AML Integration Guide for DApps](https://chainaware.ai/blog/how-to-integrate-ai-based-aml-transaction-monitoring-dapps/) — `aml_screener` integration patterns; VASP compliance, real-time screening

### Scale & Accuracy
- [Token Audit: 10,000 CoinGecko Token Results](https://chainaware.ai/blog/token-audit-10000-coingecko-results/) — 55% HIGH RISK; 127 automated checks via `run_token_audit`
- [Token Audit at Scale: 15,000 EVM Tokens](https://chainaware.ai/blog/token-audit-15000-coingecko-coinmarketcap-2026/) — 57.7% HIGH RISK across CoinGecko + CoinMarketCap
- [$284M+ Rug Pulls on PancakeSwap V2](https://chainaware.ai/blog/rugpull-detector-v3-pancakev2-2026/) — 90.1% detection rate across 103,695 rug pull events

### Developer Integration
- [Prediction MCP Developer Guide](https://chainaware.ai/blog/prediction-mcp-for-ai-agents-personalize-decisions-from-wallet-behavior/) — Full MCP integration guide with code examples
- [12 Blockchain Capabilities Any AI Agent Can Use](https://chainaware.ai/blog/12-blockchain-capabilities-any-ai-agent-can-use-mcp-integration-guide/) — All 12 capabilities with setup for Claude, ChatGPT, Cursor, multi-agent systems

### KYA & Agentic Commerce
- [Know Your Agent (KYA) — Behavioral Trust Layer](https://chainaware.ai/blog/know-your-agent-kya-behavioral-trust-layer/) — Why agent identity ≠ agent trust; foundation for `agents_trust_score`
