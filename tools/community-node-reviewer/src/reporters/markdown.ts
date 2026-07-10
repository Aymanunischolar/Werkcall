import type { CheckResult, ReviewReport } from "../types.js";

const LEVEL_EMOJI: Record<CheckResult["level"], string> = { PASS: "✅", WARN: "⚠️", FAIL: "❌" };

export function renderMarkdownReport(report: ReviewReport): string {
	const byCategory = new Map<string, CheckResult[]>();
	for (const check of report.checks) {
		byCategory.set(check.category, [...(byCategory.get(check.category) ?? []), check]);
	}

	const lines: string[] = [];
	lines.push(`## Community Node Review — ${report.repository}`);
	lines.push("");
	lines.push(`**Score:** ${report.score}/100  `);
	lines.push(`**Decision:** ${report.decision === "Approved" ? "✅ Approved" : "❌ Changes required"}`);
	lines.push("");

	const blocking = report.checks.filter((c) => c.level === "FAIL" && c.blocking);
	if (blocking.length > 0) {
		lines.push("### Blocking issues");
		for (const check of blocking) {
			lines.push(`- **${check.file ?? "repository"}**: ${check.message}`);
		}
		lines.push("");
	}

	for (const [category, checks] of byCategory) {
		lines.push(`### ${category}`);
		lines.push("");
		for (const check of checks) {
			lines.push(`- ${LEVEL_EMOJI[check.level]} ${check.message}${check.file ? ` (\`${check.file}\`)` : ""}`);
		}
		lines.push("");
	}

	return lines.join("\n");
}
