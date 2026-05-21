import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { ThemeProvider } from "./theme/ThemeProvider";
import { FormStoreProvider } from "./state/FormStore";
import "./theme/tokens.css";
import "./styles/global.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider>
      <FormStoreProvider>
        <App />
      </FormStoreProvider>
    </ThemeProvider>
  </React.StrictMode>,
);
