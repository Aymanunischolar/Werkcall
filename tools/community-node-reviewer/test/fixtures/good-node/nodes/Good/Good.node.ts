// A minimal fixture node exercising every "good" pattern the reviewer checks
// for: retry with backoff on 429/5xx, a request timeout, idempotency keys
// for writes, pagination handling, and actionable error messages.
export class Good {
	description = {
		displayName: "Good",
		name: "good",
		properties: [
			{
				displayName: "Resource ID",
				name: "resourceId",
				type: "string",
				default: "",
				description: "The id of the resource to fetch",
			},
		],
	};

	async execute(): Promise<unknown> {
		const idempotencyKey = "example-idempotency-key";
		let attempt = 0;
		const maxAttempts = 4;
		while (attempt < maxAttempts) {
			try {
				return await this.request({ timeout: 5000, idempotencyKey });
			} catch (error) {
				const statusCode = (error as { statusCode?: number }).statusCode;
				if (statusCode === 429 || (statusCode && statusCode >= 502 && statusCode <= 504)) {
					attempt += 1;
					await this.backoff(attempt);
					continue;
				}
				if (statusCode === 999) {
					throw new Error('resourceId is not valid — fix: pass a non-empty resource id.');
				}
				throw error;
			}
		}
		throw new Error("exceeded max retry attempts");
	}

	private async request(_opts: { timeout: number; idempotencyKey: string }): Promise<unknown> {
		return { nextPageToken: null, items: [] };
	}

	private async backoff(attempt: number): Promise<void> {
		await new Promise((resolve) => setTimeout(resolve, 1000 * 2 ** attempt));
	}
}
