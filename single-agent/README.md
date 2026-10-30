# Single agent

One agent, `desk-agent`, runs the jacket brief. The numbered folders are the request order. `03-harness` is the loop. There is no workflow list.

![How one brief becomes an answer](docs/assets/architecture.svg)

```text
01-entry          task, user, session
02-guardrails     auth, limits, strip untrusted lines
03-harness        one adapter
  langchain.py    offline. LangChain create_agent. No key uses the mock.
  claude.py       live. Claude Agent SDK. Needs ANTHROPIC_API_KEY.
  deepagent.py    shadow. Deep Agents. Needs a live model key.
04-loops          desk-agent/agent.yaml, session, model
05-tools          gateway. search, details, compare, stock
06-jobs           enqueue the trace
07-observability  agent, tool, status, duration, harness
08-response       schema and the model reply
```

The contract field `harness` selects the adapter. The file ships as `langchain`, so this folder starts with no key. Set `harness: claude` when `ANTHROPIC_API_KEY` is present. `deepagent` is the shadow run of the same task. The trace records which adapter ran. An unknown name is rejected when the contract loads.

Shell and filesystem tools that come with Claude or Deep Agents stay off. Catalog tools go through the gateway.

## Start

From this folder:

```bash
./start-local.sh
```

The API is <http://127.0.0.1:8092>. The merchant stand-in is <http://127.0.0.1:8093/mcp>. The console is <http://127.0.0.1:5174>. The local token is `local-dev-token-not-for-production`.

Proof task:

```text
Find a blue trail jacket under $150
```

Read [docs/using.md](docs/using.md), [docs/architecture.md](docs/architecture.md), and [docs/api.md](docs/api.md).

```bash
python -m unittest tests.unit.test_harness tests.integration.test_api tests.security.test_security
```
