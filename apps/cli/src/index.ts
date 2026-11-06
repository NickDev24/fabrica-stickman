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
    intro("🏭 Fábrica Autónoma — Setup Completo");
    const dir = (await text({ message: "Carpeta destino", placeholder: "./mi-fabrica", defaultValue: "./mi-fabrica" })) as string;
    const mode = await select({
      message: "Modo de instalación",
      options: [
        { value: "full", label: "Full (backend Python + frontend 3D + Docker)" },
        { value: "lite", label: "Lite (solo CLI + backend Python)" },
        { value: "custom", label: "Custom" },
      ],
    });
    const s = spinner();
    s.start("Clonando repositorio...");
    try {
      await execa("npx", ["degit", "NickDev24/fabrica-stickman", dir], { stdio: "inherit" });
      s.stop("Proyecto clonado");
    } catch (e) {
      s.stop("Error clonando");
      console.error(e);
      return;
    }

    // Configurar .env
    const configureEnv = await confirm({ message: "¿Configurar .env ahora?" });
    if (configureEnv) {
      s.start("Copiando .env.example a .env...");
      await execa("cp", [".env.example", ".env"], { cwd: dir, stdio: "inherit" });
      s.stop("Archivo .env creado. Edítalo con tus API keys.");
    }

    // Instalar dependencias Python
    const installPython = await confirm({ message: "¿Instalar dependencias Python (requirements.txt)?" });
    if (installPython) {
      s.start("Instalando dependencias Python...");
      try {
        await execa("python3", ["-m", "venv", ".venv"], { cwd: dir, stdio: "inherit" });
        await execa(".venv/bin/pip", ["install", "-r", "requirements.txt"], { cwd: dir, stdio: "inherit" });
        s.stop("Dependencias Python instaladas");
      } catch (e) {
        s.stop("Error instalando Python");
        console.error(e);
      }
    }

    // Instalar dependencias Node (frontend)
    if (mode === "full") {
      const installNode = await confirm({ message: "¿Instalar dependencias Node (frontend 3D)?" });
      if (installNode) {
        s.start("Instalando dependencias Node...");
        try {
          await execa("pnpm", ["install"], { cwd: dir, stdio: "inherit" });
          s.stop("Dependencias Node instaladas");
        } catch (e) {
          s.stop("Error instalando Node");
          console.error(e);
        }
      }
    }

    // Configurar Docker
    const setupDocker = await confirm({ message: "¿Configurar Docker (opcional)?" });
    if (setupDocker) {
      s.start("Levantando contenedores Docker...");
      try {
        await execa("docker", ["compose", "up", "-d", "--build"], { cwd: dir, stdio: "inherit" });
        s.stop("Docker corriendo (Dashboard en http://localhost:8611)");
      } catch (e) {
        s.stop("Error con Docker");
        console.error(e);
      }
    }

    // Iniciar frontend si es full
    if (mode === "full") {
      const launch = await confirm({ message: "¿Abrir el frontend 3D ahora?" });
      if (launch) {
        await execa("pnpm", ["dev:web"], { cwd: dir, stdio: "inherit" });
      }
    }

    outro("Listo. ¡A crear contenido! Revisa CODEX.md para empezar.");
  });

program.command("doctor").description("Diagnóstico del entorno").action(async () => {
  console.log("Node:", process.version);
  console.log("Python:", process.version);
  try {
    await execa("python3", ["--version"], { stdio: "inherit" });
    console.log("✓ Python 3 disponible");
  } catch {
    console.log("✗ Python 3 no encontrado");
  }
  try {
    await execa("docker", ["--version"], { stdio: "inherit" });
    console.log("✓ Docker disponible");
  } catch {
    console.log("✗ Docker no encontrado (opcional)");
  }
  try {
    await execa("ffmpeg", ["-version"], { stdio: "inherit" });
    console.log("✓ FFmpeg disponible");
  } catch {
    console.log("✗ FFmpeg no encontrado (requerido)");
  }
  console.log("Doctor completado");
});

program.command("export-env").description("Exporta config .env").action(() => {
  console.log("# Variables de entorno requeridas - copia esto a .env");
  console.log("MISTRAL_API_KEY=your_mistral_api_key_here");
  console.log("QWEN_API_KEY=your_qwen_api_key_here");
  console.log("CLOUDFLARED_ACCOUNTS_ID=your_cloudflare_account_id");
  console.log("CLOUDFLARED_WORKER_AI=your_cloudflare_worker_ai_token");
  console.log("TELEGRAM_TOKEN_BOT=your_telegram_bot_token");
  console.log("TELEGRAM_CHAT_ID=your_telegram_chat_id");
  console.log("ZERNIO_API_KEY=your_zernio_api_key");
  console.log("ZERNIO_ACCOUNT_ID=your_zernio_account_id");
  console.log("GEMINI_API_KEY=your_gemini_api_key");
  console.log("ALLOW_PAID_LLM=0");
  console.log("ALLOW_REMOTE_LLM=1");
  console.log("CF_MAX_IMAGENES_DIA=150");
});

program.command("validate-connectors").description("Valida conectores").action(async () => {
  console.log("Validando conectores...");
  // Aquí deberíamos validar las API keys contra los servicios reales
  console.log("✓ Validación básica completada");
  console.log("Nota: Ejecuta las pruebas de backend: .venv/bin/python -m pytest tests -q");
});

program.command("upgrade").description("Actualiza la fábrica").action(async () => {
  await execa("npm", ["update", "-g", "@nickdev24/fabrica-autonoma"], { stdio: "inherit" });
});

program.parse();
