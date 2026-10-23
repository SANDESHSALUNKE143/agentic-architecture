import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/health": "http://127.0.0.1:8090",
      "/agents": "http://127.0.0.1:8090",
      "/agent-runs": {
        target: "http://127.0.0.1:8090",
        timeout: 0,
        proxyTimeout: 0,
      },
      "/approvals": "http://127.0.0.1:8090",
      "/tools": "http://127.0.0.1:8090",
      "/plugins": "http://127.0.0.1:8090",
      "/platform": "http://127.0.0.1:8090",
      "/guide": "http://127.0.0.1:8090",
      "/settings": "http://127.0.0.1:8090",
      "/memory": "http://127.0.0.1:8090",
    },
  },
});
