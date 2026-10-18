# 02. Core runtime

The central harness and execution policies reused by every consumer agent.

**Status:** Implemented bounded execution; distributed policies are planned.

## Implementation

[Canonical source / guide](harness/runner.py). Python in this section is installed under the agentic_sdk package namespace. These folders now contain the canonical implementation, packaged under agentic_sdk.

## Read in order

1. [Central harness](harness/README.md)
2. [Execution context](context/README.md)
3. [Execution lifecycle](execution/README.md)
4. [Execution policies](policies/README.md)

## Change rule

Change the linked implementation and its behavior tests together. Record contract changes and distinguish implemented code from planned services. Agent-specific rules belong in consumer repositories.

[Back to the platform reading order](../00-START-HERE.md).


## Folder contents

Reusable framework-neutral behavior.

- [context/](context/README.md): Trusted execution identity and permission guard.
- [execution/](execution/README.md): Registered tool schemas, permissions, prerequisites and approval checks.
- [harness/](harness/README.md): Async model/tool runner and synchronous RAG example use case.
- [policies/](policies/README.md): Validated request-level limits.
