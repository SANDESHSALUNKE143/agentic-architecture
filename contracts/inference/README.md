# Inference contracts

`Predictor.predict` runs one operator-registered model. The agent supplies a model id and a feature object. Training stays outside the SDK.

## Current status

The port is implemented by the registry adapter in adapters/inference.

## Where to work

[Canonical types](types.py).

[Parent section](../README.md) · [Reading order](../../00-START-HERE.md)

## Folder contents

- [types.py](types.py): Registered-model prediction port.
