import type {
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
	IDataObject,
} from "n8n-workflow";
import { NodeConnectionTypes } from "n8n-workflow";

import { appointmentFields, appointmentOperations } from "./descriptions/AppointmentDescription";
import { sessionFields, sessionOperations } from "./descriptions/SessionDescription";
import { handoffFields, handoffOperations } from "./descriptions/HandoffDescription";
import { evaluationFields, evaluationOperations } from "./descriptions/EvaluationDescription";
import { validateGermanPostcode, werkCallApiRequest } from "./GenericFunctions";

/**
 * Native n8n node for the WerkCall AI backend (detailed spec §10). Lets an
 * operator call appointment/session/handoff/evaluation operations without
 * manually configuring generic HTTP Request nodes for every endpoint.
 */
export class WerkCall implements INodeType {
	description: INodeTypeDescription = {
		displayName: "WerkCall",
		name: "werkCall",
		icon: "file:../../icons/werkcall.svg",
		group: ["transform"],
		version: 1,
		subtitle: '={{$parameter["operation"] + ": " + $parameter["resource"]}}',
		description: "Call the WerkCall AI voice-receptionist API: appointments, sessions, handoffs, evaluations",
		defaults: { name: "WerkCall" },
		inputs: [NodeConnectionTypes.Main],
		outputs: [NodeConnectionTypes.Main],
		credentials: [
			{ name: "werkCallApi", required: true, displayOptions: { show: { authentication: ["apiKey"] } } },
			{ name: "werkCallOAuth2Api", required: true, displayOptions: { show: { authentication: ["oAuth2"] } } },
		],
		properties: [
			{
				displayName: "Authentication",
				name: "authentication",
				type: "options",
				options: [
					{ name: "API Key", value: "apiKey" },
					{ name: "OAuth2", value: "oAuth2" },
				],
				default: "apiKey",
			},
			{
				displayName: "Resource",
				name: "resource",
				type: "options",
				noDataExpression: true,
				options: [
					{ name: "Appointment", value: "appointment" },
					{ name: "Session", value: "session" },
					{ name: "Handoff", value: "handoff" },
					{ name: "Evaluation", value: "evaluation" },
				],
				default: "appointment",
			},
			...appointmentOperations,
			...appointmentFields,
			...sessionOperations,
			...sessionFields,
			...handoffOperations,
			...handoffFields,
			...evaluationOperations,
			...evaluationFields,
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];
		const resource = this.getNodeParameter("resource", 0) as string;
		const operation = this.getNodeParameter("operation", 0) as string;

		for (let i = 0; i < items.length; i++) {
			try {
				let response: IDataObject;

				if (resource === "appointment") {
					response = await executeAppointment.call(this, operation, i);
				} else if (resource === "session") {
					response = await executeSession.call(this, operation, i);
				} else if (resource === "handoff") {
					response = await executeHandoff.call(this, operation, i);
				} else if (resource === "evaluation") {
					response = await executeEvaluation.call(this, operation, i);
				} else {
					throw new Error(`Unknown resource: ${resource}`);
				}

				returnData.push({ json: response, pairedItem: { item: i } });
			} catch (error) {
				if (this.continueOnFail()) {
					returnData.push({ json: { error: (error as Error).message }, pairedItem: { item: i } });
					continue;
				}
				throw error;
			}
		}

		return [returnData];
	}
}

