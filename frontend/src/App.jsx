import { useState } from "react";
import CallUI from "./call-ui/CallUI.jsx";
import SessionTrace from "./trace-viewer/SessionTrace.jsx";
import EvalDashboard from "./dashboard/EvalDashboard.jsx";

const TABS = [
  { id: "call", label: "Browser call demo", component: CallUI },
  { id: "trace", label: "Session trace", component: SessionTrace },
  { id: "evals", label: "Evaluation results", component: EvalDashboard },
];

export default function App() {
  const [tab, setTab] = useState("call");
  const Active = TABS.find((t) => t.id === tab).component;

  return (
    <div className="app-shell">
      <div className="header">
        <h1>WerkCall AI — Bilingual Voice Receptionist</h1>
        <span className="muted">NordWerk Haustechnik GmbH (demo)</span>
      </div>

      <div className="tabs">
        {TABS.map((t) => (
          <div key={t.id} className={`tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
            {t.label}
          </div>
        ))}
      </div>

      <Active />
    </div>
  );
}
