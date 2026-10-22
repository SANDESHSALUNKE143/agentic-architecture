import { useEffect, useState } from "react";
import { api, setToken, token } from "./api";
import { DocsView } from "./docs";
import { PluginsView } from "./plugins";
import { streamRun, type StreamEvent } from "./stream";

type View = "run" | "agents" | "plugins" | "approvals" | "settings" | "docs";

type AgentCard = { name: string; description: string; tools: string[] };
type ToolInfo = { name: string; permission: string; write: boolean };
type AgentStep = {
  agent_id: string;
  status: string;
  result: Record<string, unknown>;
  tool_calls: { name: string; status: string }[];
};
type TraceEvent = { stage: string; agent_id?: string; tool?: string; status?: string };
type Run = {
  request_id: string;
  workflow: string;
  status: string;
  error: string;
  approval_id: string;
  agents: AgentStep[];
  trace: TraceEvent[];
};
type Contract = {
  name: string;
  description: string;
  instructions: string[];
  tools: string[];
  memory: { conversation_state?: boolean; long_term_memory?: string };
  permissions: Record<string, boolean>;
  approval: { required_for?: string[]; amount_gte?: number };
};
type PlatformSettings = { mode: string; timeout_seconds: number; max_hops: number; model_api_key_set: boolean };
type Approval = { id: string; agent_id: string; tool: string; status: string; arguments: Record<string, unknown> };

const NAV: { id: View; label: string; detail: string }[] = [
  { id: "run", label: "Run", detail: "Choose who runs, then watch the work stream in." },
  { id: "agents", label: "Agents", detail: "Each specialist and the tools it may use." },
  { id: "plugins", label: "Plugins", detail: "Connect a tool to the agents allowed to call it." },
  { id: "approvals", label: "Approvals", detail: "Writes stay paused until an operator decides." },
  { id: "settings", label: "Settings", detail: "Platform limits and the agent contract." },
  { id: "docs", label: "Docs", detail: "The standard for building this platform." },
];

const EXAMPLES = [
  "Find a blue trail jacket under $150",
  "Place an order for the jacket at $129",
  "Refund order 1001",
  "Analyze the sales dataset",
];

const WORKFLOWS = [
  { id: "product-discovery", label: "Product discovery", detail: "Shopping, catalog, then inventory" },
  { id: "customer-support", label: "Customer support", detail: "Support, then billing" },
  { id: "order-processing", label: "Order processing", detail: "Order, then billing" },
];

const AGENT_TASKS: Record<string, string> = {
  "catalog-agent": "Find a blue trail jacket under $150",
  "shopping-agent": "Find a blue trail jacket under $150",
  "inventory-agent": "How many blue trail jackets are in stock?",
  "order-agent": "Place an order for the jacket at $129",
  "billing-agent": "What discount applies to the blue trail jacket?",
  "support-agent": "Refund order 1001",
  "data-analysis-agent": "Analyze the sales dataset",
  "research-agent": "What does the indexed document say about the jacket?",
};

type PlayRequest = { agents: string[]; task: string };

export function App() {
  const [view, setView] = useState<View>("run");
  const [devToken, setDevToken] = useState(token());
  const [error, setError] = useState("");
  const [play, setPlay] = useState<PlayRequest | null>(null);
  const current = NAV.find((item) => item.id === view)!;

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="mark" aria-hidden="true">AG</div>
          <div>
            <strong>Agentic</strong>
            <span>Operations</span>
          </div>
        </div>
        <nav aria-label="Sections">
          {NAV.map((item) => (
            <button key={item.id} aria-current={view === item.id ? "page" : undefined} onClick={() => setView(item.id)}>
              {item.label}
            </button>
          ))}
        </nav>
        <label className="session">
          <span>Access token</span>
          <input
            aria-label="Access token"
            value={devToken}
            onChange={(event) => {
              setDevToken(event.target.value);
              setToken(event.target.value);
            }}
          />
        </label>
      </aside>
      <main className="workspace">
        <header className="page-head">
          <h1>{current.label}</h1>
          <p>{current.detail}</p>
        </header>
        {error ? <p className="banner" role="alert">{error}</p> : null}
        {view === "run" ? <RunView onError={setError} play={play} /> : null}
        {view === "agents" ? <AgentsView onError={setError} onPlay={(agent) => { setPlay({ agents: [agent], task: AGENT_TASKS[agent] || EXAMPLES[0] }); setView("run"); }} /> : null}
        {view === "plugins" ? <PluginsView onError={setError} /> : null}
        {view === "approvals" ? <ApprovalsView onError={setError} /> : null}
        {view === "settings" ? <SettingsView onError={setError} /> : null}
        {view === "docs" ? <DocsView onError={setError} /> : null}
      </main>
    </div>
  );
}

