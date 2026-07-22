import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

type MobilePlatform = "android" | "ios";
type InstallChoice = { outcome: "accepted" | "dismissed"; platform: string };
type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<InstallChoice>;
};

const dismissKey = "norevia-pwa-install-dismissed";
const dismissDuration = 7 * 24 * 60 * 60 * 1000;

export function detectMobilePlatform(userAgent: string, platform: string, maxTouchPoints: number): MobilePlatform | null {
  if (/android/i.test(userAgent)) return "android";
  if (/iphone|ipad|ipod/i.test(userAgent) || (platform === "MacIntel" && maxTouchPoints > 1)) return "ios";
  return null;
}

function isStandalone(): boolean {
  const iosNavigator = navigator as Navigator & { standalone?: boolean };
  return window.matchMedia("(display-mode: standalone)").matches || iosNavigator.standalone === true;
}

function wasRecentlyDismissed(): boolean {
  try {
    const dismissedAt = Number(window.localStorage.getItem(dismissKey));
    return Number.isFinite(dismissedAt) && dismissedAt > 0 && Date.now() - dismissedAt < dismissDuration;
  } catch {
    return false;
  }
}

function rememberDismissal(): void {
  try {
    window.localStorage.setItem(dismissKey, String(Date.now()));
  } catch {
    // Storage can be unavailable in private browsing; dismissal still applies to this render.
  }
}

export function PwaInstallPrompt() {
  const { t } = useTranslation();
  const platform = useMemo(
    () => detectMobilePlatform(navigator.userAgent, navigator.platform, navigator.maxTouchPoints),
    [],
  );
  const [installEvent, setInstallEvent] = useState<BeforeInstallPromptEvent | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!platform || isStandalone() || wasRecentlyDismissed()) return;
    setVisible(true);
    const handleBeforeInstall = (event: Event) => {
      event.preventDefault();
      setInstallEvent(event as BeforeInstallPromptEvent);
      setVisible(true);
    };
    const handleInstalled = () => {
      setVisible(false);
      setInstallEvent(null);
    };
    window.addEventListener("beforeinstallprompt", handleBeforeInstall);
    window.addEventListener("appinstalled", handleInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstall);
      window.removeEventListener("appinstalled", handleInstalled);
    };
  }, [platform]);

  if (!visible || !platform) return null;

  const dismiss = () => {
    rememberDismissal();
    setVisible(false);
  };
  const install = async () => {
    if (!installEvent) return;
    await installEvent.prompt();
    const choice = await installEvent.userChoice;
    setInstallEvent(null);
    if (choice.outcome === "accepted") setVisible(false);
    else dismiss();
  };
  const canInstallDirectly = platform === "android" && installEvent !== null;

  return <aside className="pwa-install-prompt" role="dialog" aria-modal="false" aria-labelledby="pwa-install-title">
    <button className="pwa-install-close" type="button" aria-label={t("pwa.close")} onClick={dismiss}>×</button>
    <div className="pwa-install-icon" aria-hidden="true">N</div>
    <div className="pwa-install-copy">
      <p className="eyebrow">{t(`pwa.${platform}.eyebrow`)}</p>
      <h2 id="pwa-install-title">{t("pwa.title")}</h2>
      <p>{t(`pwa.${platform}.description`)}</p>
      {!canInstallDirectly && <p className="pwa-install-steps">{t(`pwa.${platform}.instructions`)}</p>}
      <div className="pwa-install-actions">
        {canInstallDirectly
          ? <button className="button primary" type="button" onClick={() => void install()}>{t("actions.install")}</button>
          : <button className="button primary" type="button" onClick={dismiss}>{t("pwa.gotIt")}</button>}
        <button className="button secondary" type="button" onClick={dismiss}>{t("pwa.notNow")}</button>
      </div>
    </div>
  </aside>;
}
