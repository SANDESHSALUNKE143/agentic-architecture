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

type Catalog = {
  plugins: Plugin[];
  connections: Connection[];
  observability: ObservabilityTool[];
  rag: { vector: RagChoice[]; embedding: RagChoice[]; model: RagChoice[] };
  endpoints: EndpointConfig[];
};

export type EndpointConfig = {
  id: string;
  title: string;
  group: string;
  summary: string;
  url: string;
  connection_string: string;
  username: string;
  password_set: boolean;
  configured: boolean;
};

type RagChoice = ObservabilityTool & { kind: string };

type ObservabilityTool = {
  id: string;
  title: string;
  summary: string;
  variable: string;
  configured: boolean;
  detail: string;
  connected_agents: string[];
  eligible_agents: string[];
};

export function PluginsView({ onError }: { onError: (message: string) => void }) {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [active, setActive] = useState<string>("");
  const [group, setGroup] = useState("All");
  const [section, setSection] = useState<"tools" | "hosts">("tools");
  const [hostId, setHostId] = useState("n8n");

  async function load() {
    setCatalog(await api<Catalog>("/plugins"));
  }

  useEffect(() => {
    load().catch((exc) => onError(String(exc).replace(/^Error:\s*/, "")));
  }, [onError]);

  if (!catalog) return <p className="card empty">Loading plugins…</p>;
  const groups = ["All", ...new Set(catalog.plugins.map((plugin) => plugin.group))];
  const visible = catalog.plugins.filter((plugin) => group === "All" || plugin.group === group);
  const selected = catalog.plugins.find((plugin) => plugin.name === active) || null;
  const hosts = (catalog.endpoints || []).filter((item) => item.id === "n8n" || item.id === "sql");
  const host = hosts.find((item) => item.id === hostId) || hosts[0];

  return (
    <div className="fill-col">
      <div className="segmented" role="tablist" aria-label="Plugin sections">
        <button type="button" aria-pressed={section === "tools"} onClick={() => setSection("tools")}>Tools</button>
        <button type="button" aria-pressed={section === "hosts"} onClick={() => setSection("hosts")}>Hosts</button>
      </div>
      {section === "tools" ? (
        <div className="list-detail">
          <aside className="pane">
            <div className="pane-head"><h2>MCP tools</h2></div>
            <div className="pane-scroll">
              <div className="segmented" role="tablist" aria-label="Plugin groups">
                {groups.map((item) => (
                  <button key={item} type="button" aria-pressed={group === item} onClick={() => setGroup(item)}>{item}</button>
                ))}
              </div>
              {visible.map((plugin) => (
                <button key={plugin.name} type="button" className="row-button" aria-current={plugin.name === active ? "true" : undefined} onClick={() => setActive(plugin.name)}>
                  <strong>{title(plugin.name)}</strong>
                  <span className="role">{plugin.summary}</span>
                </button>
              ))}
            </div>
          </aside>
          <section className="pane">
            {selected ? (
              <div className="pane-scroll">
                <ConnectPanel
                  plugin={selected}
                  onClose={() => setActive("")}
                  onSaved={load}
                  onError={onError}
                />
              </div>
            ) : <p className="empty">Select a tool to choose which agents may call it.</p>}
          </section>
        </div>
      ) : (
        <div className="list-detail">
          <aside className="pane">
            <div className="pane-head"><h2>Hosts</h2></div>
            <div className="pane-scroll">
              <p className="muted">n8n and SQL are not part of an agent choice. Observability, retrieval, and memory hosts are configured on the agent.</p>
              {hosts.map((item) => (
                <button key={item.id} type="button" className="row-button" aria-current={host?.id === item.id ? "true" : undefined} onClick={() => setHostId(item.id)}>
                  <strong>{item.title}</strong>
                  <span className="role">{item.configured ? "Address saved" : "Mock"}</span>
                </button>
              ))}
            </div>
          </aside>
          <section className="pane">
            <div className="pane-scroll">
              {host ? <EndpointForm key={host.id} embedded endpoint={host} onSaved={load} onError={onError} /> : <p className="empty">No host is listed.</p>}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

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
      <label className="field"><span>Direct URL</span><input value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://" /></label>
      <label className="field"><span>Connection string</span><input value={connectionString} onChange={(event) => setConnectionString(event.target.value)} /></label>
      <label className="field"><span>Username</span><input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="off" /></label>
      <label className="field">
        <span>Password</span>
        <input
          type="password"
          value={password}
          placeholder={endpoint.password_set ? "Saved. Enter a new password to replace it." : ""}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="new-password"
        />
      </label>
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

function ObservePanel({
  tool,
  onClose,
  onSaved,
  onError,
}: {
  tool: ObservabilityTool;
  onClose: () => void;
  onSaved: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [chosen, setChosen] = useState<string[]>(tool.connected_agents);
  const [busy, setBusy] = useState(false);

  function toggle(agent: string) {
    setChosen((current) => current.includes(agent) ? current.filter((item) => item !== agent) : [...current, agent]);
  }

  async function save() {
    setBusy(true);
    onError("");
    try {
      await api("/settings/observability/" + tool.id, { method: "PUT", body: JSON.stringify({ agents: chosen }) });
      await onSaved();
      onClose();
    } catch (exc) {
      onError(String(exc).replace(/^Error:\s*/, ""));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card connect-panel" aria-label="Observability connection">
      <header>
        <div>
          <p className="eyebrow">Agent configuration</p>
          <h2>{tool.title}</h2>
        </div>
        <button className="secondary" type="button" onClick={onClose}>Close</button>
      </header>
      <div className="body stack">
        <p className="muted">{tool.detail} Saving writes this tool onto each selected agent contract.</p>
        <div className="check-grid">
          {tool.eligible_agents.map((agent) => (
            <label key={agent}>
              <input type="checkbox" checked={chosen.includes(agent)} onChange={() => toggle(agent)} />
              {title(agent)}
            </label>
          ))}
        </div>
      </div>
      <div className="foot">
        <button className="primary" type="button" onClick={save} disabled={busy}>
          {busy ? "Saving…" : "Save on agents"}
        </button>
      </div>
    </section>
  );
}

function RagPanel({
  choice,
  onClose,
  onSaved,
  onError,
}: {
  choice: RagChoice;
  onClose: () => void;
  onSaved: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [chosen, setChosen] = useState<string[]>(choice.connected_agents);
  const [busy, setBusy] = useState(false);

  function toggle(agent: string) {
    setChosen((current) => current.includes(agent) ? current.filter((item) => item !== agent) : [...current, agent]);
  }

  async function save() {
    setBusy(true);
    onError("");
    try {
      await api(`/settings/rag/${choice.kind}/${choice.id}`, { method: "PUT", body: JSON.stringify({ agents: chosen }) });
      await onSaved();
      onClose();
    } catch (exc) {
      onError(String(exc).replace(/^Error:\s*/, ""));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card connect-panel" aria-label="RAG connection">
      <header>
        <div>
          <p className="eyebrow">Agent configuration</p>
          <h2>{choice.title}</h2>
        </div>
        <button className="secondary" type="button" onClick={onClose}>Close</button>
      </header>
      <div className="body stack">
        <p className="muted">{choice.detail} Saving sets this choice on the selected agent contracts.</p>
        <div className="check-grid">
          {choice.eligible_agents.map((agent) => (
            <label key={agent}>
              <input type="checkbox" checked={chosen.includes(agent)} onChange={() => toggle(agent)} />
              {title(agent)}
            </label>
          ))}
        </div>
      </div>
      <div className="foot">
        <button className="primary" type="button" onClick={save} disabled={busy}>
          {busy ? "Saving…" : "Save on agents"}
        </button>
      </div>
    </section>
  );
}

function title(value: string) {
  return value.replaceAll("-", " ").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
