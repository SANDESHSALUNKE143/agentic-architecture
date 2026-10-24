/** Purpose: one agent's workspace. Sections, the run panel, and labels live beside this file. Used by: App.tsx. */
import { useEffect, useState } from "react";
import { api } from "./api";
import type { EndpointConfig } from "./plugins";
import { toolsForSave } from "./tools";
import { AgentRun, SituationPanel } from "./agent/run";
import { Instructions, Memory, Observability, Retrieval, Tools, Workflows } from "./agent/sections";
import { label, readable, role } from "./agent/text";
import { BRIEFS, SECTIONS, type AgentCard, type Contract, type PlatformSettings, type Sequence, type ToolInfo, type RunSnapshot } from "./agent/types";

export type { FeedItem } from "./agent/types";
export { activityLine, finishWithAnswer, foldStep } from "./agent/text";
export { CollapseFeed, SituationPanel } from "./agent/run";

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
  const [sequences, setSequences] = useState<Sequence[]>([]);
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
    api<{ workflows: Sequence[] }>("/platform")
      .then((platformMap) => setSequences(platformMap.workflows))
      .catch(() => setSequences([]));
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
          tools: toolsForSave(contract.tools, tools, endpoints),
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
                  {section === "tools" ? <Tools contract={contract} tools={tools} endpoints={endpoints} onChange={setContract} /> : null}
                  {section === "workflows" ? <Workflows agent={agent} sequences={sequences} /> : null}
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
