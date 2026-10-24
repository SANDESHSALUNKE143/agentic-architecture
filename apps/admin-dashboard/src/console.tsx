/** Purpose: re-exports the console screens. Each screen lives in src/views. Used by: App.tsx and config.tsx. */
export type { AgentCard, SessionRun } from "./labels";
export { initials, prettyName } from "./labels";
export { ChatView } from "./views/chat";
export { DashboardView } from "./views/dashboard";
export { HistoryView } from "./views/history";
export { LibraryView } from "./views/library";
