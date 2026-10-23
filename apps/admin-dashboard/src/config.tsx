import { Checkbox, NumberField, RadioGroup, Select, TextArea, TextField } from "@agentic/controls";
import { useEffect, useRef, useState } from "react";
import { api, token } from "./api";
import { initials, prettyName } from "./console";
import { EndpointForm, type EndpointConfig } from "./plugins";

type Contract = {
  name: string;
  description: string;
  instructions: string[];
  tools: string[];
  memory: { conversation_state?: boolean; long_term_memory?: string | boolean; notes?: string[] };
  permissions: Record<string, boolean>;
  approval: { required_for?: string[]; amount_gte?: number };
  observability: string[];
  rag: { retrieve: boolean; capture: boolean; vector: string; embedding: string; cadence?: string };
  model: { provider: string };
};

type ToolInfo = { name: string; permission: string; write: boolean; summary: string };

type Platform = {
  model_api_key_set: boolean;
  observability: { id: string; title: string; summary: string; configured: boolean }[];
};

type AgentChoice = { name: string; description: string };

const REMOTE_RECORDS = [
  { id: "otlp", title: "OpenTelemetry" },
  { id: "log_store", title: "Log store" },
  { id: "grafana", title: "Grafana" },
];

const RECORD_HOST: Record<string, string> = { otlp: "otlp", log_store: "log_store", grafana: "grafana" };

