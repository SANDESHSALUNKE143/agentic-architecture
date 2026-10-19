# Operator UI

Loopback screens for the agents a credential can see, immutable configuration revisions, registered connector allowlists, and content-free run events.

## Current status

Served by create_app in app.py. The bearer token is accepted only in the Authorization header. A published revision does not reload a running agent.

## Where to work

[Application](app.py).

[Parent section](../README.md) · [Deployment](../../deployment/README.md)

## Folder contents

- [app.py](app.py): Operator page and credential-scoped JSON routes.
