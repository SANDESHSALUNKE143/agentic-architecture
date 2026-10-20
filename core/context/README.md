# Execution context

[identity.py](identity.py) implements Context: immutable tenant identity, agent identity and permission grants. `require()` denies missing identity or permission before an operation runs. Identity must be supplied by trusted composition, never inferred from model output.

Import `Context` from `agentic_sdk.core.context.identity` or the stable `agentic_sdk.contracts` API. Both reference this implementation. Validated by scope/permission tests in the SDK and AgentN suites.


## Folder contents

Trusted execution identity and permission guard.

- [identity.py](identity.py): Trusted identity and permission checks shared by every execution path.
- [credentials.py](credentials.py): Revocable scoped credentials that sit beside the static bearer.
