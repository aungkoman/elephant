# Myanmar ECBT National Network Website

A production-ready, bilingual (English / Myanmar) static website for the national Elephant Conservation Based Tourism (ECBT) network — 20 camps, built with **Astro + Tailwind CSS**, deployed to **Cloudflare Pages**.

The raw source material is 20 camp directories under `docs/`, each containing one or two PDFs (English and/or Myanmar versions). Data extraction, site scaffolding, content, and deployment config will all be built from scratch in this session.

---

## Open Questions

> [!IMPORTANT]
> **Please answer before I start coding:**

1. **Myanmar font preference** — Should the site use [Padauk](https://fonts.google.com/specimen/Padauk) (Google Fonts, good Unicode coverage) or [Noto Sans Myanmar](https://fonts.google.com/noto/specimen/Noto+Sans+Myanmar)? Both are free. Padauk is lighter. Default: **Padauk**.
2. **i18n approach** — The recommended approach for a pure SSG Astro site is **separate URL paths** (`/en/camps/...` and `/my/camps/...`) generated at build time — no JS toggle needed. Alternatively we can do a **single URL + JS language toggle** (simpler URLs but requires a small JS bundle). Preference? Default: **JS toggle** (simpler, single URL per camp).
3. **Map integration** — Several camps have lat/lon. Should the camp detail pages embed a map? Options: (a) **Leaflet.js** (open-source, no API key), (b) **Google Maps embed** (needs no key for basic embed iframes), (c) **No map**. Default: **Leaflet.js**.
4. **Images** — The PDFs contain embedded images, but extracting them requires `pdfimages` (Poppler) or Python `pymupdf`. Do you have Python with `pymupdf` (aka `fitz`) installed, or should I use **AI-generated placeholder images** for each camp and wire up real images later?
5. **Camp slug style** — URL slugs will be derived from directory names (e.g. `hmaw-yaw-gyi`, `ngwe-saung`). Is that acceptable, or do you want custom slugs?

---

## Proposed Changes

### Phase 1 — Data Extraction & Structuring

#### [NEW] `scripts/extract_camps.py`
Python script using `pymupdf` (`pip install pymupdf`) to:
- Walk every `docs/*/` directory
- Extract text from each PDF (English & Myanmar versions separately)
- Parse out: camp name, ministry, location, lat/lon, opening hours, entrance fees, elephant-riding fees, activities, contact phones
- Emit `src/content/camps/*.json` — one file per camp — used as Astro Content Collections

#### [NEW] `src/content/config.ts`
Defines the Zod schema for the `camps` Content Collection, validating all fields.

---

### Phase 2 — Project Initialization

Run `npx create-astro@latest` in `./` with:
- Template: `minimal`
- TypeScript: `strict`
- Install Tailwind: `npx astro add tailwind`
- Install Cloudflare adapter: `npx astro add cloudflare`

**Resulting directory layout:**
```
d:\Cisco\Code\Elephant\
├── astro.config.mjs
├── tailwind.config.mjs
├── tsconfig.json
├── package.json
├── public/
│   ├── fonts/           ← Padauk woff2 files
│   └── images/          ← camp hero images (generated or extracted)
├── src/
│   ├── content/
│   │   ├── config.ts    ← Content Collection schema
│   │   └── camps/       ← 20 × camp-name.json
│   ├── layouts/
│   │   └── BaseLayout.astro
│   ├── components/
│   │   ├── Header.astro
│   │   ├── Footer.astro
│   │   ├── LangToggle.astro
│   │   ├── CampCard.astro
│   │   ├── ActivityBadge.astro
│   │   ├── PricingTable.astro
│   │   ├── HeroSection.astro
│   │   └── MapEmbed.astro
│   └── pages/
│       ├── index.astro          ← Homepage (hero + camp grid)
│       ├── camps/
│       │   └── [slug].astro     ← Dynamic route → 20 camp pages
│       └── 404.astro
└── docs/                        ← source PDFs (unchanged)
```

---

### Phase 3 — Design System & Tailwind Config

#### [NEW] `tailwind.config.mjs`
Custom design tokens:
- **Colors**: Deep forest green (`#1a3a2a`) primary, warm amber (`#c8860a`) accent, cream (`#fdf6e3`) background, dark (`#0d1f16`) header
- **Fonts**: `'Padauk'` for Myanmar text, `'Outfit'` (Google Fonts) for English headings, `'Inter'` for body
- **Custom utilities**: `.font-myanmar`, `.font-en`, `.camp-card`, etc.

#### [NEW] `src/styles/global.css`
- Google Fonts import (Outfit, Inter, Padauk)
- CSS custom properties
- Smooth scroll, selection colors
- Myanmar unicode rendering fixes (`word-break: break-word`, `line-height: 2`)

---

### Phase 4 — UI Components

#### [NEW] `src/components/Header.astro`
Sticky nav with: Logo + tagline, nav links (Home, All Camps, About), **LangToggle** button (EN | မြန်မာ). Glassmorphism style on scroll.

#### [NEW] `src/components/LangToggle.astro`
Client-side island (`client:load`) that:
- Stores preference in `localStorage`
- Toggles `.lang-en` / `.lang-my` class on `<html>`
- All bilingual text elements use CSS: `.lang-en .en { display: block }` / `.lang-my .my { display: block }`

#### [NEW] `src/components/CampCard.astro`
Props: `camp` (full camp data object). Renders:
- Hero image with gradient overlay
- Camp name (bilingual)
- Activity badges (top 3)
- Elephant count pill
- Opening hours chip
- "Explore →" CTA

#### [NEW] `src/components/HeroSection.astro`
Full-screen hero for homepage: animated particle background (CSS only), large heading in both scripts, animated stats counter (total camps, total elephants, regions covered).

#### [NEW] `src/components/PricingTable.astro`
Props: `fees` object. Renders a styled table with local vs foreigner columns, MMK formatting.

#### [NEW] `src/components/ActivityBadge.astro`
Icon-mapped activity chips. Icons via inline SVG or Heroicons. Mapping: Elephant Riding → 🐘, Photography → 📷, Jungle Walk → 🌿, Boat → ⛵, Wedding → 💐, etc.

#### [NEW] `src/components/MapEmbed.astro`
Leaflet.js map island (`client:visible`) rendering a pin at the camp's lat/lon with a popup. Falls back gracefully if no coordinates.

---

### Phase 5 — Pages

#### [NEW] `src/pages/index.astro`
- `HeroSection` with animated background
- Filterable camp grid: filter by region / activity (vanilla JS)
- Stats bar: "20 Camps · 100+ Elephants · 9 Regions"
- Footer with ministry credit

#### [NEW] `src/pages/camps/[slug].astro`
Uses `getStaticPaths()` from Content Collections. Each page:
- Full-width hero image
- Bilingual camp name & description
- Info grid: Location · Hours · Area · Elephants
- Activity badges
- Pricing table
- Contact section (phones + Facebook link if available)
- Leaflet map (if coordinates exist)
- "← Back to all camps" breadcrumb
- SEO: `<title>`, `<meta description>`, `<meta og:*>` auto-generated per camp

---

### Phase 6 — Build & Deploy Config

#### [MODIFY] `astro.config.mjs`
```js
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import cloudflare from '@astrojs/cloudflare';

export default defineConfig({
  output: 'static',          // pure SSG
  adapter: cloudflare(),
  integrations: [tailwind()],
  site: 'https://ecbt-myanmar.pages.dev', // replace with real domain
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'my'],
    routing: { prefixDefaultLocale: false }
  }
});
```

#### [NEW] `package.json` scripts
```json
{
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "astro preview",
    "extract": "python scripts/extract_camps.py"
  }
}
```

#### [NEW] `wrangler.toml` (optional, for local CF Pages preview)
```toml
name = "ecbt-myanmar"
pages_build_output_dir = "./dist"
```

#### Cloudflare Pages settings
- Build command: `npm run build`
- Output directory: `dist`
- Node version: `18`

---

## Verification Plan

### Automated
- `npm run build` — must complete with 0 errors and generate 21 HTML files (1 index + 20 camp pages)
- `astro check` — TypeScript type checks pass

### Manual
- Run `npm run dev` and visually verify: homepage hero, camp grid filter, individual camp page, language toggle, pricing table, map pin
- Check Myanmar text renders correctly in Chrome/Firefox
- Lighthouse score ≥ 90 (Performance, SEO, Accessibility)
- Verify `dist/` contains all 20 camp HTML files
