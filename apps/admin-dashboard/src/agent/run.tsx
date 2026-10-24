/** Purpose: brief one agent and show the live steps. Used by: the agent workspace. */
import { TextArea } from "@agentic/controls";
import { useEffect, useState } from "react";
import { streamRun } from "../stream";
import { activityLine, finishWithAnswer, foldStep, label, readAnswer, readSources, readTools, readable } from "./text";
import type { FeedItem, Run, RunSnapshot } from "./types";

export function AgentRun({ agent, brief, onError, onSnapshot }: { agent: string; brief: string; onError: (message: string) => void; onSnapshot: (snapshot: RunSnapshot) => void }) {
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

export function StatusLine({ label: name, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="eyebrow">{name}</p>
      <strong>{value}</strong>
    </div>
  );
}

export function tallied(values: string[]) {
  const counts = new Map<string, number>();
  for (const value of values.filter(Boolean)) counts.set(value, (counts.get(value) || 0) + 1);
  return [...counts];
}

export function idleSnapshot(): RunSnapshot {
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
