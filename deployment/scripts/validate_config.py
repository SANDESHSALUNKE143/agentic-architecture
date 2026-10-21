import json
from pathlib import Path

from jsonschema import Draft202012Validator

root = Path(__file__).resolve().parents[2]
for schema_path, config_paths in [
    (
        root / "deployment/schemas/agent-config.schema.json",
        [root / "deployment/config/local.json"],
    ),
    (
        root / "deployment/schemas/project-v2.schema.json",
        [
            root / "deployment/config/agentn-demo.json",
            root / "deployment/config/agentn-azure.example.json",
        ],
    ),
]:
    schema = json.loads(Path(schema_path).read_text())
    Draft202012Validator.check_schema(schema)
    for config in config_paths:
        Draft202012Validator(schema).validate(json.loads(Path(config).read_text()))
        print("Valid:", config)
