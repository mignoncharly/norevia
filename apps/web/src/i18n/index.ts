import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./en/translation.json";
import enIndicators from "./en/indicators.json";
import fr from "./fr/translation.json";
import frIndicators from "./fr/indicators.json";
import de from "./de/translation.json";
import deIndicators from "./de/indicators.json";

void i18n.use(initReactI18next).init({
  resources:{
    en:{translation:{...en,indicators:enIndicators}},
    fr:{translation:{...fr,indicators:frIndicators}},
    de:{translation:{...de,indicators:deIndicators}},
  },
  lng:"en",fallbackLng:"en",supportedLngs:["en","fr","de"],
  interpolation:{escapeValue:false},
});
export default i18n;
