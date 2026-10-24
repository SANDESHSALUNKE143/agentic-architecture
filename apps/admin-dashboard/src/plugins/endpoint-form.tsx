/** Purpose: save a connector URL and password. A saved password is not shown again. Used by: plugins and configuration. */
import { TextField } from "@agentic/controls";
import { useState } from "react";
import { api } from "../api";
import type { EndpointConfig } from "./types";

export function EndpointForm({
  endpoint,
  onSaved,
  onError,
  embedded = false,
}: {
  endpoint: EndpointConfig;
  onSaved: () => Promise<void>;
  onError: (message: string) => void;
  embedded?: boolean;
}) {
  const [url, setUrl] = useState(endpoint.url);
  const [connectionString, setConnectionString] = useState(endpoint.connection_string);
  const [username, setUsername] = useState(endpoint.username);
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  async function save() {
    setBusy(true);
    onError("");
    try {
      await api("/settings/connections/" + endpoint.id, {
        method: "PUT",
        body: JSON.stringify({ url, connection_string: connectionString, username, password }),
      });
      setPassword("");
      await onSaved();
    } catch (exc) {
      onError(String(exc).replace(/^Error:\s*/, ""));
    } finally {
      setBusy(false);
    }
  }

  const fields = (
    <>
      {embedded ? <h3>{endpoint.title}</h3> : <p className="muted">{endpoint.summary}</p>}
      <TextField label="Direct URL" value={url} onChange={setUrl} placeholder="https://" />
      <TextField label="Connection string" value={connectionString} onChange={setConnectionString} />
      <TextField label="Username" value={username} onChange={setUsername} autoComplete="off" />
      <TextField label="Password" type="password" value={password} placeholder={endpoint.password_set ? "Saved. Enter a new password to replace it." : ""} onChange={setPassword} autoComplete="new-password" />
      <div className="pane-foot">
        <button className="primary" type="button" onClick={save} disabled={busy}>{busy ? "Saving…" : "Save connection"}</button>
      </div>
    </>
  );

  if (embedded) return <div className="stack">{fields}</div>;

  return (
    <article className="card plugin-card">
      <header>
        <div>
          <p className="eyebrow">{endpoint.configured ? "Address saved" : "Mock"}</p>
          <h2>{endpoint.title}</h2>
        </div>
      </header>
      <div className="body stack">
        {fields}
      </div>
    </article>
  );
}
