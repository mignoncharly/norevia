# Project Specification — Official Data Destination Comparator PWA

This document is the authoritative project specification. It must be read in full before any implementation begins.

The application language must be **English by default**, with **French and German available as alternative languages**. All user-facing text, validation messages, navigation labels, metadata, SEO content, emails, notifications and generated reports must support internationalization from the beginning.

The project is feasible with React, but the main difficulty will not be the PWA itself. The main difficulty will be **harmonizing official data from dozens of different sources**.

The application should not be built as a simple “best countries” ranking. It should be built as a **transparent decision-support engine** where every score can be explained, verified and linked to its source.

# 1. Recommended architecture

```text
Official data sources
        ↓
ETL / ELT collectors
        ↓
Raw data zone
        ↓
Normalization and quality controls
        ↓
PostgreSQL + PostGIS
        ↓
Business API
        ↓
React PWA
        ↓
Comparison, weighting, maps and recommendations
```

## Technical stack

| Layer | Recommended technology | Role |
|---|---|---|
| Frontend | React + TypeScript | User interface |
| Build | Vite | Development and compilation |
| PWA | vite-plugin-pwa + Workbox | Installation, caching and offline mode |
| Server state | TanStack Query | API data caching and synchronization |
| Local state | Zustand | Preferences, weights and filters |
| Forms | React Hook Form + Zod | User questionnaire and validation |
| Charts | Apache ECharts or Recharts | Comparisons and trends |
| Mapping | MapLibre GL JS | Country and city maps |
| Backend API | FastAPI with Python | API, calculations, data and scoring |
| Database | PostgreSQL + PostGIS | Indicators, territories and geographic data |
| ETL | Python, Polars, Pandas, DuckDB | Importing and transformation |
| Orchestration | Prefect or Dagster | Scheduled updates |
| Cache | Redis | Result acceleration |
| Raw storage | S3-compatible storage, MinIO or local object storage | Preservation of source files |
| Authentication | Supabase Auth, Keycloak or Auth.js | Accounts and profiles |
| Tests | Vitest, Playwright, Pytest | Frontend and backend quality |
| Deployment | IONOS VPS running Ubuntu, Nginx as reverse proxy, Docker Compose and/or systemd services, PostgreSQL, Redis, automated backups, TLS certificates and GitHub Actions | Production hosting, service management, reverse proxying, SSL termination, monitoring and automated delivery |

PostGIS is particularly suitable because it adds geographic data storage, indexing and querying to PostgreSQL. Countries, regions, cities and distances can therefore be managed within the same database.

For a new React application, use **Vite + React TypeScript**, or a React framework only if server-side rendering becomes necessary. Do not use Create React App. `vite-plugin-pwa` must generate and register the service worker with Workbox.

skip docker
The production environment must run on an **IONOS VPS with Ubuntu**. Nginx must act as the public reverse proxy. Application components must run as isolated services. The preferred approach is Docker Compose for the web application, FastAPI backend, PostgreSQL, Redis, workers and orchestration services. Critical host-level processes, backups and monitoring agents may run as systemd services. The deployment must include HTTPS, firewall rules, automatic security updates, log rotation, health checks, database backups, restore procedures and environment-specific configuration.

# 2. Official data sources

## International country-level data

| Domain | Main source | Example indicators |
|---|---|---|
| Economy | World Bank | GDP, inflation, employment, poverty |
| Advanced economies | OECD | Income, taxation, housing, social mobility |
| Macroeconomics | IMF | Inflation, debt, economic outlook |
| Education | UNESCO, OECD | Enrollment, expenditure, educational results |
| Health | WHO, World Bank, OECD | Life expectancy, doctors, mortality |
| Labour | ILO | Unemployment, wages, labour protection |
| Human development | UNDP | HDI, inequality, development |
| Crime | UNODC | Homicides and selected crime indicators |
| Environment | WHO, UNEP, World Bank | Pollution, emissions, air quality |
| Freedoms and governance | United Nations, World Bank | Governance and institutional stability |
| Energy | IEA, Eurostat, World Bank | Prices, access, renewables |
| Europe | Eurostat | Prices, rents, employment, demographics, transport |

