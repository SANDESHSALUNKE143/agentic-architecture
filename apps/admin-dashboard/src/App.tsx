import { useEffect, useState } from "react";
import { api, setToken, token } from "./api";
import { ConfigCenter } from "./config";
import { ChatView, DashboardView, HistoryView, LibraryView, initials, prettyName, type AgentCard, type SessionRun } from "./console";
import { DocsView } from "./docs";

type View = "dashboard" | "chat" | "library" | "history" | "approvals" | "config" | "docs";

type Approval = { id: string; agent_id: string; tool: string; status: string; arguments: Record<string, unknown> };

const NAV: { id: View; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "chat", label: "Agent chat" },
  { id: "library", label: "Agent library" },
  { id: "history", label: "Run history" },
  { id: "approvals", label: "Approvals" },
  { id: "config", label: "Configuration" },
  { id: "docs", label: "Docs" },
];

const TITLES: Record<View, string> = {
  dashboard: "Dashboard",
  chat: "Chat with an agent",
  library: "Agent library",
  history: "Run history",
  approvals: "Approvals",
  config: "Configuration",
  docs: "Docs",
};

export function App() {
  const [view, setView] = useState<View>("dashboard");
  const [devToken, setDevToken] = useState(token());
  const [error, setError] = useState("");
  const [agents, setAgents] = useState<AgentCard[]>([]);
  const [agent, setAgent] = useState("catalog-agent");
  const [query, setQuery] = useState("");
  const [pending, setPending] = useState(0);
  const [history, setHistory] = useState<SessionRun[]>([]);

  useEffect(() => {
    api<AgentCard[]>("/agents").then((rows) => {
      setAgents(rows);
      if (rows[0] && !rows.some((item) => item.name === agent)) setAgent(rows[0].name);
    }).catch((exc) => setError(readableError(exc)));
  }, [agent]);

  useEffect(() => {
    api<Approval[]>("/approvals")
      .then((rows) => setPending(rows.filter((item) => item.status === "pending").length))
      .catch(() => setPending(0));
  }, [view]);

  const visible = agents.filter((item) => prettyName(item.name).toLowerCase().includes(query.trim().toLowerCase()) || item.name.includes(query.trim().toLowerCase()));

  function openChat(name: string) {
    setAgent(name);
    setView("chat");
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="mark" aria-hidden="true">AG</div>
          <div>
            <strong>Agentic Operations</strong>
            <span>AI agent workspace</span>
          </div>
        </div>
        <div className="nav-tag">Workspace</div>
        <nav aria-label="Sections">
          {NAV.filter((item) => item.id !== "config" && item.id !== "docs").map((item) => (
            <button key={item.id} type="button" aria-current={view === item.id ? "page" : undefined} onClick={() => setView(item.id)}>
              {item.label}
              {item.id === "dashboard" || item.id === "library" ? <span className="count">{agents.length}</span> : null}
              {item.id === "approvals" ? <span className="count">{pending}</span> : null}
            </button>
          ))}
          <div className="nav-sep" />
          <div className="nav-tag">Manage</div>
          <button type="button" aria-current={view === "config" ? "page" : undefined} onClick={() => setView("config")}>Configuration</button>
          <button type="button" aria-current={view === "docs" ? "page" : undefined} onClick={() => setView("docs")}>Docs</button>
        </nav>
        <div className="side-agents">
          <div className="side-head"><span>Your agents</span><span className="count">{agents.length}</span></div>
          <input className="agent-search" aria-label="Search agents" placeholder="Search agents" value={query} onChange={(event) => setQuery(event.target.value)} />
          <div className="agent-list">
            {visible.map((item) => (
              <button key={item.name} type="button" className="agent-item" aria-current={agent === item.name ? "true" : undefined} onClick={() => { setAgent(item.name); if (view !== "config") setView("chat"); }}>
                <span className="agent-avatar">{initials(item.name)}</span>
                <span className="agent-label"><strong>{prettyName(item.name)}</strong><small>{item.tools[0] ? prettyName(item.tools[0]) : "Agent"}</small></span>
              </button>
            ))}
          </div>
        </div>
        <div className="sidebar-user">
          <div className="user-circle" aria-hidden="true">LO</div>
          <div>
            <strong>Local operator</strong>
            <small>Local development</small>
          </div>
        </div>
        <details className="token-drawer">
          <summary>Access token</summary>
          <input
            aria-label="Access token"
            value={devToken}
            onChange={(event) => {
              setDevToken(event.target.value);
              setToken(event.target.value);
            }}
          />
        </details>
      </aside>
      <main className="workspace">
        <header className="topbar">
          <div>
            <div className="crumb">Workspace / {NAV.find((item) => item.id === view)?.label}</div>
            <h1>{TITLES[view]}</h1>
          </div>
          <div className="mock-pill"><i /><span>Mock mode · safe to test</span></div>
        </header>
        {error ? <p className="banner" role="alert">{error}</p> : null}
        <div className="page-body">
          {view === "dashboard" ? <DashboardView agents={agents} runs={history} onOpen={openChat} onError={setError} /> : null}
          {view === "chat" ? (
            <ChatView agent={agent} agents={agents} onFinished={(run) => setHistory((current) => [run, ...current.filter((item) => item.id !== run.id)])} onError={setError} />
          ) : null}
          {view === "library" ? <LibraryView agents={agents} onOpen={openChat} /> : null}
          {view === "history" ? <HistoryView runs={history} onOpen={openChat} /> : null}
          {view === "approvals" ? <div className="page-pad"><ApprovalsView onError={setError} /></div> : null}
          {view === "config" ? <ConfigCenter agent={agent} agents={agents} onSelect={setAgent} onOpenChat={openChat} onError={setError} /> : null}
          {view === "docs" ? <div className="page-pad"><DocsView onError={setError} /></div> : null}
        </div>
      </main>
    </div>
  );
}

