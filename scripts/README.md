# Scripts

Repository-level validation tools. validate_config.py checks supplied configuration fixtures against JSON Schemas.

[Platform reading order](../00-START-HERE.md).


## Folder contents

Validation, full-stack acceptance and local lifecycle helpers.

- [check_repository.py](check_repository.py): Check maintained-folder documentation, public API docs and local package/link integrity.
- [test_full_internals.py](test_full_internals.py): Run inside the platform container to verify telemetry and atomic reservations.
- [test_full_platform.py](test_full_platform.py): Acceptance test against the local Docker stack; never prints credentials or content.
- [validate_config.py](validate_config.py): Executable helper; consult the module and related tests.
