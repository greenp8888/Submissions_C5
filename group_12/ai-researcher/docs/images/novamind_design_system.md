# NovaMind — Design System & UI Implementation Spec (v1)

NovaMind is the product skin for the multi-agent deep researcher: a **dark, research-lab** interface that reads as precise, calm, and technical—neither playful nor generic “AI slop.”

## Brand & voice

- **Name:** NovaMind (one word, title case in headings).
- **Tagline:** *Synthesize evidence. Trace every step.*
- **Tone:** Short labels, imperative actions, no exclamation clutter. Errors stay factual.

## Color tokens (dark UI)

| Token | Hex / value | Usage |
|--------|-------------|--------|
| `--nm-bg-deep` | `#080a0f` | Page backdrop |
| `--nm-bg` | `#0c0e14` | Main surface |
| `--nm-surface` | `#12161f` | Cards, panels |
| `--nm-elevated` | `#181e2a` | Inputs, nested blocks |
| `--nm-border` | `rgba(100, 180, 255, 0.14)` | Hairline borders |
| `--nm-text` | `#e8edf7` | Primary text |
| `--nm-muted` | `#8b9cb3` | Secondary / hints |
| `--nm-accent` | `#22d3ee` | Primary actions, focus ring |
| `--nm-accent-dim` | `rgba(34, 211, 238, 0.15)` | Tinted backgrounds |
| `--nm-violet` | `#a78bfa` | Secondary emphasis, tab active |
| `--nm-success` | `#34d399` | Ready / success hints |
| `--nm-warn` | `#fbbf24` | Warnings |

## Typography

- **UI:** `DM Sans`, `Inter`, or system `ui-sans-serif` stack.
- **Data / trace:** `ui-monospace`, `SF Mono`, `Consolas` for pipeline logs (smaller size).
- **Scale:** Hero title ~1.35rem–1.5rem semibold; panel titles `0.95rem` uppercase tracking `0.06em`; body `0.92rem–1rem`.

## Layout

1. **Hero** — Full width: wordmark, tagline, one paragraph of product context.
2. **Workspace** — Two columns:
   - **Sidebar (~32–36%)** — Stacked **cards** (Connect → Corpus → Question → Retrieval → Run). Each card: title bar + content.
   - **Main (~64–68%)** — Status strip + **tabbed** workspace (Human review | Report | Sources | Trace).

## Components

- **Card (`.nm-card`):** `border-radius: 14px`, border `var(--nm-border)`, background `var(--nm-surface)`, padding `1rem 1.1rem`, subtle shadow.
- **Card title (`.nm-card-title`):** Muted uppercase label above card content.
- **Primary button:** Cyan accent fill or left-to-right gradient `cyan → violet`; text dark `#041014` for contrast on bright fill, or light text on outlined variant.
- **Secondary:** Ghost button, border only.
- **Tabs:** Pill-style or underline with violet active indicator; inactive tabs muted.
- **Inputs:** Dark elevated fill, cyan focus ring `2px`, rounded `10px`.
- **File dropzone:** Dashed border accent, elevated background on hover.

## Markdown content (Report)

- Citation links as **chips**: compact pill, elevated surface, cyan border at low opacity; hover brightens border.
- Max line length ~72ch in prose blocks where possible (readable column).

## Motion

- Prefer **Gradio built-in** loading states (`show_progress`). No custom heavy animation; optional 150ms ease on hover borders only.

## Implementation mapping (Gradio)

- Single `NOVAMIND_CSS` string injected via `Blocks(css=…)`.
- `elem_classes` on columns: `nm-card`, `nm-sidebar`, `nm-main`, `nm-hero`.
- `title` / `theme`: set `Blocks(title="NovaMind · Deep Researcher")`; theme may stay default if CSS overrides suffice—**CSS is source of truth** for NovaMind dark shell.

## Accessibility

- Maintain contrast ≥ 4.5:1 for body text on surfaces.
- Focus rings always visible (cyan).
- Do not rely on color alone for state; pair with text (“Ready”, “Loading…”).

---

## Implemented in `app.py` (reference)

- **Logo:** `assets/novamind-logo.png` (72×72 display in the hero). Replace the file to rebrand; no code change if the path stays the same.
- **Connection UI:** Top-right **compact summary** (source, model, credential *name* only) + **Configure** opens a fixed-position popover with full LLM controls. Never surface raw API keys in the summary.

---

*This file is the reference for `app.py` NovaMind styling. Update here first, then align CSS in code.*