The World Bank provides nearly 16,000 indicator series through its API, while Eurostat provides free data and metadata APIs for automated downloads. OECD also provides a free SDMX-based API, although rate limits must be respected.

Eurostat provides a REST API using JSON-stat 2.0 and offers data in English, French and German. This is particularly suitable for the multilingual application.

## City-level data

This is where the project becomes more difficult. There is no single official global API containing all cities with the same definitions.

The system must combine:

- Eurostat City Statistics and NUTS regions for Europe;
- national statistical institutes such as Destatis, INSEE, Statbel or CBS;
- municipal Open Data portals;
- local housing observatories;
- Ministry of Education datasets;
- public police or judicial data;
- environmental agencies;
- public transport operators;
- tax and energy administrations.

Each city must be linked to a territorial hierarchy:

```text
World
└── Country
    └── Region
        └── Department / district
            └── City
                └── District or neighborhood, when available
```

The application must accept that an indicator may exist for a country but not for a city. In that case, it must clearly display:

> Data available only at national level.

It must not silently assign a national value to a city without an explicit warning.

# 3. Data model

Do not create one table with 220 columns. Use a long, extensible model.

## Main tables

### `locations`

```text
id
name
location_type
parent_location_id
iso_country_code
official_geo_code
latitude
longitude
geometry
population
```

### `indicators`

```text
id
code
name
category_id
description
unit
direction
value_type
preferred_geo_level
normalization_method
official_only
```

`direction` defines the favorable direction:

```text
HIGHER_IS_BETTER
LOWER_IS_BETTER
TARGET_RANGE
DESCRIPTIVE_ONLY
```

### `observations`

```text
id
indicator_id
location_id
period_start
period_end
value
unit
source_id
source_dataset
source_url
retrieved_at
published_at
geographic_level
quality_status
methodology_version
```

### `sources`

```text
id
organization
dataset_name
official_status
license
api_endpoint
update_frequency
last_checked_at
```

### `profiles`

```text
id
user_id
name
household_type
household_size
children_count
income
preferred_languages
```

### `profile_weights`

```text
profile_id
indicator_id
weight
mandatory
minimum_acceptable_score
```

This structure allows a new indicator to be added without changing the database schema.

# 4. Indicator taxonomy

The approximately 220 criteria must be divided into three levels:

```text
Category
    Subcategory
        Measurable indicator
```

Example:

```text
Education
├── Accessibility
│   ├── Annual childcare cost
│   ├── Childcare coverage rate
│   └── University fees
├── Quality
│   ├── PISA results
│   ├── Students per teacher
│   └── School dropout rate
└── Inclusion
    ├── Achievement gap by social background
    ├── Inclusion of foreign students
    └── Availability of bilingual education
```

A common mistake would be to treat “education quality” as a single data point. It is a **composite index**, calculated from several observable indicators.

# 5. Score calculation

## Normalization

Indicators have different units. They must be converted to a common scale, for example from 0 to 100.

For an indicator where a higher value is preferable:

```text
score = 100 × (value - minimum) / (maximum - minimum)
```

For an indicator where a lower value is preferable:

```text
score = 100 × (maximum - value) / (maximum - minimum)
```

However, minimum and maximum values are sensitive to outliers. In production, use:

- the 5th percentile as the minimum;
- the 95th percentile as the maximum;
- capping of values outside this range;
- normalization by year and comparable peer group.

## Weighted score

```text
overall_score =
Σ(indicator_score × user_weight × quality_coefficient)
÷
Σ(user_weight × quality_coefficient)
```

Example:

