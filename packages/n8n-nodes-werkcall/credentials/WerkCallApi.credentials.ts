import type { ICredentialTestRequest, ICredentialType, IAuthenticateGeneric, INodeProperties } from "n8n-workflow";

/**
 * API-key credential for the WerkCall backend (detailed spec §11).
 * The key is sent only via the Authorization header, masked in the
 * n8n UI (`typeOptions.password`), and never appears in node output or logs.
 */
export class WerkCallApi implements ICredentialType {
	name = "werkCallApi";

	displayName = "WerkCall API";

	documentationUrl = "https://github.com/ayman/werkcall-ai/tree/main/packages/n8n-nodes-werkcall";

	properties: INodeProperties[] = [
		{
			displayName: "Base URL",
			name: "baseUrl",
			type: "string",
			default: "http://localhost:8000",
			placeholder: "https://your-werkcall-backend.example.com",
			description: "Base URL of the WerkCall FastAPI backend, no trailing slash",
		},
		{
			displayName: "API Key",
			name: "apiKey",
			type: "string",
			typeOptions: { password: true },
			default: "",
			description: "Sent as an Authorization: Bearer header. Never logged or returned in node output.",
		},
	];

	authenticate: IAuthenticateGeneric = {
		type: "generic",
		properties: {
			headers: {
				Authorization: "=Bearer {{$credentials.apiKey}}",
			},
		},
	};

	test: ICredentialTestRequest = {
		request: {
			baseURL: "={{$credentials.baseUrl}}",
			url: "/health",
			method: "GET",
		},
	};
}
