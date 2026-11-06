#!/usr/bin/env node
import { Command } from "commander";
import { intro, outro, select, text, confirm, spinner } from "@clack/prompts";
import { execa } from "execa";

const program = new Command();
program.name("fabrica").description("Scaffold your autonomous content factory.").version("0.1.0");

program
  .command("init")
  .description("Initialize a new factory project")
  .action(async () => {
    intro("🏭 Fábrica Autónoma — Setup");
    const dir = (await text({ message: "Carpeta destino", placeholder: "./mi-fabrica", defaultValue: "./mi-fabrica" })) as string;
    const mode = await select({
      message: "Modo de instalación",
      options: [
        { value: "full", label: "Full (frontend + conectores + docs)" },
        { value: "lite", label: "Lite (solo CLI)" },
        { value: "custom", label: "Custom" },
      ],
    });
    const s = spinner();
    s.start("Scaffoldeando proyecto...");
    try {
      await execa("npx", ["degit", "NickDev24/fabrica-stickman", dir], { stdio: "inherit" });
      s.stop("Proyecto creado");
    } catch (e) {
      s.stop("Error scaffoldeando");
      console.error(e);
    }
    const install = await confirm({ message: "¿Instalar dependencias ahora?" });
    if (install) {
      await execa("pnpm", ["install"], { cwd: dir, stdio: "inherit" });
    }
    const launch = await confirm({ message: "¿Abrir la oficina 2D ahora?" });
    if (launch) {
      await execa("pnpm", ["dev:web"], { cwd: dir, stdio: "inherit" });
    }
    outro("Listo. ¡A crear contenido!");
  });

program.command("doctor").description("Diagnóstico del entorno").action(async () => {
  console.log("Node:", process.version);
  console.log("OK");
});

program.parse();
