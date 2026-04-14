---
name: audit-security
description: Runs a deliberately small, hand-curated security sweep across a repo. Finds secrets committed to git, SQL/shell injection patterns, XSS sinks, path traversal, dangerous deserialization, missing cookie flags, wildcard CORS, and tracked credential files. Triages every finding as real / false-positive / needs-review before reporting. Language-agnostic, no heavyweight scanner required.
when_to_use: Trigger on "is this safe", "security check", "audit", "any vulnerabilities", "anything leaked", "is my .env exposed", "OWASP", before public releases or open-sourcing, after a major refactor, or when the operator mentions a data breach, incident, or scare.
allowed-tools: Grep Glob Read Bash(git log *) Bash(git show *) Bash(git ls-files *) Bash(git grep *)
---

# audit-security

A security audit that the operator will actually read.

Enterprise scanners emit hundreds of warnings. Non-developers silence them within a week and then a real vulnerability slips through because nobody's reading anymore. The opposite strategy works better: **a short, hand-curated list of patterns that are almost always actionable, each one triaged individually.** Every hit gets classified. Every classification has a reason.

## The rule

Never report more than ~20 findings. If the automated sweep returns 100 hits, triage them into categories and report the categories, not the raw list. The operator's attention is the scarcest resource and the wrong optimization is "comprehensive."

## When to trigger

Any of:

- "is this safe"
- "security check" / "security audit"
- "are there any vulnerabilities"
- "any secrets leaked"
- "is my `.env` exposed"
- "OWASP"
- before a public release or open-sourcing
- after a major refactor (run together with `refactor-verify`)
- when the operator mentions a data breach, incident, or scare

If the operator asks for something outside this skill's scope (compliance audits, penetration testing, crypto review), say so plainly and suggest a specialist tool.

## Upfront constraint lock-in

Before running, establish three things with the operator. Do not start the sweep until these are clear:

1. **Scope** — the whole repo, one directory, one file, or one PR diff?
2. **Severity threshold** — report everything found, or only HIGH/CRITICAL?
3. **Runtime context** — is this code behind an authenticated endpoint, public, internal tool, or CLI? The same pattern is a different severity depending on context.

If the operator doesn't know the answers, pick the most conservative defaults: whole repo, report all, assume public-facing. Tell them that's what you picked.

## The patterns (what to sweep)

These are the ten categories. Each category has language-specific grep/AST patterns in `references/patterns.md`. Run them all; don't skip any for time.

### 1. Hardcoded secrets in tracked files

- API keys, tokens, passwords, private keys
- Regex for typical prefix patterns (`sk-`, `ghp_`, `xoxb-`, `-----BEGIN`, etc.)
- High-entropy strings in config/source files
- `git log --all -p -S<suspect>` to see if ever committed historically

Also check whether **secret files themselves** are tracked:

```bash
git ls-files | grep -iE '\.env$|\.env\.|\.pem$|id_rsa|id_ed25519|credentials|\.ppk$'
```

Anything returned here is an immediate HIGH regardless of content.

### 2. SQL injection

SQL built by pasting strings. Language-agnostic pattern:

- Query text that contains an interpolation marker inside a function call named `execute`, `query`, `raw`, or `fetch`
- F-strings / template literals / `.format()` / `%` inside a query call
- String concatenation (`+`, `.`, `..`) inside a query call

Prepared-statement placeholders (`?`, `$1`, `:name`) are the safe form. Flag anything else.

### 3. Shell / command injection

- `subprocess.run(..., shell=True)`
- `child_process.exec(userInput)` (as opposed to `execFile`/`spawn` with args)
- Backticks or `$()` with user input in shell scripts
- `os.system` anywhere
- `eval` / `exec` / `Function(userInput)` / `setTimeout(userInput, ...)` (in JS)
- `pickle.loads` on anything that might come from a network
- `yaml.load` without `SafeLoader`

### 4. Path traversal

- `open(request.something)`, `fs.readFile(req.query.x)`, `File.new(params[:path])`
- Any file-reading call whose path argument traces back to user input without a whitelist regex
- `FileResponse` / `sendFile` with user-controlled path segments

### 5. XSS sinks

