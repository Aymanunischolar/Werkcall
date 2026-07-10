import { useState } from "react";
import type { EvaluationRunSummary } from "../types";

/**
 * Runs POST /api/evaluations/run and displays the measured completion rate
 * (detailed spec §17) — this is what turns the CV bullet from a claim into
 * a committed, reproducible measurement.
 */
export default function EvalDashboard() {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<EvaluationRunSummary | null>(null);

  const run = async () => {
    setRunning(true);
    try {
      const res = await fetch("/api/evaluations/run", { method: "POST" });
      setResult(await res.json());
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="panel">
      <button onClick={run} disabled={running}>
        {running ? "Running scenarios…" : "Run labelled evaluation scenarios"}
      </button>

      {result && (
        <>
          <div className="status-row" style={{ marginTop: 16 }}>
            <span className="badge state">
              {result.passed}/{result.scenario_count} passed ({Math.round(result.completion_rate * 100)}%)
            </span>
            <span className="badge">Model: {result.model}</span>
            <span className="badge">Run id: {result.run_id.slice(0, 8)}</span>
            <span className="badge">Run at: {result.date}</span>
          </div>
          <table className="dashboard-table">
            <thead>
              <tr>
                <th>Scenario</th>
                <th>Pass</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {result.results.map((r) => (
                <tr key={r.scenario_id}>
                  <td>{r.scenario_id}</td>
                  <td>{r.pass ? "✅" : "❌"}</td>
                  <td className="muted">{r.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
