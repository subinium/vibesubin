# Startup validation — refusing to boot on unfilled placeholders

A `.env.example` with `__REPLACE_ME__` placeholders only works if the application **refuses to start** when it sees them. Add a check in the application's boot path, before any real work.

## Python

```python
# src/config.py (or equivalent)
import os, sys

REQUIRED = ["DATABASE_URL", "SESSION_SECRET"]

def validate_env() -> None:
    missing = [k for k in REQUIRED if not os.environ.get(k)]
    placeholder = [k for k in REQUIRED if os.environ.get(k) == "__REPLACE_ME__"]
    if missing or placeholder:
        print("Refusing to start. Fix your .env first:", file=sys.stderr)
        for k in missing:
            print(f"  missing: {k}", file=sys.stderr)
        for k in placeholder:
            print(f"  unfilled placeholder: {k} is still __REPLACE_ME__", file=sys.stderr)
        sys.exit(1)
```

## Node / TypeScript

```typescript
// src/config.ts
const REQUIRED = ["DATABASE_URL", "SESSION_SECRET"] as const;

export function validateEnv(): void {
  const missing = REQUIRED.filter((k) => !process.env[k]);
  const placeholder = REQUIRED.filter((k) => process.env[k] === "__REPLACE_ME__");
  if (missing.length || placeholder.length) {
    console.error("Refusing to start. Fix your .env first:");
    for (const k of missing) console.error(`  missing: ${k}`);
    for (const k of placeholder) console.error(`  unfilled placeholder: ${k} is still __REPLACE_ME__`);
    process.exit(1);
  }
}
```

## Go

```go
// config/env.go
package config

import (
    "fmt"
    "os"
)

var required = []string{"DATABASE_URL", "SESSION_SECRET"}

func ValidateEnv() {
    var missing, placeholder []string
    for _, k := range required {
        v := os.Getenv(k)
        if v == "" {
            missing = append(missing, k)
        } else if v == "__REPLACE_ME__" {
            placeholder = append(placeholder, k)
        }
    }
    if len(missing) > 0 || len(placeholder) > 0 {
        fmt.Fprintln(os.Stderr, "Refusing to start. Fix your .env first:")
        for _, k := range missing {
            fmt.Fprintf(os.Stderr, "  missing: %s\n", k)
        }
        for _, k := range placeholder {
            fmt.Fprintf(os.Stderr, "  unfilled placeholder: %s is still __REPLACE_ME__\n", k)
        }
        os.Exit(1)
    }
}
```

## The rule, regardless of language

Read the value, check for empty or placeholder, abort boot with a clear error. **Do not continue with a fallback** — fallbacks hide the problem. A loud startup error is a feature, not a bug.
