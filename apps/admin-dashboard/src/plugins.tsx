/** Purpose: the plugins page. Tools, hosts, and MCP server settings live here. Used by: the console shell. */
import { Select } from "@agentic/controls";
import { useEffect, useState } from "react";
import { api } from "./api";
import { EndpointForm } from "./plugins/endpoint-form";
import { McpBoard } from "./plugins/mcp-board";
import { ConnectPanel, title } from "./plugins/panels";
import type { Catalog, EndpointConfig } from "./plugins/types";

export type { EndpointConfig } from "./plugins/types";
export { EndpointForm } from "./plugins/endpoint-form";

export function PluginsView({ onError }: { onError: (message: string) => void }) {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [active, setActive] = useState<string>("");
  const [group, setGroup] = useState("All");
  const [section, setSection] = useState<"tools" | "hosts" | "mcp">("tools");
  const [hostId, setHostId] = useState("sql");

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
  const hosts = catalog.endpoints.filter((item) => item.id !== "mcp");
  const host = hosts.find((item) => item.id === hostId) || hosts[0];
  const hostTools = catalog.plugins.filter((plugin) => plugin.endpoint === host?.id);

  return (
    <div className="fill-col plugin-board">
      <div className="segmented" role="tablist" aria-label="Plugin sections">
        <button type="button" aria-pressed={section === "tools"} onClick={() => setSection("tools")}>Tools</button>
        <button type="button" aria-pressed={section === "hosts"} onClick={() => setSection("hosts")}>Hosts</button>
        <button type="button" aria-pressed={section === "mcp"} onClick={() => setSection("mcp")}>MCP servers</button>
      </div>
      {section === "tools" ? (
        <div className="list-detail">
          <aside className="pane">
            <div className="pane-head"><h2>All tools</h2></div>
            <div className="pane-scroll">
              <Select
                label="Group"
                value={group}
                onChange={setGroup}
                options={groups.map((item) => ({ value: item, label: item }))}
              />
              {visible.map((plugin) => (
                <button key={plugin.name} type="button" className="row-button" aria-current={plugin.name === active ? "true" : undefined} onClick={() => setActive(plugin.name)}>
                  <strong>{title(plugin.name)}</strong>
                  <span className="role">{plugin.connection_ready ? (plugin.endpoint || plugin.connection_url ? "Connected" : "In this process") : "Needs a connection"}</span>
                </button>
              ))}
            </div>
          </aside>
          <section className="pane">
            {selected ? (
              <div className="pane-scroll">
                <ConnectPanel
                  plugin={selected}
                  endpoint={catalog.endpoints.find((item) => item.id === selected.endpoint)}
                  onClose={() => setActive("")}
                  onSaved={load}
                  onError={onError}
                />
              </div>
            ) : <p className="empty">Select a tool to see its connection and which agents may call it.</p>}
          </section>
        </div>
      ) : null}
      {section === "hosts" ? (
        <HostList
          hosts={hosts}
          host={host}
          tools={hostTools}
          onSelect={setHostId}
          onSaved={load}
          onError={onError}
        />
      ) : null}
      {section === "mcp" ? <McpBoard servers={catalog.mcp_servers || []} onSaved={load} onError={onError} /> : null}
    </div>
  );
}

function HostList({
  hosts,
  host,
  tools,
  onSelect,
  onSaved,
  onError,
}: {
  hosts: EndpointConfig[];
  host: EndpointConfig | undefined;
  tools: { name: string }[];
  onSelect: (id: string) => void;
  onSaved: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const groups = [...new Set(hosts.map((item) => item.group))];
  return (
    <div className="list-detail">
      <aside className="pane">
        <div className="pane-head"><h2>Hosts</h2></div>
        <div className="pane-scroll">
          <p className="muted">Each host stores a URL, a connection string, a username, and a password. A tool that names a host stays off until that host is configured.</p>
          {groups.map((group) => (
            <div key={group}>
              <p className="eyebrow">{group}</p>
              {hosts.filter((item) => item.group === group).map((item) => (
                <button key={item.id} type="button" className="row-button" aria-current={host?.id === item.id ? "true" : undefined} onClick={() => onSelect(item.id)}>
                  <strong>{item.title}</strong>
                  <span className="role">{item.configured ? "Address saved" : "Not configured"}</span>
                </button>
              ))}
            </div>
          ))}
        </div>
      </aside>
      <section className="pane">
        <div className="pane-scroll">
          {host ? (
            <>
              <EndpointForm key={host.id} embedded endpoint={host} onSaved={onSaved} onError={onError} />
              <p className="muted">{host.summary}</p>
              {tools.length ? <p className="muted">Tools that use this host: {tools.map((item) => title(item.name)).join(", ")}.</p> : <p className="muted">No tool requires this host. Agents choose it from their own configuration.</p>}
            </>
          ) : <p className="empty">No host is listed.</p>}
        </div>
      </section>
    </div>
  );
}
