/**
 * Purpose: mount the console on the page.
 * Used by: the Vite entry in index.html. It loads the controls stylesheet and App.
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "@agentic/controls/controls.css";
import "./styles.css";
import "./ui/library.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
