import type { CheckResult, Rule } from "../types.js";

export const nodeUxRule: Rule = (ctx) => {
	const results: CheckResult[] = [];
	const push = (id: string, level: CheckResult["level"], message: string, blocking = false, file?: string) =>
		results.push({ category: "Node UX and documentation", id, level, message, blocking, file });

	const nodeFiles = ctx.listFiles(/nodes\/.+\.node\.ts$/);
	const descriptionFiles = ctx.listFiles(/descriptions\/.+\.ts$/);
	const propertyFiles = [...nodeFiles, ...descriptionFiles];

	let propertiesWithoutDescription = 0;
	let totalProperties = 0;
	for (const file of propertyFiles) {
		const content = ctx.readFile(file) ?? "";
		const propertyBlocks = content.match(/\{\s*displayName:[\s\S]*?\n\t\},?/g) ?? [];
		for (const block of propertyBlocks) {
			totalProperties += 1;
			if (!/description\s*:/.test(block) && !/type:\s*["'](options|hidden)["']/.test(block)) {
				propertiesWithoutDescription += 1;
			}
		}
	}
	if (totalProperties === 0) {
		push("node-properties-found", "WARN", "Could not find any INodeProperties definitions to check.");
	} else if (propertiesWithoutDescription > 0) {
		push(
			"missing-field-descriptions",
			"WARN",
			`${propertiesWithoutDescription}/${totalProperties} node field(s) have no "description" — operators may not know what to enter.`,
		);
	} else {
		push("missing-field-descriptions", "PASS", "All checked node fields have a description or are self-explanatory option/hidden fields.");
	}

	const errorMessages = nodeFiles
		.map((f) => ctx.readFile(f) ?? "")
		.join("\n")
		.match(/throw new Error\(([\s\S]*?)\);/g) ?? [];
	const genericErrors = errorMessages.filter((msg) => !/fix:|must be|is not (a )?valid/i.test(msg));
	if (errorMessages.length > 0 && genericErrors.length > 0) {
		push(
			"actionable-error-messages",
			"WARN",
			`${genericErrors.length}/${errorMessages.length} thrown error(s) don't explain what the user needs to fix.`,
		);
	} else if (errorMessages.length > 0) {
		push("actionable-error-messages", "PASS", "Thrown errors explain what the user needs to fix.");
	}

	const readme = ctx.readFile("README.md");
	if (!readme) {
		push("readme-exists", "FAIL", "No README.md found at the package root.", true);
	} else {
		push("readme-exists", "PASS", "README.md found.", false, "README.md");
		const checks: Array<[RegExp, string]> = [
			[/setup|install/i, "setup/installation instructions"],
			[/limitation|known issue/i, "known limitations"],
			[/test/i, "test instructions"],
			[/rate limit/i, "rate-limit documentation"],
		];
		for (const [pattern, label] of checks) {
			if (!pattern.test(readme)) {
				push("readme-completeness", "WARN", `README.md does not appear to document ${label}.`, false, "README.md");
			}
		}
	}

	return results;
};
