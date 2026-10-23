import { Checkbox, NumberField, Select, TextArea } from "@agentic/controls";
import { useEffect, useState } from "react";
import { api } from "./api";
import { EndpointForm, type EndpointConfig } from "./plugins";
import { streamRun, type StreamEvent } from "./stream";

type AgentCard = { name: string; description: string; tools: string[] };
type ToolInfo = { name: string; permission: string; write: boolean };
type Contract = {
  name: string;
  description: string;
  instructions: string[];
  tools: string[];
  memory: { conversation_state?: boolean; long_term_memory?: string };
  permissions: Record<string, boolean>;
  approval: { required_for?: string[]; amount_gte?: number };
  observability: string[];
  rag: { retrieve: boolean; capture: boolean; vector: string; embedding: string };
  model: { provider: string };
};
type PlatformSettings = {
  observability: { id: string; title: string; summary: string; variable: string; configured: boolean }[];
  rag: { vector: RagOption[]; embedding: RagOption[]; model: RagOption[] };
};
type RagOption = { id: string; title: string; detail: string };
type Run = {
  status: string;
  error: string;
  approval_id: string;
  agents: { agent_id: string; status: string; result: Record<string, unknown>; tool_calls: { name: string; status: string }[] }[];
};

const SEQUENCES = [
  { id: "product-discovery", title: "Product discovery", steps: ["shopping-agent", "catalog-agent", "inventory-agent"] },
  { id: "customer-support", title: "Customer support", steps: ["support-agent", "billing-agent"] },
  { id: "order-processing", title: "Order processing", steps: ["order-agent", "billing-agent"] },
];

const BRIEFS: Record<string, string> = {
  "catalog-agent": "Find a blue trail jacket under $150",
  "shopping-agent": "Find a blue trail jacket under $150",
  "inventory-agent": "How many blue trail jackets are in stock?",
  "order-agent": "Place an order for the jacket at $129",
  "billing-agent": "What discount applies to the blue trail jacket?",
  "support-agent": "Refund order 1001",
  "data-analysis-agent": "Analyze the sales dataset",
  "research-agent": "What does the indexed document say about the jacket?",
};

const SECTIONS = [
  ["instructions", "Instructions"],
  ["memory", "Memory"],
  ["observability", "Observability"],
  ["retrieval", "Retrieval"],
  ["tools", "Tools"],
  ["workflows", "Workflows"],
] as const;

const SINK_HOST: Record<string, string> = { otlp: "otlp", log_store: "log_store", grafana: "grafana" };

export type FeedItem = { id: number; title: string; open: boolean; answer?: boolean };

export function foldStep(items: FeedItem[], title: string): FeedItem[] {
  const nextId = items.reduce((max, item) => Math.max(max, item.id), 0) + 1;
  return [...items.map((item) => (item.answer ? item : { ...item, open: false })), { id: nextId, title, open: true }];
}

export function finishWithAnswer(items: FeedItem[], answer: string): FeedItem[] {
  const nextId = items.reduce((max, item) => Math.max(max, item.id), 0) + 1;
  return [...items.map((item) => ({ ...item, open: false })), { id: nextId, title: answer, open: true, answer: true }];
}

export function activityLine(event: StreamEvent) {
  if (event.type === "activity") return event.message || "";
  if (event.type === "plan") return `The planner chose ${(event.agents || []).map(label).join(", ")}`;
  if (event.type === "step" && event.status === "running") return `${label(event.agent_id || "The agent")} is working`;
  if (event.type === "step") return `${label(event.agent_id || "The agent")} ${label(event.status || "finished")}`;
  if (event.type === "tool") return `${label(event.agent_id || "The agent")} used ${label(event.tool || "a tool")}${event.detail ? ` — ${event.detail}` : ""}`;
  if (event.type === "error") return event.message || "The agent stopped.";
  return "";
}

