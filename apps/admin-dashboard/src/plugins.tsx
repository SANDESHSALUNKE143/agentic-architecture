import { useEffect, useState } from "react";
import { api } from "./api";

type Plugin = {
  name: string;
  group: string;
  summary: string;
  permission: string;
  write: boolean;
  connected_agents: string[];
  eligible_agents: string[];
};

type Connection = {
  id: string;
  title: string;
  variable: string;
  configured: boolean;
  detail: string;
};

type Catalog = { plugins: Plugin[]; connections: Connection[] };

export function PluginsView({ onError }: { onError: (message: string) => void }) {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [active, setActive] = useState<Plugin | null>(null);
  const [group, setGroup] = useState("All");

  async function load() {
    setCatalog(await api<Catalog>("/plugins"));
  }

  useEffect(() => {
    load().catch((exc) => onError(String(exc).replace(/^Error:\s*/, "")));
  }, [onError]);

  if (!catalog) return <p className="card empty">Loading plugins…</p>;
  const groups = ["All", ...new Set(catalog.plugins.map((plugin) => plugin.group))];
  const visible = catalog.plugins.filter((plugin) => group === "All" || plugin.group === group);

  return (
    <div className="stack">
      <section className="metrics" aria-label="Connections">
        {catalog.connections.map((connection) => (
          <article key={connection.id} className="card metric">
            <p className="eyebrow">{connection.configured ? "Connected" : "Local"}</p>
            <h2>{connection.title}</h2>
            <p className="muted">{connection.detail}</p>
            <p className="mono">{connection.variable}</p>
          </article>
        ))}
      </section>
      <div className="segmented" role="tablist" aria-label="Plugin groups">
        {groups.map((item) => (
          <button key={item} type="button" aria-pressed={group === item} onClick={() => setGroup(item)}>
            {item}
          </button>
        ))}
      </div>
      <section className="grid">
        {visible.map((plugin) => (
          <article key={plugin.name} className="card plugin-card">
            <header>
              <div>
                <p className="eyebrow">{plugin.group}</p>
                <h2>{title(plugin.name)}</h2>
              </div>
              <span className={`badge ${plugin.write ? "pending" : "completed"}`}>
                {plugin.write ? "Needs approval" : "Read"}
              </span>
            </header>
            <div className="body stack">
              <p className="muted">{plugin.summary}</p>
              <p className="mono">Permission {plugin.permission}</p>
              <div className="tools">
                {plugin.connected_agents.length ? plugin.connected_agents.map((agent) => (
                  <span key={agent} className="tool">{title(agent)}</span>
                )) : <span className="muted">Not connected to an agent</span>}
              </div>
            </div>
            <div className="foot">
              <button className="secondary" type="button" onClick={() => setActive(plugin)}>Connect</button>
            </div>
          </article>
        ))}
      </section>
      {active ? (
        <ConnectPanel
          plugin={catalog.plugins.find((plugin) => plugin.name === active.name) || active}
          onClose={() => setActive(null)}
          onSaved={async () => {
            await load();
          }}
          onError={onError}
        />
      ) : null}
    </div>
  );
}

function ConnectPanel({
  plugin,
  onClose,
  onSaved,
  onError,
}: {
  plugin: Plugin;
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
        <p className="muted">
          Choose the agents that may call this plugin. An agent appears here only when its contract already grants {plugin.permission}.
          {plugin.write ? " This write stays behind approval." : ""}
        </p>
        {plugin.eligible_agents.length ? (
          <div className="check-grid">
            {plugin.eligible_agents.map((agent) => (
              <label key={agent}>
                <input type="checkbox" checked={chosen.includes(agent)} onChange={() => toggle(agent)} />
                {title(agent)}
              </label>
            ))}
          </div>
        ) : (
          <p className="muted">No agent has this permission yet. Add it to an agent contract before connecting the plugin.</p>
        )}
      </div>
      <div className="foot">
        <button className="primary" type="button" onClick={save} disabled={busy || plugin.eligible_agents.length === 0}>
          {busy ? "Saving…" : "Save connection"}
        </button>
      </div>
    </section>
  );
}

function title(value: string) {
  return value.replaceAll("-", " ").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
