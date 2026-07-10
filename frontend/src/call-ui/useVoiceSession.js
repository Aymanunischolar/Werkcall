import { useCallback, useRef, useState } from "react";

/**
 * Owns the session lifecycle: POST /api/sessions, then open the WebSocket
 * and translate its JSON events into transcript/tool-trace state
 * (blueprint §7). Microphone capture is wired but the mock backend expects
 * text turns, so both a `sendText` and `startMic`/`stopMic` path exist —
 * the Gemini/OpenAI adapters consume the raw PCM path.
 */
export function useVoiceSession() {
  const [sessionId, setSessionId] = useState(null);
  const [state, setState] = useState("IDLE");
  const [turns, setTurns] = useState([]);
  const [connected, setConnected] = useState(false);
  const [micActive, setMicActive] = useState(false);
  const wsRef = useRef(null);
  const audioCtxRef = useRef(null);
  const streamRef = useRef(null);

  const appendTurn = useCallback((turn) => {
    setTurns((prev) => [...prev, { ...turn, id: crypto.randomUUID() }]);
  }, []);

  const startSession = useCallback(
    async ({ language }) => {
      const res = await fetch("/api/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ language, channel: "browser", consent_given: true }),
      });
      if (!res.ok) throw new Error("failed to create session");
      const body = await res.json();
      setSessionId(body.session_id);
      appendTurn({ speaker: "assistant", text: body.disclosure_text, kind: "assistant" });

      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      const ws = new WebSocket(`${protocol}://${window.location.host}${body.websocket_url}`);
      ws.onopen = () => setConnected(true);
      ws.onclose = () => setConnected(false);
      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.state) setState(msg.state);
        if (msg.type === "final_transcript" && msg.payload.text) {
          appendTurn({ speaker: "assistant", text: msg.payload.text, kind: "assistant" });
        } else if (msg.type === "tool_call") {
          appendTurn({
            speaker: "assistant",
            text: `tool_call: ${msg.payload.tool_name} -> ${JSON.stringify(msg.payload.tool_args)}`,
            kind: "tool",
          });
        } else if (msg.type === "error") {
          appendTurn({ speaker: "assistant", text: msg.payload.error, kind: "error" });
        }
      };
      wsRef.current = ws;
      return body.session_id;
    },
    [appendTurn]
  );

  const sendText = useCallback(
    (text) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
      appendTurn({ speaker: "caller", text, kind: "caller" });
      wsRef.current.send(JSON.stringify({ type: "text_turn", payload: { text } }));
    },
    [appendTurn]
  );

  const startMic = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, sampleRate: 16000 } });
    streamRef.current = stream;
    const audioCtx = new AudioContext({ sampleRate: 16000 });
    audioCtxRef.current = audioCtx;
    const source = audioCtx.createMediaStreamSource(stream);
    const processor = audioCtx.createScriptProcessor(4096, 1, 1);
    processor.onaudioprocess = (e) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
      const input = e.inputBuffer.getChannelData(0);
      const pcm16 = new Int16Array(input.length);
      for (let i = 0; i < input.length; i++) {
        const s = Math.max(-1, Math.min(1, input[i]));
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
      }
      wsRef.current.send(pcm16.buffer);
    };
    source.connect(processor);
    processor.connect(audioCtx.destination);
    setMicActive(true);
  }, []);

  const stopMic = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    audioCtxRef.current?.close();
    setMicActive(false);
  }, []);

  const endSession = useCallback(() => {
    wsRef.current?.send(JSON.stringify({ type: "client_disconnect" }));
    wsRef.current?.close();
    stopMic();
  }, [stopMic]);

  return { sessionId, state, turns, connected, micActive, startSession, sendText, startMic, stopMic, endSession };
}
