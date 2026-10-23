import { GearButton, TextArea } from "@agentic/controls";
import { useEffect, useRef, useState } from "react";
import { activityLine } from "./agent";
import { api } from "./api";
import { streamRun, type StreamEvent } from "./stream";

export type AgentCard = { name: string; description: string; tools: string[] };

export type SessionRun = {
  id: string;
  agent: string;
  task: string;
  status: string;
  answer: string;
};

type ChatMessage = {
  id: number;
  role: "user" | "agent";
  text: string;
  whisper?: string;
  citation?: string[];
  open?: boolean;
  result?: Record<string, unknown>;
  tools?: string[];
  sources?: { id: string; count: number }[];
};

const PROMPTS: Record<string, [string, string]> = {
  "catalog-agent": ["Find a blue trail jacket under $150", "Compare the jackets you can see"],
  "shopping-agent": ["Find a blue trail jacket under $150", "Which jacket should I look at first?"],
  "inventory-agent": ["How many blue trail jackets are in stock?", "Is the trail jacket available?"],
  "order-agent": ["Place an order for the jacket at $129", "What does an order for the jacket require?"],
  "billing-agent": ["What discount applies to the blue trail jacket?", "Explain the charge for order 1001"],
  "support-agent": ["Refund order 1001", "What can you check before a refund?"],
  "data-analysis-agent": ["Analyze the sales dataset", "What stands out in the sales numbers?"],
  "research-agent": ["What does the indexed document say about the jacket?", "Cite the note you can retrieve"],
};

