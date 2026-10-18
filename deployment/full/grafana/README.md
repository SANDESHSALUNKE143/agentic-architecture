# Grafana

Grafana provisioning mounted by the full local Compose profile. Datasources configure internal backend URLs and dashboard providers load dashboard JSON. Admin credentials come from the ignored local environment file, never these YAML files.


## Folder contents

Datasource and dashboard-provider provisioning.

- [dashboards/](dashboards/README.md): Provider configuration selecting mounted dashboard JSON.
- [datasources/](datasources/README.md): Stable Grafana datasource names/UIDs.
