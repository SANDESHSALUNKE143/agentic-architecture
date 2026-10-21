# Tests

Runnable unittest modules are kept directly in this folder so `python -m unittest discover -s tests -v` runs the complete SDK suite. contract, integration and compatibility subfolders are reading guides pointing to these tests, not duplicate suites. The retrieval check is [evaluation](evaluation/README.md). Full-stack acceptance lives in [deployment/scripts](../deployment/scripts/README.md) and requires the running local Docker deployment.


## Folder contents

Discoverable SDK unittest modules.

- [compatibility/](compatibility/README.md): Reading guide to public import and RAG compatibility tests.
- [contract/](contract/README.md): Reading guide to parent contract tests.
- [integration/](integration/README.md): Reading guide to optional and full-stack tests.
- [evaluation/](evaluation/README.md): Offline retrieval check. It is not a unit test module.
- [test_adapters.py](test_adapters.py): Provider contract tests with fakes; never contact external services.
- [test_config.py](test_config.py): Executable helper; consult the module and related tests.
- [test_core.py](test_core.py): Executable helper; consult the module and related tests.
- [test_developer.py](test_developer.py): Executable helper; consult the module and related tests.
- [test_execution.py](test_execution.py): Executable helper; consult the module and related tests.
- [test_http_transport.py](test_http_transport.py): Executable helper; consult the module and related tests.
- [test_integrations.py](test_integrations.py): Executable helper; consult the module and related tests.
- [test_layout.py](test_layout.py): The old API and architectural imports must resolve to the same implementation.
- [test_optional.py](test_optional.py): In-process integrations with real optional libraries; no paid/network calls.
