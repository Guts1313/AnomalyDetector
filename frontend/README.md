# Network Anomaly Detector — React + TypeScript Frontend

Replacement for the Streamlit dashboard (`dashboard/app.py`). Pure-static SPA built with **Vite + React + TypeScript**; charts via **Plotly**. Talks to the existing FastAPI backend (`/health`, `/metrics`, `/alerts`, `/predict`).

## Highlights

- **Dark theme by default**, light theme toggle (persists to `localStorage`, respects `prefers-color-scheme` on first load).
- **Glassmorphism navbar**: sticky, translucent surface with `backdrop-filter` blur.
- **Responsive** mobile-first layout (breakpoints at 640 / 768 / 1024 px).
- **Plotly charts** themed via CSS variables — re-render on theme flip with no flicker.
- **Severity/category color palette** preserved from the Streamlit version.
- Accessibility: keyboard-sortable table with `aria-sort`, visible focus rings, `prefers-reduced-motion` respected, color never the only signal (chip text + dot + label).

## Tabs

1. **Overview** — KPI cards (flows, alerts, benign, latency) + severity bar + attacks-by-class donut.
2. **Alerts** — sortable table; severity chip; progress bar for attack score.
3. **Manual scoring** — three-column form + preset loader + threshold slider → verdict card with class-probability chart.
4. **Request examples** — accordion of the 8 categories ported from `dashboard/app.py`, each with its signals table, full JSON request body, and "Load into form" / "Send to /predict" actions.
5. **About** — short summary.

## Quick start (local dev)

```bash
cd frontend
npm install
cp .env.example .env       # adjust VITE_API_URL if your API is not on :8000
npm run dev
# → http://localhost:5173 (Vite proxies /api → http://localhost:8000)
```

If you run the API directly on `:8000`, you can also point at it without the proxy:

```bash
VITE_API_URL=http://localhost:8000 npm run dev
```

## Build & preview

```bash
npm run build       # → dist/
npm run preview     # serves dist/ on :5173
npm run typecheck   # tsc -b --noEmit
```

## Docker

A `Dockerfile` is included. Build args:

- `VITE_API_URL` (default `/api`) — baked into the SPA at build time.

```bash
docker build -t anomaly-detector-frontend ./frontend
docker run --rm -p 8080:8080 anomaly-detector-frontend
```

To wire it into the existing `docker-compose.yml`, append:

```yaml
  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_URL: /api
    image: anomaly-detector-frontend:0.1.0
    container_name: ad-frontend
    ports:
      - "8080:8080"
    depends_on:
      - api
    restart: unless-stopped
```

The bundled nginx proxies `/api/*` → `http://api:8000/*` inside the compose network.

## Project layout

```
src/
├─ main.tsx, App.tsx
├─ theme/        tokens.css · ThemeProvider · useTheme
├─ state/        FormStore (shared manual-scoring form state)
├─ api/          client · types
├─ components/   Navbar · Tabs · KPI · Badge · PlotlyChart · VerdictCard
├─ tabs/         Overview · Alerts · ManualScoring · Examples · About
├─ data/         examples.ts (the 8 preset request bodies)
└─ styles/       global.css
```

## Replacing the Streamlit dashboard

The Streamlit app stays untouched. To swap it in `docker-compose.yml`, remove (or stop) the `dashboard` service and add the `frontend` service shown above. The API is unchanged.
