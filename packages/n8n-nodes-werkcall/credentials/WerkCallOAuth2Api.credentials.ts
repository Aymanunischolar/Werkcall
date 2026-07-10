import type { ICredentialType, INodeProperties } from "n8n-workflow";

/**
 * OAuth 2.0 credential for deployments that front the WerkCall backend with
 * an OAuth-protected gateway (detailed spec §11). n8n's built-in OAuth2 flow
 * handles authorization-code exchange and automatic access-token refresh;
 * no refresh token is ever written to source control or node output.
 */
export class WerkCallOAuth2Api implements ICredentialType {
	name = "werkCallOAuth2Api";

	displayName = "WerkCall OAuth2 API";

	extends = ["oAuth2Api"];

	documentationUrl = "https://github.com/ayman/werkcall-ai/tree/main/packages/n8n-nodes-werkcall";

	properties: INodeProperties[] = [
		{
			displayName: "Grant Type",
			name: "grantType",
			type: "hidden",
			default: "authorizationCode",
		},
		{
			displayName: "Authorization URL",
			name: "authUrl",
			type: "string",
			default: "https://your-werkcall-gateway.example.com/oauth/authorize",
		},
		{
			displayName: "Access Token URL",
			name: "accessTokenUrl",
			type: "string",
			default: "https://your-werkcall-gateway.example.com/oauth/token",
		},
		{
			displayName: "Client ID",
			name: "clientId",
			type: "string",
			default: "",
		},
		{
			displayName: "Client Secret",
			name: "clientSecret",
			type: "string",
			typeOptions: { password: true },
			default: "",
		},
		{
			displayName: "Scope",
			name: "scope",
			type: "string",
			default: "appointments:read appointments:write sessions:read handoffs:write evaluations:read",
		},
		{
			displayName: "Auth URI Query Parameters",
			name: "authQueryParameters",
			type: "hidden",
			default: "",
		},
		{
			displayName: "Authentication",
			name: "authentication",
			type: "hidden",
			default: "header",
		},
	];
}
