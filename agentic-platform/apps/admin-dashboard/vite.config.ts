import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const target = "http://127.0.0.1:8090";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/health": target,
      "/agents": target,
      "/agent-runs": target,
      "/approvals": target,
      "/tools": target,
      "/delegation": target,
      "/examples": target,
      "/memory": target,
      "/webhook": target,
    },
  },
});
