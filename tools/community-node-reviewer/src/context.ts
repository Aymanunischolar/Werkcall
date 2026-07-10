import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import type { RuleContext } from "./types.js";

const IGNORED_DIRS = new Set(["node_modules", "dist", ".git", "coverage"]);

function walk(dir: string, out: string[]): void {
	for (const entry of readdirSync(dir)) {
		if (IGNORED_DIRS.has(entry)) continue;
		const full = join(dir, entry);
		const stat = statSync(full);
		if (stat.isDirectory()) {
			walk(full, out);
		} else {
			out.push(full);
		}
	}
}

export function buildContext(rootDir: string): RuleContext {
	let allFiles: string[] | null = null;
	const getAllFiles = () => {
		if (!allFiles) {
			allFiles = [];
			walk(rootDir, allFiles);
		}
		return allFiles;
	};

	return {
		rootDir,
		readFile: (relativePath: string) => {
			const full = join(rootDir, relativePath);
			if (!existsSync(full)) return null;
			try {
				return readFileSync(full, "utf-8");
			} catch {
				return null;
			}
		},
		fileExists: (relativePath: string) => existsSync(join(rootDir, relativePath)),
		listFiles: (pattern: RegExp) =>
			getAllFiles()
				.map((f) => relative(rootDir, f).replace(/\\/g, "/"))
				.filter((f) => pattern.test(f)),
	};
}
