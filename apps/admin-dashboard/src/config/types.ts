/** Purpose: the contract shape the configuration page edits. Used by: ConfigCenter and its tabs. */
export type Contract = {
  name: string;
  description: string;
  instructions: string[];
  tools: string[];
  memory: { conversation_state?: boolean; long_term_memory?: string | boolean; notes?: string[] };
  permissions: Record<string, boolean>;
  approval: { required_for?: string[]; amount_gte?: number };
  observability: string[];
  rag: { retrieve: boolean; capture: boolean; vector: string; embedding: string; cadence?: string };
  model: { provider: string };
};

export type ToolInfo = {
  name: string;
  permission: string;
  write: boolean;
  summary: string;
  endpoint?: string;
  connection_ready?: boolean;
  connection_summary?: string;
};
