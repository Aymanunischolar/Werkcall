import { describe, expect, it, vi } from "vitest";
import { WerkCall } from "../WerkCall.node";

/** Minimal IExecuteFunctions stub: only the surface WerkCall.node.ts touches. */
function makeContext(params: Record<string, unknown>, requestImpl: ReturnType<typeof vi.fn>) {
	return {
		getInputData: () => [{ json: {} }],
		getNodeParameter: (name: string) => params[name],
		getCredentials: vi.fn(async () => ({ baseUrl: "http://localhost:8000", apiKey: "test-key" })),
		getNode: vi.fn(() => ({ name: "WerkCall", type: "n8n-nodes-werkcall.werkCall" })),
		continueOnFail: () => false,
		helpers: { httpRequestWithAuthentication: { call: requestImpl } },
	} as unknown as import("n8n-workflow").IExecuteFunctions;
}

describe("WerkCall node — appointment resource", () => {
	it("rejects create when callerConfirmed is false (missing caller confirmation)", async () => {
		const requestImpl = vi.fn();
		const ctx = makeContext(
			{
				resource: "appointment",
				operation: "create",
				callerConfirmed: false,
			},
			requestImpl,
		);

		const node = new WerkCall();
		await expect(node.execute.call(ctx)).rejects.toThrow(/callerConfirmed must be true/);
		expect(requestImpl).not.toHaveBeenCalled();
	});

	it("rejects checkAvailability with an invalid postal code before calling the API", async () => {
		const requestImpl = vi.fn();
		const ctx = makeContext(
			{
				resource: "appointment",
				operation: "checkAvailability",
				service: "heating_repair",
				earliestDate: "2026-07-13",
				latestDate: "2026-07-20",
				postcode: "ABCDE",
			},
			requestImpl,
		);

		const node = new WerkCall();
		await expect(node.execute.call(ctx)).rejects.toThrow(/not a valid German postal code/);
		expect(requestImpl).not.toHaveBeenCalled();
	});

	it("builds the check-slots request body correctly and maps the response", async () => {
		const requestImpl = vi.fn(async () => ({ result_code: "OK", slots: [] }));
		const ctx = makeContext(
			{
				resource: "appointment",
				operation: "checkAvailability",
				service: "heating_repair",
				earliestDate: "2026-07-13",
				latestDate: "2026-07-20",
				postcode: "10115",
			},
			requestImpl,
		);

		const node = new WerkCall();
		const result = await node.execute.call(ctx);

		expect(requestImpl).toHaveBeenCalledTimes(1);
		const [, , sentOptions] = requestImpl.mock.calls[0];
		expect(sentOptions.method).toBe("POST");
		expect(sentOptions.url).toBe("http://localhost:8000/api/tools/check-slots");
		expect(sentOptions.body).toEqual({
			service: "heating_repair",
			earliest_date: "2026-07-13",
			latest_date: "2026-07-20",
			postcode: "10115",
		});
		expect(result[0][0].json).toEqual({ result_code: "OK", slots: [] });
	});

	it("creates a booking once caller confirmation and idempotency key are present", async () => {
		const requestImpl = vi.fn(async () => ({ result_code: "OK", booking_id: "b-1" }));
		const ctx = makeContext(
			{
				resource: "appointment",
				operation: "create",
				callerConfirmed: true,
				service: "heating_repair",
				startAt: "2026-07-13T09:00:00+02:00",
				endAt: "2026-07-13T10:30:00+02:00",
				fullName: "Demo Kunde",
				phone: "+491510000000",
				email: "demo@example.com",
				street: "Musterstrasse 12",
				postcode: "10115",
				city: "Berlin",
				idempotencyKey: "booking-session_123-20260713T0900",
			},
			requestImpl,
		);

		const node = new WerkCall();
		const result = await node.execute.call(ctx);

		const [, , sentOptions] = requestImpl.mock.calls[0];
		expect(sentOptions.body.idempotency_key).toBe("booking-session_123-20260713T0900");
		expect(sentOptions.body.contact.address).toEqual({ street: "Musterstrasse 12", postcode: "10115", city: "Berlin" });
		expect(result[0][0].json).toEqual({ result_code: "OK", booking_id: "b-1" });
	});
});

describe("WerkCall node — error handling", () => {
	it("continues on fail and surfaces the error in output when continueOnFail is true", async () => {
		const requestImpl = vi.fn();
		const ctx = makeContext(
			{ resource: "appointment", operation: "create", callerConfirmed: false },
			requestImpl,
		);
		(ctx as { continueOnFail: () => boolean }).continueOnFail = () => true;

		const node = new WerkCall();
		const result = await node.execute.call(ctx);
		expect(result[0][0].json.error).toMatch(/callerConfirmed must be true/);
	});
});
