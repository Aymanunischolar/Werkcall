export type CheckLevel = "PASS" | "WARN" | "FAIL";

export type ReviewCategory =
	| "Package structure"
	| "Code quality"
	| "Credential security"
	| "API handling"
	| "Node UX and documentation"
	| "Testing";

export interface CheckResult {
	category: ReviewCategory;
	id: string;
	level: CheckLevel;
	message: string;
	/** FAILs in a blocking category cause a non-zero exit code (detailed
	 * spec §13: "GitHub Actions exit code that can block a contribution"). */
	blocking: boolean;
	file?: string;
}

export interface ReviewReport {
	repository: string;
	checks: CheckResult[];
	score: number;
	decision: "Approved" | "Changes required";
}

export interface RuleContext {
	/** Absolute path to the repository (or extracted PR/module) being reviewed. */
	rootDir: string;
	readFile: (relativePath: string) => string | null;
	fileExists: (relativePath: string) => boolean;
	listFiles: (pattern: RegExp) => string[];
}

export type Rule = (ctx: RuleContext) => CheckResult[];
