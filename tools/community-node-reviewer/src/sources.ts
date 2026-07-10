import { execFileSync } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

/** Resolves any of the four supported input kinds (detailed spec §13) down
 * to a local directory the rule engine can walk. Network-dependent kinds
 * shell out to git/npm and fail with an actionable message if those tools
 * or network access aren't available — this keeps the reviewer usable
 * offline against a local path, which is the primary, tested path. */
export type SourceKind = "path" | "github-repo" | "github-pr" | "npm-package";

export interface ResolvedSource {
	rootDir: string;
	label: string;
	cleanup?: () => void;
}

function tempDir(prefix: string): string {
	return mkdtempSync(join(tmpdir(), prefix));
}

export function resolveSource(kind: SourceKind, value: string): ResolvedSource {
	if (kind === "path") {
		return { rootDir: value, label: value };
	}

	if (kind === "github-repo") {
		const dir = tempDir("werkcall-reviewer-repo-");
		try {
			execFileSync("git", ["clone", "--depth", "1", `https://github.com/${value}.git`, dir], { stdio: "pipe" });
		} catch (error) {
			throw new Error(`Failed to clone github.com/${value} — fix: check network access and that the repo exists. (${(error as Error).message})`);
		}
		return { rootDir: dir, label: value };
	}

	if (kind === "github-pr") {
		const [repo, prNumber] = value.split("#");
		if (!repo || !prNumber) {
			throw new Error('--github-pr expects "owner/repo#123" — fix: include the PR number after "#".');
		}
		const dir = tempDir("werkcall-reviewer-pr-");
		try {
			execFileSync("git", ["clone", "--depth", "1", `https://github.com/${repo}.git`, dir], { stdio: "pipe" });
			execFileSync("git", ["fetch", "origin", `pull/${prNumber}/head:pr-${prNumber}`], { cwd: dir, stdio: "pipe" });
			execFileSync("git", ["checkout", `pr-${prNumber}`], { cwd: dir, stdio: "pipe" });
		} catch (error) {
			throw new Error(
				`Failed to check out ${repo}#${prNumber} — fix: check network access, that the PR exists, and that git is installed. (${(error as Error).message})`,
			);
		}
		return { rootDir: dir, label: `${repo}#${prNumber}` };
	}

	if (kind === "npm-package") {
		const dir = tempDir("werkcall-reviewer-npm-");
		try {
			const packOutput = execFileSync("npm", ["pack", value, "--pack-destination", dir, "--json"], { stdio: "pipe" })
				.toString()
				.trim();
			const [{ filename }] = JSON.parse(packOutput) as Array<{ filename: string }>;
			execFileSync("tar", ["-xzf", join(dir, filename), "-C", dir], { stdio: "pipe" });
		} catch (error) {
			throw new Error(`Failed to download npm package "${value}" — fix: check the package name and network access. (${(error as Error).message})`);
		}
		return { rootDir: join(dir, "package"), label: value };
	}

	throw new Error(`Unknown source kind: ${kind}`);
}
