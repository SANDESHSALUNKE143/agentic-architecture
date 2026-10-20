# Agent scaffold

Generate the current runnable scaffold with `python -m agentic_sdk.developer init <new-folder> --name <agent-slug>`. It includes a working domain example, instructions, manifest, config, evaluation cases, package metadata and Dockerfile. The files in this assets directory illustrate repository layout; the generator is the executable scaffold source of truth.

Install the SDK first, install the generated consumer, then use validate/run/evaluate/serve commands described in docs/developer-guide.md in the platform repository. Do not copy the platform harness.


## Folder contents

Layout illustration; SDK init is the runnable generator.

- [capabilities/](capabilities/README.md): section guide
- [deployment/](deployment/README.md): section guide
- [domain/](domain/README.md): section guide
- [instructions/](instructions/README.md): section guide
- [tests/](tests/README.md): section guide
