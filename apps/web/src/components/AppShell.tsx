import { NavLink, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { Locale } from "@norevia/shared-types";
import { usePreferences } from "@/stores/usePreferences";

const nav=["overview","profile","priorities","compare","methodology","saved"] as const;
const paths={overview:"/",profile:"/profile",priorities:"/priorities",compare:"/compare",methodology:"/methodology",saved:"/saved"};
export function AppShell(){
  const {t}=useTranslation(); const {locale,setLocale,theme,toggleTheme}=usePreferences();
  return <div className="site-shell"><header className="topbar"><NavLink to="/" className="brand" aria-label={t("app.name")}><span className="brand-mark">N</span><span>Norevia</span></NavLink><nav className="main-nav" aria-label={t("app.name")}>{nav.map((item)=><NavLink key={item} to={paths[item]}>{t(`nav.${item}`)}</NavLink>)}</nav><div className="toolbar"><label className="sr-only" htmlFor="locale">{t("language.label")}</label><select id="locale" value={locale} onChange={(event)=>setLocale(event.target.value as Locale)}><option value="en">EN</option><option value="fr">FR</option><option value="de">DE</option></select><button className="icon-button" onClick={toggleTheme} title={t(`theme.${theme==="light"?"dark":"light"}`)}>{theme==="light"?"◐":"☀"}</button></div></header><main><Outlet/></main><footer><span>{t("footer.disclaimer")}</span><span>{t("footer.version")}</span></footer></div>;
}
