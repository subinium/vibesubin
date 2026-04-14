# Security patterns — language-agnostic grep rules

Each category maps to one of the ten in `SKILL.md`. Patterns are written as ripgrep (`rg`) regexes because ripgrep works the same on macOS, Linux, Windows (WSL), and most CI runners. They are deliberately coarse — the intent is high recall for a small human-triaged list, not high precision like a SAST tool.

Run each block. Triage every hit before reporting.

---

## 1. Hardcoded secrets

```bash
# Files that should never be tracked — an exact-match catch is highest signal
git ls-files | rg -i '(^|/)(\.env($|\.))|(\.pem$)|(id_rsa)|(id_ed25519)|(credentials)|(\.ppk$)'

# Common secret prefixes in source content
rg -n --hidden -g '!.git' \
  '(sk-[A-Za-z0-9]{20,})|(ghp_[A-Za-z0-9]{30,})|(xox[bpoa]-[A-Za-z0-9-]{20,})|(AKIA[0-9A-Z]{16})|(-----BEGIN [A-Z ]+PRIVATE KEY-----)|(eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})'

# Generic high-entropy assignment patterns
rg -n --hidden -g '!.git' \
  '(?i)(api[_-]?key|secret|password|token|passwd)\s*[:=]\s*[\x27"][^\x27"]{16,}[\x27"]'

# History scan — anything that was ever committed and later removed
# (slow; run only when the operator confirms a leak scare)
git log --all -p -S 'API_KEY' | head -200
```

---

## 2. SQL built with string interpolation

