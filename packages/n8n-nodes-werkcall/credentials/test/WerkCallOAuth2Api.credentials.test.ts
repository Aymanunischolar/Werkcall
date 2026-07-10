import { describe, expect, it } from "vitest";
import { WerkCallOAuth2Api } from "../WerkCallOAuth2Api.credentials";

describe("WerkCallOAuth2Api credential", () => {
	it("extends n8n's built-in oAuth2Api so access-token refresh is automatic", () => {
		const credential = new WerkCallOAuth2Api();
		// n8n's oAuth2Api base credential type transparently refreshes an
		// expired access token before a request is retried — this package
		// does not implement its own refresh logic, it relies on that base
		// type via `extends`. This test documents and locks in that choice.
		expect(credential.extends).toContain("oAuth2Api");
	});

	it("declares the required scopes for every WerkCall resource the node exposes", () => {
		const credential = new WerkCallOAuth2Api();
		const scopeField = credential.properties.find((p) => p.name === "scope");
		expect(scopeField?.default).toMatch(/appointments:write/);
		expect(scopeField?.default).toMatch(/handoffs:write/);
	});

	it("never exposes clientSecret in plain text", () => {
		const credential = new WerkCallOAuth2Api();
		const secretField = credential.properties.find((p) => p.name === "clientSecret");
		expect(secretField?.typeOptions).toEqual({ password: true });
	});
});
