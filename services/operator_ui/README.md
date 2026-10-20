# Operator UI

Generic console for whatever agents `OPERATOR_AGENTS` lists. Each binding supplies that agent's `url`. Agent configuration stays on that agent's own settings screen. The Guide page shows a sample agent that imports the SDK.

## Current status

Served by create_app in app.py. The bearer token is accepted only in the Authorization header. A published revision does not reload a running agent.

## Where to work

[Application](app.py).

[Parent section](../README.md) · [Deployment](../../deployment/README.md)

## Folder contents

- [app.py](app.py): Operator page and credential-scoped JSON routes.
