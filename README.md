# 🏭 Fábrica Autónoma

[![CI](https://github.com/NickDev24/fabrica-stickman/actions/workflows/ci.yml/badge.svg)](https://github.com/NickDev24/fabrica-stickman/actions)
[![npm](https://img.shields.io/npm/v/@nickdev24/fabrica-autonoma)](https://www.npmjs.com/package/@nickdev24/fabrica-autonoma)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Una **fábrica autónoma de contenido** (videos stickman + cómics) con una **oficina 3D isométrica interactiva** donde los agentes autónomos gestionan la producción en tiempo real.

El frontend es una **oficina 3D completamente interactiva y animada**: cámara isométrica, agentes 3D que se mueven **según su tarea real en curso**, pantalla ganadora de la semana, y un panel de métricas en 3D. Todo con identidad visual propia (tinta negra + acento cálido `#FF5C35`).

## ¿Cómo funciona la oficina 3D?

La oficina no es un dashboard plano: es un espacio vivo donde los agentes se mueven y actúan según lo que está haciendo el pipeline.

- **Cuando el pipeline busca una idea**, 1–3 agentes se sitúan trabajando en internet (`searching` / `selecting`).
- El **ganador** pasa a la pantalla principal (mobile-board) para dibujar.
- La **pizarra de generación de imágenes** muestra las imágenes conforme se van creando, con carrusel automático y manual.
- Cada **configuración** (MCP, nuevo proveedor IA, API, prompt) se comunica con un agente en modo **chat**; al terminar, cada usuario elige su propia cuenta.
- Al finalizar, el usuario **selecciona/cierra su cuenta** en Gemini, Cloudflare, Workers AI, YouTube, Zernio, etc.

| Estado del agente | Animación en 3D | ¿Qué hace el agente? |
|---|---|---|
| `idle` | quieto, rotando suavemente | En espera / bienvenida |
| `searching` / `selecting` | se acerca a la estación de trabajo | Busca idea, compara, elige el ganador |
| `creating` | bobeo suave en la pizarra | Genera imagen en la pantalla principal |
| `done` | placa de bandera / celebración | Guarda la obra y notifica |
| `error` | vibración de error (shake) | Reintenta o informa de error |

## Quick Start

```bash
npx NickDev24/fabrica-autonoma
```

## Architecture

```
apps/web        React 18 + Vite + Three.js / R3F (3D isometric oficina)
packages/agents-core  Motor de diálogo (Nova, Kai, Luna, Zern) en YAML
packages/connectors   OpenAI, Anthropic, Gemini, ElevenLabs, HeyGen, Runway, MCPs, Skills, Zernio
apps/cli          fabrica-autonoma CLI (init / doctor / upgrade / export-env)
docs            VitePress
```

### Stack de la oficina 3D

- **Three.js 0.187 + React Three Fiber + @react-three/drei** (cámara isométrica, OrbitControls, contact shadows, environment)
- **GLTFLoader** carga los modelos 3D desde `assets/oficina3d/` (personajes `office-bomi`/`office-seo` + mobiliario `conference-table-v1`, `office-chair-v1`, `mobile-board-v1`, `pub-print-bench-v1`, `pub-workstation-v1`)
- **Zustand + Context** (FactoryStore) — único estado fuente que mapea la tarea de cada agente al movimiento de su modelo 3D
- **Identidad visual**: Space Grotesk + tinta `#111827`/`#0F172A` + acento cálido `#FF5C35`

### Patrón Chat-agente

| Configuración | Agente que la gestiona | Cuenta final que selecciona |
|---|---|---|
| MCP (filesystem, fetch, playwright, github, memory, sequential-thinking) | **Kai** | — |
| Proveedor IA (OpenAI/Anthropic/Gemini) | **Luna** | Gemini |
| API (ElevenLabs/HeyGen/Runway/Stability) | **Nova** | — |
| Skill / tarea personalizada | **Zern** | Zernio (TikTok/FB/IG/YT) |
| Conector de video/cómic | **Zern** | Zernio |

## Features

| Módulo | Descripción |
|---|---|
| **Oficina 3D isométrica** | Agentes 3D animados por tarea, métricas en 3D, cámara orientable |
| **Agents Core** | 4 agentes autónomos (Nova, Kai, Luna, Zern) con YAML versionado y diálogo |
| **Conectores** | OpenAI, Anthropic, Gemini, ElevenLabs, HeyGen, Runway, MCPs, Skills, Zernio |
| **CLI** | `fabrica-autonoma` publicado (init / doctor / upgrade / export-env / validate-connectors) |
| **Config inicial** | Onboarding conversacional por agente, export `.env`, persistencia cifrada (Web Crypto AES-GCM) |

## Roadmap

Ver `ROADMAP.md`.

## License

MIT

---

# 📖 Documentación para equipo y usuario (en español)

## ¿Qué es esta oficina 3D?

Es el **frontend principal** de la fábrica. En lugar de un tablero plano, hay una **oficina 3D isométrica** donde los agentes simulados (Nova, Kai, Luna, Zern) se mueven y actúan según lo que está haciendo el pipeline.

## ¿Cómo se mueven los agentes?

Cada agente tiene un **estado de tarea** que cambia conforme avanza la fabricación:

| Estado | Animación en 3D | Acción del agente |
|---|---|---|
| `idle` | Rotación suave, quieto | En espera / bienvenida |
| `searching` / `selecting` | Se acerca a la estación de trabajo | Busca idea en internet, compara, elige el ganador |
| `creating` | Bobeo suave en la pizarra | Genera imagen en la pantalla principal |
| `done` | Placa de bandera / celebración | Guarda la obra y notifica |
| `error` | Vibración de error (shake) | Reintenta o informa de error |

## ¿Qué ve el usuario?

- **Fondo:** oficina isométrica con piso, mesa y silla.
- **Piso de métricas:** pantalla ganadora de la semana (video stickman, cómics, agentes activos).
- **Escritorio:** mesa de congreso, silla, escritorio móvil y pizarra de generación de imágenes.
- **Pizarra principal:** muestra las imágenes generadas en un carrusel **automático o manual**.
- **Agentes 3D:** personajes que caminan entre estaciones según su tarea.

## Patrón Chat-Agente

Cada configuración se comunica con un agente en modo conversacional:

| Configuración | Agente | Cuenta final que elige el usuario |
|---|---|---|
| MCP (filesystem, fetch, playwright, github, memory, sequential-thinking) | Kai | — |
| Proveedor IA (OpenAI, Anthropic, Gemini) | Luna | Gemini |
| API (ElevenLabs, HeyGen, Runway, Stability) | Nova | — |
| Skill / tarea personalizada | Zern | Zernio (TikTok, FB, IG, YT) |
| Conector de video/cómic | Zern | Zernio |

## Cuentas finales

Al terminar la configuración, el usuario **selecciona y cierra su propia cuenta** redirigido a:

- **Gemini**
- **Cloudflare**
- **Workers AI**
- **YouTube**
- **Zernio**
- y demás proveedores disponibles.

## Qué hace falta para verlo

1. Tener el repositorio clonado.
2. Ejecutar `pnpm install` en la raíz.
3. Ejecutar `pnpm dev` (frontend en `localhost:5173`).

## Qué hace falta para publicarlo

- `pnpm build` para generar la versión de producción en `apps/web/dist`.
- Subir `apps/web/dist` a cualquier hosting estático o a Cloudflare Pages.

## Estado del proyecto

- ✅ Frontend 3D listo y compilando.
- ✅ Agents Core con diálogo.
- ✅ Conectores (OpenAI, Anthropic, Gemini, ElevenLabs, HeyGen, Runway, MCPs, Skills, Zernio).
- ✅ CLI públicable (`fabrica-autonoma`).
- 📘 Documentación en `docs/` (VitePress).
