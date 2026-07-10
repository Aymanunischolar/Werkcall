import type { INodeProperties } from "n8n-workflow";

export const handoffOperations: INodeProperties[] = [
	{
		displayName: "Operation",
		name: "operation",
		type: "options",
		noDataExpression: true,
		displayOptions: { show: { resource: ["handoff"] } },
		options: [
			{ name: "Create Handoff", value: "create", action: "Create a handoff" },
			{ name: "Get Status", value: "getStatus", action: "Get handoff status" },
			{ name: "List Unresolved Handoffs", value: "listUnresolved", action: "List unresolved handoffs" },
		],
		default: "create",
	},
];

const showForOps = (...operations: string[]) => ({ resource: ["handoff"], operation: operations });

export const handoffFields: INodeProperties[] = [
	{
		displayName: "Session ID",
		name: "sessionId",
		type: "string",
		default: "",
		required: true,
		displayOptions: { show: showForOps("create") },
	},
	{
		displayName: "Reason",
		name: "reason",
		type: "options",
		options: [
			{ name: "Explicit Request", value: "explicit_request" },
			{ name: "Emergency", value: "emergency" },
			{ name: "Low Confidence", value: "low_confidence" },
			{ name: "Repeated Tool Failure", value: "repeated_tool_failure" },
		],
		default: "explicit_request",
		displayOptions: { show: showForOps("create") },
	},
	{
		displayName: "Urgency",
		name: "urgency",
		type: "options",
		options: [
			{ name: "Standard", value: "standard" },
			{ name: "Urgent", value: "urgent" },
			{ name: "Emergency", value: "emergency" },
		],
		default: "standard",
		description: "Urgency appears only for a handoff, per the detailed spec's node UX guidance (§10)",
		displayOptions: { show: showForOps("create") },
	},
	{
		displayName: "Handoff ID",
		name: "handoffId",
		type: "string",
		default: "",
		required: true,
		displayOptions: { show: showForOps("getStatus") },
	},
];
