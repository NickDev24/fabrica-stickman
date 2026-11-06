# 🏭 Fábrica Autónoma de Contenido

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Fábrica autónoma de contenido** (videos stickman + cómics) con una **oficina 3D isométrica interactiva** donde los agentes autónomos gestionan la producción en tiempo real.

**Este es el backend completo de la fábrica original (Documentales-Generator) + un frontend 3D nuevo + CLI de instalación.**

## 🎯 Qué es

Una fábrica de contenido autónoma que genera:
- **Videos documentales stickman** animados con motion blur, cámara cinemática, audio normalizado a -14 LUFS
- **Cómics** con grillas de 3 bandas, cliffhangers y continuidad visual
- **Publicación automática** a YouTube y Facebook vía Zernio

El backend Python tiene:
- Pipeline completo con LLMs (Mistral, Qwen, Bedrock, Gemini)
- Generación de imágenes con Cloudflare Workers AI (Flux)
- Síntesis de voz con Piper TTS
- Renderizado con FFmpeg
- Skills MCP para agentes especializados
- Docker corriendo 24/7 (puerto 8610 API, 8611 Dashboard)

El frontend 3D (React + Three.js) muestra:
- Oficina isométrica con agentes animados
- Estados reales del pipeline
- Chat contextual con cada agente
- Métricas en tiempo real

## 🚀 Quick Start

```bash
# Instalar con el CLI
npx @nickdev24/fabrica-autonoma init

# O clonar manualmente
git clone https://github.com/NickDev24/fabrica-stickman.git
cd fabrica-stickman

# Configurar variables de entorno
cp .env.example .env
# Edita .env con tus API keys

# Instalar dependencias Python
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Instalar dependencias Node (frontend opcional)
pnpm install

# Levantar Docker (backend + dashboard)
docker compose up -d --build

# Abrir frontend 3D (opcional)
pnpm dev:web
```

## 📁 Arquitectura

```
fabrica-stickman/
├── pipeline/           # Pipeline de producción (guion, imagen, audio, render)
├── factory/           # Motor de la fábrica (orquestador, stages, gates)
├── tools/             # Herramientas de generación (sprites, masks, GLB)
├── docker/            # Docker para factoryd (8610) y dashboard (8611)
├── .agents/skills/    # 26 skills MCP especializados
├── apps/
│   ├── web/          # Frontend 3D (React + Three.js + Vite)
│   └── cli/          # CLI de instalación (@nickdev24/fabrica-autonoma)
├── state/            # Cachés, logs, estado persistente
├── assets/           # Assets de personajes, imagenoteca, oficina 3D
├── tests/            # 170 tests de regresión
├── requirements.txt  # Dependencias Python
├── docker-compose.yml # Orquestación Docker
├── .env.example      # Template de variables de entorno
├── CODEX.md          # Documentación técnica completa
└── README.md         # Este archivo
```

## 🔧 Configuración

Edita `.env` con tus credenciales:

```bash
# LLMs
MISTRAL_API_KEY=your_key
QWEN_API_KEY=your_key
CLOUDFLARED_ACCOUNTS_ID=your_id
CLOUDFLARED_WORKER_AI=your_token

# Publicación
TELEGRAM_TOKEN_BOT=your_token
TELEGRAM_CHAT_ID=your_chat_id
ZERNIO_API_KEY=your_key
ZERNIO_ACCOUNT_ID=your_id

# Gemini (opcional, pago)
GEMINI_API_KEY=your_key
ALLOW_PAID_LLM=0
ALLOW_REMOTE_LLM=1
CF_MAX_IMAGENES_DIA=150
```

## 🏢 Frontend 3D

El frontend se conecta al backend vía API (puerto 8610):

- **Agentes animados**: Nova, Kai, Luna, Zern se mueven según el estado real del pipeline
- **Estados visuales**: idle, searching, creating, done, error
- **Cámara interactiva**: OrbitControls para explorar la oficina
- **Chat contextual**: Conversa con cada agente para configurar el sistema

Accede a: `http://localhost:5173` (desarrollo) o deployment estático.

## 🐳 Docker

```bash
# Iniciar
docker compose up -d --build

# Ver logs
docker compose logs -f

# Detener
docker compose down
```

- **pulso-factory**: API REST + WebSocket en puerto 8610
- **pulso-dashboard**: Mission Control en puerto 8611

## 🧪 Tests

```bash
# Ejecutar tests de backend
.venv/bin/python -m pytest tests -q

# Ver suite completa (170 tests)
.venv/bin/python -m pytest tests -v
```

## 📖 Documentación

- **CODEX.md**: Documentación técnica completa del backend
- **FABRICA-DE-COMICS.md**: Diseño de la extensión de cómics
- **ROADMAP.md**: Estado de desarrollo por fases
- **DEPENDENCIAS.md**: Licencias de dependencias

## � Demos

### Videos Stickman
- [Demo 1: Zombis - Día 1 del contagio](https://youtube.com/watch?v=yyuksUq4CyI) - 8 min 33 s
- Más demos en canal [Pulso Humano Curioso](https://youtube.com/@PulsoHumanoCurioso)

### Cómics
- [Demo: Robo Gardner - 13 Obras](https://github.com/NickDev24/fabrica-stickman/tree/main/projects/robo-gardner-13-obras/comics) - 15 viñetas / 2 páginas
- Formato: Grillas 3 bandas (3/3/3 + 2/2/2), cliffhangers, continuidad visual

## 📚 Tutoriales Profesionales

### Serie de Videos Explicativos
Grabaciones de pantalla profesionales del repositorio, frontend y configuraciones:

1. **Instalación Completa** (15 min)
   - Instalación con CLI npx
   - Configuración de .env
   - Setup de Docker
   - Verificación de dependencias

2. **Frontend 3D** (10 min)
   - Tour de la oficina isométrica
   - Interacción con agentes
   - Chat contextual
   - Conexión con backend API

3. **Backend Python** (20 min)
   - Arquitectura del pipeline
   - Ejecución de episodio completo
   - Gates de QC
   - Publicación automática

4. **Cómics** (8 min)
   - Extensión comics.v2
   - Generación de viñetas
   - Composición de grillas
   - Exportación y QC

5. **Troubleshooting** (12 min)
   - Diagnóstico con CLI doctor
   - Errores comunes
   - Debug de API
   - Logs Docker

*Próximamente: Grabaciones en curso con Screenplay/OBS*

## �🎨 Stack

### Backend
- Python 3.13
- FFmpeg, Tesseract
- aiohttp (REST + WebSocket)
- Cloudflare Workers AI (Flux)
- Piper TTS
- Skills MCP

### Frontend
- React 18
- Three.js 0.187
- React Three Fiber
- Vite
- Zustand
- Tailwind CSS

## 📝 CLI

```bash
npx @nickdev24/fabrica-autonoma init    # Inicializar fábrica
npx @nickdev24/fabrica-autonoma doctor  # Diagnóstico de entorno
npx @nickdev24/fabrica-autonoma upgrade # Actualizar
```

## 🤝 Contribuyendo

Este proyecto es una fábrica completa. Para contribuir:

1. Lee CODEX.md primero
2. Ejecuta los tests antes de cambios
3. No rompas el backend por el frontend
4. Documenta cambios en DEPENDENCIAS.md

## 📄 Licencia

MIT

---

**Nota importante**: Este repositorio contiene el backend Python completo de la fábrica original. NO es una reimplementación ni un mock. El frontend 3D es una capa visual nueva sobre el backend existente.
