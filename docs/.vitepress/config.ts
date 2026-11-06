import { defineConfig } from "vitepress";
export default defineConfig({
  title: "Fábrica Autónoma",
  description: "Tu fábrica autónoma de contenido con oficina 2D",
  themeConfig: {
    nav: [{ text: "Guía", link: "/guide/install" }],
    sidebar: [{ text: "Guía", items: [
      { text: "Instalación", link: "/guide/install" },
      { text: "Onboarding", link: "/guide/onboarding" },
      { text: "Conectores", link: "/guide/connectors" },
      { text: "CLI", link: "/guide/cli" },
    ]}],
  },
});