export function AgentWorkspace({
  agent,
  onAgent,
  mode,
  onMode,
  onError,
}: {
  agent: string;
  onAgent: (agent: string) => void;
  mode: "configure" | "run";
  onMode: (mode: "configure" | "run") => void;
  onError: (message: string) => void;
}) {
  const [agents, setAgents] = useState<AgentCard[]>([]);
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [platform, setPlatform] = useState<PlatformSettings | null>(null);
  const [endpoints, setEndpoints] = useState<EndpointConfig[]>([]);
  const [contract, setContract] = useState<Contract | null>(null);
  const [section, setSection] = useState<(typeof SECTIONS)[number][0]>("instructions");
  const [saved, setSaved] = useState("");
  const [situationOpen, setSituationOpen] = useState(true);
  const [snapshot, setSnapshot] = useState<RunSnapshot>({ status: "Ready", step: "Waiting for a brief", tools: [], approval: "Not required", sources: [] });

  useEffect(() => {
    Promise.all([
      api<AgentCard[]>("/agents"),
      api<ToolInfo[]>("/tools"),
      api<PlatformSettings>("/settings/platform"),
      api<EndpointConfig[]>("/settings/connections"),
    ])
      .then(([agentRows, toolRows, platformRow, endpointRows]) => {
        setAgents(agentRows);
        setTools(toolRows);
        setPlatform(platformRow);
        setEndpoints(endpointRows);
      })
      .catch((exc) => onError(readable(exc)));
  }, [onError]);

  useEffect(() => {
    setSaved("");
    setContract(null);
    api<Contract>(`/settings/agents/${agent}`).then(setContract).catch((exc) => onError(readable(exc)));
  }, [agent, onError]);

  const current = agents.find((item) => item.name === agent);

  async function save() {
    if (!contract) return;
    onError("");
    setSaved("");
    try {
      const updated = await api<Contract>(`/settings/agents/${agent}`, {
        method: "PUT",
        body: JSON.stringify({
          instructions: contract.instructions,
          tools: contract.tools,
          memory: contract.memory,
          approval: contract.approval,
          observability: contract.observability,
          rag: contract.rag,
          model: contract.model,
        }),
      });
      setContract(updated);
      setSaved("Saved. The API reloaded this contract.");
    } catch (exc) {
      onError(readable(exc));
    }
  }

  async function reloadEndpoints() {
    setEndpoints(await api<EndpointConfig[]>("/settings/connections"));
  }

  return (
    <div className={`agent-workspace${mode === "run" ? (situationOpen ? " with-situation" : " situation-closed") : ""}`}>
      <aside className="pane" aria-label="Agents">
        <div className="pane-head"><h2>Agents</h2></div>
        <div className="pane-scroll">
          {agents.map((item) => (
            <button key={item.name} type="button" className="row-button" aria-current={item.name === agent ? "true" : undefined} onClick={() => onAgent(item.name)}>
              <strong>{label(item.name)}</strong>
              <span className="role">{role(item.description)}</span>
            </button>
          ))}
        </div>
      </aside>
      <section className="pane">
        <div className="pane-head">
          <div>
            <p className="eyebrow">Agent</p>
            <h2>{label(agent)}</h2>
          </div>
          <div className="segmented" role="tablist" aria-label="Agent mode">
            <button type="button" aria-pressed={mode === "configure"} onClick={() => onMode("configure")}>Configure</button>
            <button type="button" aria-pressed={mode === "run"} onClick={() => onMode("run")}>Run</button>
          </div>
        </div>
        {mode === "configure" ? (
          contract && platform ? (
            <div className="configure">
              <nav className="section-rail" aria-label="Agent configuration">
                {SECTIONS.map(([id, title]) => (
                  <button key={id} type="button" className="row-button" aria-current={section === id ? "true" : undefined} onClick={() => setSection(id)}>{title}</button>
                ))}
              </nav>
              <div className="configure-main">
                <div className="pane-scroll stack">
                  <p className="muted">{contract.description}</p>
                  {section === "instructions" ? <Instructions contract={contract} onChange={setContract} /> : null}
                  {section === "memory" ? <Memory contract={contract} endpoints={endpoints} onChange={setContract} onSaved={reloadEndpoints} onError={onError} /> : null}
                  {section === "observability" ? <Observability contract={contract} platform={platform} endpoints={endpoints} onChange={setContract} onSaved={reloadEndpoints} onError={onError} /> : null}
                  {section === "retrieval" ? <Retrieval contract={contract} platform={platform} endpoints={endpoints} onChange={setContract} onSaved={reloadEndpoints} onError={onError} /> : null}
                  {section === "tools" ? <Tools contract={contract} tools={tools} onChange={setContract} /> : null}
                  {section === "workflows" ? <Workflows agent={agent} /> : null}
                  {saved ? <p className="banner ok">{saved}</p> : null}
                </div>
                {section !== "workflows" ? (
                  <div className="pane-foot">
                    <button className="primary" type="button" onClick={save}>Save contract</button>
                  </div>
                ) : null}
              </div>
            </div>
          ) : <p className="empty">Loading this agent…</p>
        ) : (
          <AgentRun agent={agent} brief={BRIEFS[agent] || ""} onError={onError} onSnapshot={setSnapshot} />
        )}
      </section>
      {mode === "run" ? (
        <SituationPanel open={situationOpen} onToggle={() => setSituationOpen((value) => !value)} {...snapshot} />
      ) : null}
    </div>
  );
}

