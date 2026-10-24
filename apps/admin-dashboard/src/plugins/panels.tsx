/** Purpose: connect one plugin to agents that already have its permission. Used by: the plugins page. Observability and RAG panels are separate files. */
import { Checkbox } from "@agentic/controls";
import { useState } from "react";
import { api } from "../api";
import { EndpointForm } from "./endpoint-form";
import type { EndpointConfig, Plugin } from "./types";
import { title } from "./title";

export function ConnectPanel({
  plugin,
  endpoint,
  onClose,
  onSaved,
  onError,
}: {
  plugin: Plugin;
  endpoint?: EndpointConfig;
  onClose: () => void;
  onSaved: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [chosen, setChosen] = useState<string[]>(plugin.connected_agents);
  const [busy, setBusy] = useState(false);

  function toggle(agent: string) {
    setChosen((current) => current.includes(agent) ? current.filter((item) => item !== agent) : [...current, agent]);
  }

  async function save() {
    setBusy(true);
    onError("");
    try {
      await api("/plugins/" + plugin.name, { method: "PUT", body: JSON.stringify({ agents: chosen }) });
      await onSaved();
      onClose();
    } catch (exc) {
      onError(String(exc).replace(/^Error:\s*/, ""));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card connect-panel" aria-label="Connect plugin">
      <header>
        <div>
          <p className="eyebrow">Connect plugin</p>
          <h2>{title(plugin.name)}</h2>
        </div>
        <button className="secondary" type="button" onClick={onClose}>Close</button>
      </header>
      <div className="body stack">
        <p className="muted">{plugin.summary}</p>
        {plugin.source ? <p>{plugin.source}</p> : null}
        <p className="muted">{plugin.connection_summary} Permission: {plugin.permission}.{plugin.write ? " This write stays behind approval." : ""}</p>
        {plugin.connection_url ? <p>URL: {plugin.connection_url}</p> : null}
        {plugin.connection_string ? <p>Connection string: {plugin.connection_string}</p> : null}
        {endpoint ? <EndpointForm endpoint={endpoint} embedded onSaved={onSaved} onError={onError} /> : null}
        <p className="muted">
          An agent appears here only when its contract already grants {plugin.permission}.
          {plugin.endpoint && !plugin.connection_ready ? " Saving stays off until that connection is saved." : ""}
        </p>
        {plugin.eligible_agents.length ? (
          <div className="check-grid">
            {plugin.eligible_agents.map((agent) => (
              <Checkbox key={agent} label={title(agent)} checked={chosen.includes(agent)} disabled={!plugin.connection_ready} onChange={() => toggle(agent)} />
            ))}
          </div>
        ) : (
          <p className="muted">No agent has this permission yet. Add it on the agent contract before connecting the plugin.</p>
        )}
      </div>
      <div className="foot">
        <button className="primary" type="button" onClick={save} disabled={busy || !plugin.connection_ready || plugin.eligible_agents.length === 0}>
          {busy ? "Saving…" : "Save connection"}
        </button>
      </div>
    </section>
  );
}

export { ObservePanel } from "./observe-panel";
export { RagPanel } from "./rag-panel";
export { title } from "./title";
