import { useEffect, useState } from "react";
import { api, TOKEN_KEY, unwrap, type AgentRow, type ApprovalRow, type ExampleRow, type RunResponse } from "./api";

type View = "run" | "agents" | "approvals" | "trace" | "examples";

const VIEWS: { id: View; label: string }[] = [
  { id: "run", label: "Run" },
  { id: "agents", label: "Agents" },
  { id: "approvals", label: "Approvals" },
  { id: "trace", label: "Trace" },
  { id: "examples", label: "Examples" },
];

export function App() {
  const [view, setView] = useState<View>("run");
  const [run, setRun] = useState<RunResponse | null>(null);
  const [error, setError] = useState("");

  function open(next: RunResponse) {
    const unwrapped = unwrap(next);
    setRun(unwrapped);
    setView("trace");
    setError("");
  }

  return (
    <div className="shell">
      <nav>
        <strong>Agentic platform</strong>
        {VIEWS.map((item) => (
          <button key={item.id} className={view === item.id ? "active" : ""} onClick={() => setView(item.id)}>
            {item.label}
          </button>
        ))}
      </nav>
      <main>
        {error && <p className="error">{error}</p>}
        {view === "run" && <RunView onRun={open} onError={setError} />}
        {view === "agents" && <AgentsView onRun={open} onError={setError} />}
        {view === "approvals" && <ApprovalsView onRun={open} onError={setError} />}
        {view === "examples" && <ExamplesView onRun={open} onError={setError} />}
        {view === "trace" && <TraceView run={run} onRun={open} onError={setError} />}
      </main>
    </div>
  );
}

function RunView({ onRun, onError }: { onRun: (run: RunResponse) => void; onError: (message: string) => void }) {
  const [task, setTask] = useState("Find a jacket and check whether it is available");
  const [token, setToken] = useState(sessionStorage.getItem(TOKEN_KEY) || "local-dev-token-not-for-production");

  async function submit() {
    sessionStorage.setItem(TOKEN_KEY, token);
    try {
      onRun(await api.run({ task }));
    } catch (err) {
      onError(err instanceof Error ? err.message : "Run failed");
    }
  }

  return (
    <>
      <h1>Run a task</h1>
      <p className="lead">The router picks a workflow. The trace shows each agent, tool, and any stop.</p>
      <div className="panel">
        <label>Dev token</label>
        <input value={token} onChange={(event) => setToken(event.target.value)} />
        <label>Task</label>
        <textarea rows={4} value={task} onChange={(event) => setTask(event.target.value)} />
        <div className="row">
          <button className="primary" onClick={submit}>Run</button>
        </div>
      </div>
    </>
  );
}

function AgentsView({ onRun, onError }: { onRun: (run: RunResponse) => void; onError: (message: string) => void }) {
  const [agents, setAgents] = useState<AgentRow[]>([]);
  useEffect(() => {
    api.agents().then((body) => setAgents(body.agents)).catch((err) => onError(String(err)));
  }, [onError]);

  return (
    <>
      <h1>Agents</h1>
      <p className="lead">{agents.length} specialists. A run uses only that agent's tools.</p>
      <div className="grid">
        {agents.map((agent) => (
          <article className="card" key={agent.id}>
            <strong>{agent.display_name}</strong>
            <p>{agent.description}</p>
            <p>Tools: {agent.allowed_tools.join(", ") || "none"}</p>
            <p>Approval: {agent.approval_policy}</p>
            <button
              className="ghost"
              onClick={() => api.run({ task: agent.sample_task, agents: [agent.id] }).then(onRun).catch((err) => onError(String(err)))}
            >
              Run sample
            </button>
          </article>
        ))}
      </div>
    </>
  );
}

function ApprovalsView({ onRun, onError }: { onRun: (run: RunResponse) => void; onError: (message: string) => void }) {
  const [rows, setRows] = useState<ApprovalRow[]>([]);

  function load() {
    api.approvals().then((body) => setRows(body.approvals)).catch((err) => onError(String(err)));
  }
  useEffect(load, [onError]);

  async function decide(id: string, decision: "approved" | "rejected") {
    try {
      onRun(await api.decide(id, decision));
      load();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Decision failed");
    }
  }

  return (
    <>
      <h1>Approvals</h1>
      <p className="lead">A human decision resumes the same run. The agent cannot approve itself.</p>
      {rows.length === 0 && <div className="panel">No pending approvals.</div>}
      {rows.map((row) => (
        <article className="panel" key={row.id}>
          <strong>{row.action}</strong>
          <p>{row.summary}</p>
          <p>{row.impact}</p>
          <div className="row">
            <button className="primary" onClick={() => decide(row.id, "approved")}>Approve</button>
            <button className="ghost" onClick={() => decide(row.id, "rejected")}>Reject</button>
          </div>
        </article>
      ))}
    </>
  );
}

