import * as i18n from "i18next";
import { initReactI18next } from "react-i18next";

const resources = {
  es: {
    translation: {
      title: "Fábrica Autónoma — Oficina 2D",
      help: "Usa flechas para moverte. Pulsa E cerca de un agente para hablar.",
      paste: "Pegar API Key",
      skip: "Saltar por ahora",
      test: "Probar conexión",
      next: "Siguiente",
      explain: "Explícame como si tuviera 10 años",
      export: "Exportar config .env",
      progress: "Progreso",
      saved: "Guardado cifrado (Web Crypto) + localStorage",
      how: "¿Cómo obtengo esto?",
      language: "Idioma",
      panel: "Panel",
      close: "Cerrar",
      provider: "Proveedor",
      apiKey: "API Key",
      save: "Guardar",
      circular: {
        title: "Mesa redonda — ganador de la semana",
        subtitle: "El contenido más compartido del mes",
        toggle: "Ver mesa redonda",
        button: "Abrir mesa redonda",
      },
    },
  },
  en: {
    translation: {
      title: "Autonomous Factory — 2D Office",
      help: "Use arrow keys to move. Press E near an agent to talk.",
      paste: "Paste API Key",
      skip: "Skip for now",
      test: "Test connection",
      next: "Next",
      explain: "Explain like I'm 10",
      export: "Export config .env",
      progress: "Progress",
      saved: "Saved encrypted (Web Crypto) + localStorage",
      how: "How do I get this?",
      language: "Language",
      panel: "Panel",
      close: "Close",
      provider: "Provider",
      apiKey: "API Key",
      save: "Save",
      circular: {
        title: "Round table — this week's winner",
        subtitle: "The most shared content of the month",
        toggle: "Open round table",
        button: "Open round table",
      },
    },
  },
} as const;

export async function initI18n() {
  await i18n.use(initReactI18next).init({
    resources,
    lng: "es",
    fallbackLng: "es",
    interpolation: { escapeValue: false },
  });
  return i18n;
}

export default i18n;
