"""
Process entrypoint for the insight agent.

Builds the runner once the databases accept connections, then serves the
token-protected API on port 8010 and the product page on port 8030.

Run: python -m insight_agent
"""

from insight_agent.host.server import serve
from insight_agent.runtime import build


def main() -> None:
    """
    Start the agent.

    Steps:
        1. build() opens the connections and registers the tools.
        2. serve() listens until the process stops.
    """
    runner, context, observer, tools, allowlists, bindings, sql, models, web = build()
    serve(runner, context, observer, tools, allowlists, bindings, sql, models, web)


if __name__ == "__main__":
    main()
