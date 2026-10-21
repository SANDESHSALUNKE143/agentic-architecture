from agentic_sdk.adapters.local import EchoLLM, HashEmbedder, MemoryStore, SafeTelemetry
from agentic_sdk.contracts import LLM, Context, Document

from agentic_sdk.config import load
from agentic_sdk.registry import Registry
from agentic_sdk.runtime import Agent, Budget


def main():
    cfg = load("deployment/config/local.json")
    registry = Registry[LLM]()
    registry.register("echo", EchoLLM)
    embedder = HashEmbedder()
    telemetry = SafeTelemetry()
    agent = Agent(
        registry.create(cfg.llm_adapter),
        embedder,
        MemoryStore(embedder.profile),
        telemetry,
        Budget(cfg.token_budget),
        cfg.max_output_tokens,
    )
    ctx = Context(
        cfg.tenant_id,
        cfg.agent_id,
        frozenset({"agent:invoke", "knowledge:read", "knowledge:write"}),
    )
    agent.ingest(
        ctx,
        Document("sdk-guide", "Agents reuse a versioned SDK with ports and adapters."),
    )
    answer = agent.ask(ctx, "How do agents reuse code?")
    print(answer.text)
    print("Sources:", answer.sources)
    print("Content-free telemetry:", telemetry.events)


if __name__ == "__main__":
    main()
