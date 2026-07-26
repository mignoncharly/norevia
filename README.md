# Norevia

Norevia started with a practical question: **how can someone compare places to live without relying on a black-box ranking?**

Most comparison sites mix data from different years, hide the weighting behind a single score, and rarely explain what is missing. Norevia takes the opposite approach. Every result should be traceable to an official source, the geographic scope should be clear, and missing data should remain visible instead of quietly becoming a zero.

The first version focuses on Germany. The underlying model is designed to grow beyond that scope once the source mappings and governance rules are ready.

## What the project covers

- A governed catalogue of 50 indicators
- Personal weighting across comparison categories
- Quality-aware ranking and side-by-side comparison
- English, French and German interfaces
- Long-form observations in PostgreSQL/PostGIS
- Raw-source preservation, provenance and validation records
- Source adapters for official datasets
- An installable React/Vite PWA
- A FastAPI backend with SQLAlchemy and Alembic
- Ubuntu deployment with Nginx, systemd, backups and restore procedures

## One important rule

Norevia does not ship invented observations. Until an official source has been reviewed, mapped and published, the interface shows an honest empty-data state.

Missing observations reduce coverage; they do not count as zero. Descriptive or unofficial evidence can provide context, but it cannot silently enter the official composite score.

## Repository map

| Path | Purpose |
| --- | --- |
| `apps/web` | React, TypeScript, Vite and Workbox PWA |
| `apps/api` | FastAPI, SQLAlchemy and Alembic |
| `pipelines` | Source downloads, validation and ingestion |
| `packages/indicator-catalog` | Governed Germany v1 indicator catalogue |
| `packages/scoring-engine` | Reusable scoring logic |
| `packages/shared-types` | Shared API concepts |
| `docs` | Architecture, governance and operational runbooks |
| `deploy` | Nginx, systemd, backup and restore assets |

## Run it locally

You need Node.js 20+, npm 10+, Python 3.12, PostgreSQL 16 with PostGIS, and Redis 7+.

```powershell
Copy-Item .env.example .env
npm install

python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".\apps\api[dev]" -e ".\pipelines[dev]"

Set-Location apps/api
..\..\.venv\Scripts\alembic upgrade head
..\..\.venv\Scripts\python -m app.services.seed_catalog
```

Start the API and web app in separate terminals:

```powershell
Set-Location apps/api
..\..\.venv\Scripts\uvicorn app.main:app --reload
```

```powershell
npm run dev
```

The PWA runs at `http://localhost:5173`; the OpenAPI documentation is available at `http://localhost:8000/docs`.

## Checks

```powershell
npm run typecheck
npm test
npm run build
.\.venv\Scripts\python -m ruff check apps/api pipelines
.\.venv\Scripts\python -m pytest
```

Before adding a dataset, read the architecture and data-governance notes. The difficult part is not downloading a CSV; it is making the result comparable, explainable and safe to publish.
