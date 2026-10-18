"""Validate the supplied JSON-subset YAML engineering manifest, without executing it."""

import ast
import json
import sys
import tomllib
from pathlib import Path


def main():
    root = Path(sys.argv[1]).resolve()
    raw = json.loads((root / "agent.yaml").read_text(encoding="utf-8"))
    expected = {
        "manifest_version",
        "name",
        "sdk",
        "entrypoint",
        "runtime_config",
        "instruction_reference",
        "capabilities",
        "required_before_final",
        "mode",
    }
    if set(raw) != expected or raw["manifest_version"] != 1:
        raise ValueError("unknown or missing manifest fields")
    if raw["sdk"] != {"distribution": "agentic-foundation-sdk", "version": "0.3.0"}:
        raise ValueError("unsupported SDK declaration")
    if (
        not isinstance(raw["capabilities"], list)
        or not raw["capabilities"]
        or not all(isinstance(x, str) for x in raw["capabilities"])
    ):
        raise ValueError("capabilities must be nonempty strings")
    if len(set(raw["capabilities"])) != len(raw["capabilities"]) or not set(
        raw["required_before_final"]
    ) <= set(raw["capabilities"]):
        raise ValueError("invalid capability/prerequisite list")
    if raw["mode"] != "read-only":
        raise ValueError("this baseline validates read-only agents only")
    for name in ("runtime_config", "instruction_reference"):
        path = (root / raw[name]).resolve()
        if root not in path.parents or not path.is_file():
            raise ValueError("manifest file outside repository or missing: " + name)
    config = json.loads((root / raw["runtime_config"]).read_text())
    if config.get("agent_id") != raw["name"]:
        raise ValueError("manifest and runtime agent IDs differ")
    project = tomllib.loads((root / "pyproject.toml").read_text())
    if not any(
        d.startswith("agentic-foundation-sdk") and "==0.3.0" in d
        for d in project["project"]["dependencies"]
    ):
        raise ValueError("consumer must pin the versioned SDK")
    module, sep, attribute = raw["entrypoint"].partition(":")
    if (
        not sep
        or not all(p.isidentifier() for p in module.split("."))
        or not attribute.isidentifier()
    ):
        raise ValueError("invalid entrypoint")
    source = root / "src" / Path(*module.split(".")).with_suffix(".py")
    parsed = ast.parse(source.read_text())
    if not any(
        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == attribute
        for n in parsed.body
    ):
        raise ValueError("entrypoint function not found")
    instruction = None
    for node in parsed.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "INSTRUCTION" for t in node.targets
        ):
            instruction = ast.literal_eval(node.value)
    if (
        instruction is not None
        and instruction.strip() != (root / raw["instruction_reference"]).read_text().strip()
    ):
        raise ValueError("instruction reference differs from runtime constant")
    forbidden = root / "src" / "agentic_sdk"
    if forbidden.exists():
        raise ValueError("consumer contains copied SDK package")
    print("Agent manifest, SDK pin, entrypoint and instruction reference are valid.")


if __name__ == "__main__":
    main()
