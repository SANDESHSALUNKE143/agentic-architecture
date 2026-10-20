# Documentation guide

Read current implementation guides first:

1. [How to use the SDK](how-to-use.md): what an agent imports, and what stays in the agent.
2. [Architecture](architecture.md): components, ownership and trust boundaries.
3. [Source layout](source-layout.md) and [folder index](folder-index.md): where every maintained folder belongs.
4. [Developer guide](developer-guide.md): create, configure, test and host a consumer.
5. [Contracts](contracts.md) and [implementation map](implementation-map.md): APIs and code.
6. [Full local runbook](../deployment/full/README.md): start, test, credentials and shutdown.
7. [Verification](verification.md), [security](security.md) and [release gates](release-gates.md): evidence and limits.

Supporting guides: reusable-architecture.md, new-project.md and agentn-integration.md explain the consuming-agent boundary. deployment.md, nfr-cost.md, observability.md and roadmap.md retain broader phase-one design proposals; their status banners distinguish design from shipped behavior. v0.1-baseline.md is historical. sources.md records source references, not a claim of live provider certification.

[ADRs](adr/README.md) retain decisions and their evolution. Do not edit an old decision to imply that a previously planned component already existed; add a superseding decision or implementation note.


## Folder contents

Current implementation guides, references and historical baseline.

- [adr/](adr/README.md): Numbered architecture decisions with unique IDs.
