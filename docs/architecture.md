# Architecture

Norevia is a monorepo with a Vite React PWA in `apps/web`, FastAPI in `apps/api`, source pipelines in `pipelines`, and versioned shared contracts/catalogs in `packages`.

The data path is one-way: official source → immutable SHA-256 raw object → mapped candidate observations → validation report → staging → approved long-form observations → quality-adjusted API ranking → PWA. A pipeline cannot publish when an error-level validation issue exists. Dataset-specific semantic mappings are reviewed code, not inferred at runtime.

Scores use a same-year, same-level peer group and 5th/95th percentile capping. Official evidence alone enters the official score. Representative surveys, resident perception, and user reports have distinct evidence types and must be rendered separately. A geographic fallback, if later enabled, must retain its original geographic level and receive an explicit confidence reduction; the current API does not silently fall back.

Authentication is configured as an external OIDC boundary. OIDC issuer and audience must be supplied before account synchronization is enabled. Anonymous profiles, weights, constraints, and the latest ten comparisons remain local-first in the PWA.
