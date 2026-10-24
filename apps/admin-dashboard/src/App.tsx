/**
 * Purpose: the console shell. It switches Dashboard, chat, library, history, approvals, configuration, and docs.
 * Used by: apps/admin-dashboard/src/main.tsx. The gear calls openSettings for one agent.
 */
import { GearIcon, TextField } from "@agentic/controls";
import { useEffect, useState } from "react";
import { api, setToken, token } from "./api";
import { ConfigCenter } from "./config";
import { PluginsView } from "./plugins";
import { ChatView, DashboardView, HistoryView, LibraryView, type AgentCard, type SessionRun } from "./console";
import { DocsView } from "./docs";
import { ApprovalsView, readableError } from "./views/approvals";

type View = "dashboard" | "chat" | "library" | "history" | "approvals" | "plugins" | "config" | "docs";

type Approval = { id: string; agent_id: string; tool: string; status: string; arguments: Record<string, unknown> };

const NAV: { id: View; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "chat", label: "Agent chat" },
  { id: "library", label: "Agent library" },
  { id: "history", label: "Run history" },
  { id: "approvals", label: "Approvals" },
  { id: "plugins", label: "Plugins" },
  { id: "config", label: "Configuration" },
  { id: "docs", label: "Docs" },
];

const TITLES: Record<View, string> = {
  dashboard: "Dashboard",
  chat: "Chat with an agent",
  library: "Agent library",
  history: "Run history",
  approvals: "Approvals",
  plugins: "Plugins",
  config: "Configuration",
  docs: "Docs",
};

export function App() {
  const [view, setView] = useState<View>("dashboard");
  const [devToken, setDevToken] = useState(token());
  const [error, setError] = useState("");
  const [agents, setAgents] = useState<AgentCard[]>([]);
  const [agent, setAgent] = useState("catalog-agent");
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

  function openChat(name: string) {
    setAgent(name);
    setView("chat");
  }

  function openSettings(name: string) {
    setAgent(name);
    setView("config");
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
          {NAV.filter((item) => item.id !== "plugins" && item.id !== "config" && item.id !== "docs").map((item) => (
            <button key={item.id} type="button" aria-current={view === item.id ? "page" : undefined} onClick={() => setView(item.id)}>
              {item.label}
              {item.id === "dashboard" || item.id === "library" ? <span className="count">{agents.length}</span> : null}
              {item.id === "approvals" ? <span className="count">{pending}</span> : null}
            </button>
          ))}
          <div className="nav-sep" />
          <div className="nav-tag">Manage</div>
          <button type="button" aria-current={view === "plugins" ? "page" : undefined} onClick={() => setView("plugins")}>Plugins</button>
          <button type="button" aria-current={view === "config" ? "page" : undefined} onClick={() => setView("config")}><GearIcon /> Configuration</button>
          <button type="button" aria-current={view === "docs" ? "page" : undefined} onClick={() => setView("docs")}>Docs</button>
        </nav>
        <div className="sidebar-user">
          <div className="user-circle" aria-hidden="true">LO</div>
          <div>
            <strong>Local operator</strong>
            <small>Local development</small>
          </div>
        </div>
        <details className="token-drawer">
          <summary>Access token</summary>
          <TextField
            aria-label="Access token"
            value={devToken}
            onChange={(value) => {
              setDevToken(value);
              setToken(value);
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
          {view === "dashboard" ? <DashboardView agents={agents} runs={history} onOpen={openChat} onOpenSettings={openSettings} onError={setError} /> : null}
          {view === "chat" ? (
            <ChatView agent={agent} agents={agents} onFinished={(run) => setHistory((current) => [run, ...current.filter((item) => item.id !== run.id)])} onError={setError} onOpenSettings={openSettings} />
          ) : null}
          {view === "library" ? <LibraryView agents={agents} onOpen={openChat} onOpenSettings={openSettings} /> : null}
          {view === "history" ? <HistoryView runs={history} onOpen={openChat} onOpenSettings={openSettings} /> : null}
          {view === "approvals" ? <div className="page-pad"><ApprovalsView onError={setError} onOpenSettings={openSettings} /></div> : null}
          {view === "plugins" ? <PluginsView onError={setError} /> : null}
          {view === "config" ? <ConfigCenter agent={agent} agents={agents} onSelect={setAgent} onOpenChat={openChat} onError={setError} /> : null}
          {view === "docs" ? <div className="page-pad"><DocsView onError={setError} /></div> : null}
        </div>
      </main>
    </div>
  );
}