| Criterion | Score | Weight | Contribution |
|---|---:|---:|---:|
| Education | 82 | 25% | 20.50 |
| Racism and inclusion | 65 | 20% | 13.00 |
| Employment | 76 | 20% | 15.20 |
| Housing | 48 | 20% | 9.60 |
| Health | 85 | 15% | 12.75 |
| **Total** |  | 100% | **71.05** |

# 6. Do not hide data quality

Each result must show at least three distinct scores:

```text
Destination score: 78/100
Data coverage: 84%
Methodological confidence: high
```

## Possible confidence coefficient

| Situation | Coefficient |
|---|---:|
| Recent official local data | 1.00 |
| Recent official regional data | 0.90 |
| National official data applied to a city | 0.70 |
| Old official data | 0.60 to 0.85 |
| Estimated missing data | 0.30 to 0.60 |
| Subjective unofficial data | Keep separate from the official score |

The user must be able to see:

- the producing organization;
- the reference date;
- the import date;
- the unit;
- the methodology;
- the geographic level;
- the source link;
- the transformations performed.

# 7. The sensitive case of racism

Racism cannot be correctly summarized with a single number.

Create a category composed of:

| Dimension | Possible indicator |
|---|---|
| Lived experience | Share of people reporting discrimination |
| Employment | Employment access gap for comparable skills |
| Income | Income gaps by origin where available |
| Housing | Complaints or discrimination testing |
| Institutions | Trust in police and administration |
| Hate crime | Officially recorded offenses |
| Representation | Diversity in positions of responsibility |
| Legal framework | Existence and enforcement of anti-discrimination protections |

The interface must include a methodological warning: **more recorded complaints do not necessarily mean more racism**. It can also reflect better recognition of offenses, more accessible police or a better reporting system.

Therefore, keep separate:

```text
Observed official data
Representative survey data
Resident perception
User-reported experiences
```

These four data types must not be merged without distinction.

# 8. Web application features

## Main flow

### 1. Profile creation

The user provides:

- household composition;
- children’s ages;
- occupation and sector;
- disposable income;
- languages;
- car or public transport usage;
- renter or future homeowner status;
- entrepreneurial project;
- climate preferences;
- non-negotiable criteria.

The interface language must default to English. French and German must be selectable alternatives. The selected language must persist across sessions and user accounts.

### 2. Weighting

The user distributes 100 points among categories:

```text
Education              20
Inclusion              15
Employment             15
Housing                15
Health                 10
Safety                 10
Cost of living         10
Climate                 5
```

### 3. Exclusion filters

Examples:

```text
Maximum family rent: €1,500
Maximum unemployment: 8%
Bilingual school required: yes
Airport within 90 minutes: yes
Minimum safety score: 70/100
```

### 4. Results

```text
1. City A — 82/100
2. City B — 79/100
3. City C — 77/100
```

### 5. Explanation

For each destination:

- why it matches the profile;
- its main strengths;
- its main weaknesses;
- whether exclusion criteria are met;
- missing data;
- five- or ten-year evolution;
- estimated monthly household cost.

# 9. PWA interface

The PWA must provide:

- installation on Android, iOS and desktop;
- offline access to saved comparisons;
- profile synchronization;
- notifications when a country or city dataset is updated;
- comparison of up to four destinations;
- PDF or Excel export;
- comparison sharing;
- light and dark modes;
- English as the primary language;
- French and German as alternative languages.

For offline use, cache only:

```text
application shell
user profile
weights
last viewed comparisons
essential metadata
```

Do not cache the entire global database on the user’s device.

# 10. Update pipeline

```text
1. Check source availability
2. Download new data
3. Preserve the raw file without modification
4. Validate schema and units
5. Convert to the common model
6. Detect anomalies
7. Compare with the previous publication
8. Load into staging
9. Recalculate scores
10. Publish after validation
```

## Mandatory controls

- impossible value;
- changed unit;
- series break;
- changed definition;
- duplicate;
- deleted or merged territory;
- historical revision;
- older data replacing newer data;
- abnormal annual variation;
- missing metadata.

