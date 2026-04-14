# Contributing

**This pack does not accept pull requests.** Please read the rest of this file before opening anything.

---

## How to contribute

Open an issue. That's the whole mechanism.

- [File an issue](https://github.com/subinium/vibesubin/issues/new)
- Be concrete: a concrete failure, a concrete missing case, a concrete confusing sentence
- Abstract suggestions ("add more skills") will usually be closed without action

The maintainer reviews issues and incorporates fixes directly. This keeps the pack's voice consistent.

---

## What makes a good issue

### Bug in a skill

- Which skill: `refactor-verify`, `audit-security`, etc.
- What you asked Claude to do
- What the skill did
- What it should have done
- If possible, a minimal repro — a tiny repo or file that triggers the bug

### Missing language / runtime coverage

- Which skill needs to cover it
- The canonical verification chain for that language
   (e.g., "Elixir: `mix compile`, `mix credo`, `mix dialyzer`, `mix test`")
- A link to the language's standard linter / test runner docs

### New failure mode

If you spotted a way an AI session broke things that this pack should have caught:

- Describe the failure in one paragraph
- Which skill should have intercepted it
- (Optional) A grep / AST pattern that would detect it

### Docs unclear to a non-developer

Mark the exact file and line. "The README is confusing" is not actionable; "In README.md the phrase 'call-site closure' is not explained" is.

---

## Why no PRs

Three reasons:

1. **Single voice.** The pack is written for non-developers. Mixed editorial voice makes it harder to trust. The maintainer edits everything to keep tone consistent.
2. **Skill correctness is hard to review.** A misworded trigger or a frontmatter typo can silently break a skill. The maintainer runs each change against multiple real sessions before shipping.
3. **The methodology is opinionated.** The pack codifies specific methodologies (Mikado, Tidy First, 6-step recursive verification). PRs often arrive with competing opinions that would dilute the pack.

If you strongly disagree with a methodology choice, open an issue and argue the case. If it's convincing, the maintainer will update the methodology file.

---

## Translation

The pack ships a translated README in Korean / Chinese / Japanese. If you spot a translation error or want to add another language:

- File an issue with the specific line and suggested correction
- For a new language, propose a full draft in the issue body; the maintainer will review and incorporate

---

## License

All contributions (issue text, suggestions, reproductions) are assumed to be MIT-licensed to match the pack. Do not file code snippets in issues that you cannot release under MIT.
