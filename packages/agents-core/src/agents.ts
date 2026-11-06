import type { Agent } from "./types";

export const nova: Agent = {
  id: "nova",
  name: "Nova",
  role: "Onboarding",
  avatar: "nova",
  steps: [
    { id: "welcome", type: "info", agent: "nova", title: "¡Bienvenido a tu Fábrica!", body: "Soy Nova. Te guiaré para montar tu fábrica autónoma de contenido en minutos.", next: "what-is" },
    { id: "what-is", type: "info", agent: "nova", title: "¿Qué es la fábrica?", body: "Genera videos stickman y cómics automáticamente y los publica en YouTube, TikTok, Facebook e Instagram.", next: "ready" },
    { id: "ready", type: "action", agent: "nova", title: "¿Listo para empezar?", body: "Configuraremos APIs, MCPs, skills y conectores sociales.", next: "done", branches: { yes: "done", no: "welcome" } },
    { id: "done", type: "complete", agent: "nova", title: "¡Onboarding completo!", body: "Pasemos con Kai para las APIs." },
  ],
};

export const kai: Agent = {
  id: "kai",
  name: "Kai",
  role: "APIs & MCPs",
  avatar: "kai",
  steps: [
    { id: "intro", type: "info", agent: "kai", title: "APIs y MCPs", body: "Voy a ayudarte a pegar tus API keys de forma segura. Nunca salen de tu máquina.", next: "pick" },
    { id: "pick", type: "select", agent: "kai", title: "Elige un proveedor", body: "Selecciona el servicio que quieres configurar.", inputKey: "provider", options: ["OpenAI", "Anthropic", "Gemini", "ElevenLabs", "HeyGen", "Runway"], next: "key" },
    { id: "key", type: "input", agent: "kai", title: "Pega tu API Key", body: "Pégala aquí. Se guarda cifrada en tu navegador.", inputKey: "apiKey", inputType: "secret", validate: "secret", helpUrl: "https://platform.openai.com/api-keys", explainLike10: "Es como la contraseña de tu robot para hablar con la IA.", next: "test" },
    { id: "test", type: "action", agent: "kai", title: "Probar conexión", body: "Vamos a verificar que la key funcione.", next: "done" },
    { id: "done", type: "complete", agent: "kai", title: "Proveedor configurado", body: "Puedes agregar más o continuar." },
  ],
};

export const luna: Agent = {
  id: "luna",
  name: "Luna",
  role: "Skills & Plugins",
  avatar: "luna",
  steps: [
    { id: "intro", type: "info", agent: "luna", title: "Skills y Plugins", body: "Instala skills para ampliar las capacidades de la fábrica.", next: "scan" },
    { id: "scan", type: "action", agent: "luna", title: "Escanear skills instaladas", body: "Buscamos en ~/.claude/skills y ~/.config/skills.", next: "install" },
    { id: "install", type: "input", agent: "luna", title: "Instalar skill desde GitHub", body: "Pega un repo (ej. gmpetrov/agent-screenplay).", inputKey: "skillRepo", inputType: "text", next: "done" },
    { id: "done", type: "complete", agent: "luna", title: "Listo", body: "Skills actualizadas." },
  ],
};

export const zern: Agent = {
  id: "zern",
  name: "Zern",
  role: "Conectores sociales",
  avatar: "zern",
  steps: [
    { id: "intro", type: "info", agent: "zern", title: "Conectores sociales vía Zernio", body: "Vincula TikTok, Facebook, Instagram y YouTube para publicar automáticamente.", next: "pick" },
    { id: "pick", type: "select", agent: "zern", title: "Elige plataforma", body: "Selecciona la red social.", inputKey: "platform", options: ["TikTok", "Facebook", "Instagram", "YouTube"], next: "oauth" },
    { id: "oauth", type: "action", agent: "zern", title: "Autorizar con OAuth", body: "Se abrirá tu navegador para autorizar. Redirect: http://localhost:4321/callback", next: "verify" },
    { id: "verify", type: "action", agent: "zern", title: "Verificar cuenta", body: "Mostramos avatar y nombre de la cuenta vinculada.", next: "done" },
    { id: "done", type: "complete", agent: "zern", title: "Conectado", body: "Plataforma vinculada con éxito." },
  ],
};

export const agents = { nova, kai, luna, zern };
export const agentList = [nova, kai, luna, zern];
