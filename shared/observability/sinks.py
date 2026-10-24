"""Observability tools a contract may select.

Purpose: platform trace and evaluation record in this process. OpenTelemetry, a log store, and Grafana are marked configured when an address is set.
Used by: settings and plugins routes, and by the agent YAML loader.
"""

from __future__ import annotations

import os

SINKS: list[dict[str, str]] = [
    {
        "id": "platform_trace",
        "title": "Platform trace",
        "summary": "Records the agent, the tool name, and the status in this process. The raw question is not stored.",
        "variable": "",
        "detail_local": "Recording in this API process.",
        "detail_live": "Recording in this API process.",
    },
    {
        "id": "evaluation",
        "title": "Evaluation",
        "summary": "Records status, tool names, and duration. It does not change model weights.",
        "variable": "",
        "detail_local": "Recording in this API process.",
        "detail_live": "Recording in this API process.",
    },
    {
        "id": "otlp",
        "title": "OpenTelemetry",
        "summary": "An OTLP collector for traces. This build keeps the record here and does not send the raw question.",
        "variable": "OTEL_EXPORTER_OTLP_ENDPOINT",
        "detail_local": "Using the in-process trace until an OTLP endpoint is set.",
        "detail_live": "An endpoint is set. This build still keeps the trace here and does not send the raw question.",
    },
    {
        "id": "log_store",
        "title": "Log store",
        "summary": "A log store that can read the trace export later. This build does not post the record.",
        "variable": "OBSERVABILITY_LOG_URL",
        "detail_local": "Using the in-process trace until a log store URL is set.",
        "detail_live": "A log store URL is set. This build still keeps the trace here and does not send the raw question.",
    },
    {
        "id": "grafana",
        "title": "Grafana",
        "summary": "Opens dashboards at the Grafana URL saved in connection configuration. The password is not stored on the trace.",
        "variable": "GRAFANA_URL",
        "detail_local": "Using the in-process trace until a Grafana URL is set.",
        "detail_live": "A Grafana URL is set. This build still keeps the trace here and does not send the raw question.",
    },
]

IDS = {spec["id"] for spec in SINKS}
DEFAULT = ["platform_trace", "evaluation"]


def describe(env: dict[str, str] | None = None) -> list[dict]:
    from shared.security.endpoints import is_configured

    source = os.environ if env is None else env
    rows = []
    for spec in SINKS:
        variable = spec["variable"]
        endpoint_id = spec["id"] if spec["id"] in {"otlp", "log_store", "grafana"} else ""
        configured = is_configured(endpoint_id, variable, source) if variable else True
        rows.append({
            "id": spec["id"],
            "title": spec["title"],
            "summary": spec["summary"],
            "variable": variable or "In this process",
            "configured": configured,
            "detail": spec["detail_live"] if configured and variable else spec["detail_local"],
        })
    return rows


def export_flags(selected: list[str]) -> dict[str, bool]:
    chosen = set(selected)
    return {
        spec["id"]: bool(os.environ.get(spec["variable"]))
        for spec in SINKS
        if spec["id"] in chosen and spec["variable"]
    }


def ordered(selected: list[str]) -> list[str]:
    chosen = set(selected)
    return [spec["id"] for spec in SINKS if spec["id"] in chosen]