function Instructions({ contract, onChange }: { contract: Contract; onChange: (contract: Contract) => void }) {
  return (
    <>
      <TextArea label="Instructions, one step per line" value={contract.instructions.join("\n")} onChange={(value) => onChange({ ...contract, instructions: value.split("\n").filter(Boolean) })} />
      <h3>Approval</h3>
      {contract.approval.amount_gte !== undefined ? (
        <NumberField label="Ask for approval when the amount is at least" value={contract.approval.amount_gte} onChange={(amount_gte) => onChange({ ...contract, approval: { ...contract.approval, amount_gte } })} />
      ) : <p className="muted">This agent has no amount threshold.</p>}
      {(contract.approval.required_for || []).length ? (
        <div className="check-grid">
          {(contract.approval.required_for || []).map((tool) => (
            <Checkbox key={tool} label={`${label(tool)} stays behind approval`} checked disabled />
          ))}
        </div>
      ) : <p className="muted">No write tools on this contract.</p>}
    </>
  );
}

function Memory({ contract, endpoints, onChange, onSaved, onError }: { contract: Contract; endpoints: EndpointConfig[]; onChange: (contract: Contract) => void; onSaved: () => Promise<void>; onError: (message: string) => void }) {
  const longTerm = String(contract.memory.long_term_memory || "optional") !== "false";
  const neo4j = endpoints.find((item) => item.id === "neo4j");
  return (
    <>
      <Checkbox label="Short-term memory keeps this conversation" checked={Boolean(contract.memory.conversation_state)} onChange={(conversation_state) => onChange({ ...contract, memory: { ...contract.memory, conversation_state } })} />
      <Select
        label="Long-term memory"
        value={String(contract.memory.long_term_memory || "optional")}
        onChange={(long_term_memory) => onChange({ ...contract, memory: { ...contract.memory, long_term_memory } })}
        options={[{ value: "optional", label: "May read saved notes" }, { value: "false", label: "Off" }]}
      />
      {longTerm ? (
        <>
          <p className="muted">Saved notes stay in this API process. The address is this agent's notes host. This build does not open a Neo4j session.</p>
          {neo4j ? <EndpointForm embedded endpoint={neo4j} onSaved={onSaved} onError={onError} /> : null}
        </>
      ) : <p className="muted">Long-term memory is off, so this agent does not read saved notes.</p>}
    </>
  );
}

