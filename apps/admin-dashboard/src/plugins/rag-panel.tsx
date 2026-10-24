/** Purpose: choose which agents use one RAG vector or embedding. Used by: the plugins page. */
import { Checkbox } from "@agentic/controls";
import { useState } from "react";
import { api } from "../api";
import type { RagChoice } from "./types";
import { title } from "./title";

export function RagPanel({
  choice,
  onClose,
  onSaved,
  onError,
}: {
  choice: RagChoice;
  onClose: () => void;
  onSaved: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [chosen, setChosen] = useState<string[]>(choice.connected_agents);
  const [busy, setBusy] = useState(false);

  function toggle(agent: string) {
    setChosen((current) => current.includes(agent) ? current.filter((item) => item !== agent) : [...current, agent]);
  }

  async function save() {
    setBusy(true);
    onError("");
    try {
      await api(`/settings/rag/${choice.kind}/${choice.id}`, { method: "PUT", body: JSON.stringify({ agents: chosen }) });
      await onSaved();
      onClose();
    } catch (exc) {
      onError(String(exc).replace(/^Error:\s*/, ""));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card connect-panel" aria-label="RAG connection">
      <header>
        <div>
          <p className="eyebrow">Agent configuration</p>
          <h2>{choice.title}</h2>
        </div>
        <button className="secondary" type="button" onClick={onClose}>Close</button>
      </header>
      <div className="body stack">
        <p className="muted">{choice.detail} Saving sets this choice on the selected agent contracts.</p>
        <div className="check-grid">
          {choice.eligible_agents.map((agent) => (
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

