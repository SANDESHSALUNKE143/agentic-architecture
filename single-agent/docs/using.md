# Using the single agent

From `single-agent/`:

```bash
./start-local.sh
```

| Process | Address |
| --- | --- |
| API | http://127.0.0.1:8092 |
| Merchant | http://127.0.0.1:8093/mcp |
| Console | http://127.0.0.1:5174 |

Send `Authorization: Bearer local-dev-token-not-for-production`.

`harness: langchain` in `agentic/04-loops/specialists/desk-agent/agent.yaml` needs no key. `PLATFORM_LLM_MODE=live` and `MODEL_API_KEY` make that same adapter call `ChatOpenAI`.

Set `harness: claude` only when `ANTHROPIC_API_KEY` is set. Set `harness: deepagent` for a shadow run, and install the `deep` extra. Without the key for that adapter, the run fails and does not fall back to the mock.

```bash
python -m unittest tests.unit.test_harness tests.integration.test_api tests.security.test_security
```
