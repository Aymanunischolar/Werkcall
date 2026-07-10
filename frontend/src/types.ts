export type Language = "de" | "en";
export type Channel = "browser" | "telephone";

export interface CreateSessionResponse {
  session_id: string;
  websocket_url: string;
  disclosure_text: string;
}

export type TurnKind = "assistant" | "caller" | "tool" | "error";

export interface TranscriptTurn {
  id: string;
  speaker: "assistant" | "caller";
  text: string;
  kind: TurnKind;
}

export interface ConversationTurn {
  speaker: "caller" | "assistant";
  redacted_text: string;
  timestamp: string;
  latency_ms: number | null;
}

export interface ToolExecutionRecord {
  tool: string;
  validated_input: Record<string, unknown>;
  result_code: string;
  retries: number;
  duration_ms: number;
  idempotency_key: string | null;
}

export interface SessionDetail {
  session_id: string;
  started_at: string;
  language: Language;
  channel: Channel;
  consent_at: string | null;
  outcome: string;
  state: string;
  duration_ms: number | null;
  model_provider: string;
  turns: ConversationTurn[];
  tool_executions: ToolExecutionRecord[];
}

export interface WsInboundMessage {
  type: string;
  payload: {
    text?: string;
    tool_name?: string;
    tool_args?: Record<string, unknown>;
    error?: string;
  };
  state?: string;
  timestamp: string;
}

export interface EvaluationScenarioResult {
  scenario_id: string;
  pass: boolean;
  notes: string;
  actual: { tool_name: string | null; tool_args: Record<string, unknown> };
}

export interface EvaluationRunSummary {
  run_id: string;
  model: string;
  date: string;
  scenario_count: number;
  passed: number;
  completion_rate: number;
  results: EvaluationScenarioResult[];
}
