// Deliberately bad fixture node: hard-coded secret, logged token, no retry
// handling, no field descriptions, generic error message, no tests.
export class Bad {
	description = {
		displayName: "Bad",
		name: "bad",
		properties: [
			{
				displayName: "Thing",
				name: "thing",
				type: "string",
				default: "",
			},
		],
	};

	async execute(): Promise<unknown> {
		const apiKey = "AKIAABCDEFGHIJKLMNOP";
		console.log("using token", apiKey);
		const response = await fetch(`https://example.com/data?apiKey=${apiKey}`);
		if (!response.ok) {
			throw new Error("failed");
		}
		return response.json();
	}
}
