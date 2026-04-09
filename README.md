# ChainAware Examples

Python examples showing how to use the [ChainAware Behavioral Prediction MCP](https://github.com/ChainAware/behavioral-prediction-mcp) with Claude.

---

## Prerequisites

```bash
pip install anthropic
```

```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export CHAINAWARE_API_KEY="your-chainaware-key"
```

Get a ChainAware API key at [chainaware.ai/pricing](https://chainaware.ai/pricing).

---

## Examples

### `python/agents/` — Agent-based examples

These scripts load a `.claude/agents/*.md` definition as the system prompt, keeping
tool instructions and output format in the agent file rather than in code.

| Script | Agent | What it does |
|--------|-------|-------------|
| `fraud_detector.py` | `chainaware-fraud-detector.md` | Fraud probability + AML forensics on a wallet |
| `wallet_auditor.py` | `chainaware-wallet-auditor.md` | Full behavioral profile + personalized recommendations |
| `rug_pull_checker.py` | `chainaware-rug-pull-detector.md` | Rug pull risk on a smart contract or LP |

```bash
python python/agents/fraud_detector.py
python python/agents/wallet_auditor.py
python python/agents/rug_pull_checker.py
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

`python/MCP/chainaware.py` is imported by all scripts. It configures the Anthropic
client with the ChainAware MCP server and exposes a single `run(prompt, system, model)`
function.

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
