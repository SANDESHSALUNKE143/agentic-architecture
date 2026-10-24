/** Purpose: counts of agents, pending approvals, and runs from this browser session. Used by: the console shell. */
import { GearButton } from "@agentic/controls";
import { useEffect, useState } from "react";
import { api } from "../api";
import { initials, prettyName, type AgentCard, type SessionRun } from "../labels";

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

