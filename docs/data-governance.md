# Data governance and source onboarding

Every source onboarding change must identify the producing organization, dataset, license, stable endpoint, update frequency, expected unit, geographic code system, reference-period fields, publication field, methodology version, and target indicator. Reviewers must verify the meaning of a series against source metadata before enabling publication.

Raw responses are immutable and addressed by SHA-256. A re-download with identical bytes reuses the object. Candidate observations are rejected for impossible values, unexpected units, duplicate natural keys, missing provenance, invalid periods, or replacement of newer data by older data. Series breaks and abnormal annual variation require review. Territory merges/deletions are represented with `valid_from` and `valid_to`; observations are never reassigned to successor territories without an explicit mapping record in a future migration.

No observation values ship as seed data. Tests use synthetic values under test-only fixtures. The production catalog contains 50 indicator definitions and location/source metadata only.

## External dependencies still required

- Approved table-to-indicator mappings for each selected Destatis GENESIS table.
- Approved JSON-stat dimension mappings for each Eurostat dataset.
- OIDC provider credentials for cross-device profile synchronization.
- A production domain, TLS email, PostgreSQL password, and optional paid/private source credentials.

These are configuration and data-governance gates. The application must not treat a successful download as approval to publish.
