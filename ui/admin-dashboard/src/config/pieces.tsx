/** Purpose: the agent picker and the host forms on the configuration page. Used by: ConfigCenter. */
import { TextField } from "@agentic/controls";
import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { initials, prettyName } from "../console";
import { EndpointForm, type EndpointConfig } from "../plugins";

type AgentChoice = { name: string; description: string };

export function AgentPicker({
  agents,
  agent,
  onSelect,
}: {
  agents: AgentChoice[];
  agent: string;
  onSelect: (agent: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const root = useRef<HTMLDivElement>(null);
  const selected = agents.find((item) => item.name === agent);
  const visible = agents.filter((item) => {
    const haystack = `${prettyName(item.name)} ${item.description}`.toLowerCase();
    return haystack.includes(query.trim().toLowerCase());
  });

  useEffect(() => {
    if (!open) return;
    function close(event: MouseEvent) {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  function choose(name: string) {
    onSelect(name);
    setOpen(false);
    setQuery("");
  }

  return (
    <div className="agent-picker" ref={root}>
      <span id="agent-picker-label">Choose the agent</span>
      <button
        type="button"
        className="agent-picker-trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-labelledby="agent-picker-label"
        onClick={() => setOpen((value) => !value)}
      >
        <span className="picker-avatar" aria-hidden="true">{initials(agent)}</span>
        <span className="picker-copy">
          <strong>{prettyName(agent)}</strong>
          <small>{selected?.description}</small>
        </span>
        <svg className="picker-chevron" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" /></svg>
      </button>
      {open ? (
        <div className="agent-picker-menu" role="listbox" aria-labelledby="agent-picker-label">
          <TextField className="agent-picker-search" aria-label="Search agents" placeholder="Search agents" value={query} onChange={setQuery} autoFocus />
          {visible.map((item) => (
            <button key={item.name} type="button" role="option" aria-selected={item.name === agent} className="agent-picker-option" onClick={() => choose(item.name)}>
              <span className="picker-avatar" aria-hidden="true">{initials(item.name)}</span>
              <span className="picker-copy">
                <strong>{prettyName(item.name)}</strong>
                <small>{item.description}</small>
              </span>
              <span className="picker-mark" aria-hidden="true" />
            </button>
          ))}
          {visible.length === 0 ? <p className="agent-picker-empty">No agent matches.</p> : null}
        </div>
      ) : null}
    </div>
  );
}

export function HostBlock({
  endpoint,
  onSaved,
  onError,
}: {
  endpoint: EndpointConfig | undefined;
  onSaved: () => Promise<void>;
  onError: (message: string) => void;
}) {
  if (!endpoint) return null;
  return (
    <>
      <p className="eyebrow">{endpoint.configured ? "Address saved" : "Mock"}</p>
      <EndpointForm endpoint={endpoint} embedded onSaved={onSaved} onError={onError} />
    </>
  );
}

export function ModelHost({ endpoint, onSaved, onError }: { endpoint: EndpointConfig; onSaved: () => Promise<void>; onError: (message: string) => void }) {
  const [url, setUrl] = useState(endpoint.url);
  const [connectionString, setConnectionString] = useState(endpoint.connection_string);
  const [busyHost, setBusyHost] = useState(false);
  async function saveHost() {
    setBusyHost(true);
    onError("");
    try {
      await api("/settings/connections/model", {
        method: "PUT",
        body: JSON.stringify({ url, connection_string: connectionString, username: endpoint.username, password: "" }),
      });
      await onSaved();
    } catch (exc) {
      onError(String(exc).replace(/^Error:\s*/, ""));
    } finally {
      setBusyHost(false);
    }
  }
  return (
    <div className="stack">
      <p className="muted">Host address for this agent. The model key is not entered here.</p>
      <TextField label="Host URL" value={url} onChange={setUrl} placeholder="https://" />
      <TextField label="Connection string" value={connectionString} onChange={setConnectionString} />
      <button className="primary" type="button" onClick={saveHost} disabled={busyHost}>{busyHost ? "Saving…" : "Save host"}</button>
    </div>
  );
}
