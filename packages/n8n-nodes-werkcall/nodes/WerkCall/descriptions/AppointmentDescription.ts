import type { INodeProperties } from "n8n-workflow";

export const appointmentOperations: INodeProperties[] = [
	{
		displayName: "Operation",
		name: "operation",
		type: "options",
		noDataExpression: true,
		displayOptions: { show: { resource: ["appointment"] } },
		options: [
			{ name: "Check Availability", value: "checkAvailability", action: "Check appointment availability" },
			{ name: "Create", value: "create", action: "Create an appointment" },
			{ name: "Get", value: "get", action: "Get an appointment" },
			{ name: "Reschedule", value: "reschedule", action: "Reschedule an appointment" },
			{ name: "Cancel", value: "cancel", action: "Cancel an appointment" },
		],
		default: "checkAvailability",
	},
];

const showForOps = (...operations: string[]) => ({ resource: ["appointment"], operation: operations });

export const appointmentFields: INodeProperties[] = [
	// ---- Check Availability ----
	{
		displayName: "Service",
		name: "service",
		type: "options",
		options: [
			{ name: "Heating Repair", value: "heating_repair" },
			{ name: "Maintenance", value: "maintenance" },
			{ name: "Installation Enquiry", value: "installation_enquiry" },
		],
		default: "heating_repair",
		displayOptions: { show: showForOps("checkAvailability", "create") },
	},
	{
		displayName: "Earliest Date",
		name: "earliestDate",
		type: "dateTime",
		default: "",
		required: true,
		displayOptions: { show: showForOps("checkAvailability") },
	},
	{
		displayName: "Latest Date",
		name: "latestDate",
		type: "dateTime",
		default: "",
		required: true,
		displayOptions: { show: showForOps("checkAvailability") },
	},
	{
		displayName: "Postal Code",
		name: "postcode",
		type: "string",
		default: "",
		required: true,
		placeholder: "10115",
		description: "5-digit German Postleitzahl",
		displayOptions: { show: showForOps("checkAvailability", "create") },
	},

	// ---- Get / Reschedule / Cancel: booking id ----
	{
		displayName: "Booking ID",
		name: "bookingId",
		type: "string",
		default: "",
		required: true,
		displayOptions: { show: showForOps("get", "reschedule", "cancel") },
	},

	// ---- Create / Reschedule: slot ----
	{
		displayName: "Start At",
		name: "startAt",
		type: "dateTime",
		default: "",
		required: true,
		description: "Confirmed slot start time, must be a value returned by Check Availability",
		displayOptions: { show: showForOps("create", "reschedule") },
	},
	{
		displayName: "End At",
		name: "endAt",
		type: "dateTime",
		default: "",
		required: true,
		displayOptions: { show: showForOps("create", "reschedule") },
	},

	// ---- Create: contact ----
	{
		displayName: "Full Name",
		name: "fullName",
		type: "string",
		default: "",
		required: true,
		displayOptions: { show: showForOps("create") },
	},
	{
		displayName: "Phone",
		name: "phone",
		type: "string",
		default: "",
		required: true,
		placeholder: "+491511234567",
		displayOptions: { show: showForOps("create") },
	},
	{
		displayName: "Email",
		name: "email",
		type: "string",
		default: "",
		displayOptions: { show: showForOps("create") },
	},
	{
		displayName: "Street",
		name: "street",
		type: "string",
		default: "",
		required: true,
		displayOptions: { show: showForOps("create") },
	},
	{
		displayName: "City",
		name: "city",
		type: "string",
		default: "",
		required: true,
		displayOptions: { show: showForOps("create") },
	},

	// ---- Create: confirmation gate ----
	{
		displayName: "Caller Confirmed",
		name: "callerConfirmed",
		type: "boolean",
		default: false,
		required: true,
		description:
			"Whether the caller explicitly confirmed the final date, time, address and phone number. The API rejects the booking otherwise (detailed spec §6).",
		displayOptions: { show: showForOps("create") },
	},
	{
		displayName: "Idempotency Key",
		name: "idempotencyKey",
		type: "string",
		default: "",
		required: true,
		placeholder: "booking-{{$json.sessionId}}-{{$json.confirmedSlot}}",
		description: "Replaying the same key returns the previous result instead of creating a duplicate booking",
		displayOptions: { show: showForOps("create", "reschedule", "cancel") },
	},

	// ---- Cancel: reason only shown here ----
	{
		displayName: "Cancellation Reason",
		name: "cancellationReason",
		type: "string",
		default: "",
		required: true,
		displayOptions: { show: showForOps("cancel") },
	},
];
