import type { RankingResult } from "@norevia/shared-types";

export interface ProfileState {
  name: string; adults: number; childrenAges: number[]; occupation: string; sector: string;
  disposableIncome: number | null; languages: string[]; mobility: "car" | "transit" | "both";
  tenure: "rent" | "buy"; entrepreneurialProject: boolean; climatePreference: "cool" | "temperate" | "warm";
}
export interface RankingResponse { id: string; methodologyVersion: string; createdAt: string; results: RankingResult[]; warnings: string[] }
export interface LocationOption { id: string; slug: string; name: string; locationType: string; isoCountryCode: string }
export interface RankingRequest {
  locationType: "city" | "state"; countries: string[]; locationSlugs: string[];
  household: { adults: number; children: number }; weights: Record<string, number>;
  constraints: { indicatorCode: string; operator: "lte" | "gte" | "eq"; value: number; required: boolean }[];
}
