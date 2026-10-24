/** Purpose: labels and the live activity line. Used by: the agent workspace, chat, and the run panel. */
import type { StreamEvent } from "../stream";
import type { FeedItem, Run } from "./types";

export function foldStep(items: FeedItem[], title: string): FeedItem[] {
  const nextId = items.reduce((max, item) => Math.max(max, item.id), 0) + 1;
  return [...items.map((item) => (item.answer ? item : { ...item, open: false })), { id: nextId, title, open: true }];
}

export function finishWithAnswer(items: FeedItem[], answer: string): FeedItem[] {
  const nextId = items.reduce((max, item) => Math.max(max, item.id), 0) + 1;
  return [...items.map((item) => ({ ...item, open: false })), { id: nextId, title: answer, open: true, answer: true }];
}

export function activityLine(event: StreamEvent) {
  if (event.type === "activity") return event.message || "";
  if (event.type === "plan") return `The planner chose ${(event.agents || []).map(label).join(", ")}`;
  if (event.type === "step" && event.status === "running") return `${label(event.agent_id || "The agent")} is working`;
  if (event.type === "step") return `${label(event.agent_id || "The agent")} ${label(event.status || "finished")}`;
  if (event.type === "tool") return `${label(event.agent_id || "The agent")} used ${label(event.tool || "a tool")}${event.detail ? ` — ${event.detail}` : ""}`;
  if (event.type === "error") return event.message || "The agent stopped.";
  return "";
}

export function readAnswer(run: Run) {
  if (run.error) return run.error;
  const result = run.agents.at(-1)?.result || {};
  if (typeof result.explanation === "string" && result.explanation.trim()) return result.explanation;
  const text = Object.entries(result).filter(([, value]) => typeof value === "string" && value).map(([key, value]) => `${label(key)}: ${value}`).join("\n");
  return text || "The agent answered.";
}

export function readTools(run: Run) {
  return [...new Set(run.agents.flatMap((agent) => agent.tool_calls.map((call) => call.name)))];
}

export function readSources(run: Run) {
  return run.agents.flatMap((agent) => {
    const sources = agent.result.sources;
    if (!Array.isArray(sources)) return [];
    return sources.map((item) => {
      if (typeof item === "string") return item;
      const source = item as { source_id?: string; location?: string };
      return [source.source_id, source.location].filter(Boolean).join(" · ");
    });
  }).filter(Boolean);
}

export function role(description: string) {
  const sentence = description.split(/(?<=\.)\s/)[0].replace(/\.$/, "");
  return sentence.length > 72 ? `${sentence.slice(0, 69)}…` : sentence;
}

export function label(value: string) {
  return value.replace(/[_-]+/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function readable(exc: unknown) {
  return String(exc).replace(/^Error:\s*/, "");
}
