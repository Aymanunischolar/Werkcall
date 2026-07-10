import type { CheckResult, Rule } from "../types.js";

const HARDCODED_SECRET_PATTERNS = [
	/["'](sk|pk)_(live|test)_[A-Za-z0-9]{10,}["']/,
	/["']AKIA[0-9A-Z]{16}["']/,
	/apiKey\s*[:=]\s*["'][A-Za-z0-9\-_]{16,}["']/,
	/(client_secret|clientSecret)\s*[:=]\s*["'][A-Za-z0-9\-_]{10,}["']/,
];

export const credentialSecurityRule: Rule = (ctx) => {
	const results: CheckResult[] = [];
	const push = (id: string, level: CheckResult["level"], message: string, blocking = false, file?: string) =>
		results.push({ category: "Credential security", id, level, message, blocking, file });

	const credentialFiles = ctx.listFiles(/credentials\/.+\.credentials\.ts$/);
	const nodeFiles = ctx.listFiles(/nodes\/.+\.node\.ts$/);
	const allSourceFiles = ctx.listFiles(/\.ts$/).filter((f) => !f.endsWith(".test.ts"));

	if (credentialFiles.length === 0) {
		push("credential-files-exist", "WARN", "No *.credentials.ts file found — is authentication handled elsewhere?");
	} else {
		push("credential-files-exist", "PASS", `${credentialFiles.length} credential file(s) found.`);
	}

	let hardcodedFound = false;
	for (const file of allSourceFiles) {
		const content = ctx.readFile(file) ?? "";
		for (const pattern of HARDCODED_SECRET_PATTERNS) {
			if (pattern.test(content)) {
				hardcodedFound = true;
				push("hardcoded-secret", "FAIL", `Possible hard-coded secret literal found in ${file}.`, true, file);
			}
		}
	}
	if (!hardcodedFound) {
		push("hardcoded-secret", "PASS", "No hard-coded secret literals detected.");
	}

	for (const file of credentialFiles) {
		const content = ctx.readFile(file) ?? "";
		const looksLikeSecret = /name:\s*["'](apiKey|secret|token|clientSecret|password)["']/i.test(content);
		if (looksLikeSecret && !/typeOptions:\s*\{\s*password:\s*true/.test(content)) {
			push(
				"credential-masking",
				"FAIL",
				`${file} defines a secret-looking field without typeOptions: { password: true } — it will render in plain text in the UI.`,
				true,
				file,
			);
		} else if (looksLikeSecret) {
			push("credential-masking", "PASS", `${file} masks its secret field(s) in the UI.`, false, file);
		}

		if (!/\btest\s*[:=]/.test(content) && !/extends\s*=\s*\[["']oAuth2Api["']\]/.test(content)) {
			push("credential-test-operation", "WARN", `${file} has no credential test operation — users can't verify setup before running a workflow.`, false, file);
		} else {
			push("credential-test-operation", "PASS", `${file} provides a way to verify credentials.`, false, file);
		}
	}

	for (const file of nodeFiles) {
		const content = ctx.readFile(file) ?? "";
		const hasQueryStringAuth =
			/qs\s*:\s*\{[^}]*\b(apiKey|api_key|token|secret)\b/i.test(content) ||
			/[?&](apiKey|api_key|token|secret|access_token)=/i.test(content);
		if (hasQueryStringAuth) {
			push(
				"query-string-auth",
				"WARN",
				`${file} appears to send an auth token via query string — prefer an Authorization header (query strings leak into logs/proxies).`,
				false,
				file,
			);
		}
		if (/console\.(log|error|warn)\([^)]*(apiKey|token|secret|password)/i.test(content)) {
			push("secret-in-logs", "FAIL", `${file} appears to log a credential value directly.`, true, file);
		}
		if (/return\s*\{[^}]*credentials\b/i.test(content)) {
			push("secret-in-output", "FAIL", `${file} appears to return raw credentials in node output.`, true, file);
		}
	}

	return results;
};
