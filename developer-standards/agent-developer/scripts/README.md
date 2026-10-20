# Scripts

validate-agent.py checks the developer manifest and SDK pin; validate-config.py applies the installed runtime schema; check-contracts.py runs the SDK behavior suite. Scripts do not invoke live services.

Read the parent guide for context. This directory does not independently start a service.


## Folder contents

Explicit-path manifest/config/contract validators.

- [check-contracts.py](check-contracts.py): Run the platform behavior suite from an explicit trusted checkout.
- [validate-agent.py](validate-agent.py): Validate the supplied JSON-subset YAML engineering manifest, without executing it.
- [validate-config.py](validate-config.py): Validate a v2 runtime configuration using the installed SDK contract.
