import { useTranslation } from "react-i18next";
import { usePreferences } from "@/stores/usePreferences";
import type { ApiRankingResponse } from "@/types/ranking";

export function SavedPage(){const {t}=useTranslation();const saved=usePreferences((state)=>state.savedComparisons) as unknown as ApiRankingResponse[];return <section className="page"><p className="eyebrow">{t("nav.saved")}</p><h1>{t("saved.title")}</h1><p className="page-intro">{saved.length?t("saved.count",{count:saved.length}):t("saved.empty")}</p><div className="saved-list">{saved.map((comparison)=><article key={comparison.id}><time>{new Date(comparison.createdAt).toLocaleString()}</time><div>{comparison.results.map((item)=><span key={item.location.id}>{item.location.name}<strong>{item.destinationScore===null?"—":Math.round(item.destinationScore)}</strong></span>)}</div><small>{t("compare.offline")}</small></article>)}</div></section>}