- `innerHTML =`, `dangerouslySetInnerHTML`, `v-html`, `{@html ...}` (Svelte)
- `document.write(`
- Jinja2 `|safe`, Django `mark_safe`
- Markdown renderers whose HTML output is injected into the DOM without an explicit sanitizer step:
  - **`marked`** does **not** sanitize HTML output. The historical `sanitize: true` option was deprecated and removed. The renderer will faithfully reproduce any `<script>` it finds in the input. Pair it with **DOMPurify** on the rendered HTML before injecting it into the DOM.
  - **`markdown-it`** disables HTML input by default (`html: false`), which is safe as long as the option is not overridden. If `html: true` is set anywhere, the output must be sanitized downstream (DOMPurify again).
  - **`showdown`** similarly does not sanitize. Use a sanitizer on the output.
  - Any other Markdown library — check its docs. "Sanitize" in a Markdown renderer's API almost always means "disable raw HTML input," not "clean the HTML output." They are different guarantees, and non-developers conflate them.
- **Server-side rendering of user-authored Markdown into HTML** — same rules. Use `bleach` (Python), `sanitize-html` (Node), or language-equivalent after rendering. Never trust Markdown input to be safe just because the renderer "supports" sanitization.

### 6. Dangerous deserialization

- `pickle.loads` / `cloudpickle.loads`
- `yaml.load` / `yaml.Loader` (use `yaml.safe_load` / `yaml.SafeLoader`)
- `Marshal.load` (Ruby) on untrusted input
- `ObjectInputStream` (Java) on untrusted streams
- `unserialize` (PHP) on user input

### 7. Missing cookie safety flags

Every `set_cookie` / `Set-Cookie` call should include `httpOnly`, `Secure`, and `SameSite`. Flag any that don't.

### 8. CORS wildcard

Any response header `Access-Control-Allow-Origin: *` on an endpoint that isn't a public CDN. Especially dangerous if combined with `Access-Control-Allow-Credentials: true` (actually forbidden by the spec but some code tries).

### 9. Dependency / lockfile hygiene

- Unpinned dependencies in production (`requirements.txt` with no `==`, `package.json` with `^` or `*`, `Cargo.toml` with no lockfile)
- Known-bad packages (typosquats, abandoned packages) — name match against a small blocklist
- Lockfile missing for a language that should have one (`package-lock.json`, `Cargo.lock`, `Gemfile.lock`)

### 10. Auth / session pitfalls

- Session cookies without rotation on login
- Hardcoded admin bypass paths (`if user_id == 1:` style)
- JWT signing with `none` algorithm
- Password comparison with `==` instead of constant-time compare
- `Math.random()` used for session tokens / salts / OTPs (not cryptographically secure)

## Triage — the critical step

For every hit, classify it as one of:

| Classification | Meaning | Action |
|---|---|---|
| **REAL — CRITICAL** | Exploitable remotely, data exposure, or secret leak | Fix now, then commit |
| **REAL — HIGH** | Exploitable but requires auth or specific context | Fix this sprint |
| **REAL — MEDIUM** | Defense-in-depth gap, not directly exploitable | Queue for cleanup |
| **FALSE POSITIVE** | The pattern matched but the code is actually safe | Explain *why* it's safe and move on — do not "fix" it |
| **NEEDS REVIEW** | You can't tell without more context (e.g., is this input trusted?) | Ask the operator one specific question |

**Never just list findings without classification.** A raw list of grep matches is worse than no audit, because the operator can't tell signal from noise.

When explaining a false positive, be specific: *"This f-string inside a query is safe because `days` is an integer from `int(request.query.get(...))` clamped to `0..365` on line 391."* The specificity proves you actually looked.

Per-pattern triage rules: `references/false-positive-triage.md`

## Output format

Always structured. Never a prose wall.

```markdown
# Security sweep — <scope>

## Summary
- Scope: <files/dirs swept>
- Runtime context: <public / authenticated / internal>
- Total findings: <N>
- Triage: <X critical, Y high, Z medium, W false-positive>

## Critical (<N>)

### 1. <Category> — <file:line>
**What was found:** <quoted line>
**Why it's real:** <one-sentence reason>
**Fix:** <concrete code change or command>

### 2. ...

## High (<N>)
...

## Medium (<N>)
...

## False positives (<N>)
Listed only to show they were checked. No action needed.

### 1. <Category> — <file:line>
**Why not a vulnerability:** <specific reason>

## Needs review (<N>)
One specific question per item so the operator can answer and close it.

### 1. <Category> — <file:line>
**Question:** <precise question>
```

## Deliberately out of scope

This skill is a **minimal hand-curated sweep**, not a full application security audit. If the operator needs any of the following, say so plainly and recommend a dedicated tool or human reviewer.

