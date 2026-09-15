---
name: AgroSmart Tamil Nadu Extension OS
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#3f493f'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#6f7a6e'
  outline-variant: '#becabc'
  surface-tint: '#006d30'
  primary: '#00652c'
  on-primary: '#ffffff'
  primary-container: '#15803d'
  on-primary-container: '#d3ffd5'
  inverse-primary: '#79db8d'
  secondary: '#006a63'
  on-secondary: '#ffffff'
  secondary-container: '#99efe5'
  on-secondary-container: '#006f67'
  tertiary: '#854600'
  on-tertiary: '#ffffff'
  tertiary-container: '#a95b00'
  on-tertiary-container: '#fff1e9'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#95f8a7'
  primary-fixed-dim: '#79db8d'
  on-primary-fixed: '#00210a'
  on-primary-fixed-variant: '#005323'
  secondary-fixed: '#9cf2e8'
  secondary-fixed-dim: '#80d5cb'
  on-secondary-fixed: '#00201d'
  on-secondary-fixed-variant: '#00504a'
  tertiary-fixed: '#ffdcc3'
  tertiary-fixed-dim: '#ffb77d'
  on-tertiary-fixed: '#2f1500'
  on-tertiary-fixed-variant: '#6e3900'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 2rem
    fontWeight: '700'
    lineHeight: 2.5rem
    letterSpacing: -0.025em
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.5rem
    fontWeight: '700'
    lineHeight: 2rem
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.5rem
    fontWeight: '600'
    lineHeight: 2rem
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: 1.75rem
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.125rem
    fontWeight: '600'
    lineHeight: 1.5rem
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: '400'
    lineHeight: 1.5rem
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: '400'
    lineHeight: 1.25rem
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: '400'
    lineHeight: 1rem
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: '500'
    lineHeight: 1.25rem
    letterSpacing: -0.005em
  label-sm:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: '600'
    lineHeight: 1rem
    letterSpacing: 0.02em
  data-metric:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.75rem
    fontWeight: '700'
    lineHeight: 2rem
    letterSpacing: -0.03em
  data-tabular:
    fontFamily: Inter
    fontSize: 0.8125rem
    fontWeight: '500'
    lineHeight: 1.125rem
    letterSpacing: 0em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style
This design system serves district agricultural officers, extension field staff, and state agronomists across Tamil Nadu. The visual tone balances institutional authority with high-velocity data clarity—eschewing bureaucratic heaviness in favor of crisp, modern GovTech enterprise precision. 

The aesthetic is grounded, precise, and utilitarian:
- **Tone:** Civic authority, empirical accuracy, high readability under adverse field lighting conditions (direct sun, low-end mobile devices, and office monitors).
- **Style Mix:** Contemporary enterprise SaaS with structural GovTech discipline—relying on high-contrast typography, hairline architectural containment (`1px` neutral dividers), micro-badges, and calibrated status fills over ornamental flourishes.
- **Emotional Impact:** Reassuring, mission-critical, swift, and resilient. Officers should experience instant cognitive triage: healthy crops feel systematically secure; outbreaks and infestations communicate immediate operational urgency without chaotic visual noise.

## Colors
The color architecture mirrors Tamil Nadu’s agrarian topography while satisfying strict enterprise accessibility guidelines (minimum WCAG AAA compliance on all primary data indicators).

### Functional Palette Structure
- **Primary Canvas & Surfaces:**
  - App Canvas Base: `#F8FAFC` (Slate-50) creates subtle ambient depth beneath white containers.
  - Surface Card Background: `#FFFFFF` (Pure Crisp White).
  - Surface Inset / Subdued Background: `#F0FDF4` (Field Mint 50) and `#F1F5F9` (Slate-100) for nested groups and table filters.
  - Borders & Outlines: `#E2E8F0` (Default Hairline) and `#CBD5E1` (Interactive Form Boundaries).

