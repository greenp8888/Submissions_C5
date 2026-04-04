# Frontend — Ideascope

Next.js 14 frontend with streaming SSE support for real-time competitive intelligence reports.

## Prerequisites

- Node.js 18 or higher

## Setup

```bash
cd frontend
npm install
```

### Environment Variables (Optional)

```bash
cp .env.local.example .env.local
```

Defaults to `http://localhost:8000` for backend.

## Run

```bash
npm run dev
```

Visit `http://localhost:3000`

## Build for Production

```bash
npm run build
npm start
```

## Design System

### Typography

- **Headings**: Instrument Serif
- **Data/Code**: DM Mono

### Colors

```
--paper: #F9F8F6      /* Background */
--ink: #0F0F0E        /* Text */
--muted: #8A8882      /* Secondary */
--border: #E8E6E1     /* Borders */
--green: #1A7A4A      /* Traffic light */
--amber: #B45309
--red: #B91C1C
```

## Structure

```
app/
  ├── page.tsx              # Landing + form
  ├── layout.tsx            # Root layout
  ├── globals.css           # Tailwind config
  ├── api/analyze/route.ts  # API endpoint
  └── report/[id]/page.tsx  # Streaming report

components/
  ├── TrafficLight.tsx
  ├── FeatureTable.tsx
  ├── SourceCard.tsx
  └── StreamingProgress.tsx
```
