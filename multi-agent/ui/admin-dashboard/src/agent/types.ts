/** Purpose: the contract and run shapes for one agent screen. Used by: the agent workspace, its sections, and its run panel. */
export type AgentCard = { name: string; description: string; tools: string[]; examples?: string[] };
export type ToolInfo = { name: string; permission: string; write: boolean };
export type Contract = {
  name: string;
  description: string;
  instructions: string[];
  tools: string[];
  memory: { conversation_state?: boolean; long_term_memory?: string };
  permissions: Record<string, boolean>;
  approval: { required_for?: string[]; amount_gte?: number };
  observability: string[];
  rag: { retrieve: boolean; capture: boolean; vector: string; embedding: string };
  model: { provider: string };
};
export type PlatformSettings = {
  observability: { id: string; title: string; summary: string; variable: string; configured: boolean }[];
  rag: { vector: RagOption[]; embedding: RagOption[]; model: RagOption[] };
};
export type RagOption = { id: string; title: string; detail: string };
export type Run = {
  status: string;
  error: string;
  approval_id: string;
  agents: { agent_id: string; status: string; result: Record<string, unknown>; tool_calls: { name: string; status: string }[] }[];
};

export type Sequence = { id: string; agents: string[] };

export type FeedItem = { id: number; title: string; open: boolean; answer?: boolean };

export type RunSnapshot = { status: string; step: string; tools: string[]; approval: string; sources: string[] };

export const SECTIONS = [
  ["instructions", "Instructions"],
  ["memory", "Memory"],
  ["observability", "Observability"],
  ["retrieval", "Retrieval"],
  ["tools", "Tools"],
  ["workflows", "Workflows"],
] as const;
