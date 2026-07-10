export class GoodApi {
	name = "goodApi";
	displayName = "Good API";
	properties = [
		{
			displayName: "API Key",
			name: "apiKey",
			type: "string",
			typeOptions: { password: true },
			default: "",
			description: "Sent as an Authorization header, never logged.",
		},
	];
	test = {
		request: { url: "/health", method: "GET" },
	};
}
