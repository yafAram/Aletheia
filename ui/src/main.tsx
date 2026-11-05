import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import DesktopCompanion from "./desktop/DesktopCompanion";
import "./styles.css";

const root = ReactDOM.createRoot(document.getElementById("root")!);
const desktopMode = new URLSearchParams(window.location.search).get("desktop") === "1";

if (desktopMode) {
  void import("./desktop/desktop.css").then(() => root.render(
    <React.StrictMode><DesktopCompanion /></React.StrictMode>
  ));
} else {
  root.render(<React.StrictMode><App /></React.StrictMode>);
}