# 11. Data freshness

“Current” data does not necessarily mean “published this year”.

Example:

```text
Indicator: academic achievement
Observed period: 2022
Publication: 2023
Imported into the application: 2026
```

Therefore store separately:

- `reference_period`;
- `published_at`;
- `retrieved_at`;
- `next_expected_update`.

The IMF provides SDMX 2.1 and 3.0 APIs, while the World Bank API exposes data, sources, units and methodological notes. These metadata must be retained, not only the numerical values.

# 12. React project organization

```text
apps/
├── web/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── onboarding/
│   │   │   ├── comparison/
│   │   │   ├── locations/
│   │   │   ├── scoring/
│   │   │   └── saved-searches/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── stores/
│   │   ├── types/
│   │   └── workers/
│   └── vite.config.ts
├── api/
│   ├── app/
│   │   ├── routes/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── scoring/
│   │   └── services/
├── pipelines/
│   ├── sources/
│   │   ├── world_bank/
│   │   ├── eurostat/
│   │   ├── oecd/
│   │   └── national_sources/
│   ├── validation/
│   └── normalization/
└── packages/
    ├── indicator-catalog/
    ├── shared-types/
    └── scoring-engine/
```

Internationalization resources must be organized from the start, for example:

```text
apps/web/src/i18n/
├── en/
├── fr/
└── de/
```

English must be the source language. French and German translations must use stable translation keys rather than duplicated inline strings.

# 13. Business API

Example URLs:

```http
GET /api/v1/locations?type=city&country=DE
GET /api/v1/locations/berlin
GET /api/v1/indicators?category=education
GET /api/v1/observations?location=berlin&indicator=rent
POST /api/v1/comparisons
POST /api/v1/rankings
GET /api/v1/rankings/{id}
GET /api/v1/sources/{id}
```

Example request:

```json
{
  "locationType": "city",
  "countries": ["DE", "NL", "BE", "FR"],
  "household": {
    "adults": 2,
    "children": 1
  },
  "weights": {
    "education": 0.20,
    "inclusion": 0.15,
    "employment": 0.15,
    "housing": 0.15,
    "health": 0.10,
    "safety": 0.10,
    "cost_of_living": 0.10,
    "climate": 0.05
  },
  "constraints": {
    "maximumMonthlyRent": 1500,
    "maximumCommuteMinutes": 45
  }
}
```

All API error messages, validation responses and user-facing labels must be localization-ready. Internal API field names remain in English.

# 14. Development stages

## Version 1 — Germany and national data

- 10 to 15 categories;
- 40 to 60 indicators;
- comparison of German Länder and major cities;
- Destatis, Eurostat and regional portal data;
- profiles and weighting;
- source history;
- English as the primary language;
- French and German as alternative languages.

## Version 2 — European Union

- EU countries and major cities;
- 80 to 120 indicators;
- Eurostat and OECD data;
- family cost of living;
- real estate;
- maps;
- export functionality.

## Version 3 — International coverage

- World Bank, IMF, WHO, UNESCO and ILO;
- 150 to 220 indicators;
- global country coverage;
- variable urban coverage;
- advanced recommendation engine.

## Version 4 — Separate community data

- expatriate ratings;
- discrimination experiences;
- perceived neighborhood quality;
- validation and moderation;
- comparison between official data and perception.

# Product positioning

The product must be positioned as:

> **A destination comparison platform based on verifiable data, personalized to a person’s life project and transparent about the quality of each data point.**

The true differentiation will not come from the number of criteria. It will come from five elements:

1. complete data traceability;
2. personalized weighting;
3. distinction between country, region, city and neighborhood;
4. transparency about missing data;
5. understandable explanations for every ranking.

Start with **Germany and 50 strong indicators**, rather than 220 partially reliable global indicators. However, the architecture must be designed from the beginning to support all countries.
