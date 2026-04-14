---
name: unify-design
description: Establishes a web project's design system as the single source of truth — colors, spacing, typography, radius, shadow, breakpoints — then audits the codebase for drift against it (hardcoded hex values, arbitrary Tailwind values, magic px/rem numbers, duplicate component variants, inconsistent navigation) and fixes the drift by extracting repeated values to design tokens. Framework-aware — Tailwind (v3 and v4), CSS Modules, styled-components / Emotion, Material UI, Chakra UI, vanilla CSS with custom properties. Multi-file rewrites hand off to refactor-verify.
when_to_use: Trigger on "make this match the design system", "unify the buttons", "extract these colors to tokens", "why do these two pages look different", "too many hardcoded values", "design drift", "브랜드 일관성", "디자인 통일해줘", "토큰으로 뽑아줘", "デザインを統一", "設計システム", "设计系统", "品牌一致性", before a public launch, after porting from a template, or when a project's spacing and colors visibly drift across pages.
allowed-tools: Read Write Edit Glob Grep Bash(grep *) Bash(git grep *) Bash(git log *) Bash(npm *) Bash(pnpm *) Bash(yarn *) Bash(bun *) Bash(npx *) Bash(stylelint *) Bash(eslint *)
---

# unify-design

Most vibe-coder web projects start with a template, get rushed into production, and end up with two versions of every button, three shades of "primary blue", spacing values that were eyeballed to the nearest pixel, and a navigation bar that doesn't match between two of the pages. None of those are bugs on their own, but together they make the product look like it was assembled from three different apps.

This skill treats the project's **brand identity (BI)** — colors, spacing, typography, radii, shadows, breakpoints, and the handful of components that appear on every page — as the single source of truth. Everything else in the codebase is expected to reference it. When the code drifts, this skill finds the drift and pushes the values back into tokens.

**What this skill is:** a design-system auditor and a token extractor. It establishes the source of truth when it's missing, finds every place the source of truth is bypassed, and rewrites those places to reference the tokens.

