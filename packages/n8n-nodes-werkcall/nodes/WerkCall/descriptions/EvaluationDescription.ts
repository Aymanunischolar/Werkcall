import type { INodeProperties } from "n8n-workflow";

export const evaluationOperations: INodeProperties[] = [
	{
		displayName: "Operation",
		name: "operation",
		type: "options",
		noDataExpression: true,
		displayOptions: { show: { resource: ["evaluation"] } },
		options: [
			{ name: "Start Evaluation Run", value: "startRun", action: "Start an evaluation run" },
			{ name: "Get Evaluation Result", value: "getResult", action: "Get an evaluation result" },
		],
		default: "startRun",
	},
];

export const evaluationFields: INodeProperties[] = [
	{
		displayName: "Run ID",
		name: "runId",
		type: "string",
		default: "",
		required: true,
		displayOptions: { show: { resource: ["evaluation"], operation: ["getResult"] } },
	},
];
