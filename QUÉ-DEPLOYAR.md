# QUÉ SE DEPLOYARÁ EN GITHUB — fabrica-stickman
Objetivo: repo público `NickDev24/fabrica-stickman`. Un usuario sin conocimiento técnico ejecuta `npx NickDev24/fabrica-autonoma` y obtiene su propia fábrica autónoma de contenido con oficina 2D/3D interactiva.

## Producto final (solo esto va al repo)
1. Frontend 2D "oficina de agentes" (React 18 + Phaser 3 + Vite + Tailwind + Zustand + i18next):
   - Escena con mapa 1600x1100, cámara con scroll limitado, cursor custom, día/noche, partículas.
   - 4 agentes stickman autónomos con idle/talk/walk/celebrate/error:
     - Nova (Onboarding), Kai (APIs & MCPs), Luna (Skills & Plugins), Zern (Conectores sociales Zernio → TikTok/FB/IG/YT).
   - Sistema de diálogo cableado a `packages/agents-core` (pasos, ramas, validación), botones grandes, modo "explicame como si tuviera 10 años".
   - Panel lateral: progreso, credenciales enmascaradas, exportar `.env`.
   - Persistencia cifrada (Web Crypto AES-GCM) + localStorage, i18n ES/EN, a11y teclado/ARIA.
   - Showcase 3D opcional tipo Fénix (referencia, no copia): tres modelos GLB CC0 + muebles, con latido "curso/ok/error" y globos de estado.
2. CLI publicable `npx NickDev24/fabrica-autonoma` (Node 20+, Commander + @clack/prompts + degit + execa):
   - `fabrica init` (Full/Lite/Custom, detecta SO/Node/pnpm, ofrece abrir oficina 2D), `doctor`, `upgrade`, `export-env`, `validate-connectors`.
3. Agents Core (`packages/agents-core`): motor de diálogo (XState o custom), agentes en YAML versionado (Nova/Kai/Luna/Zern), API start/next/validate/onError/onComplete, tests ≥85%.
4. Conectores (`packages/connectors`):
   - API keys: OpenAI, Anthropic, Gemini, ElevenLabs, HeyGen, Runway, Stability (Zod + probe real + doc link).
   - MCP: detecta instalados, sugiere populares, custom JSON.
   - Skills: escanea `~/.claude/skills`, `~/.config/skills`, `npx skills add`.
   - Zernio: OAuth local en `:4321` (Hono) con PKCE, scopes TikTok/FB/IG/YT, keytar, post-connect validation (avatar/handle) o mock+TODO.
   - Config exporter: `.env` + `fabrica.config.json` sin filtrar secretos.
5. Docs VitePress (12+ páginas), README estrella-ready (hero SVG animado, badges custom, GIF real, Quick Start 3 líneas), CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CODEOWNERS, plantillas issue/PR, examples/.
6. Videos (F7): tutorial 5-10min, 3 spots 30s, promo repo <30s, intro 10s; comprimidos en `assets/videos/` (LFS) o `docs/BLOCKERS.md` con guion si falla.
7. CI/CD GitHub Actions: ci, release (npm publish on tag), docs (GitHub Pages), e2e (Playwright), codeql, gitleaks. CHANGELOG, RELEASE_NOTES v0.1.0, LAUNCH_KIT.md.

## NO va al repo (queda local/producción)
- Pulso Curioso (docker-compose, dashboard, factory :8610/:8611, projects, state, models, assets documentales, vibe_images, avatar_*, .venv, .env, *.onnx).
- Fénix en `barto:/el-cazador/fenix` (código y assets 3D con licencia de uso interno; solo referencia de diseño, no copia).
- Secrets, node_modules, caches, backups (.bak), dumps, zips.

## Flujo de publicación
- pnpm workspaces + Turborepo/tsup, ESLint flat + Prettier + Husky + lint-staged, Vitest + Playwright, Conventional Commits + changesets.
- Push a `NickDev24/fabrica-stickman` tras PARADA 2 (npm pack) y PARADA 3 (git status/log).

## Checkpoint actual
Scaffold inicial subido y confirmado como `NickDev24`. Siguiente: F2a (oficina 2D premium + showcase 3D opcional), con tu OK.
