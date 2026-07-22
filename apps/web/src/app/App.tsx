import { Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/AppShell";
import { OverviewPage } from "@/features/locations/OverviewPage";
import { ProfilePage } from "@/features/onboarding/ProfilePage";
import { PrioritiesPage } from "@/features/scoring/PrioritiesPage";
import { ComparePage } from "@/features/comparison/ComparePage";
import { MethodologyPage } from "@/features/scoring/MethodologyPage";
import { SavedPage } from "@/features/saved-searches/SavedPage";

export function App(){return <Routes><Route element={<AppShell/>}><Route index element={<OverviewPage/>}/><Route path="profile" element={<ProfilePage/>}/><Route path="priorities" element={<PrioritiesPage/>}/><Route path="compare" element={<ComparePage/>}/><Route path="methodology" element={<MethodologyPage/>}/><Route path="saved" element={<SavedPage/>}/></Route></Routes>}