function RunView({ onError, play }: { onError: (message: string) => void; play: PlayRequest | null }) {
  const [task, setTask] = useState(play?.task || EXAMPLES[0]);
  const [mode, setMode] = useState<"auto" | "workflow" | "agents">(play ? "agents" : "auto");
  const [workflow, setWorkflow] = useState(WORKFLOWS[0].id);
  const [chosen, setChosen] = useState<string[]>(play?.agents || []);
  const [agents, setAgents] = useState<AgentCard[]>([]);
  const [run, setRun] = useState<Run | null>(null);
  const [lines, setLines] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<AgentCard[]>("/agents").then(setAgents).catch((exc) => onError(readableError(exc)));
  }, [onError]);

  useEffect(() => {
    if (!play) return;
    setMode("agents");
    setChosen(play.agents);
    setTask(play.task);
  }, [play]);

  function toggleAgent(name: string) {
    setChosen((current) => current.includes(name) ? current.filter((item) => item !== name) : [...current, name]);
  }

  async function submit() {
    onError("");
    setRun(null);
    setLines([]);
    setBusy(true);
    const body: { task: string; workflow?: string; agents?: string[] } = { task };
    if (mode === "workflow") body.workflow = workflow;
    if (mode === "agents") body.agents = chosen;
    try {
      await streamRun(body, (event) => {
        const line = activityLine(event);
        if (line) setLines((current) => [...current, line]);
        if (event.type === "error" && event.message) onError(event.message);
        if (event.type === "done" && event.run) setRun(event.run);
      });
    } catch (exc) {
      onError(readableError(exc));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <section className="card">
        <header>
          <div>
            <p className="eyebrow">New task</p>
            <h2>Ask the platform</h2>
          </div>
        </header>
        <div className="body stack">
          <div className="segmented" role="tablist" aria-label="Who should run">
            <button type="button" aria-pressed={mode === "auto"} onClick={() => setMode("auto")}>Automatic</button>
            <button type="button" aria-pressed={mode === "workflow"} onClick={() => setMode("workflow")}>Workflow</button>
            <button type="button" aria-pressed={mode === "agents"} onClick={() => setMode("agents")}>Selected agents</button>
          </div>
          {mode === "auto" ? <p className="muted">The router picks a workflow from the wording of the task.</p> : null}
          {mode === "workflow" ? (
            <div className="check-grid">
              {WORKFLOWS.map((item) => (
                <label key={item.id}>
                  <input type="radio" name="workflow" checked={workflow === item.id} onChange={() => setWorkflow(item.id)} />
                  <span>{item.label}<br /><span className="muted">{item.detail}</span></span>
                </label>
              ))}
            </div>
          ) : null}
          {mode === "agents" ? (
            <div className="check-grid">
              {agents.map((agent) => (
                <label key={agent.name}>
                  <input type="checkbox" checked={chosen.includes(agent.name)} onChange={() => toggleAgent(agent.name)} />
                  {label(agent.name)}
                </label>
              ))}
            </div>
          ) : null}
          <label className="field">
            <span>Describe the work in plain language</span>
            <textarea value={task} onChange={(event) => setTask(event.target.value)} />
          </label>
          <div className="suggestions" aria-label="Examples">
            {EXAMPLES.map((example) => (
              <button key={example} className="chip" type="button" onClick={() => setTask(example)}>
                {example}
              </button>
            ))}
          </div>
        </div>
        <div className="foot">
          <button className="primary" type="button" onClick={submit} disabled={busy || !task.trim() || (mode === "agents" && chosen.length === 0)}>
            {busy ? "Running…" : "Run task"}
          </button>
        </div>
      </section>
      {lines.length ? (
        <section className="card">
          <header>
            <div>
              <p className="eyebrow">Live</p>
              <h2>{busy ? "Working" : "Progress"}</h2>
            </div>
            {busy ? <span className="badge pending">Streaming</span> : null}
          </header>
          <div className="body">
            <ol className="timeline live-feed">
              {lines.map((line, index) => <li key={index}><div>{line}</div></li>)}
            </ol>
          </div>
        </section>
      ) : null}
      {run ? <RunResult run={run} /> : null}
    </div>
  );
}

function activityLine(event: StreamEvent) {
  if (event.type === "activity") return event.message || "";
  if (event.type === "plan") return `Planned ${label(event.workflow || "request")}: ${(event.agents || []).map(label).join(", ")}`;
  if (event.type === "step" && event.status === "running") return `${label(event.agent_id || "agent")} started`;
  if (event.type === "step") return `${label(event.agent_id || "agent")} ${label(event.status || "finished")}`;
  if (event.type === "tool") return `${label(event.agent_id || "")} called ${label(event.tool || "tool")}${event.detail ? ` — ${event.detail}` : ""}`;
  if (event.type === "error") return event.message || "The run failed.";
  if (event.type === "done") return "The response is ready.";
  return "";
}