export function prettyName(value: string) {
  return value.replaceAll("-", " ").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function initials(name: string) {
  return name.replace(/-agent$/, "").split("-").slice(0, 2).map((part) => part[0]?.toUpperCase() || "").join("");
}

export function ChatView({
  agent,
  agents,
  onFinished,
  onError,
  onOpenSettings,
}: {
  agent: string;
  agents: AgentCard[];
  onFinished: (run: SessionRun) => void;
  onError: (message: string) => void;
  onOpenSettings: (agent: string) => void;
}) {
  const card = agents.find((item) => item.name === agent);
  const prompts = PROMPTS[agent] || ["What can you do?", "Show the sources you use"];
  const [task, setTask] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const threadEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages([]);
    setTask("");
  }, [agent]);

  useEffect(() => {
    threadEnd.current?.scrollIntoView({ block: "end" });
  }, [messages]);

  async function send(text: string) {
    const brief = text.trim();
    if (!brief || busy) return;
    onError("");
    setTask("");
    const userId = Date.now();
    const replyId = userId + 1;
    setMessages((current) => [
      ...current,
      { id: userId, role: "user", text: brief },
      { id: replyId, role: "agent", text: "", whisper: "The agent accepted the brief", citation: [], open: false },
    ]);
    setBusy(true);
    const citation: string[] = [];
    const tools: string[] = [];
    try {
      await streamRun({ task: brief, agents: [agent] }, (event) => {
        const line = activityLine(event);
        if (line) {
          citation.push(line);
          const steps = [...citation];
          setMessages((current) => current.map((item) => item.id === replyId ? { ...item, whisper: line, citation: steps, tools: [...tools] } : item));
        }
        if (event.type === "tool" && event.tool && !tools.includes(event.tool)) tools.push(event.tool);
        if (event.type === "error" && event.message) onError(event.message);
        if (event.type === "done" && event.run) finish(replyId, brief, event.run, citation, tools);
      });
    } catch (exc) {
      const message = String(exc).replace(/^Error:\s*/, "");
      onError(message);
      setMessages((current) => current.map((item) => item.id === replyId ? { ...item, text: message, whisper: "" } : item));
    } finally {
      setBusy(false);
    }
  }

  function finish(replyId: number, brief: string, run: NonNullable<StreamEvent["run"]>, citation: string[], tools: string[]) {
    const result = run.agents.at(-1)?.result || {};
    const answer = answerOf(result, run.error);
    const sources = sourcesOf(run);
    setMessages((current) => current.map((item) => item.id === replyId ? { ...item, text: answer, result, tools: [...tools], sources, whisper: "", citation: [...citation], open: false } : item));
    const status = run.approval_id ? "Needs approval" : prettyName(run.status || "completed");
    onFinished({ id: run.request_id, agent, task: brief, status, answer });
  }

  return (
    <div className="chat-column">
      <div className="chat-scroll">
        {messages.length === 0 ? (
          <div className="welcome">
            <div className="agent-hero">
              <div className="hero-icon" aria-hidden="true">{initials(agent)}</div>
              <div className="hero-copy">
                <p className="eyebrow">Agent workspace</p>
                <h2>{prettyName(agent)}</h2>
                <p>{card?.description || "Give this agent a goal and follow the work in the conversation."}</p>
              </div>
              <GearButton className="hero-settings" label={`Settings for ${prettyName(agent)}`} onClick={() => onOpenSettings(agent)} />
            </div>
            <div className="capability-row">
              {(card?.tools || []).map((tool) => <span className="chip" key={tool}>{prettyName(tool)}</span>)}
              <span className="chip">Citation stays closed</span>
              <span className="chip">Writes wait for approval</span>
            </div>
            <div className="section-label">Try asking</div>
            <div className="prompt-grid">
              {prompts.map((prompt) => (
                <button key={prompt} type="button" className="prompt-card" onClick={() => send(prompt)}>
                  <strong>{prompt}</strong>
                  <span>Send this brief to {prettyName(agent)}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="thread" aria-live="polite">
            <div className="thread-settings">
              <GearButton label={`Settings for ${prettyName(agent)}`} onClick={() => onOpenSettings(agent)} />
            </div>
            {messages.map((message) => (
              <article key={message.id} className={`turn ${message.role}`}>
                {message.role === "user" ? <div className="user-pill">{message.text}</div> : (
                  <div className="assistant">
                    {message.whisper ? <p className="whisper">{message.whisper}</p> : <AnswerBody text={message.text} result={message.result} />}
                    {!message.whisper && (message.tools?.length || message.sources?.length) ? (
                      <p className="used-line">
                        {message.tools?.length ? `Used ${message.tools.map(prettyName).join(", ")}` : ""}
                        {message.tools?.length && message.sources?.length ? " · " : ""}
                        {message.sources?.length ? `${message.sources.length} source${message.sources.length === 1 ? "" : "s"}` : ""}
                      </p>
                    ) : null}
                    {message.citation && message.citation.length > 0 && !message.whisper ? (
                      <p>
                        <button type="button" className="citation-toggle" aria-expanded={message.open ? "true" : "false"} onClick={() => setMessages((current) => current.map((item) => item.id === message.id ? { ...item, open: !item.open } : item))}>
                          Citation · {message.citation.length} steps
                        </button>
                      </p>
                    ) : null}
                    {message.open && message.citation ? (
                      <ol className="citation">
                        {message.citation.map((line, index) => <li key={`${message.id}-${index}`}><span>{index + 1}</span>{line}</li>)}
                      </ol>
                    ) : null}
                  </div>
                )}
              </article>
            ))}
            <div ref={threadEnd} />
          </div>
        )}
      </div>
      <div className="composer-wrap">
        <form className="composer" onSubmit={(event) => { event.preventDefault(); send(task); }}>
          <TextArea aria-label="Brief" value={task} placeholder={`Brief ${prettyName(agent)}`} onChange={setTask} />
          <div className="composer-bottom">
            <button className="send-btn" type="submit" disabled={busy || !task.trim()} aria-label={busy ? "Working" : "Send"}>{busy ? "…" : "↑"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function DashboardView({
  agents,
  runs,
  onOpen,
  onOpenSettings,
  onError,
}: {
  agents: AgentCard[];
  runs: SessionRun[];
  onOpen: (agent: string) => void;
  onOpenSettings: (agent: string) => void;
  onError: (message: string) => void;
}) {
  const [mode, setMode] = useState("mock");
  const [waiting, setWaiting] = useState<Record<string, number>>({});

  useEffect(() => {
    api<{ mode: string }>("/settings/platform")
      .then((settings) => setMode(settings.mode || "mock"))
      .catch((exc) => onError(String(exc).replace(/^Error:\s*/, "")));
    api<{ agent_id: string; status: string }[]>("/approvals")
      .then((rows) => {
        const counts: Record<string, number> = {};
        rows.filter((row) => row.status === "pending").forEach((row) => {
          counts[row.agent_id] = (counts[row.agent_id] || 0) + 1;
        });
        setWaiting(counts);
      })
      .catch((exc) => onError(String(exc).replace(/^Error:\s*/, "")));
  }, [onError]);

  const pending = Object.values(waiting).reduce((sum, count) => sum + count, 0);

  return (
    <div className="library-view">
      <div className="library-intro">
        <p className="eyebrow">Dashboard</p>
        <h2>All agents</h2>
        <p>Every contract loaded in this process. Open one to brief it.</p>
      </div>
      <div className="dashboard-metrics">
        <div className="metric"><span>Agents</span><strong>{agents.length}</strong></div>
        <div className="metric"><span>Pending approvals</span><strong>{pending}</strong></div>
        <div className="metric"><span>Runs this session</span><strong>{runs.length}</strong></div>
        <div className="metric"><span>Mode</span><strong>{prettyName(mode)}</strong></div>
      </div>
      <div className="table-scroll">
        <table className="config-table dashboard-table">
          <thead>
            <tr>
              <th>Agent</th>
              <th>Purpose</th>
              <th>Tools</th>
              <th>Last run</th>
              <th>Approval</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {agents.map((agent) => {
              const latest = runs.find((run) => run.agent === agent.name);
              return (
                <tr key={agent.name}>
                  <td>
                    <div className="agent-cell">
                      <span className="hero-icon" aria-hidden="true">{initials(agent.name)}</span>
                      <strong>{prettyName(agent.name)}</strong>
                    </div>
                  </td>
                  <td className="purpose">{agent.description}</td>
                  <td>{agent.tools.length}</td>
                  <td>{latest ? latest.status : "No run yet"}</td>
                  <td>{waiting[agent.name] ? `${waiting[agent.name]} waiting` : "Clear"}</td>
                  <td>
                    <div className="row-actions">
                      <button type="button" className="text-button" onClick={() => onOpen(agent.name)}>Open chat</button>
                      <GearButton label={`Settings for ${prettyName(agent.name)}`} onClick={() => onOpenSettings(agent.name)} />
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function LibraryView({ agents, onOpen, onOpenSettings }: { agents: AgentCard[]; onOpen: (agent: string) => void; onOpenSettings: (agent: string) => void }) {
  return (
    <div className="library-view">
      <div className="library-intro">
        <p className="eyebrow">Agent library</p>
        <h2>Choose the agent for the job</h2>
        <p>Names, descriptions, and tools come from the contracts this process loaded.</p>
      </div>
      <div className="library-grid">
        {agents.map((agent) => (
          <article key={agent.name} className="library-card">
            <div className="library-card-head">
              <div className="hero-icon" aria-hidden="true">{initials(agent.name)}</div>
              <GearButton label={`Settings for ${prettyName(agent.name)}`} onClick={() => onOpenSettings(agent.name)} />
            </div>
            <h3>{prettyName(agent.name)}</h3>
            <p>{agent.description}</p>
            <div className="capability-row">
              {agent.tools.map((tool) => <span className="chip" key={tool}>{prettyName(tool)}</span>)}
            </div>
            <button type="button" onClick={() => onOpen(agent.name)}>Open chat</button>
          </article>
        ))}
      </div>
    </div>
  );
}

export function HistoryView({ runs, onOpen, onOpenSettings }: { runs: SessionRun[]; onOpen: (agent: string) => void; onOpenSettings: (agent: string) => void }) {
  return (
    <div className="history-view">
      <p className="eyebrow">Run history</p>
      <h2>Runs from this browser session</h2>
      <p className="muted">This API can read a run by id while the process is up. It does not keep a run list.</p>
      {runs.length === 0 ? <p className="card empty">No runs yet. Send a brief from Agent chat.</p> : null}
      <div className="history-list">
        {runs.map((run) => (
          <article key={run.id} className="history-card">
            <p className="eyebrow">{prettyName(run.agent)}</p>
            <h3>{run.task}</h3>
            <p>{run.answer}</p>
            <p className="muted">{run.status} · {run.id}</p>
            <div className="row-actions">
              <button type="button" className="text-button" onClick={() => onOpen(run.agent)}>Open chat</button>
              <GearButton label={`Settings for ${prettyName(run.agent)}`} onClick={() => onOpenSettings(run.agent)} />
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function answerOf(result: Record<string, unknown>, error = "") {
  if (error) return error;
  const products = productRows(result);
  if (products.length === 1) {
    const product = products[0];
    return `${product.name} is ${money(product.price)}, with ${product.stock} in stock.`;
  }
  if (products.length > 1) {
    return products.map((product) => `${product.name} — ${money(product.price)}, ${product.stock} in stock`).join("\n");
  }
  if (typeof result.answer === "string" && result.answer.trim()) return result.answer;
  if (typeof result.explanation === "string" && result.explanation.trim()) return result.explanation;
  return "The agent answered.";
}

function productRows(result: Record<string, unknown>) {
  if (!Array.isArray(result.products)) return [];
  return result.products.map((item) => {
    const product = item as { product_id?: string; name?: string; price?: number; stock?: number };
    return {
      id: product.product_id || product.name || "product",
      name: product.name || product.product_id || "Product",
      price: product.price,
      stock: product.stock ?? "—",
    };
  });
}

function money(value: number | undefined) {
  return value === undefined ? "—" : `$${value}`;
}

function AnswerBody({ text, result }: { text: string; result?: Record<string, unknown> }) {
  const products = result ? productRows(result) : [];
  const explanation = typeof result?.explanation === "string" ? result.explanation : "";
  const scalars = result
    ? Object.entries(result).filter(([key, value]) => !["products", "sources", "explanation", "answer"].includes(key) && (typeof value === "string" || typeof value === "number" || typeof value === "boolean"))
    : [];
  return (
    <div className="answer-block">
      <p className="answer-text">{text}</p>
      {products.length ? (
        <table className="product-table">
          <thead><tr><th>Product</th><th>Price</th><th>Stock</th></tr></thead>
          <tbody>
            {products.map((product) => (
              <tr key={product.id}><td>{product.name}</td><td>{money(product.price)}</td><td>{product.stock}</td></tr>
            ))}
          </tbody>
        </table>
      ) : null}
      {explanation && explanation !== text ? <p className="muted">{explanation}</p> : null}
      {scalars.length ? (
        <dl className="result">
          {scalars.map(([key, value]) => (
            <div key={key}><dt>{prettyName(key)}</dt><dd>{String(value)}</dd></div>
          ))}
        </dl>
      ) : null}
    </div>
  );
}

function sourcesOf(run: NonNullable<StreamEvent["run"]>) {
  const counts = new Map<string, number>();
  for (const step of run.agents) {
    const value = step.result.sources;
    if (!Array.isArray(value)) continue;
    for (const item of value) {
      const id = typeof item === "string" ? item : String((item as { source_id?: string }).source_id || "");
      if (!id) continue;
      counts.set(id, (counts.get(id) || 0) + 1);
    }
  }
  return [...counts.entries()].map(([id, count]) => ({ id, count }));
}
