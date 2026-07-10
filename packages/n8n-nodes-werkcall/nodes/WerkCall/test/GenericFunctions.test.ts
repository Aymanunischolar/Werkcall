import { describe, expect, it, vi } from "vitest";
import type { IExecuteFunctions } from "n8n-workflow";
import { redactSecrets, validateGermanPostcode, werkCallApiRequest } from "../GenericFunctions";

function makeExecuteFunctionsStub(opts: {
	credentials?: Record<string, unknown>;
	requestImpl: ReturnType<typeof vi.fn>;
}): IExecuteFunctions {
	return {
		getCredentials: vi.fn(async () => opts.credentials ?? { baseUrl: "http://localhost:8000", apiKey: "secret-key" }),
		getNode: vi.fn(() => ({ name: "WerkCall", type: "n8n-nodes-werkcall.werkCall" })),
		helpers: {
			httpRequestWithAuthentication: { call: opts.requestImpl },
		},
	} as unknown as IExecuteFunctions;
}

describe("redactSecrets", () => {
	it("masks a Bearer token", () => {
		expect(redactSecrets("Authorization: Bearer abc123.def456")).toContain("Bearer [REDACTED]");
		expect(redactSecrets("Authorization: Bearer abc123.def456")).not.toContain("abc123");
	});

	it("masks apiKey and clientSecret and access_token fields in JSON-ish strings", () => {
		const msg = '{"apiKey":"sk-live-123","clientSecret":"cs-456","access_token":"at-789"}';
		const redacted = redactSecrets(msg);
		expect(redacted).not.toContain("sk-live-123");
		expect(redacted).not.toContain("cs-456");
		expect(redacted).not.toContain("at-789");
	});
});

describe("validateGermanPostcode", () => {
	it("accepts a valid 5-digit postcode", () => {
		expect(() => validateGermanPostcode("10115")).not.toThrow();
	});

	it("rejects an invalid postcode with an actionable message", () => {
		expect(() => validateGermanPostcode("123")).toThrow(/not a valid German postal code/);
	});
});

describe("werkCallApiRequest retries", () => {
	it("retries on 429 and eventually succeeds", async () => {
		let calls = 0;
		const requestImpl = vi.fn(async () => {
			calls += 1;
			if (calls < 3) {
				const err: { statusCode: number } & Error = Object.assign(new Error("Too Many Requests"), { statusCode: 429 });
				throw err;
			}
			return { result_code: "OK" };
		});
		const ctx = makeExecuteFunctionsStub({ requestImpl });

		const result = await werkCallApiRequest.call(ctx, { method: "GET", endpoint: "/api/tools/check-slots", retryable: true });
		expect(result).toEqual({ result_code: "OK" });
		expect(calls).toBe(3);
	});

	it("retries on 5xx", async () => {
		let calls = 0;
		const requestImpl = vi.fn(async () => {
			calls += 1;
			if (calls < 2) {
				const err: { statusCode: number } & Error = Object.assign(new Error("Bad Gateway"), { statusCode: 502 });
				throw err;
			}
			return { result_code: "OK" };
		});
		const ctx = makeExecuteFunctionsStub({ requestImpl });

		const result = await werkCallApiRequest.call(ctx, { method: "GET", endpoint: "/api/tools/check-slots", retryable: true });
		expect(result).toEqual({ result_code: "OK" });
		expect(calls).toBe(2);
	});

	it("does not retry a write call when retryable is false", async () => {
		const requestImpl = vi.fn(async () => {
			const err: { statusCode: number } & Error = Object.assign(new Error("Conflict"), { statusCode: 409 });
			throw err;
		});
		const ctx = makeExecuteFunctionsStub({ requestImpl });

		await expect(
			werkCallApiRequest.call(ctx, { method: "POST", endpoint: "/api/tools/book", retryable: false }),
		).rejects.toThrow();
		expect(requestImpl).toHaveBeenCalledTimes(1);
	});

	it("redacts the API key from a thrown error message", async () => {
		const requestImpl = vi.fn(async () => {
			throw new Error('upstream rejected Authorization: Bearer secret-key-abc');
		});
		const ctx = makeExecuteFunctionsStub({ requestImpl });

		try {
			await werkCallApiRequest.call(ctx, { method: "GET", endpoint: "/api/tools/check-slots", retryable: false });
			throw new Error("expected werkCallApiRequest to throw");
		} catch (error) {
			expect((error as Error).message).not.toContain("secret-key-abc");
		}
	});
});
