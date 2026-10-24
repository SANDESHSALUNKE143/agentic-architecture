/** Purpose: names and initials shared by every console screen. Used by: the views and the shell. */
export type AgentCard = { name: string; description: string; tools: string[] };

export type SessionRun = {
  id: string;
  agent: string;
  task: string;
  status: string;
  answer: string;
};

export function prettyName(value: string) {
  return value.replaceAll("-", " ").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function initials(name: string) {
  return name.replace(/-agent$/, "").split("-").slice(0, 2).map((part) => part[0]?.toUpperCase() || "").join("");
}
