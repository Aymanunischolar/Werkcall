import type { INodeProperties } from "n8n-workflow";

export const sessionOperations: INodeProperties[] = [
	{
		displayName: "Operation",
		name: "operation",
		type: "options",
		noDataExpression: true,
		displayOptions: { show: { resource: ["session"] } },
		options: [
			{ name: "Get Session", value: "get", action: "Get a session" },
			{ name: "List Sessions", value: "list", action: "List sessions" },
			{ name: "Get Redacted Transcript", value: "getTranscript", action: "Get a redacted transcript" },
			{ name: "Get Tool Executions", value: "getToolExecutions", action: "Get tool executions" },
			{ name: "Delete Session", value: "delete", action: "Delete a session" },
		],
		default: "get",
	},
];

const showForOps = (...operations: string[]) => ({ resource: ["session"], operation: operations });

export const sessionFields: INodeProperties[] = [
	{
		displayName: "Session ID",
		name: "sessionId",
		type: "string",
		default: "",
		required: true,
		displayOptions: { show: showForOps("get", "getTranscript", "getToolExecutions", "delete") },
	},
];
