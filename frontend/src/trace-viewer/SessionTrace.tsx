import { useState } from "react";
import type { SessionDetail } from "../types";

/**
 * Trace viewer (detailed spec §5): fetch GET /api/sessions/{id} and show
 * transcript, tool calls, latency and outcome for recruiter inspection.
 */
export default function SessionTrace() {
  const [sessionId, setSessionId] = useState("");
  const [detail, setDetail] = useState<SessionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const lookup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setDetail(null);
    try {
      const res = await fetch(`/api/sessions/${sessionId}`);
      if (!res.ok) throw new Error(`session not found (${res.status})`);
      setDetail(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const deleteSession = async () => {
    await fetch(`/api/sessions/${sessionId}`, { method: "DELETE" });
    setDetail(null);
  };

  return (
    <div className="panel">
      <form className="composer" onSubmit={lookup}>
        <input value={sessionId} onChange={(e) => setSessionId(e.target.value)} placeholder="Paste a session id…" />
        <button type="submit">Load trace</button>
      </form>

      {error && <p className="muted">{error}</p>}

      {detail && (
        <>
          <div className="status-row">
            <span className="badge">Outcome: {detail.outcome}</span>
            <span className="badge state">State: {detail.state}</span>
            <span className="badge">Provider: {detail.model_provider}</span>
            <span className="badge">Language: {detail.language}</span>
          </div>

          <h3>Transcript</h3>
          <table className="dashboard-table">
            <thead>
              <tr>
                <th>Speaker</th>
                <th>Text (redacted)</th>
                <th>Latency (ms)</th>
              </tr>
            </thead>
            <tbody>
              {detail.turns.map((t, i) => (
                <tr key={i}>
                  <td>{t.speaker}</td>
                  <td>{t.redacted_text}</td>
                  <td>{t.latency_ms ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h3>Tool executions</h3>
          <table className="dashboard-table">
            <thead>
              <tr>
                <th>Tool</th>
                <th>Result</th>
                <th>Retries</th>
                <th>Duration (ms)</th>
              </tr>
            </thead>
            <tbody>
              {detail.tool_executions.map((t, i) => (
                <tr key={i}>
                  <td>{t.tool}</td>
                  <td>{t.result_code}</td>
                  <td>{t.retries}</td>
                  <td>{t.duration_ms}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <button className="danger" onClick={deleteSession}>
            Delete this session's data
          </button>
        </>
      )}
    </div>
  );
}
