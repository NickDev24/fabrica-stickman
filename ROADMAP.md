# ROADMAP

## Ruta de producción vigente (2026-11-04)

La ruta objetivo de producción de esta fábrica es **keyframe 2.5D**, según `CODEX.md`:
imágenes generadas por beat, movimiento de cámara con FFmpeg y audio/subtítulos compuestos al
final. La ruta `avatar` con Three.js/SwiftShader descrita abajo en la FASE 0 es una línea
experimental/legacy independiente; sus mediciones no validan la calidad ni los tiempos de
keyframes. No usar la decisión histórica de “seguir con la animación en vivo” como criterio
para cambiar la ruta de producción sin una decisión explícita del dueño del canal.

El pipeline todavía no es una fábrica autónoma de publicación: `pipeline.run auto` ejecuta
investigación, guion, render y derivados en secuencia, pero la placa keyframe no tiene un gate
de aprobación efectivo y las credenciales/plataformas de publicación siguen pendientes. No
prometer publicación desatendida ni ingresos garantizados hasta cerrar esos puntos y medir
episodios reales. Una meta de ingresos a tres meses es un objetivo comercial, no un resultado
que el software pueda garantizar.

Lo que **no** se implementa en esta fase, una línea por ítem. Nada de esto tiene código ni
archivos vacíos a propósito.

## Bloqueantes del avatar

- **GLB real del "cloak man"** → el avatar que se renderiza hoy (`assets/characters/cloakman.glb`)
  lo generamos nosotros con `tools/make_character_glb.py`; el archivo del usuario sigue sin existir
  en ninguna parte de la máquina (`find ~ -iname '*.glb'` = 0). Cuando llegue, entra por `--glb` o
  por el glob `assets/**/*.glb` sin tocar código.
- **glTF-Transform sobre el GLB real** → optimizar polycount/texturas sin romper esqueleto ni morph
  targets, y cachear el resultado. Se corre el día que exista el archivo.
- **`rig_map` del cloak man real** → el procedural ya tiene su mapa por nodos
  (`state/personajes/rig_cloakman.json`); falta mapear los parámetros del actor a los nombres
  reales de morph targets y huesos del GLB del usuario (el motor ya lee ambas formas de sidecar).
- **Material 2.5D ya disponible**: `avatar_4f/contact_p1.png` y `contact_p2.png` son la plancha de
  identidad del canal (50 poses/expresiones etiquetadas: Aburrimiento, Confusión Profunda, Dolor,
  Inspiración, Sarcasmo, Happy, Sad, gestos de mano y vistas de cuerpo). Si el GLB nunca llega, esa
  plancha es la fuente directa del fallback por sprites de `VIABILIDAD.md` — no hay que generarla.

## Motor de IA

- Motor multiproveedor (Mistral / Qwen / AionLabs / Bedrock / Cloudflare) con healthcheck, rutas por
  tarea y caché en disco **ya existe** en `pipeline/llm.py`; lo que falta es balanceo por costo real
  y métricas de latencia por proveedor.
- Motor editorial multinicho (un mismo guion, distintos ángulos por nicho).
- **Presupuesto de tokens por mensaje** — `PRESUPUESTO_USD_MSJ` existe en el perfil de hardware pero
  hoy está en 0 (sin límite): falta el control de gasto real por corrida.
- **Reintento con backoff** ya está (patrón tomado de Stickman-Studio, sin su SDK): `pipeline/llm.py:_post`
  reintenta 429/5xx/cortes de red en el mismo proveedor con `Retry-After`, y nunca reintenta
  401/403/400. Lo que sigue pendiente es reintentos a nivel de *tarea* (reencolar el paso, no la llamada).

## Skills restantes (17 de 23)

- `viral-story-researcher`, `documentary-investigator`, `storyboard-architect`,
  `retention-scriptwriter`, `emotional-story-director`, `series-universe-builder` — investigación y
  guion: hoy el pipeline los hace con prompts fijos, sin contrato de salida verificado.
- `sound-design-engineer`, `audio-quality-inspector` — cama musical sintetizada existe en
  `pipeline/stages/short.py`; falta mezcla con ducking y QC de loudness medido.
- `cinematic-video-editor`, `render-optimization-engineer`, `visual-quality-inspector` — edición y
  optimización de render (ver decisión de FASE 0 sobre resolución/overdraw).
- `thumbnail-art-director`, `youtube-growth-analyst`, `facebook-content-strategist`,
  `community-manager-ai`, `monetization-policy-reviewer`, `copyright-compliance-reviewer` —
  distribución y cumplimiento.
- `phoneme-lipsync-engineer` y las otras 5 críticas sí se implementan ahora.

## Lip-sync fino

- **whisper.cpp** (modelo tiny/base quantizado) — la medición real ya existe
  (`factory/acting/lipsync.py:medir_alineacion`, reportada en `render_avatar.json`): con el
  modelo acústico en-US de Rhubarb sobre español da **96 % de cubrimiento** de la voz (25,16 s
  habladas, 182 cues, 7,2 cues/s) en la pieza de aceptación, y 95,5 % con 33 cues en silencio en
  los 58 s de `pulso-001`. Con ese número, whisper.cpp queda como mejora de precisión fonémica,
  no como necesidad.

## Credenciales y servicios (PENDIENTES, no bloquean el render)

- **LLM de partitura emocional** — `aionlabs` responde vacío, `mistral` en rate-limit 429 y
  `qwen` 403 (cuota gratuita agotada). La fábrica no se cae: usa el arco determinista de
  `director._partitura_determinista` y lo declara (`timeline.partitura = "determinista"`).
  Falta una clave con cuota para la dirección por IA.
- **Zernio / Telegram** — sin API key en el entorno; publicación y avisos quedan en dry-run.

## Continuidad del personaje

- **Identidad en conflicto**: `state/personajes/principal.json` describe a **4F** (capucha
  negra, tiras magenta/cian, glow verde) y apunta a `assets/4F/pulso-4f.glb`, que no existe;
  el brief pide el avatar **"cloak man"** (victoriano, capa). Hay que decidir cuál de los dos
  es el personaje del canal y registrar un solo perfil.
- **Paleta del perfil no aplicada al render** — el renderer usa un fondo fijo `0x10151d` y
  luces neutras; el `paleta` del perfil (key/rim/ambient) todavía no se lee en
  `factory/render/actor_page.html`.

## Publicación y control

- Publicación automática a YouTube / Facebook (hoy `publicacion.py` solo notifica por Telegram).
- Bot de Telegram como centro de control del pipeline.
- Dashboard de episodes, colas y métricas de render.
