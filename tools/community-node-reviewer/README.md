# n8n-community-node-reviewer

Analyses an n8n community node repository and produces structured, actionable review feedback before a human reviewer looks at it (detailed spec §13). Checks package structure, code quality, credential security, API reliability handling, node UX/documentation, and testing — then scores the submission and decides whether it needs changes.

## Usage

```bash
npm install && npm run build

# Local path
node dist/cli.js ../path/to/community-node --format terminal

# GitHub repository (shallow clone)
node dist/cli.js --github-repo someone/n8n-nodes-example --format markdown --out review.md

# GitHub pull request (fetches the PR head ref)
node dist/cli.js --github-pr someone/n8n-nodes-example#42 --format json --out review.json

# Packaged npm module (npm pack + extract)
node dist/cli.js --npm-package n8n-nodes-example --format terminal
```

`--format` is `terminal` (default), `markdown`, or `json`. `--out <file>` writes the report to a file instead of stdout — pipe the markdown output into `gh pr comment` to post it, or the JSON output into a CI step to gate merges.

## Exit code

Exits `1` if any check both `FAIL`s and is marked blocking (e.g. a missing `n8n` field in `package.json`, a hard-coded secret, a credential returned in node output, or OAuth2 credentials with no refresh test) — wire this into a GitHub Actions step to block a contribution automatically. Exits `0` otherwise, even if there are non-blocking `WARN`s.

## Review categories

| Category | Examples of what's checked |
|---|---|
| Package structure | Valid `package.json`, `n8n.nodes`/`n8n.credentials` registration, naming/keywords, `tsconfig.json`, node metadata JSON |
| Code quality | `any` usage, unhandled-promise patterns, oversized files, unused dependencies, `eslint-disable` overuse |
| Credential security | Hard-coded secrets, unmasked password fields, missing credential test operation, query-string auth, secrets logged or returned in node output |
| API handling | 429/5xx retry with backoff, request timeouts, idempotency for writes, pagination, OAuth refresh, response validation |
| Node UX and documentation | Field descriptions, actionable error messages, README completeness (setup, limitations, tests, rate limits) |
| Testing | Test files exist, auth/credential tests, OAuth refresh tests, API mocks, pagination tests, retry tests, credential-redaction tests |

## Example output

Running against a fixture with real problems (`test/fixtures/bad-node`):

```
Community Node Review
Repository: test/fixtures/bad-node

FAIL  package.json is missing the "n8n" field registering nodes/credentials.
FAIL  No tsconfig.json found — TypeScript configuration is required.
FAIL  Possible hard-coded secret literal found in nodes/Bad/Bad.node.ts.
FAIL  nodes/Bad/Bad.node.ts appears to log a credential value directly.
WARN  nodes/Bad/Bad.node.ts appears to send an auth token via query string...
FAIL  No handling found for HTTP 429 (rate limit) responses with retry/backoff.
FAIL  No test files (*.test.ts) found.

Score: 41/100
Decision: Changes required
```

Running against this repo's own [`packages/n8n-nodes-werkcall`](../../packages/n8n-nodes-werkcall):

```
Score: 95/100
Decision: Approved
```

(Two honest `WARN`s remain — a list operation with no pagination, and a handful of fields without descriptions — see the tool run its own check against itself in `test/reviewer.test.ts`.)

## Known limitations

- Rules are regex/heuristic-based static analysis, not a full TypeScript type-check or AST walk — they catch common, real problems (see the bad-node fixture) but can produce false positives/negatives on unusual code styles. This is a first-pass triage tool, not a replacement for human review.
- `--github-pr` and `--github-repo` require `git` on PATH and network access; `--npm-package` requires `npm` and `tar`. All three fail with an actionable error message rather than crashing if the tool/network isn't available.
- No GitHub PR-comment posting is built in yet — pipe the markdown output into `gh pr comment --body-file` yourself (see the Usage section).

## Testing

```bash
npm test        # vitest: good fixture, bad fixture, and a dogfood run against packages/n8n-nodes-werkcall
npm run lint
npm run build && node dist/cli.js test/fixtures/good-node
```
