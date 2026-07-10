import { buildContext } from "./context.js";
import { apiHandlingRule } from "./rules/apiHandling.js";
import { codeQualityRule } from "./rules/codeQuality.js";
import { credentialSecurityRule } from "./rules/credentialSecurity.js";
import { nodeUxRule } from "./rules/nodeUx.js";
import { packageStructureRule } from "./rules/packageStructure.js";
import { testingRule } from "./rules/testing.js";
import type { CheckResult, ReviewReport, Rule } from "./types.js";

const RULES: Rule[] = [packageStructureRule, codeQualityRule, credentialSecurityRule, apiHandlingRule, nodeUxRule, testingRule];

const LEVEL_WEIGHT: Record<CheckResult["level"], number> = { PASS: 1, WARN: 0.5, FAIL: 0 };

export function reviewRepository(rootDir: string, repositoryLabel: string): ReviewReport {
	const ctx = buildContext(rootDir);
	const checks = RULES.flatMap((rule) => rule(ctx));

	const score = checks.length === 0 ? 0 : Math.round((checks.reduce((sum, c) => sum + LEVEL_WEIGHT[c.level], 0) / checks.length) * 100);

	const hasBlockingFailure = checks.some((c) => c.level === "FAIL" && c.blocking);
	const decision = hasBlockingFailure ? "Changes required" : "Approved";

	return { repository: repositoryLabel, checks, score, decision };
}
