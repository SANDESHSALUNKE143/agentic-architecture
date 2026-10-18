import json
from pathlib import Path

from jsonschema import Draft202012Validator

for schema_path, config_paths in [
    ("schemas/agent-config.schema.json", ["config/local.json"]),
    (
        "schemas/project-v2.schema.json",
        ["config/agentn-demo.json", "config/agentn-azure.example.json"],
    ),
]:
    schema = json.loads(Path(schema_path).read_text())
    Draft202012Validator.check_schema(schema)
    for config in config_paths:
        Draft202012Validator(schema).validate(json.loads(Path(config).read_text()))
        print("Valid:", config)