async function executeAppointment(this: IExecuteFunctions, operation: string, i: number): Promise<IDataObject> {
	if (operation === "checkAvailability") {
		const postcode = this.getNodeParameter("postcode", i) as string;
		validateGermanPostcode(postcode);
		return werkCallApiRequest.call(this, {
			method: "POST",
			endpoint: "/api/tools/check-slots",
			retryable: true, // read-only
			body: {
				service: this.getNodeParameter("service", i) as string,
				earliest_date: this.getNodeParameter("earliestDate", i) as string,
				latest_date: this.getNodeParameter("latestDate", i) as string,
				postcode,
			},
		});
	}

	if (operation === "create") {
		if (!(this.getNodeParameter("callerConfirmed", i) as boolean)) {
			throw new Error(
				"callerConfirmed must be true before a booking can be created (detailed spec §7 Confirmation policy) — " +
					"fix: set 'Caller Confirmed' to true only after reading the final slot/address/phone back to the caller.",
			);
		}
		const postcode = this.getNodeParameter("postcode", i) as string;
		validateGermanPostcode(postcode);
		return werkCallApiRequest.call(this, {
			method: "POST",
			endpoint: "/api/tools/book",
			retryable: false, // write, protected by idempotency key instead
			body: {
				service: this.getNodeParameter("service", i) as string,
				slot: {
					start_at: this.getNodeParameter("startAt", i) as string,
					end_at: this.getNodeParameter("endAt", i) as string,
				},
				contact: {
					full_name: this.getNodeParameter("fullName", i) as string,
					phone: this.getNodeParameter("phone", i) as string,
					email: (this.getNodeParameter("email", i) as string) || undefined,
					address: {
						street: this.getNodeParameter("street", i) as string,
						postcode,
						city: this.getNodeParameter("city", i) as string,
					},
				},
				idempotency_key: this.getNodeParameter("idempotencyKey", i) as string,
			},
		});
	}

	if (operation === "get") {
		// Bookings are exposed through the session detail; a dedicated
		// GET /api/bookings/{id} is not yet implemented server-side, so this
		// operation surfaces a clear, actionable error rather than a raw 404.
		throw new Error(
			"Appointment.get is not implemented by the WerkCall backend yet — fix: use Session > Get Session " +
				"and read the booking from its tool_executions, or implement GET /api/bookings/{id} server-side.",
		);
	}

	if (operation === "reschedule") {
		return werkCallApiRequest.call(this, {
			method: "POST",
			endpoint: "/api/tools/reschedule",
			retryable: false,
			body: {
				booking_id: this.getNodeParameter("bookingId", i) as string,
				new_slot: {
					start_at: this.getNodeParameter("startAt", i) as string,
					end_at: this.getNodeParameter("endAt", i) as string,
				},
				idempotency_key: this.getNodeParameter("idempotencyKey", i) as string,
			},
		});
	}

	if (operation === "cancel") {
		return werkCallApiRequest.call(this, {
			method: "POST",
			endpoint: "/api/tools/cancel",
			retryable: false,
			body: {
				booking_id: this.getNodeParameter("bookingId", i) as string,
				reason: this.getNodeParameter("cancellationReason", i) as string,
				idempotency_key: this.getNodeParameter("idempotencyKey", i) as string,
			},
		});
	}

	throw new Error(`Unknown appointment operation: ${operation}`);
}

async function executeSession(this: IExecuteFunctions, operation: string, i: number): Promise<IDataObject> {
	if (operation === "list") {
		return { sessions: await werkCallApiRequest.call(this, { method: "GET", endpoint: "/api/sessions", retryable: true }) };
	}

	const sessionId = this.getNodeParameter("sessionId", i) as string;

	if (operation === "get") {
		return werkCallApiRequest.call(this, { method: "GET", endpoint: `/api/sessions/${sessionId}`, retryable: true });
	}

	if (operation === "getTranscript") {
		const detail = await werkCallApiRequest.call(this, { method: "GET", endpoint: `/api/sessions/${sessionId}`, retryable: true });
		return { session_id: sessionId, turns: detail.turns ?? [] };
	}

	if (operation === "getToolExecutions") {
		const detail = await werkCallApiRequest.call(this, { method: "GET", endpoint: `/api/sessions/${sessionId}`, retryable: true });
		return { session_id: sessionId, tool_executions: detail.tool_executions ?? [] };
	}

	if (operation === "delete") {
		return werkCallApiRequest.call(this, { method: "DELETE", endpoint: `/api/sessions/${sessionId}`, retryable: false });
	}

	throw new Error(`Unknown session operation: ${operation}`);
}

async function executeHandoff(this: IExecuteFunctions, operation: string, i: number): Promise<IDataObject> {
	if (operation === "create") {
		return werkCallApiRequest.call(this, {
			method: "POST",
			endpoint: "/api/handoffs",
			retryable: false,
			body: {
				session_id: this.getNodeParameter("sessionId", i) as string,
				reason: this.getNodeParameter("reason", i) as string,
				urgency: this.getNodeParameter("urgency", i) as string,
			},
		});
	}

	if (operation === "getStatus") {
		const handoffId = this.getNodeParameter("handoffId", i) as string;
		return werkCallApiRequest.call(this, { method: "GET", endpoint: `/api/handoffs/${handoffId}`, retryable: true });
	}

	if (operation === "listUnresolved") {
		return {
			handoffs: await werkCallApiRequest.call(this, {
				method: "GET",
				endpoint: "/api/handoffs",
				qs: { unresolved: true },
				retryable: true,
			}),
		};
	}

	throw new Error(`Unknown handoff operation: ${operation}`);
}

async function executeEvaluation(this: IExecuteFunctions, operation: string, i: number): Promise<IDataObject> {
	if (operation === "startRun") {
		return werkCallApiRequest.call(this, { method: "POST", endpoint: "/api/evaluations/run", retryable: false });
	}

	if (operation === "getResult") {
		const runId = this.getNodeParameter("runId", i) as string;
		return werkCallApiRequest.call(this, { method: "GET", endpoint: `/api/evaluations/${runId}`, retryable: true });
	}

	throw new Error(`Unknown evaluation operation: ${operation}`);
}
