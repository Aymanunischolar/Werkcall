import type { CheckResult, Rule } from "../types.js";

export const packageStructureRule: Rule = (ctx) => {
	const results: CheckResult[] = [];
	const push = (id: string, level: CheckResult["level"], message: string, blocking = false, file?: string) =>
		results.push({ category: "Package structure", id, level, message, blocking, file });

	const pkgRaw = ctx.readFile("package.json");
	if (!pkgRaw) {
		push("pkg-json-exists", "FAIL", "No package.json found at the repository root.", true);
		return results;
	}

	let pkg: Record<string, unknown>;
	try {
		pkg = JSON.parse(pkgRaw);
	} catch {
		push("pkg-json-valid", "FAIL", "package.json is not valid JSON.", true, "package.json");
		return results;
	}
	push("pkg-json-valid", "PASS", "package.json is valid JSON.", false, "package.json");

	const name = typeof pkg.name === "string" ? pkg.name : "";
	if (!name.startsWith("n8n-nodes-")) {
		push("pkg-naming", "WARN", `Package name "${name}" does not follow the n8n-nodes-* convention.`, false, "package.json");
	} else {
		push("pkg-naming", "PASS", "Package name follows the n8n-nodes-* convention.", false, "package.json");
	}

	const keywords = Array.isArray(pkg.keywords) ? (pkg.keywords as string[]) : [];
	if (!keywords.includes("n8n-community-node-package")) {
		push(
			"pkg-keywords",
			"WARN",
			'package.json keywords should include "n8n-community-node-package" so npm/n8n can discover it.',
			false,
			"package.json",
		);
	} else {
		push("pkg-keywords", "PASS", 'Keywords include "n8n-community-node-package".', false, "package.json");
	}

	const n8nField = pkg.n8n as { nodes?: string[]; credentials?: string[] } | undefined;
	if (!n8nField) {
		push("pkg-n8n-field", "FAIL", 'package.json is missing the "n8n" field registering nodes/credentials.', true, "package.json");
	} else {
		const nodes = n8nField.nodes ?? [];
		const credentials = n8nField.credentials ?? [];
		if (nodes.length === 0) {
			push("pkg-n8n-nodes", "FAIL", 'package.json "n8n.nodes" is empty — no node is registered.', true, "package.json");
		} else {
			push("pkg-n8n-nodes", "PASS", `${nodes.length} node(s) registered in package.json.`, false, "package.json");
		}
		if (credentials.length === 0) {
			push("pkg-n8n-credentials", "WARN", 'package.json "n8n.credentials" is empty.', false, "package.json");
		} else {
			push("pkg-n8n-credentials", "PASS", `${credentials.length} credential type(s) registered.`, false, "package.json");
		}
	}

	if (!ctx.fileExists("tsconfig.json")) {
		push("tsconfig-exists", "FAIL", "No tsconfig.json found — TypeScript configuration is required.", true);
	} else {
		push("tsconfig-exists", "PASS", "tsconfig.json is present.", false, "tsconfig.json");
		const tsconfigRaw = ctx.readFile("tsconfig.json") ?? "{}";
		if (!/"outDir"/.test(tsconfigRaw)) {
			push("tsconfig-outdir", "WARN", "tsconfig.json does not set outDir for compiled output.", false, "tsconfig.json");
		}
	}

	const nodeFiles = ctx.listFiles(/nodes\/.+\.node\.ts$/);
	if (nodeFiles.length === 0) {
		push("node-files-exist", "FAIL", "No *.node.ts file found under nodes/.", true);
	} else {
		for (const nodeFile of nodeFiles) {
			const jsonSibling = nodeFile.replace(/\.node\.ts$/, ".node.json");
			if (!ctx.fileExists(jsonSibling)) {
				push("node-metadata-json", "WARN", `Missing ${jsonSibling} (node codex metadata).`, false, nodeFile);
			}
		}
	}

	return results;
};