function ApprovalsView({ onError }: { onError: (message: string) => void }) {
  const [items, setItems] = useState<Approval[] | null>(null);
  const [actor, setActor] = useState("local-operator");

  async function load() {
    setItems(await api<Approval[]>("/approvals"));
  }

  useEffect(() => {
    load().catch((exc) => onError(readableError(exc)));
  }, [onError]);

  async function decide(id: string, decision: string) {
    onError("");
    try {
      await api(`/approvals/${id}/decision`, { method: "POST", body: JSON.stringify({ decision, actor }) });
      await load();
    } catch (exc) {
      onError(readableError(exc));
    }
  }

  return (
    <div className="pane">
      <div className="pane-scroll stack">
      <section className="card">
        <header>
          <div>
            <p className="eyebrow">Operator</p>
            <h2>Who is deciding</h2>
          </div>
        </header>
        <div className="body">
          <label className="field">
            <span>The actor cannot approve a request from their own agent.</span>
            <input value={actor} onChange={(event) => setActor(event.target.value)} />
          </label>
        </div>
      </section>
      {!items ? <p className="card empty">Loading approvals…</p> : null}
      {items && items.length === 0 ? <p className="card empty">No approvals yet. A write above the order threshold will appear here.</p> : null}
      {items?.map((item) => (
        <article key={item.id} className="card">
          <header>
            <div>
              <p className="eyebrow">{label(item.tool)}</p>
              <h2>{label(item.agent_id)}</h2>
              <p className="mono">{item.id}</p>
            </div>
            <Status value={item.status} />
          </header>
          <div className="body">
            <ResultBody result={item.arguments} />
          </div>
          {item.status === "pending" ? (
            <div className="foot">
              <button className="danger" type="button" onClick={() => decide(item.id, "reject")}>Reject</button>
              <button className="primary" type="button" onClick={() => decide(item.id, "approve")}>Approve</button>
            </div>
          ) : null}
        </article>
      ))}
      </div>
    </div>
  );
}

function Status({ value }: { value: string }) {
  return <span className={`badge ${value}`}>{label(value)}</span>;
}

function ResultBody({ result }: { result: Record<string, unknown> }) {
  const entries = Object.entries(result).filter(([, value]) => value !== "" && value !== null && value !== undefined);
  if (!entries.length) return <p className="muted">No structured result.</p>;
  return (
    <dl className="result">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt>{label(key)}</dt>
          <dd>{renderValue(key, value)}</dd>
        </div>
      ))}
    </dl>
  );
}

function renderValue(key: string, value: unknown) {
  if (key === "products" && Array.isArray(value)) {
    return (
      <table className="product-table">
        <thead>
          <tr><th>Product</th><th>Price</th><th>Stock</th></tr>
        </thead>
        <tbody>
          {value.map((item) => {
            const product = item as { product_id?: string; name?: string; price?: number; stock?: number };
            return (
              <tr key={product.product_id}>
                <td>{product.name || product.product_id}</td>
                <td>{product.price ?? "—"}</td>
                <td>{product.stock ?? "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    );
  }
  if (key === "sources" && Array.isArray(value)) {
    return (
      <ul>
        {value.map((item, index) => {
          const source = item as { source_id?: string; location?: string };
          return <li key={index}>{source.source_id}{source.location ? ` · ${source.location}` : ""}</li>;
        })}
      </ul>
    );
  }
  if (Array.isArray(value)) {
    if (!value.length) return <span className="muted">None</span>;
    return <span>{value.map((item) => typeof item === "object" ? JSON.stringify(item) : String(item)).join(", ")}</span>;
  }
  if (typeof value === "object" && value) return <span>{JSON.stringify(value)}</span>;
  return <span>{String(value)}</span>;
}

function label(value: string) {
  const known: Record<string, string> = {
    "product-discovery": "Product discovery",
    "customer-support": "Customer support",
    "order-processing": "Order processing",
    "data-analysis": "Data analysis",
    needs_approval: "Needs approval",
    completed: "Completed",
    failed: "Failed",
    pending: "Pending",
    approved: "Approved",
    rejected: "Rejected",
    load_instructions: "The agent loaded its instructions",
    reason: "The agent chose its next step",
    tool: "The agent used a tool",
    persist: "The agent saved its answer",
    product_id: "Product",
    order_id: "Order",
    mean_amount: "Mean amount",
  };
  if (known[value]) return known[value];
  return value.replaceAll("-", " ").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function readableError(exc: unknown) {
  const text = String(exc);
  if (text.includes("401")) return "The access token was rejected.";
  return text.replace(/^Error:\s*/, "");
}