function ExamplesView({ onRun, onError }: { onRun: (run: RunResponse) => void; onError: (message: string) => void }) {
  const [rows, setRows] = useState<ExampleRow[]>([]);
  useEffect(() => {
    api.examples().then((body) => setRows(body.examples)).catch((err) => onError(String(err)));
  }, [onError]);
  const groups = [...new Set(rows.map((row) => row.group))];

  return (
    <>
      <h1>Examples</h1>
      <p className="lead">Each button starts the scenario from the developer guide.</p>
      {groups.map((group) => (
        <section key={group}>
          <h2>{group}</h2>
          <div className="row">
            {rows.filter((row) => row.group === group).map((row) => (
              <button
                className="ghost"
                key={row.id}
                onClick={() => api.run({ example_id: row.id }).then(onRun).catch((err) => onError(String(err)))}
              >
                {row.title}
              </button>
            ))}
          </div>
        </section>
      ))}
    </>
  );
}

function TraceView({
  run,
  onRun,
  onError,
}: {
  run: RunResponse | null;
  onRun: (run: RunResponse) => void;
  onError: (message: string) => void;
}) {
  if (!run) return <div className="panel">No steps were recorded. Run a task first.</div>;
  const problems = run.errors || [];
  const showProblems = run.status !== "completed" || problems.length > 0;

  return (
    <>
      <h1>Trace</h1>
      <p className="lead">
        <span className={`pill ${run.status === "completed" ? "ok" : run.status === "needs_approval" ? "warn" : "bad"}`}>
          {run.status}
        </span>
        {run.workflow || run.selected_agent}
        {run.learned_from ? ` · learned_from ${run.learned_from}` : ""}
      </p>
      {showProblems && (
        <section className="panel bad">
          <h2>What went wrong</h2>
          {problems.length === 0 && <p>The run stopped. The timeline has the last step.</p>}
          {problems.map((event) => (
            <p key={event.sequence}>
              <strong>{event.error_code || event.status}</strong> · {event.stage}
              {event.agent_id ? ` · ${event.agent_id}` : ""}
              {event.tool_name ? ` · ${event.tool_name}` : ""}
              <br />
              {event.message}
            </p>
          ))}
        </section>
      )}
      <section className="panel">
        <h2>Result</h2>
        <p>{run.result?.summary}</p>
        {run.requires_qualified_review && <p>Qualified human review is required.</p>}
        {run.approval_id && (
          <div className="row">
            <button className="primary" onClick={() => api.decide(run.approval_id!, "approved").then(onRun).catch((err) => onError(String(err)))}>
              Approve
            </button>
            <button className="ghost" onClick={() => api.decide(run.approval_id!, "rejected").then(onRun).catch((err) => onError(String(err)))}>
              Reject
            </button>
          </div>
        )}
      </section>
      <section className="panel">
        <h2>Handoff</h2>
        <div className="hop">
          {(run.planned_agents || run.agents).map((agent) => (
            <span key={agent} className={run.agents.includes(agent) ? "ok" : ""}>{agent}</span>
          ))}
        </div>
      </section>
      <section className="panel">
        <h2>Timeline</h2>
        {(run.trace || []).length === 0 && <p>No steps were recorded.</p>}
        <ol className="timeline">
          {(run.trace || []).map((event) => (
            <li key={event.sequence} className={event.status}>
              <strong>{event.stage}</strong> {event.status}
              {event.agent_id ? ` · ${event.agent_id}` : ""}
              {event.tool_name ? ` · ${event.tool_name}` : ""}
              <div>{event.message}</div>
            </li>
          ))}
        </ol>
      </section>
      <section className="panel">
        <h2>Tools and citations</h2>
        {(run.tool_calls || []).map((call, index) => (
          <details key={`${call.name}-${index}`}>
            <summary>{call.name} · {call.ok ? "ok" : "stopped"}</summary>
            <pre><code>{JSON.stringify(call.result, null, 2)}</code></pre>
          </details>
        ))}
        {(run.citations || []).map((row) => (
          <p key={`${row.source_id}-${row.location}`}>{row.source_id} · {row.location}</p>
        ))}
        {run.request_id && (
          <button
            className="ghost"
            onClick={() => api.feedback(run.request_id, "jacket questions should start at catalog").catch((err) => onError(String(err)))}
          >
            Save feedback
          </button>
        )}
      </section>
    </>
  );
}
