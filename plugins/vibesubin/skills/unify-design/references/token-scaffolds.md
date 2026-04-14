# Token scaffolds

Starter tokens files for each supported framework. The skill copies the relevant one into the project only when no tokens file exists — never overwrites an existing one.

Every scaffold is intentionally opinionated: one spacing scale, one typography scale, one radius scale, one shadow scale, and semantic color slots that the operator fills with real values. The defaults are meant to be a starting point the operator can ship with, not the only possible choice.

## Tailwind v3 — `tailwind.config.ts`

```ts
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx,js,jsx,mdx}',
    './src/**/*.{ts,tsx,js,jsx,mdx}',
    './components/**/*.{ts,tsx,js,jsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50:  '__REPLACE_ME__',
          100: '__REPLACE_ME__',
          200: '__REPLACE_ME__',
          300: '__REPLACE_ME__',
          400: '__REPLACE_ME__',
          500: '__REPLACE_ME__',
          600: '__REPLACE_ME__',
          700: '__REPLACE_ME__',
          800: '__REPLACE_ME__',
          900: '__REPLACE_ME__',
        },
        neutral: {
          0:    '#ffffff',
          50:   '#f9fafb',
          100:  '#f3f4f6',
          200:  '#e5e7eb',
          300:  '#d1d5db',
          400:  '#9ca3af',
          500:  '#6b7280',
          600:  '#4b5563',
          700:  '#374151',
          800:  '#1f2937',
          900:  '#111827',
          1000: '#000000',
        },
        success: { 500: '#10b981' },
        warning: { 500: '#f59e0b' },
        danger:  { 500: '#ef4444' },
      },
      spacing: {
        '3.5': '14px',
        '18':  '72px',
      },
      fontFamily: {
        sans:    ['__REPLACE_ME_TEXT_FONT__', 'system-ui', 'sans-serif'],
        display: ['__REPLACE_ME_DISPLAY_FONT__', 'ui-serif', 'serif'],
        mono:    ['ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      borderRadius: {
        none: '0',
        sm:   '2px',
        DEFAULT: '6px',
        md:   '8px',
        lg:   '12px',
        xl:   '16px',
        '2xl':'24px',
        full: '9999px',
      },
    },
  },
  plugins: [],
};

export default config;
```

## Tailwind v4 — `app/globals.css`

```css
@import "tailwindcss";

@theme {
  --color-primary-50:  __REPLACE_ME__;
  --color-primary-100: __REPLACE_ME__;
  --color-primary-500: __REPLACE_ME__;
  --color-primary-600: __REPLACE_ME__;
  --color-primary-900: __REPLACE_ME__;

  --color-neutral-0:    #ffffff;
  --color-neutral-50:   #f9fafb;
  --color-neutral-100:  #f3f4f6;
  --color-neutral-500:  #6b7280;
  --color-neutral-900:  #111827;
  --color-neutral-1000: #000000;

  --color-success-500: #10b981;
  --color-warning-500: #f59e0b;
  --color-danger-500:  #ef4444;

  --font-sans:    __REPLACE_ME_TEXT_FONT__, system-ui, sans-serif;
  --font-display: __REPLACE_ME_DISPLAY_FONT__, ui-serif, serif;
  --font-mono:    ui-monospace, SFMono-Regular, monospace;

  --radius-sm: 2px;
  --radius:    6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
}
```

## styled-components / Emotion — `lib/theme.ts`

```ts
export const theme = {
  colors: {
    primary: {
      50:  '__REPLACE_ME__',
      500: '__REPLACE_ME__',
      900: '__REPLACE_ME__',
    },
    neutral: {
      0:    '#ffffff',
      50:   '#f9fafb',
      500:  '#6b7280',
      900:  '#111827',
      1000: '#000000',
    },
    success: '#10b981',
    warning: '#f59e0b',
    danger:  '#ef4444',
  },
  spacing: {
    0: '0',
    1: '4px',
    2: '8px',
    3: '12px',
    4: '16px',
    6: '24px',
    8: '32px',
    12: '48px',
    16: '64px',
  },
  fontSize: {
    xs:   '12px',
    sm:   '14px',
    base: '16px',
    lg:   '18px',
    xl:   '20px',
    '2xl':'24px',
    '3xl':'30px',
    '4xl':'36px',
  },
  radius: {
    sm: '2px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    full: '9999px',
  },
  breakpoint: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
} as const;

export type Theme = typeof theme;
```

## Material UI — `lib/theme.ts`

```ts
import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    primary: {
      main:  '__REPLACE_ME__',
      light: '__REPLACE_ME__',
      dark:  '__REPLACE_ME__',
    },
    secondary: {
      main: '__REPLACE_ME__',
    },
  },
  typography: {
    fontFamily: '__REPLACE_ME_TEXT_FONT__, system-ui, sans-serif',
    h1: { fontSize: '2.25rem', fontWeight: 700 },
    h2: { fontSize: '1.875rem', fontWeight: 700 },
    h3: { fontSize: '1.5rem', fontWeight: 600 },
    body1: { fontSize: '1rem' },
    body2: { fontSize: '0.875rem' },
  },
  spacing: 4,
  shape: { borderRadius: 8 },
});
```

## Chakra UI — `lib/theme.ts`

```ts
import { extendTheme } from '@chakra-ui/react';

export const theme = extendTheme({
  colors: {
    primary: {
      50:  '__REPLACE_ME__',
      500: '__REPLACE_ME__',
      900: '__REPLACE_ME__',
    },
  },
  fonts: {
    heading: '__REPLACE_ME_DISPLAY_FONT__, system-ui, sans-serif',
    body:    '__REPLACE_ME_TEXT_FONT__, system-ui, sans-serif',
  },
  radii: {
    sm: '2px',
    md: '8px',
    lg: '12px',
    xl: '16px',
  },
});
```

## Vanilla CSS / CSS Modules — `src/styles/tokens.css`

```css
:root {
  /* color palette */
  --color-primary-50:  __REPLACE_ME__;
  --color-primary-500: __REPLACE_ME__;
  --color-primary-900: __REPLACE_ME__;

  --color-neutral-0:    #ffffff;
  --color-neutral-50:   #f9fafb;
  --color-neutral-500:  #6b7280;
  --color-neutral-900:  #111827;
  --color-neutral-1000: #000000;

  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger:  #ef4444;

  /* spacing scale */
  --space-0: 0;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;

  /* typography */
  --font-sans:    __REPLACE_ME_TEXT_FONT__, system-ui, sans-serif;
  --font-display: __REPLACE_ME_DISPLAY_FONT__, ui-serif, serif;
  --text-xs:   12px;
  --text-sm:   14px;
  --text-base: 16px;
  --text-lg:   18px;
  --text-xl:   20px;

  /* radius and shadow */
  --radius-sm: 2px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
```

## Operator-facing defaults checklist

When the skill scaffolds any of the files above, the operator gets a short checklist instead of a wall of text:

```
✅ Tokens file scaffolded at <path>.
   Next — fill in these 5 values and you're set up:
   1. --color-primary-500    (your brand color)
   2. --color-primary-50     (brand color at 10%)
   3. --color-primary-900    (brand color at 90%)
   4. __REPLACE_ME_TEXT_FONT__    (your body font, e.g. "Inter")
   5. __REPLACE_ME_DISPLAY_FONT__ (your headline font, e.g. "Fraunces")

Every other token has a working default. You can adjust anything you want,
but you can also ship without touching the rest.
```
