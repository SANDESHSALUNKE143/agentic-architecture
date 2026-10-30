# API

The token is `Authorization: Bearer`.

## `GET /health`

Returns `status`, `mode`, `agents`, and `harness`.

## `GET /settings/harness`

Returns the selected `harness` and the three options: `langchain`, `claude`, and `deepagent`.

## `PUT /settings/harness`

```json
{"harness": "claude"}
```

Writes that name onto `desk-agent/agent.yaml`. The next run uses it. Any other name is `422`.

## `POST /agent-runs`

```json
{"task": "Find a blue trail jacket under $150", "session_id": "ses-jacket"}
```

`session_id` may be empty. A later call with the same id sends the earlier turns into the harness.

The response includes `status`, `result`, `reply`, `tool_calls`, `errors`, `harness`, and `trace`. `result` has `products`, `available`, `explanation`, and `sources`. A missing schema field fails the run. The trace omits the raw question and records `harness`.

## `POST /agent-runs/stream`

The same body. The response is `text/event-stream`. Events are `activity`, `tool`, `error`, and `done`. `done` carries the run object.
