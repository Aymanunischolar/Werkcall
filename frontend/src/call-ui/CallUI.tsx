import { useState } from "react";
import ConsentModal from "./ConsentModal.tsx";
import { useVoiceSession } from "./useVoiceSession.ts";
import type { Language } from "../types";

export default function CallUI() {
  const [language, setLanguage] = useState<Language>("de");
  const [consented, setConsented] = useState(false);
  const [draft, setDraft] = useState("");
  const { sessionId, state, turns, connected, micActive, startSession, sendText, startMic, stopMic, endSession } =
    useVoiceSession();

  const handleAccept = async () => {
    setConsented(true);
    await startSession({ language });
  };

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!draft.trim()) return;
    sendText(draft.trim());
    setDraft("");
  };

  return (
    <div className="panel">
      {!consented && <ConsentModal language={language} onLanguageChange={setLanguage} onAccept={handleAccept} />}

      <div className="status-row">
        <span className={`badge ${connected ? "state" : ""}`}>{connected ? "Connected" : "Not connected"}</span>
        <span className="badge state">State: {state}</span>
        {sessionId && <span className="badge">Session {sessionId.slice(0, 8)}</span>}
      </div>

      <div className="disclosure-banner">
        Say (German): "Meine Heizung ist ausgefallen. Ich brauche morgen einen Termin." — the demo backend
        (mock provider by default) will detect intent, emergencies, and explicit human requests without
        any paid API key. Set VOICE_PROVIDER=gemini_live for real speech.
      </div>

      <div className="transcript">
        {turns.map((t) => (
          <div key={t.id} className={`turn ${t.kind}`}>
            {t.text}
          </div>
        ))}
      </div>

      <form className="composer" onSubmit={handleSend}>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={consented ? "Type what the caller says…" : "Accept the consent dialog first"}
          disabled={!consented}
        />
        <button type="submit" disabled={!consented}>
          Send
        </button>
        {!micActive ? (
          <button type="button" className="secondary" disabled={!consented} onClick={startMic}>
            🎙 Start mic
          </button>
        ) : (
          <button type="button" className="secondary" onClick={stopMic}>
            ⏹ Stop mic
          </button>
        )}
        {consented && (
          <button type="button" className="danger" onClick={endSession}>
            End call
          </button>
        )}
      </form>
    </div>
  );
}
