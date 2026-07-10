import type { IExecuteFunctions, IHttpRequestMethods, IDataObject, JsonObject } from "n8n-workflow";
import { NodeApiError } from "n8n-workflow";

const RETRYABLE_STATUS_CODES = new Set([429, 500, 502, 503, 504]);
const MAX_ATTEMPTS = 4;
const BASE_BACKOFF_MS = 1000; // 1s -> 2s -> 4s -> 8s (detailed spec §15)

function sleep(ms: number): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Strips anything that looks like a credential from an error message before
 * it reaches node output or n8n's execution log (detailed spec §11: "Never
 * include it in logs, node output or error messages"). */
export function redactSecrets(message: string): string {
	return message
		.replace(/Bearer\s+[A-Za-z0-9\-_.~+/]+=*/gi, "Bearer [REDACTED]")
		.replace(/"apiKey"\s*:\s*"[^"]*"/gi, '"apiKey":"[REDACTED]"')
		.replace(/"clientSecret"\s*:\s*"[^"]*"/gi, '"clientSecret":"[REDACTED]"')
		.replace(/"access_token"\s*:\s*"[^"]*"/gi, '"access_token":"[REDACTED]"');
}

const GERMAN_POSTCODE_RE = /^\d{5}$/;

/** Fail fast with an actionable message instead of letting an obviously
 * invalid postcode reach the API and come back as a generic 422 (detailed
 * spec §10: "Error messages must explain what the user needs to fix"). */
export function validateGermanPostcode(postcode: string): void {
	if (!GERMAN_POSTCODE_RE.test(postcode)) {
		throw new Error(
			`"${postcode}" is not a valid German postal code — fix: use exactly 5 digits, e.g. "10115".`,
		);
	}
}

export interface WerkCallRequestOptions {
	method: IHttpRequestMethods;
	endpoint: string;
	body?: IDataObject;
	qs?: IDataObject;
	/** Only GET/read-only calls, or writes protected by an idempotency key in
	 * `body`, may be retried (detailed spec §15 reliability design). */
	retryable?: boolean;
}

/**
 * Calls the WerkCall FastAPI backend with either credential type, retrying
 * 429/5xx responses with exponential backoff up to MAX_ATTEMPTS, and
 * redacting secrets from any error that bubbles up to the node's output.
 */
export async function werkCallApiRequest(
	this: IExecuteFunctions,
	options: WerkCallRequestOptions,
): Promise<IDataObject> {
	const credentialType = (await this.getCredentials("werkCallApi").catch(() => null))
		? "werkCallApi"
		: "werkCallOAuth2Api";
	const credentials = await this.getCredentials(credentialType);
	const baseUrl = (credentials.baseUrl as string) ?? "http://localhost:8000";

	let attempt = 0;
	// eslint-disable-next-line no-constant-condition
	while (true) {
		attempt += 1;
		try {
			const response = await this.helpers.httpRequestWithAuthentication.call(this, credentialType, {
				method: options.method,
				url: `${baseUrl}${options.endpoint}`,
				body: options.body,
				qs: options.qs,
				json: true,
			});
			return response as IDataObject;
		} catch (error) {
			const statusCode = (error as { statusCode?: number; response?: { statusCode?: number } }).statusCode ??
				(error as { response?: { statusCode?: number } }).response?.statusCode;

			const canRetry = options.retryable !== false && statusCode !== undefined && RETRYABLE_STATUS_CODES.has(statusCode);
			if (canRetry && attempt < MAX_ATTEMPTS) {
				await sleep(BASE_BACKOFF_MS * 2 ** (attempt - 1));
				continue;
			}

			const rawMessage = error instanceof Error ? error.message : String(error);
			throw new NodeApiError(this.getNode(), error as JsonObject, {
				message: redactSecrets(rawMessage),
				description: "Check the WerkCall API base URL, credentials, and request payload.",
			});
		}
	}
}