| Class of issue | Why this skill doesn't cover it | What to use instead |
|---|---|---|
| **SSRF** (Server-Side Request Forgery) | Requires dataflow tracing from user input to outbound HTTP clients. Language-agnostic grep is too coarse to avoid false positives. | Semgrep with SSRF rulepacks; language-specific SAST |
| **CSRF** (Cross-Site Request Forgery) | Framework-specific. Django, Rails, Next.js each have their own CSRF story. A generic checker gives false confidence. | Verify the framework's CSRF middleware is enabled and tokens are required on state-changing routes |
| **IDOR** (Insecure Direct Object Reference) | Requires understanding the application's authorization model. "Does this user have permission to read `/orders/42`?" cannot be answered by grep. | Manual review of every route that takes an ID from the URL; pen test for critical flows |
| **Unsafe file upload** | Requires runtime behavior (magic bytes, content-type validation, storage isolation). A pattern match catches obvious cases but misses most. | Dedicated upload validation libraries; storage in a separate origin |
| **Open redirect** | Partially covered (hardcoded redirects), but dynamic redirect targets built from query parameters need dataflow analysis. | Whitelist allowed redirect domains; Semgrep `open-redirect` rulepack |
| **Business logic flaws** | "The coupon code can be used twice" is a logic bug that no scanner can find. | Pen test; exploratory testing; code review |
| **Crypto primitive choice** | "You're using AES-CBC without HMAC" is a crypto-design issue. Not a pattern match. | Cryptography review by someone qualified |
| **Supply chain compromises in transitive deps** | Requires a full SBOM + CVE database join. Out of scope for a single grep sweep. | `pip-audit` / `npm audit` / `cargo audit` / Dependabot |
| **Compliance frameworks** (SOC 2, HIPAA, PCI-DSS, GDPR) | Legal / procedural, not technical. | Compliance consultant |

When the operator asks for one of these, respond with: *"That's outside what audit-security does well. Here's what it would take to actually cover it: [link or tool]. Do you want me to run the standard audit-security sweep in the meantime?"*

## Incident runbook — when something leaked

If the sweep finds a live credential leak, or the operator says *"I accidentally pushed my `.env`"*, switch immediately to incident mode. Do not run the full triage. Do the following in order:

### Step 1 — Rotate every exposed credential **now**

Before anything else. Cleanup comes after rotation — as long as the old credentials are still valid, the attacker's window is open.

- API tokens: revoke + regenerate in the provider's dashboard
- OAuth client secrets: regenerate
- Database passwords: change + update every deployment that uses them
- SSH keys: revoke the compromised public key from `~/.ssh/authorized_keys` on every server, generate a new keypair
- Signing keys (JWT secret, cookie secret): rotate + invalidate all existing sessions
- Cloud provider IAM keys: delete + generate new ones

**Do not skip this step because "the repo is private."** Private repos have been exfiltrated by compromised collaborator accounts, leaked CI logs, cloned forks, and accidental public-setting toggles. Treat every exposure as public.

### Step 2 — Remove the secret from git history

The secret is still in every past commit until you rewrite history.

```bash
# Modern tool (recommended)
git filter-repo --path <path/to/leaked/file> --invert-paths
# or for a specific string:
git filter-repo --replace-text <file-with-patterns>.txt

# Legacy alternative (BFG Repo-Cleaner):
bfg --delete-files <leaked-file>
bfg --replace-text <file-with-secrets>.txt
```

Then force-push:

```bash
git push --force-with-lease origin --all
git push --force-with-lease origin --tags
```

**Warn the operator before force-pushing.** All collaborators need to re-clone; their existing clones will diverge.

### Step 3 — Notify and re-authenticate

- Every collaborator with access to the repo needs to:
  - Pull the rewritten history (effectively re-clone)
  - Delete their local copy of the old credentials
  - Pull new credentials if they had the old ones in a local `.env`
- If the repo is part of a CI/CD pipeline, rotate any cached copies of the secret on build runners

### Step 4 — Audit for reuse

Ask the operator: *"Was this secret also used in any other project, service, or environment?"* Credentials are often reused — the leak of one may mean several places are compromised.

### Step 5 — Document the incident

Write a short post-mortem in `docs/security/incidents/<date>-<what-happened>.md`:

- What leaked
- When (commit SHA, push timestamp)
- How (`.env` committed directly? secret in `.github/workflows/*.yml`? hardcoded in source?)
- How it was detected
- Rotation status for each affected credential
- What changed to prevent recurrence (pre-commit hook, `.gitignore` update, `.env.example` audit)

Hand the file off to `write-for-ai` to format. This file is for future AI sessions so the same mistake doesn't recur.