function Observability({ contract, platform, endpoints, onChange, onSaved, onError }: { contract: Contract; platform: PlatformSettings; endpoints: EndpointConfig[]; onChange: (contract: Contract) => void; onSaved: () => Promise<void>; onError: (message: string) => void }) {
  return (
    <>
      <p className="muted">Choose what this agent records. Platform trace and evaluation stay in this process. OpenTelemetry, the log store, and Grafana open the address where the record is pushed. This reference still keeps the record here and does not send the raw question. A password is not shown again.</p>
      {(platform.observability || []).map((tool) => {
        const selected = contract.observability.includes(tool.id);
        const host = endpoints.find((item) => item.id === SINK_HOST[tool.id]);
        return (
          <div key={tool.id} className="stack">
            <Checkbox
              label={tool.title}
              checked={selected}
              onChange={() => {
                const next = selected ? contract.observability.filter((item) => item !== tool.id) : [...contract.observability, tool.id];
                onChange({ ...contract, observability: next });
              }}
            />
            {selected && host ? (
              <>
                <p className="muted">This address is for this agent. Saving it does not start shipping traces.</p>
                <EndpointForm embedded endpoint={host} onSaved={onSaved} onError={onError} />
              </>
            ) : null}
          </div>
        );
      })}
    </>
  );
}

function Retrieval({ contract, platform, endpoints, onChange, onSaved, onError }: { contract: Contract; platform: PlatformSettings; endpoints: EndpointConfig[]; onChange: (contract: Contract) => void; onSaved: () => Promise<void>; onError: (message: string) => void }) {
  const hosts = retrievalHosts(contract).map((id) => endpoints.find((item) => item.id === id)).filter((item): item is EndpointConfig => Boolean(item));
  return (
    <>
      <p className="muted">A host address appears only when this agent selects that store. A password is not shown again.</p>
      <Checkbox label="Read from the index" checked={Boolean(contract.rag?.retrieve)} onChange={(retrieve) => onChange({ ...contract, rag: { ...contract.rag, retrieve } })} />
      <Checkbox label="Capture this turn as a redacted note" checked={Boolean(contract.rag?.capture)} onChange={(capture) => onChange({ ...contract, rag: { ...contract.rag, capture } })} />
      <Choice label="Vector database" value={contract.rag?.vector || "local"} options={platform.rag?.vector || []} onChange={(vector) => onChange({ ...contract, rag: { ...contract.rag, vector } })} />
      <Choice label="Embedding model" value={contract.rag?.embedding || "local"} options={platform.rag?.embedding || []} onChange={(embedding) => onChange({ ...contract, rag: { ...contract.rag, embedding } })} />
      <Choice label="Chat model" value={contract.model?.provider || "platform"} options={platform.rag?.model || []} onChange={(provider) => onChange({ ...contract, model: { provider } })} />
      {hosts.map((endpoint) => (
        <EndpointForm key={endpoint.id} embedded endpoint={endpoint} onSaved={onSaved} onError={onError} />
      ))}
      {hosts.length === 0 ? <p className="muted">The index, the embedding, and the chat model stay in this process.</p> : null}
    </>
  );
}

function Tools({ contract, tools, onChange }: { contract: Contract; tools: ToolInfo[]; onChange: (contract: Contract) => void }) {
  const allowed = tools.filter((tool) => contract.permissions[tool.permission]);
  const writes = new Set(allowed.filter((tool) => tool.write).map((tool) => tool.name));
  function toggle(name: string) {
    const next = contract.tools.includes(name) ? contract.tools.filter((item) => item !== name) : [...contract.tools, name];
    const required = new Set(contract.approval.required_for || []);
    if (writes.has(name) && next.includes(name)) required.add(name);
    onChange({ ...contract, tools: next, approval: { ...contract.approval, required_for: [...required] } });
  }
  return (
    <>
      <p className="muted">These are the MCP tools this agent may call. A tool is listed only when the contract already has its permission. A write stays behind approval.</p>
      <div className="check-grid">
        {allowed.map((tool) => (
          <Checkbox key={tool.name} label={label(tool.name)} checked={contract.tools.includes(tool.name)} onChange={() => toggle(tool.name)} />
        ))}
      </div>
    </>
  );
}

