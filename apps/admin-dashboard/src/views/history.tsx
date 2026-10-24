/** Purpose: runs started in this browser session. Used by: the console shell. */
import { GearButton } from "@agentic/controls";
import { prettyName, type SessionRun } from "../labels";

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