### Step 6 — Prevent recurrence

Add these guards before closing the incident:

- `.gitignore` entries for every secret file type (hand off to `manage-config-env`)
- Pre-commit hook that runs `audit-security` (or at minimum a secrets-scanning step like `gitleaks`) on every commit
- Branch protection on `main` so no one can force-push again
- Secret-scanning enabled on the hosting provider (GitHub Secret Scanning, GitLab push rules, etc.)

## Things not to do

- **Don't run a full SAST scanner and dump its output.** This skill is the opposite of that.
- **Don't copy-paste OWASP descriptions.** If you quote OWASP, do it in one sentence, in the operator's words.
- **Don't be decorative.** No banners, no ASCII art, no emojis beyond what the operator uses. The report is a tool, not a trophy.
- **Don't pretend to be a compliance audit.** This skill finds technical issues. SOC 2 / HIPAA / PCI-DSS require a different kind of review.
- **Don't fix things on your own beyond CRITICAL.** Report, let the operator decide. Especially for "fixes" that touch business logic — what looks like a simple param sanitization might break a workflow.

## Common AI failure modes around security

Things to watch for in your own output:

- **Over-scoping** — the sweep asked about one file and you scanned the whole repo. Don't. Respect the scope the operator set.
- **False-positive fatigue** — reporting 100 findings without triage, knowing the operator will ignore most. Always triage. If you can't triage, say so and ask one specific question.
- **Lecturing** — rehashing OWASP Top 10 theory when the operator asked "is my login page secure." Answer the specific question.
- **Fabricated severity** — inventing "CVSS 9.8" scores you didn't actually compute. Use plain labels (critical/high/medium) and explain the reasoning.
- **Missing the obvious** — running grep for `eval(` and missing a `.env` file sitting in `git ls-files`. Always check tracked secrets first; it's the highest signal-per-second category.

## Harsh mode — no hedging

When the task context contains the `tone=harsh` marker (usually set by the `/vibesubin harsh` umbrella invocation, but can also come from direct requests like *"don't sugarcoat"* / *"brutal review"* / *"매운 맛"*), switch output rules:

- **Lead with the worst finding**, not the summary. First line of the report is the single most dangerous issue, in one sentence, with file and line.
- **No softening words.** Drop *"potential"*, *"could be"*, *"might allow"*, *"consider"*, *"you may want to"*. Replace with blast-radius framing: *"a stranger can read every user's record via `src/api/users.py:47`"*, not *"potential information disclosure in the users endpoint"*.
- **Severity labels stay literal.** CRITICAL stays CRITICAL. HIGH stays HIGH. Do not inflate — harsh mode is about framing, not severity inflation.
- **Triage still applies.** Every finding is still real / false-positive / needs-human-review. Harsh mode removes *hedge words*, not the triage discipline — a false positive is still a false positive, but labeled *"false positive, ignore"* rather than *"probably not exploitable in this codebase, but worth reviewing"*.
- **No *"looks fine"* closures.** If any finding is CRITICAL or HIGH, the verdict line does not end with reassurance. *"Don't ship until items 1–3 are fixed and secrets are rotated"*, not *"mostly clean, two things to look at"*.
- **Incident findings get urgency language.** If a secret is in git history, the first line of the report is *"Stop what you're doing. Rotate the credential now. Here's the incident runbook."* — no preamble.
- **Plain-language impact still required.** *"CWE-89"* is never the headline; *"a user can run arbitrary SQL against your database"* is. Harsh mode uses the same plain language, just without the softening connectives around it.

Harsh mode does not invent findings, fabricate CVSS scores, or become rude. Every harsh statement must be backed by the same evidence the balanced version would cite. The change is framing, not substance.

## Hand-offs

- Critical findings involving refactoring sensitive code → hand off to `refactor-verify` for the fix
- Tracked `.env` files → hand off to `manage-config-env` for the remediation pattern (rotate, remove from history, add to gitignore, re-examine collaborators)
- Issues in CI/CD pipeline secrets → hand off to `setup-ci`
- Repo-rot-adjacent findings (stale dependencies, unused libraries with CVEs) → hand off to `fight-repo-rot`

## Details

- `references/patterns.md` — concrete grep / AST patterns per category
- `references/false-positive-triage.md` — how to classify borderline hits

**Optional helper tools** (the pack does not require them, but uses them when available): Semgrep, Bandit (Python), ESLint-security (JS), gosec (Go), cargo-audit (Rust), pip-audit (Python), npm audit (Node), `gitleaks` / `trufflehog` for secret scanning.
