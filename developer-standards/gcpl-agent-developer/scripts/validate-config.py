"""Validate a v2 runtime configuration using the installed SDK contract."""

import sys

from agentic_sdk.project import ProjectConfig

if __name__ == "__main__":
    config = ProjectConfig.load(sys.argv[1])
    print("Runtime configuration valid:", config.agent_id)
