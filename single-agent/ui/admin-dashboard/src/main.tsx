/** Purpose: mount the desk-agent chat. Used by index.html. */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "@agentic/controls/controls.css";

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}
