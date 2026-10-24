/** Purpose: one agent's chat, including the live whisper and the answer. Used by: the console shell. */
import { GearButton, TextArea } from "@agentic/controls";
import { useEffect, useRef, useState } from "react";
import { activityLine } from "../agent";
import { api } from "../api";
import { initials, prettyName, type AgentCard, type SessionRun } from "../labels";
import { answerOf, AnswerBody, sourcesOf } from "./chat-answer";
import { streamRun, type StreamEvent } from "../stream";

type ChatMessage = {
  id: number;
  role: "user" | "agent";
  text: string;
  whisper?: string;
  citation?: string[];
  open?: boolean;
  result?: Record<string, unknown>;
  tools?: string[];
  sources?: { id: string; count: number }[];
};

const PROMPTS: Record<string, [string, string]> = {
  "catalog-agent": ["Find a blue trail jacket under $150", "Compare the jackets you can see"],
  "shopping-agent": ["Find a blue trail jacket under $150", "Which jacket should I look at first?"],
  "inventory-agent": ["How many blue trail jackets are in stock?", "Is the trail jacket available?"],
  "order-agent": ["Place an order for the jacket at $129", "What does an order for the jacket require?"],
  "billing-agent": ["What discount applies to the blue trail jacket?", "Explain the charge for order 1001"],
  "support-agent": ["Refund order 1001", "What can you check before a refund?"],
  "data-analysis-agent": ["Analyze the sales dataset", "What stands out in the sales numbers?"],
  "research-agent": ["What does the indexed document say about the jacket?", "Cite the note you can retrieve"],
};

export function ChatView({
  agent,
  agents,
  onFinished,
  onError,
  onOpenSettings,
}: {
  agent: string;
  agents: AgentCard[];
  onFinished: (run: SessionRun) => void;
  onError: (message: string) => void;
  onOpenSettings: (agent: string) => void;
}) {
  const card = agents.find((item) => item.name === agent);
  const prompts = PROMPTS[agent] || ["What can you do?", "Show the sources you use"];
  const [task, setTask] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const threadEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages([]);
    setTask("");
  }, [agent]);

  useEffect(() => {
    threadEnd.current?.scrollIntoView({ block: "end" });
  }, [messages]);

  async function send(text: string) {
    const brief = text.trim();
    if (!brief || busy) return;
    onError("");
    setTask("");
    const userId = Date.now();
    const replyId = userId + 1;
    setMessages((current) => [
      ...current,
      { id: userId, role: "user", text: brief },
      { id: replyId, role: "agent", text: "", whisper: "The agent accepted the brief", citation: [], open: false },
    ]);
    setBusy(true);
    const citation: string[] = [];
    const tools: string[] = [];
    try {
      await streamRun({ task: brief, agents: [agent] }, (event) => {
        const line = activityLine(event);
        if (line) {
          citation.push(line);
          const steps = [...citation];
          setMessages((current) => current.map((item) => item.id === replyId ? { ...item, whisper: line, citation: steps, tools: [...tools] } : item));
        }
        if (event.type === "tool" && event.tool && !tools.includes(event.tool)) tools.push(event.tool);
        if (event.type === "error" && event.message) onError(event.message);
        if (event.type === "done" && event.run) finish(replyId, brief, event.run, citation, tools);
      });
    } catch (exc) {
      const message = String(exc).replace(/^Error:\s*/, "");
      onError(message);
      setMessages((current) => current.map((item) => item.id === replyId ? { ...item, text: message, whisper: "" } : item));
    } finally {
      setBusy(false);
    }
  }

  function finish(replyId: number, brief: string, run: NonNullable<StreamEvent["run"]>, citation: string[], tools: string[]) {
    const result = run.agents.at(-1)?.result || {};
    const answer = answerOf(result, run.error);
    const sources = sourcesOf(run);
    setMessages((current) => current.map((item) => item.id === replyId ? { ...item, text: answer, result, tools: [...tools], sources, whisper: "", citation: [...citation], open: false } : item));
    const status = run.approval_id ? "Needs approval" : prettyName(run.status || "completed");
    onFinished({ id: run.request_id, agent, task: brief, status, answer });
  }

  return (
    <div className="chat-column">
      <div className="chat-scroll">
        {messages.length === 0 ? (
          <div className="welcome">
            <div className="agent-hero">
              <div className="hero-icon" aria-hidden="true">{initials(agent)}</div>
              <div className="hero-copy">
                <p className="eyebrow">Agent workspace</p>
                <h2>{prettyName(agent)}</h2>
                <p>{card?.description || "Give this agent a goal and follow the work in the conversation."}</p>
              </div>
              <GearButton className="hero-settings" label={`Settings for ${prettyName(agent)}`} onClick={() => onOpenSettings(agent)} />
            </div>
            <div className="capability-row">
              {(card?.tools || []).map((tool) => <span className="chip" key={tool}>{prettyName(tool)}</span>)}
              <span className="chip">Citation stays closed</span>
              <span className="chip">Writes wait for approval</span>
            </div>
            <div className="section-label">Try asking</div>
            <div className="prompt-grid">
              {prompts.map((prompt) => (
                <button key={prompt} type="button" className="prompt-card" onClick={() => send(prompt)}>
                  <strong>{prompt}</strong>
                  <span>Send this brief to {prettyName(agent)}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="thread" aria-live="polite">
            <div className="thread-settings">
              <GearButton label={`Settings for ${prettyName(agent)}`} onClick={() => onOpenSettings(agent)} />
            </div>
            {messages.map((message) => (
              <article key={message.id} className={`turn ${message.role}`}>
                {message.role === "user" ? <div className="user-pill">{message.text}</div> : (
                  <div className="assistant">
                    {message.whisper ? <p className="whisper">{message.whisper}</p> : <AnswerBody text={message.text} result={message.result} />}
                    {!message.whisper && (message.tools?.length || message.sources?.length) ? (
                      <p className="used-line">
                        {message.tools?.length ? `Used ${message.tools.map(prettyName).join(", ")}` : ""}
                        {message.tools?.length && message.sources?.length ? " · " : ""}
                        {message.sources?.length ? `${message.sources.length} source${message.sources.length === 1 ? "" : "s"}` : ""}
                      </p>
                    ) : null}
                    {message.citation && message.citation.length > 0 && !message.whisper ? (
                      <p>
                        <button type="button" className="citation-toggle" aria-expanded={message.open ? "true" : "false"} onClick={() => setMessages((current) => current.map((item) => item.id === message.id ? { ...item, open: !item.open } : item))}>
                          Citation · {message.citation.length} steps
                        </button>
                      </p>
                    ) : null}
                    {message.open && message.citation ? (
                      <ol className="citation">
                        {message.citation.map((line, index) => <li key={`${message.id}-${index}`}><span>{index + 1}</span>{line}</li>)}
                      </ol>
                    ) : null}
                  </div>
                )}
              </article>
            ))}
            <div ref={threadEnd} />
          </div>
        )}
      </div>
      <div className="composer-wrap">
        <form className="composer" onSubmit={(event) => { event.preventDefault(); send(task); }}>
          <TextArea aria-label="Brief" value={task} placeholder={`Brief ${prettyName(agent)}`} onChange={setTask} />
          <div className="composer-bottom">
            <button className="send-btn" type="submit" disabled={busy || !task.trim()} aria-label={busy ? "Working" : "Send"}>{busy ? "…" : "↑"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

