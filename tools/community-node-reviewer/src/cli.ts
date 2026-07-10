#!/usr/bin/env node
import { writeFileSync } from "node:fs";
import { renderJsonReport } from "./reporters/json.js";
import { renderMarkdownReport } from "./reporters/markdown.js";
import { renderTerminalReport } from "./reporters/terminal.js";
import { reviewRepository } from "./reviewer.js";
import { resolveSource, type SourceKind } from "./sources.js";

interface ParsedArgs {
	sourceKind: SourceKind;
	sourceValue: string;
	format: "terminal" | "markdown" | "json";
	outFile?: string;
}

function parseArgs(argv: string[]): ParsedArgs {
	let sourceKind: SourceKind = "path";
	let sourceValue: string | undefined;
	let format: ParsedArgs["format"] = "terminal";
	let outFile: string | undefined;

	for (let i = 0; i < argv.length; i++) {
		const arg = argv[i];
		if (arg === "--github-repo") {
			sourceKind = "github-repo";
			sourceValue = argv[++i];
		} else if (arg === "--github-pr") {
			sourceKind = "github-pr";
			sourceValue = argv[++i];
		} else if (arg === "--npm-package") {
			sourceKind = "npm-package";
			sourceValue = argv[++i];
		} else if (arg === "--format") {
			format = argv[++i] as ParsedArgs["format"];
		} else if (arg === "--out") {
			outFile = argv[++i];
		} else if (!arg.startsWith("--")) {
			sourceKind = "path";
			sourceValue = arg;
		}
	}

	if (!sourceValue) {
		throw new Error(
			"Usage: community-node-reviewer <path> | --github-repo owner/repo | --github-pr owner/repo#123 | --npm-package name [--format terminal|markdown|json] [--out file]",
		);
	}

	return { sourceKind, sourceValue, format, outFile };
}

function main(): void {
	const args = parseArgs(process.argv.slice(2));
	const source = resolveSource(args.sourceKind, args.sourceValue);

	try {
		const report = reviewRepository(source.rootDir, source.label);

		const rendered =
			args.format === "markdown" ? renderMarkdownReport(report) : args.format === "json" ? renderJsonReport(report) : renderTerminalReport(report);

		if (args.outFile) {
			writeFileSync(args.outFile, rendered);
		} else {
			console.log(rendered);
		}

		process.exitCode = report.decision === "Changes required" ? 1 : 0;
	} finally {
		source.cleanup?.();
	}
}

main();
