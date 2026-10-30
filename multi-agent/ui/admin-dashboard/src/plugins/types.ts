/** Purpose: the plugin and connector shapes returned by GET /plugins. Used by: the plugin panels. */
export type Plugin = {
  name: string;
  group: string;
  summary: string;
  permission: string;
  write: boolean;
  endpoint: string;
  mcp_purpose: string;
  mcp_server_id: string;
  mcp_server_title: string;
  mcp_password_set: boolean;
  connection_ready: boolean;
  connection_summary: string;
  connection_url: string;
  connection_string: string;
  source: string;
  connected_agents: string[];
  eligible_agents: string[];
};

export type Connection = {
  id: string;
  title: string;
  variable: string;
  configured: boolean;
  detail: string;
};

export type Catalog = {
  plugins: Plugin[];
  connections: Connection[];
  observability: ObservabilityTool[];
  rag: { vector: RagChoice[]; embedding: RagChoice[]; model: RagChoice[] };
  endpoints: EndpointConfig[];
  mcp_servers: McpServer[];
};

export type McpServer = {
  id: string;
  title: string;
  purpose: string;
  url: string;
  username: string;
  password_set: boolean;
  configured: boolean;
  check_status: string;
  check_detail: string;
};

export type EndpointConfig = {
  id: string;
  title: string;
  group: string;
  summary: string;
  url: string;
  connection_string: string;
  username: string;
  password_set: boolean;
  configured: boolean;
};

export type RagChoice = ObservabilityTool & { kind: string };

export type ObservabilityTool = {
  id: string;
  title: string;
  summary: string;
  variable: string;
  configured: boolean;
  detail: string;
  connected_agents: string[];
  eligible_agents: string[];
};
