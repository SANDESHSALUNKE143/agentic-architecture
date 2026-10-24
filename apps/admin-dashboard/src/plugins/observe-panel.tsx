/** Purpose: choose which agents record one observability sink. Used by: the plugins page. */
import { Checkbox } from "@agentic/controls";
import { useState } from "react";
import { api } from "../api";
import type { ObservabilityTool } from "./types";
import { title } from "./title";

export function ObservePanel({
  tool,
  onClose,
  onSaved,
  onError,
}: {
  tool: ObservabilityTool;
  onClose: () => void;
  onSaved: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [chosen, setChosen] = useState<string[]>(tool.connected_agents);
  const [busy, setBusy] = useState(false);

  function toggle(agent: string) {
    setChosen((current) => current.includes(agent) ? current.filter((item) => item !== agent) : [...current, agent]);
  }

  async function save() {
    setBusy(true);
    onError("");
    try {
      await api("/settings/observability/" + tool.id, { method: "PUT", body: JSON.stringify({ agents: chosen }) });
      await onSaved();
      onClose();
    } catch (exc) {
      onError(String(exc).replace(/^Error:\s*/, ""));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card connect-panel" aria-label="Observability connection">
      <header>
        <div>
          <p className="eyebrow">Agent configuration</p>
          <h2>{tool.title}</h2>
        </div>
        <button className="secondary" type="button" onClick={onClose}>Close</button>
      </header>
      <div className="body stack">
        <p className="muted">{tool.detail} Saving writes this tool onto each selected agent contract.</p>
        <div className="check-grid">
          {tool.eligible_agents.map((agent) => (
            <Checkbox key={agent} label={title(agent)} checked={chosen.includes(agent)} onChange={() => toggle(agent)} />
          ))}
        </div>
      </div>
      <div className="foot">
        <button className="primary" type="button" onClick={save} disabled={busy}>
          {busy ? "Saving…" : "Save on agents"}
        </button>
      </div>
    </section>
  );
}