**What this skill is not:** a brand designer (it uses the project's existing BI or scaffolds opinionated defaults), a visual regression tester (Chromatic and Percy already do that), a component-library rewriter (it respects the framework the project already uses), or a figma-to-code converter.

## When to trigger

Direct operator asks:

- "make this match the design system" / "unify the buttons"
- "why do these two pages look different"
- "extract these colors to tokens" / "these spacings are all over the place"
- "too many hardcoded values" / "디자인 통일해줘" / "토큰으로 뽑아줘"
- "design system audit" / "BI audit" / "brand consistency"

Situational:

- **Before a public launch.** Inconsistencies read as amateurish to a first-time visitor more than any single missing feature does.
- **After porting from a template.** Templates ship with hardcoded values everywhere. Unwinding them is the difference between "feels like yours" and "feels like a cloned demo."
- **After three or more AI-generated UI sessions.** Each session tends to reinvent spacing and colors because the model doesn't remember the prior session's choices. Drift accumulates quietly.
- **When two operators are working on different pages.** Two humans plus two AI sessions equals four slightly different blues within a week.

## The three things this skill does

### 1. Establish the BI source of truth

If the project has a tokens file, use it. If it doesn't, scaffold one. The scaffold is opinionated, not arbitrary — the operator can adjust, but the defaults come from something real.

**Detect the framework first.** The tokens file lives wherever the framework expects it:

| Framework marker | Where tokens live | Notes |
|---|---|---|
| `tailwind.config.ts` / `tailwind.config.js` | `theme.extend` block (Tailwind v3) | Also update `content:` globs so JIT sees the new files |
| `@tailwindcss/postcss` + `@import "tailwindcss"` in CSS | `@theme { ... }` in `app/globals.css` or `src/styles/globals.css` (Tailwind v4) | v4 is CSS-first; no JS config by default |
| `tailwind.config.ts` + CSS with `@theme` | **warn** — mixed v3/v4, pick one | v3 `theme.extend` and v4 `@theme` produce silent conflicts |
| `theme.ts` + `ThemeProvider` from `styled-components` / `@emotion/react` | a single `lib/theme.ts` module exported as the shared theme object | |
| `createTheme` from `@mui/material` | `lib/theme.ts` returning the result of `createTheme({ ... })` | |
| `extendTheme` from `@chakra-ui/react` | `lib/theme.ts` returning `extendTheme({ ... })` | |
| Plain CSS / CSS Modules | `src/styles/tokens.css` with `:root { --name: value; }` | Single source everyone imports first |
| SCSS | `src/styles/_tokens.scss` with `$name: value;` | Same principle, SCSS variables |
| Vanilla Extract | `src/styles/tokens.css.ts` exported as `vars` | |

**Scaffolded defaults** — only used when the project has nothing. Each scale is opinionated on purpose so the operator doesn't have to invent one:

```ts
// Spacing — 4px base, powers of ~1.5
spacing: {
  0: '0',
  px: '1px',
  0.5: '2px',
  1:   '4px',
  2:   '8px',
  3:   '12px',
  4:   '16px',
  5:   '20px',
  6:   '24px',
  8:   '32px',
  10:  '40px',
  12:  '48px',
  16:  '64px',
  20:  '80px',
  24:  '96px',
}

// Typography scale — major third (1.25)
fontSize: {
  xs:   ['12px', { lineHeight: '16px' }],
  sm:   ['14px', { lineHeight: '20px' }],
  base: ['16px', { lineHeight: '24px' }],
  lg:   ['18px', { lineHeight: '28px' }],
  xl:   ['20px', { lineHeight: '28px' }],
  '2xl':['24px', { lineHeight: '32px' }],
  '3xl':['30px', { lineHeight: '36px' }],
  '4xl':['36px', { lineHeight: '40px' }],
  '5xl':['48px', { lineHeight: '1' }],
}

// Radius — conservative, on-brand
borderRadius: {
  none: '0',
  sm:   '2px',
  DEFAULT: '6px',
  md:   '8px',
  lg:   '12px',
  xl:   '16px',
  '2xl':'24px',
  full: '9999px',
}

// Semantic color slots — operator fills with actual hex values
colors: {
  primary:   { 50: '#...', 100: '#...', /* 200–900 */ },
  neutral:   { 0: '#ffffff', 50: '#...', /* ... */, 1000: '#000000' },
  success:   { 500: '#...' },
  warning:   { 500: '#...' },
  danger:    { 500: '#...' },
  // no "brand" aliases until the operator picks one — "primary" covers it
}
```

**Do not invent hex values the operator did not choose.** If the scaffold needs a color palette and the project has no logo or guidance, prompt the operator for one color (*"what's the one color you want the product to feel like?"*) and derive the palette from it with a consistent scale — e.g., OKLCH stepping, or a tool like `color-generate` — **not** by making up six random hexes.

**Typography goes through the same scaffold.** Default to one display typeface and one text typeface, both from Google Fonts or the project's existing import. Do not introduce a third.

### 2. Audit for drift against the BI

Once the tokens file is authoritative, every other file in the codebase is expected to reference it. The audit flags every place that bypasses it.

**Audit patterns** — run across `src/`, `app/`, `components/`, `pages/`, skipping `node_modules`, `.next`, `dist`, `build`, `public`, and the tokens file itself.

```bash
# Hardcoded hex colors outside the tokens file
git grep -nE '#[0-9a-fA-F]{3,8}\b' -- \
  '*.tsx' '*.ts' '*.jsx' '*.js' '*.vue' '*.svelte' '*.css' '*.scss' '*.html' \
  ':!*tokens*' ':!*theme*' ':!*tailwind.config.*'

# Hardcoded rgb() / hsl() / oklch()
git grep -nE '(rgba?|hsla?|oklch|oklab)\(' -- \
  '*.tsx' '*.ts' '*.jsx' '*.js' '*.css' '*.scss' \
  ':!*tokens*' ':!*theme*'

# Tailwind arbitrary values — the escape hatch that bypasses the theme scale
git grep -nE '\b(w|h|p|m|pt|pb|pl|pr|px|py|mt|mb|ml|mr|mx|my|gap|top|right|bottom|left|text|bg|border|rounded|shadow|z|inset)-\[' -- \
  '*.tsx' '*.jsx' '*.html'

# Magic pixel / rem values inside JSX style props or CSS
git grep -nE '\b[0-9]+(\.[0-9]+)?(px|rem|em|vh|vw)\b' -- \
  '*.tsx' '*.ts' '*.jsx' '*.js' '*.vue' '*.svelte' \
  ':!*tokens*' ':!*theme*' ':!*.config.*' ':!*stories*'

# Inline style objects (usually a sign of a one-off that should be a token)
git grep -nE 'style=\{\{' -- '*.tsx' '*.jsx'
```

**Classify every hit.** A grep match is a candidate, not a finding. Each candidate gets one of four classifications:

| Classification | Meaning | Action |
|---|---|---|
| **DRIFT — trivial** | Hardcoded value equals an existing token (e.g., `#3B82F6` when `--color-primary-500` is exactly `#3B82F6`) | Replace with the token name. Safe, zero-risk. |
| **DRIFT — near-match** | Hardcoded value is close to a token but not equal (e.g., `#3b82f7` vs `#3B82F6`) | Almost always a copy-paste error. Replace with the token. Ask the operator once if the difference was intentional. |
| **DRIFT — missing token** | Hardcoded value has no matching token (e.g., a `#ff6b35` accent that exists nowhere in the palette) | Two options: add the value to the tokens file (if it's reused >2 times) or replace with the closest existing token (if it's a one-off accident). |
| **INTENTIONAL** | The hardcoded value is context-specific and correct (a brand image overlay, a third-party iframe border, a placeholder gradient) | Label it explicitly with a comment: `/* unify-design:ignore — this is a one-off product photo gradient */`. Counted as reviewed, not flagged again. |

**Component-level audits** — not just individual values. Some drift is structural:

- **Multiple `Button.tsx` files** — find every file named `Button.*` or that exports a `Button` component. Diff the prop shapes. If two buttons differ only in padding or color, they're the same component with two hardcoded variants; consolidate.
- **Multiple navigation components** — find every `<nav>` tag. If two pages have different navigation structures, flag for consolidation unless they're intentionally different (e.g., an authenticated vs. marketing nav).
- **Duplicate card / modal / form shells** — same pattern. The giveaway is three files with nearly identical JSX scaffolding and different class names.
- **Inconsistent page-level layout** — different pages wrap their content in different max-width or padding. Usually means the project is missing a `<PageShell />` or `<Container />`.
- **Logo sprawl** — multiple copies of the logo as separate files (`logo.png`, `logo-dark.png`, `logo-small.svg`, `Logo2.tsx`, etc.) with no consolidation. Pick one SVG source and wrap it in a `<Logo />` component with `variant` and `size` props.

### 3. Fix drift by extracting to tokens

For every DRIFT finding, the skill produces a concrete diff proposal. Small, local fixes apply directly (with the operator's approval). Fixes that touch more than a few files hand off to `refactor-verify` — the token rename or component consolidation becomes a refactor node with symbol-level verification.

**Pattern — hardcoded color to token:**

```diff
  <button
-   className="bg-[#3B82F6] text-white px-[12px] py-[6px] rounded-[8px]"
+   className="bg-primary-500 text-neutral-0 px-3 py-1.5 rounded-md"
  >
```

**Pattern — duplicate button components to one:**

```diff
- // components/PrimaryButton.tsx
- export const PrimaryButton = ({ children }) => (
-   <button className="bg-primary-500 text-white px-4 py-2 rounded">{children}</button>
- );
-
- // components/CTAButton.tsx
- export const CTAButton = ({ children }) => (
-   <button className="bg-primary-600 text-white px-5 py-2.5 rounded-md">{children}</button>
- );

+ // components/ui/Button.tsx
+ type ButtonVariant = 'primary' | 'cta' | 'secondary' | 'ghost';
+ type ButtonSize = 'sm' | 'md' | 'lg';
+ export const Button = ({ variant = 'primary', size = 'md', children }) => (
+   <button className={cn(buttonBase, variantStyles[variant], sizeStyles[size])}>
+     {children}
+   </button>
+ );
```

Then hand off to `refactor-verify` to rename every import site from `PrimaryButton` / `CTAButton` to `Button` with the right variant, with call-site closure verified.

**Pattern — inline style to token class:**

```diff
- <div style={{ padding: '14px', backgroundColor: '#F9FAFB', borderRadius: 8 }}>
+ <div className="p-3.5 bg-neutral-50 rounded-md">
```

If `p-3.5` doesn't exist in the scale, either add it (`3.5: '14px'`) or round to the nearest token (`p-4` = 16px, `p-3` = 12px). The skill asks once per unique value, not once per usage — a single decision covers every `14px` in the repo.

## Output format

```markdown
# Design unification audit — <scope> — <date>

## BI source of truth
- Framework: <Tailwind v4 | Tailwind v3 | CSS Modules | styled-components | MUI | Chakra | vanilla>
- Tokens file: `<path>` (✅ exists / ⚠ missing, scaffold proposed)
- Palette size: <N colors across M semantic slots>
- Spacing scale: <N tokens>
- Typography scale: <N tokens>

## Summary
- Total candidates scanned: <N>
- DRIFT — trivial: <N> (auto-replaceable)
- DRIFT — near-match: <N> (needs one confirmation, then replaceable)
- DRIFT — missing token: <N> (operator decides: add to tokens or replace)
- INTENTIONAL — already labeled: <N>

## Top drift hotspots (files with >5 drift findings)
1. `src/app/(marketing)/page.tsx` — 23 drift findings (19 hardcoded px values, 4 hex colors)
2. `src/components/Hero.tsx` — 11 drift findings (1 color, 10 spacing)
3. `src/app/pricing/page.tsx` — 9 drift findings (3 near-match colors, 6 spacing)

## Duplicate components
- **Button**: 3 variants across `PrimaryButton.tsx`, `CTAButton.tsx`, `OutlineButton.tsx`. Consolidate to one `Button` with `variant="primary" | "cta" | "outline"`. Hand off to `refactor-verify` for the rename + import-site update.
- **Card**: 2 variants in `FeatureCard.tsx`, `PricingCard.tsx`. Same JSX shell, different padding. Consolidate with `padding` prop.
- **Logo**: 4 files (`logo.png`, `logo-dark.svg`, `Logo.tsx`, `BrandMark.tsx`). Pick the SVG, wrap in one `<Logo />`.

## Proposed tokens to add
- `spacing.3.5: '14px'` (appears 12 times across 4 files)
- `colors.accent.500: '#FF6B35'` (appears 3 times, no matching token; operator confirms it's a brand color)

## Fixes applied (this session)
- <list of files edited with before/after context>

## Fixes pending operator approval
- <list of files with the proposed diff, one-sentence rationale>

## Hand-offs
- Multi-file refactor (Button consolidation, Card consolidation) → `refactor-verify`
- New env-var for theme-switching (dark mode) → `manage-secrets-env` if one is added
- Documentation of the token system in `CLAUDE.md` → `write-for-ai`
```

## Things not to do

- **Don't invent a brand.** If the project has no BI at all, scaffold opinionated defaults and ask the operator for one real value (primary color, display font) before proceeding. Never write arbitrary hex values into a tokens file and call it done.
- **Don't rewrite history or restructure the repo.** Token extraction is an in-place refactor, not a rearrangement of the directory tree.
- **Don't migrate frameworks.** If the project is on styled-components, use its theme object; don't propose switching to Tailwind. Respect the project's framework choice.
- **Don't touch anything outside `src/` / `app/` / `components/` / `pages/` / `styles/`.** Config files, build scripts, CI workflows, and backend code are out of scope.
- **Don't fix every drift finding at once.** Scope every run to one area (one page, one component tree, one color concern) unless the operator explicitly asks for a full sweep. A 400-file unified diff is impossible to review.
- **Don't count `.storybook/` or `*.stories.*` files as drift sources.** Stories are intentionally hardcoded — they're documentation, not production code.
- **Don't count `tailwind.config.*`, `*tokens*`, `*theme*`, or `globals.css` as drift sources.** Those files contain the source of truth; they're supposed to have literal values.
- **Don't silently replace near-match colors.** `#3b82f7` vs `#3B82F6` is close, but only the operator knows whether it was intentional. Ask once.
- **Don't break contrast or accessibility.** Every color replacement must preserve WCAG AA contrast. If a replacement drops a color to a lower contrast tier, flag it and ask.

## Sweep mode — read-only audit

When invoked from `/vibesubin` (the umbrella skill's parallel sweep), this skill runs in **read-only audit mode**. Do not scaffold the tokens file, do not edit components, do not consolidate duplicates. Produce a findings-only report.

- BI source of truth: present / missing / stale.
- Drift counts by file, sorted by hotspot.
- Duplicate component candidates (Button, Card, Nav, Logo) with file lists.
- Stoplight verdict: 🟢 design is consistent and token-driven / 🟡 drift in a few files, no structural duplication / 🔴 multiple duplicate components, tokens file missing or ignored, visible cross-page inconsistency.
- One-line "fix with" pointer indicating `/unify-design` will scaffold and extract when invoked directly.

How to tell: the task context from the umbrella will include a `sweep=read-only` marker or an explicit "produce findings only, do not edit" instruction. Obey it. If the operator invokes this skill by name, the full procedure applies and editing is expected.

## Harsh mode — no hedging

When the task context contains the `tone=harsh` marker (usually set by the `/vibesubin harsh` umbrella invocation, but can also come from direct requests like *"don't sugarcoat"* / *"brutal review"* / *"매운 맛"* / *"厳しめ"*), switch output rules:

- **Lead with the worst structural drift.** First line of the report is the single most visible inconsistency — *"the primary button has three different implementations in this repo and two of them ship on the same page"*, *"`#3B82F6`, `#3b82f7`, and `#4A90E2` all exist in this codebase and none of them are tokens"*, *"there is no `<Logo />` component — the logo is pasted into 6 files as raw `<img>` tags."* No preamble.
- **No *"might want to consider"* softening.** Drop *"could benefit from"*, *"worth thinking about"*, *"some consolidation would help"*. Replace with directive verbs: *"consolidate the three button components now"*, *"extract these 23 hardcoded spacings to tokens before the next push"*, *"fix the palette before launch — four near-match blues will show up in one design review."*
- **Drift hotspots get named victims.** Balanced mode says *"several files have high drift counts"*. Harsh mode says *"`src/app/pricing/page.tsx` has 23 drift findings — it was clearly pasted together in one session and never revisited. Fix this page first."*
- **Inconsistencies become consequences.** *"Two of your pages use different navigation structures. A first-time visitor who lands on `/pricing` and then navigates to `/docs` will think they ended up on a different product."*
- **No *"mostly consistent with a few polish items"* closures.** If the audit found any duplicate component or any missing tokens file, the verdict line commits: *"Do not ship this until the button is consolidated and the tokens file exists."*
- **Missing BI source gets urgency framing.** *"There is no tokens file. Every change you've made to this project has been a silent vote for a different shade of blue. Scaffold the tokens file now; argue about the palette after."*

Harsh mode does not invent drift, exaggerate counts, or become rude. Every harsh statement must cite the same file, line, or grep output the balanced version would cite. The change is framing, not substance.

## Hand-offs

- **Multi-file token rename or component consolidation** → `refactor-verify` with the rename/merge plan, call-site closure verified against the old and new names
- **Documentation of the token system, component library, or BI decisions** → `write-for-ai` to produce a `DESIGN.md` or to update `CLAUDE.md` with the invariants ("always reference `colors.primary`, never a literal hex")
- **Adding Stylelint or ESLint rules to catch future drift in CI** → `setup-ci` for the workflow integration, plus a `stylelint.config.js` with rules like `color-no-hex` and `declaration-property-value-allowed-list`
- **Logo files, brand assets, or oversized images found during the audit** → `manage-assets` for bloat triage (PNGs that should be SVG, unused font files, logo duplicates sitting in `public/`)
- **Component deletions** (after consolidation, the old `PrimaryButton.tsx` is dead) → `fight-repo-rot` to confirm unused, then `refactor-verify` to delete safely
- **Secrets-adjacent work** (API keys for a theme-switching service, environment-specific brand configs) → `manage-secrets-env`

## Framework-specific notes

### Tailwind v3

Tokens live in `tailwind.config.ts` under `theme.extend`. Arbitrary values like `w-[432px]` bypass the theme — flag every instance. Custom plugins that generate utility classes (e.g., `tailwind-variants`, `cva`) count as part of the token source if they reference `theme()`.

### Tailwind v4

Tokens live in CSS via `@theme { --color-primary-500: ...; }`. No `tailwind.config.js` by default. Don't mix v3 `theme.extend` and v4 `@theme` in the same project — the conflict is silent and one will win unpredictably. If you find both, warn the operator and pick one.

### styled-components / Emotion

The theme object in `lib/theme.ts` is the source of truth. Components access it via `props.theme` or the `useTheme` hook. Hardcoded values inside `styled.div\`...\`` template literals are drift. Replace with `${props => props.theme.colors.primary[500]}`.

### Material UI

`createTheme` builds the theme. The `palette`, `spacing`, `typography`, and `shape` sections are the tokens. Components accept `sx` props that should reference theme values: `sx={{ p: 2 }}` (= `theme.spacing(2)`), not `sx={{ p: '16px' }}`.

### Chakra UI

`extendTheme` wraps Chakra's defaults. The operator's custom tokens extend the theme. Chakra's style props should reference theme values: `<Box p={4} bg="primary.500" />`, not `<Box p="16px" bg="#3B82F6" />`.

### CSS Modules / vanilla CSS

`:root { --color-primary-500: #3B82F6; }` in `src/styles/tokens.css`, imported first in `layout.tsx` / `_app.tsx` / `index.html`. Components use `var(--color-primary-500)`. Hardcoded hex values in any `.module.css` file that doesn't reference a `var()` are drift.

## References and templates

- `references/token-scaffolds.md` — per-framework starter tokens file with opinionated defaults (spacing scale, typography scale, radius scale, shadow scale; palette slots that the operator fills with real values). Kept intentionally minimal.

The grep patterns, classification rules, and fix templates are inlined in this SKILL.md rather than split into references — the audit is the primary deliverable and the analysis needs to live in one readable file. Framework-specific notes (Tailwind, styled-components, MUI, Chakra, vanilla CSS) are inlined above for the same reason.
