import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css"; // global styles

// Mount React to the root div in index.html
const rootElement = document.getElementById("root");
const root = createRoot(rootElement);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
