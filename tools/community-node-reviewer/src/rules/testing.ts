import type { CheckResult, Rule } from "../types.js";

export const testingRule: Rule = (ctx) => {
	const results: CheckResult[] = [];
	const push = (id: string, level: CheckResult["level"], message: string, blocking = false, file?: string) =>
		results.push({ category: "Testing", id, level, message, blocking, file });

	const testFiles = ctx.listFiles(/\.test\.ts$/);
	if (testFiles.length === 0) {
		push("tests-exist", "FAIL", "No test files (*.test.ts) found.", true);
		return results;
	}
	push("tests-exist", "PASS", `${testFiles.length} test file(s) found.`);

	const combinedTests = testFiles.map((f) => ctx.readFile(f) ?? "").join("\n");
	const combinedSource = ctx
		.listFiles(/\.ts$/)
		.filter((f) => !f.endsWith(".test.ts"))
		.map((f) => ctx.readFile(f) ?? "")
		.join("\n");

	const usesOAuth = /oAuth2Api|extends\s*=\s*\[.*oAuth2/i.test(combinedSource);
	const hasAuthTests = /(credential|auth|oauth|token)/i.test(combinedTests);
	push(
		"authentication-tests",
		hasAuthTests ? "PASS" : "WARN",
		hasAuthTests ? "Tests cover authentication/credential behaviour." : "No tests reference credentials, auth, or tokens.",
	);
	if (usesOAuth) {
		const hasOAuthRefreshTest = /refresh/i.test(combinedTests);
		push(
			"oauth-refresh-tests",
			hasOAuthRefreshTest ? "PASS" : "FAIL",
			hasOAuthRefreshTest ? "OAuth refresh behaviour is covered by tests." : "OAuth2 credential exists but no test covers token refresh/expiry.",
			!hasOAuthRefreshTest,
		);
	}

	const hasApiMocks = /vi\.fn|jest\.fn|nock|msw|sinon/i.test(combinedTests);
	push("api-mocks", hasApiMocks ? "PASS" : "WARN", hasApiMocks ? "Tests use mocked API calls." : "No mocking library usage detected in tests — are API calls tested at all?");

	const hasPaginationTests = /pagination|nextPage|cursor/i.test(combinedTests);
	const hasPaginationSource = /pagination|nextPage|cursor/i.test(combinedSource);
	if (hasPaginationSource) {
		push("pagination-tests", hasPaginationTests ? "PASS" : "WARN", hasPaginationTests ? "Pagination is covered by tests." : "Pagination logic exists but has no dedicated test.");
	}

	const hasRetryTests = /(429|5xx|502|503|backoff)/i.test(combinedTests);
	push("retry-tests", hasRetryTests ? "PASS" : "WARN", hasRetryTests ? "Retry/backoff behaviour is covered by tests." : "No tests found for retry/backoff behaviour on 429/5xx.");

	const hasRedactionTests = /redact/i.test(combinedTests);
	const hasRedactionSource = /redact/i.test(combinedSource);
	if (hasRedactionSource) {
		push(
			"credential-redaction-tests",
			hasRedactionTests ? "PASS" : "FAIL",
			hasRedactionTests ? "Credential redaction is covered by tests." : "Redaction logic exists in source but is not tested.",
			!hasRedactionTests,
		);
	}

	return results;
};
