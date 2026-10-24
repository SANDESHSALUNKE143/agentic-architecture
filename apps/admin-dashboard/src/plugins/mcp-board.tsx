/** Purpose: onboard more than one MCP server. Used by: the Plugins page. */
import { Select, TextField } from "@agentic/controls";
import { useState } from "react";
import { api } from "../api";
import type { McpServer } from "./types";

const PURPOSES = [
  { value: "product", label: "Product" },
  { value: "orders", label: "Orders" },
  { value: "billing", label: "Billing" },
  { value: "support", label: "Support" },
  { value: "research", label: "Research" },
  { value: "other", label: "Other" },
];

const EMPTY = { title: "", purpose: "product", url: "", username: "", password: "" };

export function McpBoard({
  servers,
  onSaved,
  onError,
}: {
  servers: McpServer[];
  onSaved: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [selected, setSelected] = useState("new");
  const [form, setForm] = useState(EMPTY);
  const [busy, setBusy] = useState(false);
  const current = servers.find((server) => server.id === selected);

  function choose(id: string) {
    setSelected(id);
    const server = servers.find((item) => item.id === id);
    setForm(server ? { title: server.title, purpose: server.purpose, url: server.url, username: server.username, password: "" } : EMPTY);
  }

  function setField(key: keyof typeof EMPTY, value: string) {
    setForm((item) => ({ ...item, [key]: value }));
  }

  async function save() {
    setBusy(true);
    onError("");
    try {
      const body = JSON.stringify(form);
      const saved = selected === "new"
        ? await api<McpServer>("/settings/mcp-servers", { method: "POST", body })
        : await api<McpServer>(`/settings/mcp-servers/${selected}`, { method: "PUT", body });
      await onSaved();
      setSelected(saved.id);
      setForm({ title: saved.title, purpose: saved.purpose, url: saved.url, username: saved.username, password: "" });
    } catch (exc) {
      onError(String(exc).replace(/^Error:\s*/, ""));
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (selected === "new") return;
    setBusy(true);
    onError("");
    try {
      await api(`/settings/mcp-servers/${selected}`, { method: "DELETE" });
      await onSaved();
      choose("new");
    } catch (exc) {
      onError(String(exc).replace(/^Error:\s*/, ""));
    } finally {
      setBusy(false);
    }
  }

  async function check() {
    if (selected === "new") return;
    setBusy(true);
    onError("");
    try {
      await api(`/settings/mcp-servers/${selected}/check`, { method: "POST" });
      await onSaved();
    } catch (exc) {
      onError(String(exc).replace(/^Error:\s*/, ""));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="list-detail">
      <aside className="pane">
        <div className="pane-head"><h2>MCP servers</h2></div>
        <div className="pane-scroll">
          <p className="muted">This process is the client. Add one server per system: a product server, an orders server, a billing server, or a support server. Catalog, order, billing, and support tools read that server. They do not keep prices or rules in this repository. The local example is examples/merchant-mcp.</p>
          <button type="button" className="row-button" aria-current={selected === "new" ? "true" : undefined} onClick={() => choose("new")}>
            <strong>Onboard a server</strong>
            <span className="role">New connection</span>
          </button>
          {servers.map((server) => (
            <button key={server.id} type="button" className="row-button" aria-current={selected === server.id ? "true" : undefined} onClick={() => choose(server.id)}>
              <strong>{server.title}</strong>
              <span className="role">{server.purpose} · {server.check_status === "ok" ? "Answered" : server.configured ? "Address saved" : "Not configured"}</span>
            </button>
          ))}
        </div>
      </aside>
      <section className="pane">
        <div className="pane-scroll stack">
          <h3>{selected === "new" ? "New MCP server" : form.title || "MCP server"}</h3>
          <TextField label="Name" value={form.title} onChange={(value) => setField("title", value)} placeholder="Product catalog" />
          <Select label="Purpose" value={form.purpose} onChange={(value) => setField("purpose", value)} options={PURPOSES} />
          <TextField label="Server URL" value={form.url} onChange={(value) => setField("url", value)} placeholder="https://" />
          <TextField label="Username" value={form.username} onChange={(value) => setField("username", value)} autoComplete="off" />
          <TextField label="Token" type="password" value={form.password} onChange={(value) => setField("password", value)} placeholder={current?.password_set ? "Saved. Enter a new token to replace it." : ""} autoComplete="new-password" />
          {current?.check_detail ? <p className="muted">{current.check_detail}</p> : null}
          <div className="pane-foot">
            <button className="primary" type="button" onClick={save} disabled={busy}>{busy ? "Saving…" : selected === "new" ? "Onboard server" : "Save server"}</button>
            {selected !== "new" ? <button className="secondary" type="button" onClick={check} disabled={busy}>Check connection</button> : null}
            {selected !== "new" ? <button className="secondary" type="button" onClick={remove} disabled={busy}>Remove</button> : null}
          </div>
        </div>
      </section>
    </div>
  );
}
