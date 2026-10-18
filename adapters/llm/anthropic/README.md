# Native Anthropic adapter

[Implementation](messages.py) maps the Messages API to Completion, including cached input usage. ProjectConfig accepts adapter=anthropic, model and api_key_env. Contract-tested with a fake client; no paid calls performed. Provider deadlines are bounded and retries are not automatic. See the [official Messages API](https://platform.claude.com/docs/en/api/messages/create).


## Folder contents

Native Messages API mapping.

- [messages.py](messages.py): Native Anthropic Messages API adapter using the provider-neutral Completion port.