export function ConfigCenter({
  agent,
  agents,
  onSelect,
  onOpenChat,
  onError,
}: {
  agent: string;
  agents: AgentChoice[];
  onSelect: (agent: string) => void;
  onOpenChat: (agent: string) => void;
  onError: (message: string) => void;
}) {
  const [contract, setContract] = useState<Contract | null>(null);
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [endpoints, setEndpoints] = useState<EndpointConfig[]>([]);
  const [keySet, setKeySet] = useState(false);
  const [page, setPage] = useState("prompt");
  const [saved, setSaved] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    Promise.all([
      api<ToolInfo[]>("/tools"),
      api<EndpointConfig[]>("/settings/connections"),
      api<Platform>("/settings/platform"),
    ]).then(([toolRows, endpointRows, platform]) => {
      setTools(toolRows);
      setEndpoints(endpointRows);
      setKeySet(platform.model_api_key_set);
    }).catch((exc) => onError(String(exc).replace(/^Error:\s*/, "")));
  }, [onError]);

  useEffect(() => {
    let current = true;
    setContract(null);
    setSaved("");
    api<Contract>(`/settings/agents/${agent}`)
      .then((row) => {
        if (current) setContract(row);
      })
      .catch((exc) => {
        if (current) onError(String(exc).replace(/^Error:\s*/, ""));
      });
    return () => {
      current = false;
    };
  }, [agent, onError]);

  async function reloadEndpoints() {
    setEndpoints(await api<EndpointConfig[]>("/settings/connections"));
  }

  async function save() {
    if (!contract) return false;
    setBusy(true);
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
      setSaved("Saved for this agent.");
      return true;
    } catch (exc) {
      onError(String(exc).replace(/^Error:\s*/, ""));
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function generate() {
    const ok = await save();
    if (!ok) return;
    const response = await fetch(`/settings/agents/${agent}/file`, { headers: { Authorization: `Bearer ${token()}` } });
    if (!response.ok) {
      onError(await response.text());
      return;
    }
    const blob = new Blob([await response.text()], { type: "text/yaml" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${agent}.yaml`;
    link.click();
    URL.revokeObjectURL(url);
    setSaved("Agent file generated.");
  }

  if (!contract) return <div className="config-view"><p>Loading this agent…</p></div>;

  const notesOn = String(contract.memory.long_term_memory || "optional") !== "false";
  const details = Array.isArray(contract.memory.notes) ? contract.memory.notes.map(String) : [];
  const host = (id: string) => endpoints.find((item) => item.id === id);
  const allowed = tools.filter((tool) => contract.permissions[tool.permission]);
  const writes = new Set(allowed.filter((tool) => tool.write).map((tool) => tool.name));
  const waiting = contract.approval.required_for || [];
  const sqlAllowed = allowed.some((tool) => tool.name === "analyze_dataset");
  const availableRecords = REMOTE_RECORDS.filter((item) => !contract.observability.includes(item.id));
  const sections: [string, string][] = [
    ["prompt", "Prompt"],
    ["knowledge", "Knowledge base"],
    ["ingestion", "Ingestion"],
    ...(sqlAllowed ? [["sql", "SQL"] as [string, string]] : []),
    ["observability", "Observability"],
    ["notes", "Notes"],
    ["model", "Model"],
    ["tools", "Tools"],
    ["approval", "Approval"],
  ];
  const active = sections.some(([id]) => id === page) ? page : "prompt";

  function toggleTool(name: string) {
    const next = contract!.tools.includes(name) ? contract!.tools.filter((item) => item !== name) : [...contract!.tools, name];
    const required = new Set(waiting);
    if (writes.has(name) && next.includes(name)) required.add(name);
    setContract({ ...contract!, tools: next, approval: { ...contract!.approval, required_for: [...required] } });
  }

  function setDetails(next: string[]) {
    setContract({ ...contract!, memory: { ...contract!.memory, notes: next } });
  }

  return (
    <div className="config-view">
      <AgentPicker agents={agents} agent={agent} onSelect={onSelect} />
      <div className="agent-config-head">
        <div>
          <p className="eyebrow">Configuring</p>
          <h2>{prettyName(agent)}</h2>
          <p>{contract.description}</p>
        </div>
        <button type="button" className="text-button" onClick={() => onOpenChat(agent)}>Open chat</button>
      </div>

      <div className="agent-config">
        <nav className="config-tabs" aria-label="Configuration for this agent">
          {sections.map(([id, label]) => (
            <button key={id} type="button" className="config-tab" aria-current={active === id} onClick={() => setPage(id)}>{label}</button>
          ))}
        </nav>
        <div className="config-panel">
          {active === "prompt" ? (
            <section className="config-card">
              <h3>Prompt</h3>
              <TextArea label="One step per line. This is the prompt stored on the agent file." value={contract.instructions.join("\n")} onChange={(value) => setContract({ ...contract, instructions: value.split("\n").filter(Boolean) })} />
            </section>
          ) : null}

          {active === "knowledge" ? (
            <section className="config-card">
              <h3>Knowledge base</h3>
              <Checkbox label="Read the index" checked={contract.rag.retrieve} onChange={(retrieve) => setContract({ ...contract, rag: { ...contract.rag, retrieve } })} />
              <div className="config-fields">
                <Select
                  label="Where this agent stores vectors"
                  value={contract.rag.vector}
                  onChange={(vector) => setContract({ ...contract, rag: { ...contract.rag, vector } })}
                  options={[{ value: "local", label: "Local index" }, { value: "qdrant", label: "Qdrant" }, { value: "aws", label: "AWS" }]}
                />
                <Select
                  label="Embedding for this agent"
                  value={contract.rag.embedding}
                  onChange={(embedding) => setContract({ ...contract, rag: { ...contract.rag, embedding } })}
                  options={[{ value: "local", label: "Local embeddings" }, { value: "openai", label: "OpenAI-compatible" }, { value: "aws", label: "AWS" }]}
                />
              </div>
              {contract.rag.vector === "local" && contract.rag.embedding === "local" ? <p className="muted">This agent uses the index and embeddings in this process.</p> : null}
              {contract.rag.vector === "qdrant" ? <HostBlock endpoint={host("qdrant")} onSaved={reloadEndpoints} onError={onError} /> : null}
              {contract.rag.vector === "aws" ? <HostBlock endpoint={host("aws_vector")} onSaved={reloadEndpoints} onError={onError} /> : null}
              {contract.rag.embedding === "openai" || contract.rag.embedding === "aws" ? <HostBlock endpoint={host("embedding")} onSaved={reloadEndpoints} onError={onError} /> : null}
            </section>
          ) : null}

          {active === "ingestion" ? (
            <section className="config-card">
              <h3>Ingestion</h3>
              <Checkbox
                label="Write a redacted note back after a run"
                checked={contract.rag.capture}
                onChange={(capture) => setContract({
                  ...contract,
                  rag: {
                    ...contract.rag,
                    capture,
                    cadence: capture ? (contract.rag.cadence && contract.rag.cadence !== "off" ? contract.rag.cadence : "each_run") : "off",
                  },
                })}
              />
              {contract.rag.capture ? (
                <Select
                  label="How often"
                  value={contract.rag.cadence || "each_run"}
                  onChange={(cadence) => setContract({ ...contract, rag: { ...contract.rag, cadence } })}
                  options={[{ value: "each_run", label: "After each run" }, { value: "hourly", label: "Hourly" }, { value: "daily", label: "Daily" }]}
                />
              ) : <p>This agent does not write the knowledge base back.</p>}
              <p className="muted">After each run is what this process writes. Hourly and daily are stored on the agent file. There is no separate document pipeline.</p>
            </section>
          ) : null}

          {active === "sql" ? (
            <section className="config-card">
              <h3>SQL</h3>
              <Checkbox label="Read the dataset" checked={contract.tools.includes("analyze_dataset")} onChange={() => toggleTool("analyze_dataset")} />
              <p className="muted">Answers in this build come from the local sales fixture. The address below is this agent's database access.</p>
              {host("sql") ? <HostBlock endpoint={host("sql")} onSaved={reloadEndpoints} onError={onError} /> : null}
            </section>
          ) : null}

          {active === "observability" ? (
            <section className="config-card">
              <h3>Observability</h3>
              <p className="muted">Platform trace and evaluation stay in this process. A remote destination shows its URL, connection string, username, and password after you add it. An address does not mean traces are shipping.</p>
              {["platform_trace", "evaluation"].map((id) => (
                <Checkbox
                  key={id}
                  label={`${prettyName(id)} · in this process`}
                  checked={contract.observability.includes(id)}
                  onChange={(checked) => {
                    const next = checked ? [...contract.observability, id] : contract.observability.filter((item) => item !== id);
                    setContract({ ...contract, observability: next });
                  }}
                />
              ))}
              {contract.observability.filter((id) => RECORD_HOST[id]).map((id) => (
                <div key={id}>
                  <p>{prettyName(id)} for this agent.</p>
                  <HostBlock endpoint={host(RECORD_HOST[id])} onSaved={reloadEndpoints} onError={onError} />
                  <button type="button" className="text-button" onClick={() => setContract({ ...contract, observability: contract.observability.filter((item) => item !== id) })}>Remove {prettyName(id)}</button>
                </div>
              ))}
              {availableRecords.length ? (
                <Select
                  label="Add an observability destination"
                  value=""
                  placeholder="None"
                  onChange={(destination) => { if (destination) setContract({ ...contract, observability: [...contract.observability, destination] }); }}
                  options={availableRecords.map((item) => ({ value: item.id, label: item.title }))}
                />
              ) : null}
            </section>
          ) : null}

          {active === "notes" ? (
            <section className="config-card">
              <h3>Notes</h3>
              <Checkbox label="Keep this conversation" checked={Boolean(contract.memory.conversation_state)} onChange={(conversation_state) => setContract({ ...contract, memory: { ...contract.memory, conversation_state } })} />
              <Checkbox label="Read saved notes" checked={notesOn} onChange={(checked) => setContract({ ...contract, memory: { ...contract.memory, long_term_memory: checked ? "optional" : false } })} />
              <p className="muted">Add as many details as this agent file should keep. Each note is one block.</p>
              {details.map((note, index) => (
                <label key={index} className="ui-field">
                  <span>Note {index + 1}</span>
                  <TextArea value={note} onChange={(value) => setDetails(details.map((item, itemIndex) => itemIndex === index ? value : item))} />
                  <button type="button" className="text-button" onClick={() => setDetails(details.filter((_, itemIndex) => itemIndex !== index))}>Remove note {index + 1}</button>
                </label>
              ))}
              <button type="button" className="secondary" onClick={() => setDetails([...details, ""])}>Add a note</button>
            </section>
          ) : null}

          {active === "model" ? (
            <section className="config-card">
              <h3>Model</h3>
              <p className="muted">The choice belongs to this agent. The model key is reported as set or not set. This form has no key field.</p>
              <RadioGroup
                name="provider"
                value={contract.model.provider || "platform"}
                onChange={(provider) => setContract({ ...contract, model: { provider } })}
                options={[{ value: "platform", label: "Platform" }, { value: "openai", label: "OpenAI-compatible" }, { value: "aws", label: "AWS" }]}
              />
              <p>{keySet ? "Model key is set in the process environment." : "Model key is not set. Mock mode answers without one."}</p>
              {contract.model.provider !== "platform" && host("model") ? (
                <ModelHost endpoint={host("model")!} onSaved={reloadEndpoints} onError={onError} />
              ) : null}
            </section>
          ) : null}

          {active === "tools" ? (
            <section className="config-card">
              <h3>Tools</h3>
              <p className="muted">Only tools this contract is already allowed to call. A write stays behind approval. This page cannot grant a new permission.</p>
              <div className="check-grid">
                {allowed.map((tool) => (
                  <Checkbox key={tool.name} label={prettyName(tool.name)} checked={contract.tools.includes(tool.name)} onChange={() => toggleTool(tool.name)} />
                ))}
              </div>
            </section>
          ) : null}

          {active === "approval" ? (
            <section className="config-card">
              <h3>Approval</h3>
              {waiting.length === 0 && contract.approval.amount_gte === undefined ? <p>This agent has no write. Nothing waits for approval.</p> : null}
              {waiting.map((tool) => <p key={tool}>{prettyName(tool)} stays behind approval.</p>)}
              {contract.approval.amount_gte !== undefined ? (
                <NumberField label="Wait when the amount is at least" value={contract.approval.amount_gte} onChange={(amount_gte) => setContract({ ...contract, approval: { ...contract.approval, amount_gte } })} />
              ) : null}
            </section>
          ) : null}

          <div className="agent-config-save">
            {saved ? <p>{saved}</p> : null}
            <button className="secondary" type="button" onClick={generate} disabled={busy}>Generate YAML</button>
            <button className="primary" type="button" onClick={save} disabled={busy}>{busy ? "Saving…" : "Save this agent"}</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function AgentPicker({
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

function HostBlock({
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

function ModelHost({ endpoint, onSaved, onError }: { endpoint: EndpointConfig; onSaved: () => Promise<void>; onError: (message: string) => void }) {
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
