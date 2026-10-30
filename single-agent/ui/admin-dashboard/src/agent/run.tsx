/** Purpose: brief desk-agent and show the answer. Used by App. */
import { TextArea } from "@agentic/controls";
import { useState } from "react";
import { streamRun } from "../stream";

type Run = {
  status?: string;
  reply?: string;
  result?: { explanation?: string; products?: unknown[]; available?: number };
  harness?: string;
};

export function AgentRun({ harness }: { harness: string }) {
  const [task, setTask] = useState("Find a blue trail jacket under $150");
  const [sessionId] = useState(() => `ses_${Math.random().toString(16).slice(2)}`);
  const [lines, setLines] = useState<string[]>([]);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    setError("");
    setLines([]);
    setAnswer("");
    setBusy(true);
    try {
      await streamRun(task, sessionId, (event) => {
        if (event.type === "activity" && typeof event.message === "string") {
          setLines((current) => [...current, event.message as string]);
        }
        if (event.type === "tool" && typeof event.tool === "string") {
          setLines((current) => [...current, `${event.tool}: ${event.status}`]);
        }
        if (event.type === "error" && typeof event.message === "string") setError(event.message);
        if (event.type === "done" && event.run) {
          const run = event.run as Run;
          const sentence = run.result?.explanation || run.reply || run.status || "";
          const stock = run.result?.available;
          setAnswer(stock === undefined ? sentence : `${sentence} Available: ${stock}.`);
        }
      });
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "The run failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <p>This run uses {harness || "the saved harness"}.</p>
      <TextArea label="Brief" value={task} onChange={setTask} />
      <button type="button" onClick={submit} disabled={busy}>
        {busy ? "Working" : "Send"}
      </button>
      {error ? <p>{error}</p> : null}
      <ul>
        {lines.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
      {answer ? <p>{answer}</p> : null}
    </section>
  );
}
