export default function ConsentModal({ language, onLanguageChange, onAccept }) {
  return (
    <div className="consent-overlay">
      <div className="consent-card">
        <h2>Before we start</h2>
        <p>
          You are about to speak with an <strong>AI voice assistant</strong> for NordWerk Haustechnik
          (a fictional demo company). This call may capture your microphone audio for real-time
          processing. No raw audio is stored by default, and this demo uses synthetic data only —
          please do not share real personal information.
        </p>
        <label className="muted">
          Language:{" "}
          <select value={language} onChange={(e) => onLanguageChange(e.target.value)}>
            <option value="de">Deutsch</option>
            <option value="en">English</option>
          </select>
        </label>
        <div>
          <button onClick={onAccept}>I understand — start the call</button>
        </div>
      </div>
    </div>
  );
}
