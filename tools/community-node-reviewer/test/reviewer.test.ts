import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { describe, expect, it } from "vitest";
import { reviewRepository } from "../src/reviewer.js";

const __dirname = dirname(fileURLToPath(import.meta.url));

describe("reviewRepository — good fixture", () => {
	const report = reviewRepository(join(__dirname, "fixtures/good-node"), "fixtures/good-node");

	it("finds no blocking failures", () => {
		const blocking = report.checks.filter((c) => c.level === "FAIL" && c.blocking);
		expect(blocking).toEqual([]);
	});

	it("decides Approved", () => {
		expect(report.decision).toBe("Approved");
	});

	it("scores reasonably high", () => {
		expect(report.score).toBeGreaterThanOrEqual(70);
	});
});

describe("reviewRepository — bad fixture", () => {
	const report = reviewRepository(join(__dirname, "fixtures/bad-node"), "fixtures/bad-node");

	it("flags the missing tsconfig.json as a blocking failure", () => {
		expect(report.checks.some((c) => c.id === "tsconfig-exists" && c.level === "FAIL")).toBe(true);
	});

	it("flags the missing n8n package.json field as a blocking failure", () => {
		expect(report.checks.some((c) => c.id === "pkg-n8n-field" && c.level === "FAIL")).toBe(true);
	});

	it("flags the hard-coded secret", () => {
		expect(report.checks.some((c) => c.id === "hardcoded-secret" && c.level === "FAIL")).toBe(true);
	});

	it("flags the token being logged", () => {
		expect(report.checks.some((c) => c.id === "secret-in-logs" && c.level === "FAIL")).toBe(true);
	});

	it("flags the query-string auth token", () => {
		expect(report.checks.some((c) => c.id === "query-string-auth")).toBe(true);
	});

	it("flags no rate-limit/retry handling", () => {
		expect(report.checks.some((c) => c.id === "rate-limit-handling" && c.level === "FAIL")).toBe(true);
	});

	it("flags no tests", () => {
		expect(report.checks.some((c) => c.id === "tests-exist" && c.level === "FAIL")).toBe(true);
	});

	it("decides Changes required", () => {
		expect(report.decision).toBe("Changes required");
	});

	it("scores lower than the good fixture", () => {
		const goodReport = reviewRepository(join(__dirname, "fixtures/good-node"), "fixtures/good-node");
		expect(report.score).toBeLessThan(goodReport.score);
	});
});

describe("reviewRepository — dogfood: the real n8n-nodes-werkcall package", () => {
	const rootDir = join(__dirname, "../../../packages/n8n-nodes-werkcall");
	const report = reviewRepository(rootDir, "packages/n8n-nodes-werkcall");

	it("finds no blocking credential-security failures", () => {
		const blocking = report.checks.filter(
			(c) => c.level === "FAIL" && c.blocking && c.category === "Credential security",
		);
		expect(blocking).toEqual([]);
	});

	it("passes API handling's rate-limit/backoff check", () => {
		expect(report.checks.some((c) => c.id === "rate-limit-handling" && c.level === "PASS")).toBe(true);
	});

	it("passes the testing category's tests-exist check", () => {
		expect(report.checks.some((c) => c.id === "tests-exist" && c.level === "PASS")).toBe(true);
	});
});
