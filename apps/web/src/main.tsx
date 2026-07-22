import { StrictMode, useEffect } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { registerSW } from "virtual:pwa-register";
import { useTranslation } from "react-i18next";
import "./i18n";
import "./styles.css";
import { App } from "./app/App";
import { usePreferences } from "./stores/usePreferences";

registerSW({ immediate:true });
const queryClient=new QueryClient({defaultOptions:{queries:{staleTime:300_000,retry:1}}});
function Bootstrap(){
  const {i18n}=useTranslation(); const locale=usePreferences((state)=>state.locale); const theme=usePreferences((state)=>state.theme);
  useEffect(()=>{void i18n.changeLanguage(locale);document.documentElement.lang=locale;},[i18n,locale]);
  useEffect(()=>{document.documentElement.dataset.theme=theme;},[theme]);
  return <App/>;
}
createRoot(document.getElementById("root")!).render(<StrictMode><QueryClientProvider client={queryClient}><BrowserRouter><Bootstrap/></BrowserRouter></QueryClientProvider></StrictMode>);
