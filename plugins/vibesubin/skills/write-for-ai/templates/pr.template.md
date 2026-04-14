## Summary

<One to three sentences. What this PR does and why. The reviewer should
be able to decide "is this worth looking at?" from this block alone.>

## Changes

- `<file or section>` — <what changed, one line>
- `<file or section>` — <what changed, one line>
- `<file or section>` — <what changed, one line>

## Verification

| Check | Command | Result |
|---|---|---|
| Typecheck | `<command>` | ✅ clean |
| Lint | `<command>` | ✅ clean |
| Tests | `<command>` | ✅ N/M passing |
| Smoke | `<command>` | ✅ loads, health check green |
| Call-site closure *(only for refactors)* | `<command>` | ✅ count before/after match |

## Risks

<Things the reviewer should specifically watch for. Be honest — flagged
risks are always welcome, surprised risks are painful. If there is no risk
beyond the ordinary, write "none beyond normal review.">

## For the reviewer / next AI session

<What to read first. Anything counter-intuitive. Any "I tried X, it didn't
work, so I used Y" notes. This section is for the person picking up the
context cold, which includes a future AI session rereading this PR.>

## After merge

- [ ] <Action the reviewer or maintainer should take post-merge>
- [ ] <Action, if any — deploy, rotate credentials, notify users, etc.>

---
<!--
Reminder for the author:
- Paste this template, fill it in, then delete this reminder block.
- Use backticks around every file path and command.
- Never include real secrets or local absolute paths.
- If the PR is a refactor, include the symbol-set / call-site counts in Verification.
-->