```bash
# Python
rg -n -t py '\.(execute|executemany|fetch|fetchone|fetchall|raw)\s*\(\s*f[\x27"]'   # f-string queries
rg -n -t py '\.(execute|executemany)\s*\([^)]*%\s*[\x27"]'                          # % formatting
rg -n -t py '\.(execute|executemany)\s*\([^)]*\.format\s*\('                        # .format()

# JavaScript / TypeScript
rg -n -t js -t ts '\.(query|execute|raw)\s*\(\s*`[^`]*\$\{'                         # template literal with ${}
rg -n -t js -t ts '\.(query|execute|raw)\s*\([^)]*\+\s*\w'                          # string concat

# Go
rg -n -t go 'db\.(Query|Exec|QueryRow)\([^)]*fmt\.Sprintf'

# Ruby
rg -n -t ruby '\.(execute|query)\s*\([\x27"][^\x27"]*#\{'

# PHP
rg -n -t php 'mysqli_query\s*\([^,]*\$|mysql_query\s*\([^)]*\$'
```

The safe forms (not flagged) use placeholders: `?`, `$1`, `:name`, `%s` with a driver that escapes.

---

## 3. Shell / command injection

```bash
# Python
rg -n -t py 'subprocess\.(run|call|check_output|check_call|Popen)\([^)]*shell\s*=\s*True'
rg -n -t py 'os\.system\s*\('
rg -n -t py '\beval\s*\('
rg -n -t py '\bexec\s*\('
rg -n -t py 'pickle\.loads\s*\('
rg -n -t py 'yaml\.load\s*\([^)]*\)(?![^,]*Loader)'

# Node / TypeScript
rg -n -t js -t ts 'child_process\.(exec|execSync)\s*\('
rg -n -t js -t ts '\beval\s*\('
rg -n -t js -t ts 'new\s+Function\s*\('
rg -n -t js -t ts 'require\(\s*`[^`]*\$\{'                                           # dynamic require

# Go
rg -n -t go 'exec\.Command\s*\(\s*[\x27"][^\x27"]*\s*[\x27"]\s*,\s*os\.Args'        # user args to exec
rg -n -t go 'exec\.Command\s*\(\s*[\x27"]sh[\x27"]\s*,\s*[\x27"]-c[\x27"]'           # shell -c

# Ruby
rg -n -t ruby '(?:Kernel\.)?(?:system|exec)\s*\([\x27"][^\x27"]*#\{'
rg -n -t ruby '`[^`]*#\{'                                                            # backtick interpolation

# Shell scripts
rg -n --type sh 'eval\s+[\x27"]?\$'
```

---

## 4. Path traversal

```bash
# Catches request-derived paths going into file APIs. Coarse — triage required.
rg -n '\b(open|readFile|readFileSync|FileResponse|sendFile|File\.new|File\.open|os\.path\.join)\s*\([^)]*(request\.|req\.|params|query|body)'

# Specific file-reading with user-controlled filename
rg -n -t py 'open\s*\(\s*request\.'
rg -n -t js -t ts 'fs\.readFile(Sync)?\s*\(\s*req\.'
rg -n -t go 'ioutil\.ReadFile\s*\([^)]*r\.URL'
```

---

## 5. XSS sinks

```bash
# DOM sinks
rg -n -t html -t js -t ts 'innerHTML\s*='
rg -n -t js -t ts 'dangerouslySetInnerHTML'
rg -n -t vue -t html 'v-html\s*='
rg -n 'document\.write\s*\('

# Template engine escape hatches
rg -n -t py '\|safe\b'                           # Jinja2 / Django
rg -n -t py 'mark_safe\s*\('                     # Django
rg -n -t html '\{@html\s'                        # Svelte

# Markdown renderers — presence alone is suspicious when combined with injection
rg -n 'marked\s*\(|markdown-it\(\)|showdown\.Converter'
```

Manual check for each hit: does the value being injected come from user input? If yes, it needs a sanitizer (DOMPurify on rendered HTML, `bleach` on server-side HTML, or equivalent).

---

## 6. Dangerous deserialization

```bash
rg -n -t py 'pickle\.loads\s*\('
rg -n -t py 'cloudpickle\.loads\s*\('
rg -n -t py 'yaml\.load\s*\('                    # not safe_load
rg -n -t ruby 'Marshal\.load\s*\('
rg -n -t java 'ObjectInputStream\s*\('
rg -n -t php 'unserialize\s*\('
rg -n -t js -t ts 'JSON\.parse\s*\(.*req\.'      # JSON.parse on user input is fine — but flag for review in auth paths
```

---

## 7. Missing cookie safety flags

```bash
# Any set_cookie / Set-Cookie call
rg -n '(?i)(set_cookie|set-cookie|cookies\.set|res\.cookie|response\.cookies)'
```

Triage: for each hit, verify the call includes `httponly`, `secure`, and `samesite` (or the framework default is safe). Flag the ones that don't.

---

## 8. Wildcard CORS

```bash
rg -n 'Access-Control-Allow-Origin.*[\x27"]\*[\x27"]'
rg -n 'cors\s*\(\s*\{\s*origin\s*:\s*[\x27"]\*[\x27"]'
rg -n 'allow_origins\s*=\s*\[\s*[\x27"]\*[\x27"]'
```

A wildcard CORS header is only safe on genuinely public endpoints. On anything authenticated, it's a flag.

---

## 9. Dependency / lockfile hygiene

```bash
# Unpinned Python deps
rg -n '^[^#][^=]*>=|^[^#][^=]*~=|^[a-zA-Z][^=<>~]*$' requirements.txt 2>/dev/null
rg -n -g 'pyproject.toml' 'version\s*=\s*[\x27"][~^>*]'

# Unpinned Node deps (caret/tilde/asterisk ranges)
rg -n -g 'package.json' '"\^|"\~|"\*|latest'

# Missing lockfiles
for lock in package-lock.json yarn.lock pnpm-lock.yaml Cargo.lock Gemfile.lock composer.lock go.sum; do
  [ -f "$lock" ] || echo "missing lockfile: $lock"
done
```

---

## 10. Auth / session pitfalls

```bash
# JWT with "none" algorithm
rg -n '(?i)(alg|algorithm)\s*[:=]\s*[\x27"]none[\x27"]'

# Non-constant-time comparison of secrets
rg -n -t py '==\s*(password|token|secret|api_key)'
rg -n -t js -t ts '==\s*(password|token|secret|apiKey)'

# Math.random / random() used where crypto randomness is needed
rg -n -t js -t ts 'Math\.random\s*\(\)' -g '*token*' -g '*secret*' -g '*otp*' -g '*session*'
rg -n -t py 'random\.random\s*\(\)' -g '*token*' -g '*secret*' -g '*otp*' -g '*session*'

# Hardcoded admin bypasses
rg -n '(?i)(if|unless)\s+(user_id|userId|username|email)\s*==\s*[\x27"]?(admin|1|root)'
```

---

## How to run the full sweep

```bash
# From the repo root, run each category's block and concatenate output.
# The `audit-security` SKILL.md walks through the triage procedure afterwards.
```

The output of this file is deliberately raw — you triage each hit in the SKILL.md's output format, not here.
