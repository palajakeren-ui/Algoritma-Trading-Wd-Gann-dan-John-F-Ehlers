import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

// Use createRoot for concurrent rendering
const rootElement = document.getElementById("root")!;

// Pre-allocate root to avoid re-creation
createRoot(rootElement).render(<App />);
