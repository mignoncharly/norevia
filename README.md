# Norevia

Norevia is a transparent destination-comparison PWA: verifiable official evidence, personal weighting, explicit geographic scope, and visible uncertainty. Version 1 targets Germany with a governed 50-indicator catalog and architecture that can expand across the EU and internationally.

The repository began empty. The implemented foundation covers the React/Vite PWA, English/French/German localization, PostgreSQL/PostGIS long-form model, provenance and raw-import records, quality-aware scoring, FastAPI business endpoints, source adapters and validation, automated tests, and an IONOS Ubuntu deployment using Nginx and systemd. Docker is intentionally absent because the implementation brief explicitly says to skip it.

## Repository layout

```text
apps/web                   React, TypeScript, Vite, Workbox PWA
apps/api                   FastAPI, SQLAlchemy, Alembic
pipelines                  immutable source downloads and validation
packages/indicator-catalog governed Germany v1 catalog (50 indicators)
packages/scoring-engine    browser-compatible scoring primitives
packages/shared-types      shared API concepts
deploy                     Nginx, systemd, backup and restore assets
docs                       architecture, governance and VPS runbooks
```

## Local prerequisites

- Node.js 20 or later and npm 10 or later
- Python 3.12
- PostgreSQL 16+ with PostGIS
- Redis 7+

No observation values are seeded or invented. Until reviewed official source mappings have published observations, the UI intentionally shows an empty-data state.

## Install and run

```powershell
Copy-Item .env.example .env
npm install
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".\apps\api[dev]" -e ".\pipelines[dev]"
Set-Location apps/api
..\..\.venv\Scripts\alembic upgrade head
..\..\.venv\Scripts\python -m app.services.seed_catalog
Set-Location ../..
```

Run the API and PWA in separate terminals:

```powershell
Set-Location apps/api
..\..\.venv\Scripts\uvicorn app.main:app --reload
```

```powershell
npm run dev
```

Open `http://localhost:5173`; OpenAPI is at `http://localhost:8000/docs`.

## Quality commands

```powershell
npm run typecheck
npm test
npm run build
.\.venv\Scripts\python -m ruff check apps/api pipelines
.\.venv\Scripts\python -m pytest
```

Download and preserve a source response (this does not publish it):

```powershell
.\.venv\Scripts\norevia-pipeline eurostat demo_r_d3dens --raw-root raw
.\.venv\Scripts\norevia-pipeline destatis 12411-0015 --raw-root raw
```

## API

Core routes include:

- `GET /api/v1/locations?type=city&country=DE`
- `GET /api/v1/locations/{slug}`
- `GET /api/v1/indicators?category=education`
- `GET /api/v1/observations?location=berlin&indicator=median_cold_rent`
- `POST /api/v1/rankings` and `POST /api/v1/comparisons`
- `GET /health/live` and `GET /health/ready`

Ranking category weights must total exactly 100. Missing observations lower data coverage and never count as zero. Descriptive-only and non-official evidence cannot enter the official composite score.

## Production

Follow [the IONOS Ubuntu runbook](docs/deployment-ionos.md). It includes firewall policy, secrets, migrations, TLS, systemd isolation, restart policies, health checks, monitoring, log rotation, nightly backups, restore drills, updates, and rollback.

See [architecture](docs/architecture.md) and [data governance](docs/data-governance.md) before onboarding a dataset.
