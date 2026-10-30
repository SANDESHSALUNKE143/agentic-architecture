/**
 * Purpose: the single-agent console. It proxies the run routes to 127.0.0.1:8092.
 * Used by: npm run dev.
 */
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5174,
    proxy: {
      "/health": "http://127.0.0.1:8092",
      "/settings": "http://127.0.0.1:8092",
      "/agent-runs": {
        target: "http://127.0.0.1:8092",
        timeout: 0,
        proxyTimeout: 0,
      },
    },
  },
});
