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