- **Brand Hierarchy:**
  - Primary Base (`#15803D`): Evergreen Foliage used for primary CTAs, active navigation items, and state confirmation elements. Deepened to `#14532D` for high-emphasis text and interactive hover states.
  - Secondary / Tech Accent (`#0F766E`): Deep Teal reserved for AI inference models, drone telemetry, satellite spectral feeds, and prescriptive ML advisories.
  - Neutral Base (`#0F172A`): Deep Slate-900 for primary typography, headers, and dense data labels to eliminate visual softness.

- **Agronomic Severity & Alert Protocol:**
  - **Critical / Pest Outbreak (High Risk):** Text `#B91C1C`, Icon/Fill `#DC2626`, Tinted Background `#FEF2F2`, Border `#FECACA`.
  - **Warning / Moisture Stress (Medium Risk):** Text `#B45309`, Icon/Fill `#D97706`, Tinted Background `#FFFBEB`, Border `#FDE68A`.
  - **Vigor / Optimal Canopy (Healthy / Low Risk):** Text `#15803D`, Icon/Fill `#16A34A`, Tinted Background `#ECFDF5`, Border `#A7F3D0`.
  - **Informational / Drone Sync (Neutral Signal):** Text `#1E3A8A`, Icon/Fill `#2563EB`, Tinted Background `#EFF6FF`, Border `#BFDBFE`.

## Typography
The system employs **Plus Jakarta Sans** for structural headers, analytical metric readouts, and top-level navigation, providing geometric authority and clear personality without visual fatigue. **Inter** powers data tables, diagnostic field notes, forms, and dense taxonomic classifications.

### Typographic Directives
- **Tabular Figures:** All statistical table cells, acreage numbers, telemetry metrics, and coordinate values must enforce OpenType `tnum` (tabular numerals) to guarantee vertical scanning alignment.
- **Bilingual Considerations:** Type scales and vertical rhythm accommodate dual Tamil/English layout labels where required by state mandate; generous line-height modifiers (`1.4` to `1.5` minimum on body copy) prevent multi-script diacritic clipping.
- **Micro-Labels:** Metadata badges, taluk identifiers, and sensor status pills use uppercase `label-sm` with slight positive tracking (`0.02em`) for immediate scannability.

## Layout & Spacing
The layout follows a modular 12-column responsive fluid grid designed for density without visual congestion, balancing deep GIS mapping panes alongside telemetry tables.

### Layout Philosophy
- **Screen Margins & Gutters:** Desktop monitors deploy `margin-desktop` (2rem) and `gutter-desktop` (1.5rem). Mobile field interfaces drop to a compact 1rem margin and 1rem gutter to preserve critical horizontal viewport space for inspection logs.
- **Component Density:** Dense tabular metrics require a baseline 8px grid with half-steps (`0.25rem` / 4px) strictly allocated for internal pill margins, status indicators, and adjacent sparkline indicators.
- **Responsive Breakpoints:**
  - **Mobile (< 640px):** Single-column stacked triage cards; sticky bottom navigation for field inspection actions; horizontal scrolling for tabular ledger matrices.
  - **Tablet (640px – 1023px):** 6-column reflow; side-by-side metric tiles; collapsible auxiliary navigation drawer.
  - **Desktop (1024px+):** Full 12-column command center layout; persistent left navigation rail (narrowed or expanded); dual-split viewports (GIS cadastral maps on left 7 columns, analytical drill-down on right 5 columns).

## Elevation & Depth
Depth in this system is communicated primarily through crisp hairline boundaries and hyper-subtle architectural shadows. Heavy blur drop shadows and frosted glass effects are avoided to maintain maximum computational performance and display integrity on low-power field tablets.

