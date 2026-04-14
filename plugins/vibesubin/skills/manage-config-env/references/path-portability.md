# Path portability — full pattern-and-fix table

Every absolute path, IP literal, username, or platform separator in source is a time bomb. `SKILL.md` lists the core patterns; this reference has the full table with language-specific fixes.

## Grep patterns and their fixes

| Pattern | Why it's bad | Fix |
|---|---|---|
| `C:\\` / `C:/` / `c:\\` | Windows absolute path in source | `os.path.join` (Python) / `path.join` (Node) / env var |
| `/Users/<name>` | macOS absolute home | `~` expansion or env var |
| `/home/<name>` | Linux absolute home | `~` expansion or env var |
| Literal IPv4 (`\d+\.\d+\.\d+\.\d+`) | Hard-coded hostname | Env var or config entry |
| `\\` in string literals | Windows path separator hardcoded | `os.sep` / `path.sep` / POSIX-style `/` |
| Username in paths | Breaks on any other machine | Env var or detect-at-runtime helper |
| `/tmp/<specific>` | Assumes POSIX tmp | `tempfile.mkdtemp()` / `os.tmpdir()` / `TMPDIR` env |
| Hardcoded SSH host (`user@1.2.3.4`) | Credential + host both in source | Environment variables for both |
| `sqlite:////absolute/path` | Absolute DB path | Relative to project root or env var |

## Language-specific replacements

### Python

```python
import os
from pathlib import Path

# Bad
data_dir = "/Users/alice/project/data"

# Good
data_dir = Path(__file__).parent / "data"
# or, when the value should be overridable
data_dir = Path(os.environ.get("DATA_DIR", "./data"))
```

### Node / TypeScript

```typescript
import path from "node:path";
import { fileURLToPath } from "node:url";

// Bad
const dataDir = "/Users/alice/project/data";

// Good
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(__dirname, "data");
```

### Go

```go
import (
    "os"
    "path/filepath"
)

// Bad
dataDir := "/home/bob/project/data"

// Good
exe, _ := os.Executable()
dataDir := filepath.Join(filepath.Dir(exe), "data")
```

## When the audit finds more than a few hits

Hand off to `refactor-safely`. The 1:1 semantic preservation that skill provides is valuable when rewriting path handling across a codebase — the kind of change that silently breaks on a different OS six months later.
