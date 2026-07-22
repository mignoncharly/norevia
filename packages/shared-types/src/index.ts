export type Locale = "en" | "fr" | "de";
export type LocationType = "country" | "state" | "district" | "city" | "neighborhood";
export type Direction = "HIGHER_IS_BETTER" | "LOWER_IS_BETTER" | "TARGET_RANGE" | "DESCRIPTIVE_ONLY";
export type EvidenceType = "OFFICIAL" | "REPRESENTATIVE_SURVEY" | "RESIDENT_PERCEPTION" | "USER_REPORTED";
export type QualityStatus = "VALIDATED" | "PROVISIONAL" | "ESTIMATED" | "STALE" | "REJECTED";
export type ConfidenceBand = "high" | "medium" | "low" | "insufficient";

export interface LocationSummary {
  id: string;
  slug: string;
  name: string;
  locationType: LocationType;
  parentLocationId: string | null;
  isoCountryCode: string;
  officialGeoCode: string | null;
  latitude: number | null;
  longitude: number | null;
  population: number | null;
}

export interface Provenance {
  organization: string;
  datasetName: string;
  sourceUrl: string;
  referencePeriod: string;
  publishedAt: string | null;
  retrievedAt: string;
  geographicLevel: LocationType;
  methodologyVersion: string;
  qualityStatus: QualityStatus;
  transformations: string[];
}

export interface RankedIndicator {
  indicatorCode: string;
  indicatorName: string;
  categoryCode: string;
  rawValue: number;
  unit: string;
  score: number | null;
  weight: number;
  qualityCoefficient: number;
  evidenceType: EvidenceType;
  provenance: Provenance;
}

export interface RankingResult {
  location: LocationSummary;
  destinationScore: number | null;
  dataCoverage: number;
  methodologicalConfidence: ConfidenceBand;
  constraintsMet: boolean;
  failedConstraints: string[];
  indicators: RankedIndicator[];
}
