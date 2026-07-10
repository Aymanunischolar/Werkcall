import { useState, type ComponentType } from "react";
import CallUI from "./call-ui/CallUI.tsx";
import SessionTrace from "./trace-viewer/SessionTrace.tsx";
import EvalDashboard from "./dashboard/EvalDashboard.tsx";

interface Tab {
  id: string;
  label: string;
  component: ComponentType;
}

const TABS: Tab[] = [
  { id: "call", label: "Browser call demo", component: CallUI },
  { id: "trace", label: "Session trace", component: SessionTrace },
  { id: "evals", label: "Evaluation results", component: EvalDashboard },
];

export default function App() {
  const [tab, setTab] = useState("call");
  const Active = TABS.find((t) => t.id === tab)!.component;

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