### Layer Hierarchy
1. **Canvas Level (0):** `#F8FAFC` slate-tinted canvas backdrop.
2. **Structural Panels (1):** Pure `#FFFFFF` surfaces bounded by an explicit `1px solid #E2E8F0` hairline border and an ambient structural shadow: `0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.03)`.
3. **Interactive Metric Cards & Hover States (2):** On hover or selection, borders elevate to `#CBD5E1` with a tinted lift: `0 4px 6px -1px rgba(21, 128, 61, 0.05), 0 2px 4px -2px rgba(15, 23, 42, 0.04)`.
4. **Modals, Flyouts & Diagnostic Drawers (3):** Deep contextual overlays with focused shadow dispersion: `0 20px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04)`.
5. **Cadastral Map Floating Controls (4):** Floating map tools use solid white with crisp perimeter borders: `0 10px 15px -3px rgba(15, 23, 42, 0.1), 0 4px 6px -4px rgba(15, 23, 42, 0.05)`.

## Shapes
A conservative, structural roundedness (`level 1` / `0.25rem` base) conveys GovTech discipline, institutional resilience, and dense data alignment. 

### Geometric Execution
- **Data Cards & Surface Panels:** Standard `0.375rem` (6px) or `0.5rem` (`rounded-lg`) corner radii to keep structural grid lines crisp and non-distracting.
- **Form Controls & Inputs:** Precision `0.25rem` (4px) or `0.375rem` corners reinforce mechanical reliability and tabular cohesion.
- **Status Pills, Badges & AI Chips:** Fully curved pill shapes (`9999px`) are reserved exclusively for categorical tags, outbreak indicators, and active filter tokens to instantly differentiate semantic labels from actionable square-cornered UI buttons.

## Components

### Buttons
- **Primary:** Solid `#15803D` background with white text, `0.375rem` corner radius, font weight 600. Active state uses `#14532D`.
- **Secondary / AI Action:** Deep Teal `#0F766E` background with white text, paired with micro spark or intelligence glyphs.
- **Outline / Filter Action:** Pure white background, `1px solid #E2E8F0`, text `#0F172A`, hover background `#F8FAFC`.
- **Destructive / Quarantine:** `#DC2626` background with white text, reserved for rapid containment orders and crop alert broadcasts.

### Status Indicators & Severity Badges
- Constructed with a two-part anatomy: a static 6px circular indicator dot alongside bold tabular uppercase text (`label-sm`).
- **Critical (Fall Armyworm / Blast):** Background `#FEF2F2`, border `#FECACA`, text `#B91C1C`, dot `#DC2626`.
- **Warning (Moderate Stress):** Background `#FFFBEB`, border `#FDE68A`, text `#B45309`, dot `#D97706`.
- **Healthy (Normal Vigor):** Background `#ECFDF5`, border `#A7F3D0`, text `#15803D`, dot `#16A34A`.

### Tables & Data Grids
- **Header:** Background `#F8FAFC`, uppercase `label-sm` text `#64748B`, `1px solid #E2E8F0` bottom border.
- **Rows:** Alternating rows remain crisp pure white with `1px solid #F1F5F9` dividers; hover transitions instantaneously to `#F0FDF4` (subtle mint highlight) for immediate row tracking.
- **Numeric Cells:** Set in `data-tabular` using `font-variant-numeric: tabular-nums` aligned right.

### Metric Cards & Sparklines
- Metric card contains: Category Label (`label-sm` in `#64748B`), Primary Metric Value (`data-metric` in `#0F172A`), Delta Tag (pill badge indicating % change over prior harvest cycle), and inline SVG sparkline graph (`1.5rem` height) rendered in emerald green or cautionary amber.

### Forms & Input Fields
- Background `#FFFFFF`, border `1px solid #CBD5E1`, text `#0F172A`, placeholder `#94A3B8`.
- Focus state applies a crisp `0 0 0 2px #15803D` outer ring without layout shift.
- Validation states swap the border directly to `#DC2626` (Error) or `#16A34A` (Verified Parcel ID).

### Custom Domain Components
- **Cadastral Farm Parcel Inspector:** Segmented card showing survey number, block, current soil moisture bar, pest threat gauge, and satellite sync timestamp.
- **AI Recommendation Banner:** Clean container with `#F0FDFA` teal tint, a `#0F766E` 3px left accent rail, diagnostic confidence score pill (e.g., "98.4% Match - Paddy Stem Borer"), and recommended biological pesticide protocol actions.