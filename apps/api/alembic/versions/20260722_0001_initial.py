"""Initial PostGIS long-form data model."""

from alembic import op

revision = "20260722_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute(
        "CREATE TYPE location_type AS ENUM ('COUNTRY','STATE','DISTRICT','CITY','NEIGHBORHOOD')"
    )
    op.execute(
        "CREATE TYPE preferred_geo_level AS ENUM ('COUNTRY','STATE','DISTRICT','CITY','NEIGHBORHOOD')"
    )
    op.execute(
        "CREATE TYPE observation_geo_level AS ENUM ('COUNTRY','STATE','DISTRICT','CITY','NEIGHBORHOOD')"
    )
    op.execute(
        "CREATE TYPE indicator_direction AS ENUM ('HIGHER_IS_BETTER','LOWER_IS_BETTER','TARGET_RANGE','DESCRIPTIVE_ONLY')"
    )
    op.execute(
        "CREATE TYPE evidence_type AS ENUM ('OFFICIAL','REPRESENTATIVE_SURVEY','RESIDENT_PERCEPTION','USER_REPORTED')"
    )
    op.execute(
        "CREATE TYPE quality_status AS ENUM ('VALIDATED','PROVISIONAL','ESTIMATED','STALE','REJECTED')"
    )
    for statement in """
    CREATE TABLE categories (
      id uuid PRIMARY KEY, code varchar(80) NOT NULL UNIQUE,
      parent_id uuid REFERENCES categories(id), sort_order integer NOT NULL DEFAULT 0
    );
    CREATE TABLE locations (
      id uuid PRIMARY KEY, slug varchar(160) NOT NULL UNIQUE, name varchar(200) NOT NULL,
      location_type location_type NOT NULL, parent_location_id uuid REFERENCES locations(id),
      iso_country_code varchar(2) NOT NULL, official_geo_code varchar(40),
      latitude numeric(9,6), longitude numeric(9,6), geometry geometry(GEOMETRY,4326),
      population integer, valid_from date, valid_to date
    );
    CREATE INDEX ix_locations_country_type ON locations(iso_country_code, location_type);
    CREATE INDEX ix_locations_geometry ON locations USING gist(geometry);
    CREATE TABLE indicators (
      id uuid PRIMARY KEY, code varchar(120) NOT NULL UNIQUE, category_id uuid NOT NULL REFERENCES categories(id),
      description_key varchar(180) NOT NULL, name_key varchar(180) NOT NULL, unit varchar(60) NOT NULL,
      direction indicator_direction NOT NULL, value_type varchar(30) NOT NULL DEFAULT 'number',
      preferred_geo_level preferred_geo_level NOT NULL, normalization_method varchar(40) NOT NULL DEFAULT 'winsorized_minmax',
      official_only boolean NOT NULL DEFAULT true, target_min numeric(18,6), target_max numeric(18,6), active boolean NOT NULL DEFAULT true
    );
    CREATE TABLE sources (
      id uuid PRIMARY KEY, organization varchar(200) NOT NULL, dataset_name varchar(300) NOT NULL,
      official_status boolean NOT NULL, evidence_type evidence_type NOT NULL, license varchar(200), api_endpoint text,
      update_frequency varchar(80), last_checked_at timestamptz, next_expected_update date,
      UNIQUE(organization, dataset_name)
    );
    CREATE TABLE import_batches (
      id uuid PRIMARY KEY, source_id uuid NOT NULL REFERENCES sources(id), raw_object_key text NOT NULL,
      raw_sha256 varchar(64) NOT NULL, started_at timestamptz NOT NULL, completed_at timestamptz,
      status varchar(30) NOT NULL, validation_report jsonb NOT NULL DEFAULT '{}'::jsonb
    );
    CREATE TABLE observations (
      id uuid PRIMARY KEY, indicator_id uuid NOT NULL REFERENCES indicators(id), location_id uuid NOT NULL REFERENCES locations(id),
      period_start date NOT NULL, period_end date NOT NULL, value numeric(24,8) NOT NULL, unit varchar(60) NOT NULL,
      source_id uuid NOT NULL REFERENCES sources(id), source_dataset varchar(300) NOT NULL, source_url text NOT NULL,
      retrieved_at timestamptz NOT NULL, published_at timestamptz, geographic_level observation_geo_level NOT NULL,
      quality_status quality_status NOT NULL, methodology_version varchar(120) NOT NULL,
      transformations text[] NOT NULL DEFAULT '{}', import_batch_id uuid REFERENCES import_batches(id),
      UNIQUE(indicator_id, location_id, period_start, period_end, source_id, methodology_version)
    );
    CREATE INDEX ix_observations_latest ON observations(indicator_id, location_id, period_end DESC);
    CREATE TABLE profiles (
      id uuid PRIMARY KEY, user_id varchar(200) NOT NULL, name varchar(120) NOT NULL,
      household_type varchar(60) NOT NULL, household_size integer NOT NULL CHECK(household_size > 0),
      children_ages integer[] NOT NULL DEFAULT '{}', disposable_income numeric(14,2),
      preferred_languages varchar(8)[] NOT NULL DEFAULT '{}', attributes jsonb NOT NULL DEFAULT '{}'::jsonb
    );
    CREATE INDEX ix_profiles_user_id ON profiles(user_id);
    CREATE TABLE profile_weights (
      profile_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
      indicator_id uuid NOT NULL REFERENCES indicators(id), weight numeric(8,4) NOT NULL CHECK(weight >= 0),
      mandatory boolean NOT NULL DEFAULT false, minimum_acceptable_score numeric(6,2),
      PRIMARY KEY(profile_id, indicator_id)
    );
    CREATE TABLE rankings (
      id uuid PRIMARY KEY, user_id varchar(200), request_payload jsonb NOT NULL, result_payload jsonb NOT NULL,
      methodology_version varchar(60) NOT NULL, created_at timestamptz NOT NULL, expires_at timestamptz
    );
    """.split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade() -> None:
    op.execute(
        "DROP TABLE IF EXISTS rankings, profile_weights, profiles, observations, import_batches, sources, indicators, locations, categories CASCADE"
    )
    for enum_name in (
        "quality_status",
        "evidence_type",
        "indicator_direction",
        "observation_geo_level",
        "preferred_geo_level",
        "location_type",
    ):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
