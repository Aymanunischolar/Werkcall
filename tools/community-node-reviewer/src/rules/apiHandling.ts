import type { CheckResult, Rule } from "../types.js";

export const apiHandlingRule: Rule = (ctx) => {
	const results: CheckResult[] = [];
	const push = (id: string, level: CheckResult["level"], message: string, blocking = false, file?: string) =>
		results.push({ category: "API handling", id, level, message, blocking, file });

	const sourceFiles = ctx.listFiles(/\.ts$/).filter((f) => !f.endsWith(".test.ts") && !f.endsWith(".d.ts"));
	const combined = sourceFiles.map((f) => ctx.readFile(f) ?? "").join("\n");

	const has429Handling = /\b429\b/.test(combined) && /(backoff|retry|retries)/i.test(combined);
	push(
		"rate-limit-handling",
		has429Handling ? "PASS" : "FAIL",
		has429Handling
			? "429 responses are retried with backoff."
			: "No handling found for HTTP 429 (rate limit) responses with retry/backoff.",
		!has429Handling,
	);

	const has5xxHandling = /5(00|02|03|04)/.test(combined) && /(retry|retries)/i.test(combined);
	push(
		"server-error-handling",
		has5xxHandling ? "PASS" : "WARN",
		has5xxHandling ? "5xx responses are retried." : "No explicit retry handling found for 5xx server errors.",
	);

	const hasTimeout = /timeout/i.test(combined);
	push("timeout-configured", hasTimeout ? "PASS" : "WARN", hasTimeout ? "A request timeout is configured somewhere in the package." : "No request timeout configuration found — a hung upstream call could hang the workflow.");

	const hasIdempotency = /idempotenc(y|ies)/i.test(combined);
	push(
		"idempotency-for-writes",
		hasIdempotency ? "PASS" : "WARN",
		hasIdempotency ? "Idempotency keys are used for write operations." : "No idempotency-key handling found — replayed writes may create duplicates.",
	);

	const hasPagination = /(nextPageToken|cursor|pageToken|hasMore|has_more|paginat)/i.test(combined);
	const hasListOperation = /\blist[A-Z]|\bList\b/.test(combined);
	if (hasListOperation && !hasPagination) {
		push("pagination-handling", "WARN", "A list-style operation exists but no pagination handling was detected.");
	} else if (hasPagination) {
		push("pagination-handling", "PASS", "Pagination handling detected.");
	}

	const hasOAuthRefresh = /oAuth2Api|extends\s*=\s*\[.*oAuth2/i.test(combined);
	if (hasOAuthRefresh) {
		const mentionsRefresh = /refresh/i.test(combined);
		push(
			"oauth-refresh-handling",
			mentionsRefresh ? "PASS" : "WARN",
			mentionsRefresh
				? "OAuth2 credential extends n8n's built-in refresh handling."
				: "OAuth2 credential is defined but no refresh-token handling or comment about it was found.",
		);
	}

	const hasResponseValidation = /(zod|joi|ajv|assert|throw new (Node)?Error)/i.test(combined);
	push(
		"response-validation",
		hasResponseValidation ? "PASS" : "WARN",
		hasResponseValidation ? "External responses appear to be validated/asserted before use." : "No explicit validation of external API responses was found.",
	);

	return results;
};
