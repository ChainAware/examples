# ChainAware Examples — Claude Code Instructions

## Project Structure

```
python/MCP/        Direct MCP examples (call tools via user prompt)
python/agents/     Agent-based examples (load .md as system prompt)
.claude/agents/    32 agent definitions pulled from behavioral-prediction-mcp repo
```

## Shared Helper

All scripts import `chainaware` from `python/MCP/chainaware.py`.
Scripts in `python/agents/` must add this to their `sys.path`:

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "MCP"))
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
python python/agents/fraud_detector.py
python python/agents/wallet_auditor.py
python python/agents/rug_pull_checker.py

python python/MCP/fraud_detector.py
python python/MCP/rug_pull_checker.py
python python/MCP/token_ranker.py
```

## Environment Variables

```bash
export ANTHROPIC_API_KEY="..."
export CHAINAWARE_API_KEY="..."
```

Never pass `API Key` in the user message — the key is already embedded in the
MCP server URL inside `chainaware.py`.