function Workflows({ agent }: { agent: string }) {
  const mine = SEQUENCES.filter((item) => item.steps.includes(agent));
  if (!mine.length) return <p className="muted">This agent runs on its own. It is not a step in a workflow. The planner can still choose it from the brief.</p>;
  return (
    <>
      <p className="muted">The planner chooses one of these sequences from the brief. The order is the configuration.</p>
      {mine.map((item) => (
        <article key={item.id} className="collapse">
          <div className="body">
            <strong>{item.title}</strong>
            <ol>
              {item.steps.map((step, index) => <li key={step}>{index + 1}. {label(step)}</li>)}
            </ol>
          </div>
        </article>
      ))}
    </>
  );
}

type RunSnapshot = { status: string; step: string; tools: string[]; approval: string; sources: string[] };

function AgentRun({ agent, brief, onError, onSnapshot }: { agent: string; brief: string; onError: (message: string) => void; onSnapshot: (snapshot: RunSnapshot) => void }) {
  const [task, setTask] = useState(brief);
  const [items, setItems] = useState<FeedItem[]>([]);
  const [busy, setBusy] = useState(false);
  const picture = { current: idleSnapshot() };

  function publish(next: RunSnapshot) {
    picture.current = next;
    onSnapshot(next);
  }

  useEffect(() => {
    setTask(brief);
    setItems([]);
    publish(idleSnapshot());
  }, [agent, brief]);

  async function submit() {
    onError("");
    setItems([]);
    setBusy(true);
    publish({ status: "Working", step: "The agent accepted the brief", tools: [], approval: "Not required", sources: [] });
    const seen = new Set<string>();
    try {
      await streamRun({ task, agents: [agent] }, (event) => {
        const line = activityLine(event);
        if (line) {
          setItems((current) => foldStep(current, line));
          publish({ ...picture.current, step: line, status: "Working" });
        }
        if (event.type === "tool" && event.tool && !seen.has(event.tool)) {
          seen.add(event.tool);
          publish({ ...picture.current, tools: [...picture.current.tools, event.tool] });
        }
        if (event.type === "error" && event.message) onError(event.message);
        if (event.type === "done" && event.run) {
          const run = event.run as Run;
          setItems((current) => finishWithAnswer(current, readAnswer(run)));
          publish({
            status: label(run.status || "completed"),
            step: "The agent answered.",
            tools: readTools(run),
            approval: run.approval_id ? "Waiting" : "Not required",
            sources: readSources(run),
          });
        }
      });
    } catch (exc) {
      onError(readable(exc));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="pane-scroll stack">
        <TextArea label="What should the agent do?" value={task} onChange={setTask} />
        <CollapseFeed items={items} busy={busy} />
        {items.length === 0 ? <p className="muted">The agent whispers one step at a time. The answer appears when it finishes.</p> : null}
      </div>
      <div className="pane-foot">
        <button className="primary" type="button" onClick={submit} disabled={busy || !task.trim()}>{busy ? "The agent is working…" : "Run the agent"}</button>
      </div>
    </>
  );
}

function StatusLine({ label: name, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="eyebrow">{name}</p>
      <strong>{value}</strong>
    </div>
  );
}

function tallied(values: string[]) {
  const counts = new Map<string, number>();
  for (const value of values.filter(Boolean)) counts.set(value, (counts.get(value) || 0) + 1);
  return [...counts];
}

function idleSnapshot(): RunSnapshot {
  return { status: "Ready", step: "Waiting for a brief", tools: [], approval: "Not required", sources: [] };
}

export function CollapseFeed({ items, busy }: { items: FeedItem[]; busy?: boolean }) {
  const [citationOpen, setCitationOpen] = useState(false);
  const steps = items.filter((item) => !item.answer);
  const answer = items.find((item) => item.answer);
  const whisper = steps.at(-1);

  useEffect(() => {
    if (!items.length) setCitationOpen(false);
  }, [items.length]);

  return (
    <div className="session">
      {busy && whisper ? <p className="whisper">{whisper.title}</p> : null}
      {answer ? <p className="answer-text">{answer.title}</p> : null}
      {steps.length ? (
        <div>
          <button className="citation-toggle" type="button" aria-expanded={citationOpen} onClick={() => setCitationOpen((open) => !open)}>
            {citationOpen ? "Hide citation" : `Citation · ${steps.length} steps`}
          </button>
          {citationOpen ? (
            <ol className="citation">
              {steps.map((step, index) => <li key={step.id}><span>{index + 1}</span>{step.title}</li>)}
            </ol>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export function SituationPanel({
  open,
  onToggle,
  status,
  step,
  tools,
  approval,
  sources,
}: {
  open: boolean;
  onToggle: () => void;
  status: string;
  step: string;
  tools: string[];
  approval: string;
  sources: string[];
}) {
  if (!open) return <button type="button" className="situation-toggle pane" onClick={onToggle}>Situation</button>;
  return (
    <aside className="pane" aria-label="Situation">
      <div className="pane-head">
        <h2>Situation</h2>
        <button className="secondary" type="button" onClick={onToggle}>Collapse</button>
      </div>
      <div className="pane-scroll stack">
        <div className="situation-status">
          <StatusLine label="Status" value={status} />
          <StatusLine label="Approval" value={approval} />
        </div>
        <p className="muted">{step}</p>
        <div>
          <p className="eyebrow">Tools</p>
          <div className="tools">
            {tools.length ? tools.map((tool) => <span key={tool} className="tool">{label(tool)}</span>) : <span className="muted">None yet</span>}
          </div>
        </div>
        <div>
          <p className="eyebrow">Sources</p>
          <div className="tools">
            {tallied(sources).length ? tallied(sources).map(([source, count]) => (
              <span key={source} className="tool mono">{source}{count > 1 ? ` × ${count}` : ""}</span>
            )) : <span className="muted">None yet</span>}
          </div>
        </div>
      </div>
    </aside>
  );
}

function Choice({ label: name, value, options, onChange }: { label: string; value: string; options: RagOption[]; onChange: (value: string) => void }) {
  const current = options.find((option) => option.id === value);
  return (
    <Select
      label={name}
      value={value}
      hint={current?.detail}
      onChange={onChange}
      options={options.map((option) => ({ value: option.id, label: option.title }))}
    />
  );
}

function retrievalHosts(contract: Contract) {
  const ids: string[] = [];
  if (contract.rag?.vector === "qdrant") ids.push("qdrant");
  if (contract.rag?.vector === "aws") ids.push("aws_vector");
  if (contract.rag?.embedding === "openai" || contract.rag?.embedding === "aws") ids.push("embedding");
  if (contract.model?.provider === "openai" || contract.model?.provider === "aws") ids.push("model");
  return ids;
}

function readAnswer(run: Run) {
  if (run.error) return run.error;
  const result = run.agents.at(-1)?.result || {};
  if (typeof result.explanation === "string" && result.explanation.trim()) return result.explanation;
  const text = Object.entries(result).filter(([, value]) => typeof value === "string" && value).map(([key, value]) => `${label(key)}: ${value}`).join("\n");
  return text || "The agent answered.";
}

function readTools(run: Run) {
  return [...new Set(run.agents.flatMap((agent) => agent.tool_calls.map((call) => call.name)))];
}

function readSources(run: Run) {
  return run.agents.flatMap((agent) => {
    const sources = agent.result.sources;
    if (!Array.isArray(sources)) return [];
    return sources.map((item) => {
      if (typeof item === "string") return item;
      const source = item as { source_id?: string; location?: string };
      return [source.source_id, source.location].filter(Boolean).join(" · ");
    });
  }).filter(Boolean);
}

function role(description: string) {
  const sentence = description.split(/(?<=\.)\s/)[0].replace(/\.$/, "");
  return sentence.length > 72 ? `${sentence.slice(0, 69)}…` : sentence;
}

function label(value: string) {
  return value.replace(/[_-]+/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function readable(exc: unknown) {
  return String(exc).replace(/^Error:\s*/, "");
}
