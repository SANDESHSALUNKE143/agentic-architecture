# Deployment

Use the [full local platform](full/README.md) for the complete local service path. The [AgentN-only path](local/README.md) remains a smaller alternative; do not run both on port 8010. See [release gates](../doc/release-gates.md) before remote or production deployment.


## Folder contents

Supported local profiles and operating runbooks.

- [full/](full/README.md): Ten-container local platform and monitoring profile.
- [local/](local/README.md): Smaller AgentN-only profile; shares port 8010 with full profile.
- [earlier/](earlier/README.md): Earlier Grafana, Helm, collector, and schema drafts.
- [config/](config/README.md): Example settings. No real secrets.
- [schemas/](schemas/README.md): The JSON contracts for those settings.
- [scripts/](scripts/README.md): Repository checks and the local start scripts.
