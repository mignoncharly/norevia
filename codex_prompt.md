# Codex Implementation Prompt

Start by opening and reading the entire file:

```text
Norevia.md
```

Do not write or modify any code before you have read that file completely.

Treat `Norevia.md` as the authoritative and non-negotiable project specification. The 14 numbered sections must be implemented without reducing their scope, omitting requirements or replacing them with placeholders.

Your task is to build the project described in `Norevia.md` as a production-grade React PWA and data platform.

## Mandatory instructions

1. Read `Norevia.md` completely before beginning.
2. Inspect the existing repository, including all source files, configuration files, documentation, migrations, scripts and deployment files.
3. If the repository already contains `AGENTS.md`, `README.md`, architecture documentation or coding standards, read them before making changes.
4. Create a clear implementation plan based on the existing repository and the complete specification.
5. Do not build a superficial MVP, mock-only interface or placeholder architecture.
6. Do not remove or simplify any of the 14 sections from `Norevia.md`.
7. Use English as the primary and source language.
8. Implement French and German as complete alternative languages from the beginning.
9. Do not hardcode user-facing strings in React components.
10. Use stable internationalization keys and language resource files.
11. Use React with TypeScript and Vite.
12. Implement the PWA using `vite-plugin-pwa` and Workbox.
13. Use FastAPI for the backend.
14. Use PostgreSQL with PostGIS for geographic and indicator data.
15. Use Redis for caching where appropriate.
16. Implement the extensible long-form indicator and observation model described in the specification.
17. Preserve source provenance, reference period, publication date, retrieval date, geographic level, methodology version and quality status.
18. Implement scoring, weighting, confidence coefficients, data coverage and methodological confidence as distinct concepts.
19. Keep official data, representative surveys, resident perception and user-reported experiences separate.
20. Build the first production scope around Germany with approximately 40 to 60 strong indicators.
21. Prepare the architecture for later EU and international expansion.
22. Implement automated tests for critical frontend, backend, scoring and data-processing logic.
23. Add migrations, seed data, validation scripts and reproducible local development commands.
24. Provide Docker Compose services for the web app, API, PostgreSQL/PostGIS, Redis, workers and any required orchestration components. skip this
25. Prepare production deployment for an IONOS VPS running Ubuntu.
26. Use Nginx as the public reverse proxy and TLS termination layer.
27. Use Docker Compose and/or systemd services as described in `Norevia.md`. skip this
28. Include firewall guidance, environment variables, automated backups, restore procedures, health checks, log rotation and service restart policies.
29. Do not configure deployment for Vercel, Netlify, Render, Railway or another managed frontend platform as the primary production target.
30. Document all commands required to install, configure, migrate, test, build, deploy, monitor, back up and restore the system on the IONOS Ubuntu VPS.

## Required working method

First, audit the repository and produce a concise gap analysis against `Norevia.md`.

Then implement the foundation in this order:

1. repository and monorepo structure;
2. shared TypeScript and Python conventions;
3. internationalization foundation;
4. database schema and migrations;
5. source and indicator catalog;
6. observation and provenance model;
7. scoring engine;
8. FastAPI endpoints;
9. React application shell;
10. onboarding and profile creation;
11. weighting and exclusion filters;
12. comparison and ranking views;
13. source transparency and data-quality views;
14. PWA support;
15. ETL source adapters and validation pipeline;
16. tests;
17. Docker Compose; skip this
18. Nginx and IONOS Ubuntu deployment;
19. monitoring, backup and restore documentation.

At every stage:

- use real implementations rather than placeholders;
- keep the application runnable;
- preserve type safety;
- validate external data;
- handle missing data explicitly;
- write migrations instead of manually modifying production tables;
- add tests for scoring and normalization;
- document assumptions;
- do not silently invent official data;
- do not silently reuse national data for a city;
- do not merge official and subjective data into one unexplained score.

When a requirement cannot yet be completed because an external API key, dataset or credential is unavailable, implement the full interface, schema, adapter contract, validation and error handling. Clearly document the missing external dependency without pretending that the integration is complete.

Begin now by reading `Norevia.md`.
