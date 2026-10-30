/**
 * Purpose: the Configuration page for the selected agent, including YAML download.
 * Used by: App.tsx. Saves go to PUT /settings/agents/{id}.
 */
import { useEffect, useState } from "react";
import { api, token } from "./api";
import { ConfigPanels } from "./config/panels";
import { AgentPicker } from "./config/pieces";
import type { Contract, ToolInfo } from "./config/types";
import { prettyName } from "./labels";
import type { EndpointConfig } from "./plugins";
import { toolsForSave } from "./tools";

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
          tools: toolsForSave(contract.tools, tools, endpoints),
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
          <ConfigPanels
            active={active}
            contract={contract}
            setContract={setContract}
            host={host}
            onError={onError}
            reloadEndpoints={reloadEndpoints}
            toggleTool={toggleTool}
            details={details}
            setDetails={setDetails}
            notesOn={notesOn}
            keySet={keySet}
            waiting={waiting}
            availableRecords={availableRecords}
            tools={tools}
            endpoints={endpoints}
          />
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
