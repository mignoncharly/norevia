import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { Locale } from "@norevia/shared-types";
import { PwaInstallPrompt } from "@/components/PwaInstallPrompt";
import { usePreferences } from "@/stores/usePreferences";

const nav = ["overview", "profile", "priorities", "compare", "methodology", "saved"] as const;
const paths = { overview: "/", profile: "/profile", priorities: "/priorities", compare: "/compare", methodology: "/methodology", saved: "/saved" };

export function AppShell() {
  const { t } = useTranslation();
  const { locale, setLocale, theme, toggleTheme } = usePreferences();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => setMenuOpen(false), [location.pathname]);
  useEffect(() => {
    if (!menuOpen) return;
    const previousOverflow = document.body.style.overflow;
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") setMenuOpen(false); };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [menuOpen]);

  return <div className="site-shell">
    {menuOpen && <button className="menu-scrim" type="button" aria-label={t("mobile.closeMenu")} onClick={() => setMenuOpen(false)} />}
    <header className="topbar">
      <NavLink to="/" className="brand" aria-label={t("app.name")}><span className="brand-mark">N</span><span>Norevia</span></NavLink>
      <nav id="main-navigation" className="main-nav" data-open={menuOpen} aria-label={t("mobile.navigation")}>
        {nav.map((item) => <NavLink key={item} to={paths[item]} onClick={() => setMenuOpen(false)}>{t(`nav.${item}`)}</NavLink>)}
      </nav>
      <div className="toolbar">
        <label className="sr-only" htmlFor="locale">{t("language.label")}</label>
        <select id="locale" value={locale} onChange={(event) => setLocale(event.target.value as Locale)} aria-label={t("language.label")}><option value="en">EN</option><option value="fr">FR</option><option value="de">DE</option></select>
        <button className="icon-button" type="button" onClick={toggleTheme} title={t(`theme.${theme === "light" ? "dark" : "light"}`)} aria-label={t(`theme.${theme === "light" ? "dark" : "light"}`)}><span aria-hidden="true">{theme === "light" ? "\u25D0" : "\u2600"}</span></button>
      </div>
      <button className="menu-toggle" type="button" aria-controls="main-navigation" aria-expanded={menuOpen} aria-label={t(menuOpen ? "mobile.closeMenu" : "mobile.openMenu")} onClick={() => setMenuOpen((open) => !open)}><span /><span /><span /></button>
    </header>
    <main><Outlet /></main>
    <footer><span>{t("footer.disclaimer")}</span><span>{t("footer.version")}</span></footer>
    <PwaInstallPrompt />
  </div>;
}
