import type { CheckResult, Rule } from "../types.js";

const MAX_RECOMMENDED_LINES = 400;

export const codeQualityRule: Rule = (ctx) => {
	const results: CheckResult[] = [];
	const push = (id: string, level: CheckResult["level"], message: string, blocking = false, file?: string) =>
		results.push({ category: "Code quality", id, level, message, blocking, file });

	const tsFiles = ctx.listFiles(/\.ts$/).filter((f) => !f.endsWith(".d.ts") && !f.includes("/test/") && !f.endsWith(".test.ts"));

	if (tsFiles.length === 0) {
		push("ts-source-exists", "FAIL", "No TypeScript source files found.", true);
		return results;
	}
	push("ts-source-exists", "PASS", `${tsFiles.length} TypeScript source file(s) found.`);

	let anyCount = 0;
	let unhandledPromiseCandidates = 0;
	let oversizedFiles = 0;
	let disableComments = 0;

	for (const file of tsFiles) {
		const content = ctx.readFile(file) ?? "";
		const lines = content.split("\n");
		if (lines.length > MAX_RECOMMENDED_LINES) {
			oversizedFiles += 1;
			push(
				"oversized-file",
				"WARN",
				`${file} is ${lines.length} lines — consider splitting into smaller modules.`,
				false,
				file,
			);
		}

		anyCount += (content.match(/:\s*any\b/g) ?? []).length;

		// Heuristic: a bare `someAsyncCall()` on its own statement line, not
		// preceded by await/return/void and not assigned, is a likely
		// unhandled promise (detailed spec §13 "Unhandled promises").
		const bareAsyncCalls = content.match(/^\s*[a-zA-Z_$][\w$.]*\([^)]*\);\s*$/gm) ?? [];
		for (const line of bareAsyncCalls) {
			if (/\b(request|fetch|Promise|send|execute|save|delete|update|create)\w*\(/i.test(line)) {
				unhandledPromiseCandidates += 1;
			}
		}

		disableComments += (content.match(/eslint-disable/g) ?? []).length;
	}

	if (anyCount > 0) {
		push("unsafe-any", anyCount > 5 ? "WARN" : "PASS", `Found ${anyCount} explicit "any" type annotation(s) across the package.`);
	} else {
		push("unsafe-any", "PASS", 'No explicit "any" type annotations found.');
	}

	if (unhandledPromiseCandidates > 0) {
		push(
			"unhandled-promises",
			"WARN",
			`Found ${unhandledPromiseCandidates} statement(s) that look like un-awaited async calls — verify they don't swallow rejections.`,
		);
	} else {
		push("unhandled-promises", "PASS", "No obvious unhandled-promise patterns found.");
	}

	if (disableComments > 3) {
		push("eslint-disable-count", "WARN", `${disableComments} eslint-disable comments found — check they're not masking real issues.`);
	} else {
		push("eslint-disable-count", "PASS", "eslint-disable usage is limited.");
	}

	if (oversizedFiles === 0) {
		push("oversized-file", "PASS", "No files exceed the recommended size — this line only fires if none were flagged above.");
	}

	// Unused dependency heuristic: a dependency listed in package.json that
	// never appears in any import/require statement.
	const pkgRaw = ctx.readFile("package.json");
	if (pkgRaw) {
		try {
			const pkg = JSON.parse(pkgRaw) as { dependencies?: Record<string, string> };
			const deps = Object.keys(pkg.dependencies ?? {});
			const allSource = tsFiles.map((f) => ctx.readFile(f) ?? "").join("\n");
			const unused = deps.filter((dep) => !new RegExp(`['"\`]${dep.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}['"\`]`).test(allSource));
			if (unused.length > 0) {
				push("unused-dependencies", "WARN", `Possibly unused dependencies: ${unused.join(", ")}.`);
			} else if (deps.length > 0) {
				push("unused-dependencies", "PASS", "All declared dependencies appear to be used.");
			}
		} catch {
			// package.json already flagged by packageStructureRule
		}
	}

	return results;
};