function RunResult({ run }: { run: Run }) {
  return (
    <div className="stack">
      <section className="card">
        <header>
          <div>
            <p className="eyebrow">Result</p>
            <h2>{label(run.workflow || "Request")}</h2>
            <p className="mono">{run.request_id}</p>
          </div>
          <Status value={run.status} />
        </header>
        <div className="body">
          {run.error ? <p className="banner">{run.error}</p> : null}
          <dl className="facts">
            <div>
              <dt>Workflow</dt>
              <dd>{run.workflow || "—"}</dd>
            </div>
            <div>
              <dt>Steps</dt>
              <dd>{run.agents.length}</dd>
            </div>
            <div>
              <dt>Approval</dt>
              <dd>{run.approval_id ? "Waiting" : "Not required"}</dd>
            </div>
          </dl>
        </div>
      </section>
      {run.agents.map((agent, index) => (
        <article key={`${agent.agent_id}-${index}`} className="card">
          <header>
            <div>
              <p className="eyebrow">Step {index + 1}</p>
              <h2>{label(agent.agent_id)}</h2>
            </div>
            <Status value={agent.status} />
          </header>
          <div className="body stack">
            <div className="tools">
              {agent.tool_calls.length ? agent.tool_calls.map((call) => (
                <span key={call.name} className="tool">{label(call.name)}</span>
              )) : <span className="muted">No tools called</span>}
            </div>
            <ResultBody result={agent.result} />
          </div>
        </article>
      ))}
      <section className="card">
        <header>
          <div>
            <p className="eyebrow">Activity</p>
            <h2>Trace</h2>
          </div>
        </header>
        <div className="body">
          <ol className="timeline">
            {run.trace.map((event, index) => (
              <li key={index}>
                <div>
                  <strong>{traceLabel(event.stage)}</strong>
                  <div className="muted">
                    {[event.agent_id, event.tool, event.status].filter((item): item is string => Boolean(item)).map(label).join(" · ")}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>
    </div>
  );
}

function AgentsView({ onError, onPlay }: { onError: (message: string) => void; onPlay: (agent: string) => void }) {
  const [agents, setAgents] = useState<AgentCard[] | null>(null);
  useEffect(() => {
    api<AgentCard[]>("/agents").then(setAgents).catch((exc) => onError(readableError(exc)));
  }, [onError]);
  if (!agents) return <p className="card empty">Loading agents…</p>;
  return (
    <section className="grid">
      {agents.map((agent) => (
        <article key={agent.name} className="card agent-card">
          <header>
            <h2>{label(agent.name)}</h2>
          </header>
          <div className="body stack">
            <p className="muted">{agent.description}</p>
            <div className="tools">
              {agent.tools.map((tool) => <span key={tool} className="tool">{label(tool)}</span>)}
            </div>
            <button className="secondary" type="button" onClick={() => onPlay(agent.name)}>Run this agent</button>
          </div>
        </article>
      ))}
    </section>
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
    <div className="stack">
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
  );
}

function SettingsView({ onError }: { onError: (message: string) => void }) {
  const [agents, setAgents] = useState<AgentCard[]>([]);
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [selected, setSelected] = useState("catalog-agent");
  const [contract, setContract] = useState<Contract | null>(null);
  const [platform, setPlatform] = useState<PlatformSettings | null>(null);
  const [saved, setSaved] = useState("");

  useEffect(() => {
    Promise.all([api<AgentCard[]>("/agents"), api<ToolInfo[]>("/tools"), api<PlatformSettings>("/settings/platform")])
      .then(([agentRows, toolRows, platformRow]) => {
        setAgents(agentRows);
        setTools(toolRows);
        setPlatform(platformRow);
      })
      .catch((exc) => onError(readableError(exc)));
  }, [onError]);

  useEffect(() => {
    setSaved("");
    api<Contract>(`/settings/agents/${selected}`).then(setContract).catch((exc) => onError(readableError(exc)));
  }, [selected, onError]);

  if (!contract || !platform) return <p className="card empty">Loading settings…</p>;
  const allowed = tools.filter((tool) => contract.permissions[tool.permission]);
  const writeNames = new Set(allowed.filter((tool) => tool.write).map((tool) => tool.name));

  function toggleTool(name: string) {
    const next = contract!.tools.includes(name) ? contract!.tools.filter((item) => item !== name) : [...contract!.tools, name];
    const required = new Set(contract!.approval.required_for || []);
    if (writeNames.has(name) && next.includes(name)) required.add(name);
    setContract({ ...contract!, tools: next, approval: { ...contract!.approval, required_for: [...required] } });
  }

  async function save() {
    onError("");
    setSaved("");
    try {
      const updated = await api<Contract>(`/settings/agents/${selected}`, {
        method: "PUT",
        body: JSON.stringify({
          instructions: contract!.instructions,
          tools: contract!.tools,
          memory: contract!.memory,
          approval: contract!.approval,
        }),
      });
      setContract(updated);
      setSaved("Saved. The API reloaded this contract.");
    } catch (exc) {
      onError(readableError(exc));
    }
  }

  return (
    <div className="stack">
      <section className="metrics" aria-label="Platform">
        <Metric label="Mode" value={platform.mode === "mock" ? "Mock" : "Live"} hint="No key required in mock mode" />
        <Metric label="Timeout" value={`${platform.timeout_seconds}s`} hint="Per agent step" />
        <Metric label="Max hops" value={String(platform.max_hops)} hint="Planner stops after this" />
        <Metric label="Model API key" value={platform.model_api_key_set ? "Configured" : "Not set"} hint="The key itself is never shown" />
      </section>
      <div className="split">
        <section className="card">
          <header>
            <div>
              <p className="eyebrow">Contract</p>
              <h2>{label(contract.name)}</h2>
            </div>
          </header>
          <div className="body stack">
            <label className="field">
              <span>Agent</span>
              <select value={selected} onChange={(event) => setSelected(event.target.value)}>
                {agents.map((agent) => (
                  <option key={agent.name} value={agent.name}>{label(agent.name)}</option>
                ))}
              </select>
            </label>
            <p className="muted">{contract.description}</p>
            <label className="field">
              <span>Instructions, one step per line</span>
              <textarea
                value={contract.instructions.join("\n")}
                onChange={(event) => setContract({ ...contract, instructions: event.target.value.split("\n").filter(Boolean) })}
              />
            </label>
            <div>
              <p className="eyebrow">Tools this agent may call</p>
              <div className="check-grid">
                {allowed.map((tool) => (
                  <label key={tool.name}>
                    <input type="checkbox" checked={contract.tools.includes(tool.name)} onChange={() => toggleTool(tool.name)} />
                    {label(tool.name)}
                  </label>
                ))}
              </div>
            </div>
          </div>
          <div className="foot">
            <button className="primary" type="button" onClick={save}>Save contract</button>
          </div>
        </section>
        <div className="stack">
          <section className="card">
            <header><h2>Memory</h2></header>
            <div className="body stack">
              <label className="switch">
                <input
                  type="checkbox"
                  checked={Boolean(contract.memory.conversation_state)}
                  onChange={(event) => setContract({ ...contract, memory: { ...contract.memory, conversation_state: event.target.checked } })}
                />
                Keep conversation state
              </label>
              <label className="field">
                <span>Long-term notes</span>
                <select
                  value={String(contract.memory.long_term_memory || "optional")}
                  onChange={(event) => setContract({ ...contract, memory: { ...contract.memory, long_term_memory: event.target.value } })}
                >
                  <option value="optional">May read saved notes</option>
                  <option value="false">Do not read notes</option>
                </select>
              </label>
            </div>
          </section>
          <section className="card">
            <header><h2>Approval</h2></header>
            <div className="body stack">
              {contract.approval.amount_gte !== undefined ? (
                <label className="field">
                  <span>Ask for approval when the amount is at least</span>
                  <input
                    type="number"
                    value={contract.approval.amount_gte}
                    onChange={(event) => setContract({ ...contract, approval: { ...contract.approval, amount_gte: Number(event.target.value) } })}
                  />
                </label>
              ) : <p className="muted">This agent has no amount threshold.</p>}
              {(contract.approval.required_for || []).length ? (
                <div className="check-grid">
                  {(contract.approval.required_for || []).map((tool) => (
                    <label key={tool}>
                      <input type="checkbox" checked disabled />
                      {label(tool)} stays behind approval
                    </label>
                  ))}
                </div>
              ) : <p className="muted">No write tools on this contract.</p>}
            </div>
          </section>
          {saved ? <p className="banner ok">{saved}</p> : null}
        </div>
      </div>
    </div>
  );
}

function Metric({ label: name, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <article className="card metric">
      <p className="eyebrow">{name}</p>
      <h2>{value}</h2>
      <p className="muted">{hint}</p>
    </article>
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
    load_instructions: "Loaded the contract",
    reason: "Chose the next step",
    tool: "Called a tool",
    persist: "Saved the result",
    product_id: "Product",
    order_id: "Order",
    mean_amount: "Mean amount",
  };
  if (known[value]) return known[value];
  return value.replaceAll("-", " ").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function traceLabel(stage: string) {
  return label(stage);
}

function readableError(exc: unknown) {
  const text = String(exc);
  if (text.includes("401")) return "The access token was rejected.";
  return text.replace(/^Error:\s*/, "");
}
