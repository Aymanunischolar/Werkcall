import type { ReviewReport } from "../types.js";

const LEVEL_LABEL: Record<string, string> = { PASS: "PASS", WARN: "WARN", FAIL: "FAIL" };

export function renderTerminalReport(report: ReviewReport): string {
	const lines: string[] = [];
	lines.push("Community Node Review");
	lines.push(`Repository: ${report.repository}`);
	lines.push("");

	for (const check of report.checks) {
		const label = LEVEL_LABEL[check.level].padEnd(5);
		lines.push(`${label} ${check.message}`);
	}

	lines.push("");
	lines.push(`Score: ${report.score}/100`);
	lines.push(`Decision: ${report.decision}`);

	return lines.join("\n");
}
