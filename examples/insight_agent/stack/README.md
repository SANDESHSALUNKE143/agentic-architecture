# Insight stack

Containers for the insight agent. The agent code stays in the parent folder. This folder holds the compose file, the images, and the sample data.

Run from this directory:

```sh
docker compose --env-file .env.example up --build
```

The SDK is copied in as an extra build context (`../../..`). The agent image installs that checkout. The operator image runs `agentic_sdk.services.operator_ui` and calls the agent over HTTP. The agent process does not import the operator.

## Folder contents

- [fixtures/](fixtures/README.md): The sample metrics table.
- [site/](site/README.md): The allowlisted public page.
- [ui/](ui/README.md): The operator console image.
- [observability/](observability/README.md): The collector config for this stack.
