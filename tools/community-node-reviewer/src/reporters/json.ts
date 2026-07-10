import type { ReviewReport } from "../types.js";

export function renderJsonReport(report: ReviewReport): string {
	return JSON.stringify(report, null, 2);
}
