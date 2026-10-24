/** Purpose: decide whether a tool can be turned on for an agent. Used by: configuration and the plugins page. */
import type { EndpointConfig } from "./plugins";

export type ToolConnection = {
  name: string;
  permission: string;
  write: boolean;
  summary?: string;
  endpoint?: string;
  connection_ready?: boolean;
  connection_summary?: string;
  connection_url?: string;
  connection_string?: string;
};

export function connectionState(tool: ToolConnection, endpoints: EndpointConfig[]) {
  const host = tool.endpoint ? endpoints.find((item) => item.id === tool.endpoint) : undefined;
  if (tool.connection_ready === false) {
    return { ready: false, detail: tool.connection_summary || "Save the connection before this tool can be used." };
  }
  if (!tool.endpoint) {
    return { ready: true, detail: tool.connection_summary || "Runs in this process. No connection string." };
  }
  const ready = host ? host.configured : Boolean(tool.connection_ready);
  const title = host?.title || tool.endpoint;
  if (!ready) {
    return { ready: false, detail: `Save the ${title} connection on Plugins before this tool can be used.` };
  }
  const where = [host?.url, host?.connection_string].filter(Boolean).join(" · ");
  return { ready: true, detail: where ? `${title} is configured. ${where}` : `${title} is configured.` };
}

export function toolsForSave(names: string[], tools: ToolConnection[], endpoints: EndpointConfig[]) {
  return names.filter((name) => {
    const tool = tools.find((item) => item.name === name);
    if (!tool) return true;
    return connectionState(tool, endpoints).ready;
  });
}
