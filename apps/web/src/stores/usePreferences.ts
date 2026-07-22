import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Locale } from "@norevia/shared-types";
import type { ProfileState, RankingResponse } from "@/types/api";

export const categories = ["education","inclusion","employment","housing","health","safety","cost_of_living","mobility","environment","climate","digital","entrepreneurship"] as const;
export type Category = typeof categories[number];
const initialWeights: Record<Category, number> = { education:15,inclusion:10,employment:15,housing:15,health:10,safety:10,cost_of_living:10,mobility:5,environment:3,climate:3,digital:2,entrepreneurship:2 };
const initialProfile: ProfileState = { name:"",adults:1,childrenAges:[],occupation:"",sector:"",disposableIncome:null,languages:[],mobility:"transit",tenure:"rent",entrepreneurialProject:false,climatePreference:"temperate" };

interface PreferencesState {
  locale: Locale; theme: "light" | "dark"; profile: ProfileState; weights: Record<Category, number>;
  selectedLocations: string[]; constraints: RankingRequestConstraint[]; savedComparisons: RankingResponse[];
  setLocale(locale: Locale): void; toggleTheme(): void; setProfile(profile: ProfileState): void;
  setWeight(category: Category, weight: number): void; setSelectedLocations(slugs: string[]): void;
  setConstraints(constraints: RankingRequestConstraint[]): void; saveComparison(result: RankingResponse): void;
}
export type RankingRequestConstraint = { indicatorCode:string; operator:"lte"|"gte"|"eq"; value:number; required:boolean };

export const usePreferences = create<PreferencesState>()(persist((set) => ({
  locale:"en",theme:"light",profile:initialProfile,weights:initialWeights,selectedLocations:[],constraints:[],savedComparisons:[],
  setLocale:(locale)=>set({locale}), toggleTheme:()=>set((state)=>({theme:state.theme==="light"?"dark":"light"})),
  setProfile:(profile)=>set({profile}), setWeight:(category,weight)=>set((state)=>({weights:{...state.weights,[category]:weight}})),
  setSelectedLocations:(selectedLocations)=>set({selectedLocations:selectedLocations.slice(0,4)}), setConstraints:(constraints)=>set({constraints}),
  saveComparison:(result)=>set((state)=>({savedComparisons:[result,...state.savedComparisons.filter((item)=>item.id!==result.id)].slice(0,10)})),
}), { name:"norevia-preferences", partialize:(state)=>({locale:state.locale,theme:state.theme,profile:state.profile,weights:state.weights,selectedLocations:state.selectedLocations,constraints:state.constraints,savedComparisons:state.savedComparisons}) }));
