# BRIEF DE TRABAJO — CÓDEX (fábrica de contenido premium)

Abrí Codex CLI en otra terminal sobre este repo (`/home/facu/Documentos/Documentales-Generator`) y puse a trabajar al modelo en el **perfeccionamiento y terminación de la fábrica**. Este archivo es el punto de partida: le ahorrá leer todo el código, que está en los `.md`.

Regla de uso: **leer primero este archivo y `ROADMAP.md`**. No releer el código fuente completo para "tomar contexto": el contexto vive acá.

---

## 1. Misión

Generar **videos de documentales / historias animadas tipo stickman que compitan con lo que ya es viral**, 100 % gratis, 100 % automáticos, desde una máquina que es una basura. Un guion nuevo entra, un `.mp4` terminado sale por el bot de Telegram.

El producto NO es "un SVG animado ni un muñeco 3D de plástico". El producto es el formato viral real: **30-40 imágenes generadas por minuto, con la cámara moviéndose encima de cada una**, un solo personaje consistente, cortes cada ~1,6 s, una palabra gigante en pantalla, música y SFX por corte, normalizado a −14 LUFS.

## 2. Restricciones duras (no negociables)

| | |
|---|---|
| Hardware | Intel Pentium B950 @ 2,10 GHz, **2 núcleos**, ~11 GiB RAM útil, **disco HDD**, **sin GPU dedicada ni aceleración** |
| Costo | Cero pesos. Sólo capas gratuitas. Sin suscripciones |
| Prohibido | **Blender bajo ninguna circunstancia.** Nada de render 3D por fotograma en esta caja |
| Imágenes del usuario | No subirlas ni copiarlas fuera del repo; **preguntar antes de enviar cualquier imagen a un servicio externo** |
| Dependencias nuevas | Documentar licencia en `DEPENDENCIAS.md` (archivo breve, no comentarios sueltos) |
| Pruebas | **No inventar resultados.** Si algo no corrió, decir "no corrió" |
| Métricas obligatorias de cada render | RAM pico, uso de CPU, tiempo total, peso del archivo, errores encontrados, y el `.mp4` real entregado |
| Destrucción | No borrar repos, modelos, episodios ni configuraciones existentes sin necesidad |
| Bloqueos | Si falta una credencial o un servicio, marcarlo **PENDIENTE** con evidencia y seguir con el resto |

## 3. Lo que YA funciona y está medido (no rehacer)

**Motor visual keyframe** — `pipeline/stages/keyframes.py` + `pipeline/imagen.py` + `state/estilo/personaje.json` + `factory/acting/beats.py`:

- Motor de imagen: **Cloudflare Workers AI** (`@cf/black-forest-labs/flux-1-schnell`), credenciales ya en `.env` (`CLOUDFLARED_ACCOUNTS_ID`, `CLOUDFLARED_WORKER_AI`). Medido: **2,1 s por imagen** (promedio de 6). Alternativas descartadas por medida: dreamshaper-8-lcm 4,4-7,9 s y **no sirve para este personaje**; sdxl 40,2 s.
- Densidad conseguida: **37,7 imágenes/minuto** (18 beats en 28,4 s).
- Personaje **consistente en las 18 tomas** (verificado en la placa de contactos).
- Render de prueba entregado: `projects/avatar-30s/renders/avatar-30s-keyframe.mp4` — 28,4 s, 1280×720@30, **2,9 MB**, **−14,0 LUFS medidos con ebur128**, **47,8 s de render** (con keyframes ya en caché; 2 min 08 s la primera corrida), **RAM pico 295 MB**.
- Hoja de contactos ANTES de renderizar: `projects/<slug>/artifacts/contacto.png` (`--contacto`).
- Suite: **36 tests verdes** (`.venv/bin/python -m pytest tests -q`).

**Cadena de audio** (medida, no teórica):
- Voz: **Piper** `es_ES-carlfm-x_low` (`~/piper-env/bin/piper`), 22,5 s de síntesis para 45 s de audio.
- Piper entrega la voz **clavada en 0 dBFS** (max_volume −0,0 dB). Con esa cresta de 17 dB **no existe ganancia lineal que dé −14 LUFS sin pasar −1,5 dBFS de pico**: loudnorm de una pasada se queda en −15,9. La solución implementada es `alimiter=limit=0.35:level=0` (baja la cresta a 12,6 dB) + **loudnorm en DOS pasadas con `linear=true`**. Resultado medido: −14,0 LUFS.
- Cama musical sintetizada con lavfi (autoría propia, sin licencia ajena) + **un SFX por corte** generado también con lavfi.
- Subtítulos ASS: se valida el `Format:` de 10 campos con `montaje.validar_ass` (un Format corto quema `,0,0,0,,palabra` en pantalla; bug real de `pulso-001-main.mp4`).

**Investigación y texto**:
- Cascada LLM multi-proveedor con reintento de lo transitorio en un solo dueño (`llm._post`); `chat()` sólo conmuta proveedor.
- **Hoy sólo responde Bedrock** (`openai.gpt-oss-120b-1:0`). mistral 429, qwen/DashScope 403 `AllocationQuota.FreeTierOnly`, aionlabs vacío.
- gpt-oss escribe su razonamiento **dentro de `content`** como `<reasoning>…</reasoning>` y si el presupuesto no alcanza, no deja respuesta. Arreglado: `reasoning_effort=low` en el payload + `_sin_razonamiento()` en `llm.py`.
- Scrapling (`parser`) + `curl_cffi` para leer fuentes sin instalar Playwright/Patchright (decisión documentada: 48,5 MB de rueda + ~300 MB de Chromium + 1 GB por pestaña en una caja de 11 GiB).
- `descubrir.py` ahora puntúa **relevancia (raíz de 6 caracteres, desacentuada) × prestigio**: antes cualquier `.gov` le ganaba a una fuente pertinente y un tema de zombis devolvía Medicare y NOAA.

**Lab completo (inventariado, sin GPU en ninguna máquina)**: local B950; VPS `lab` 2c/7 GB; `manager1` y `bart` 2c/7 GB con Intel UHD 600; `debian` 2c/1 GB (GM965); `medios`; `vps-amazon`. **ComfyUI + Wan local no es factible** en ninguna. El catálogo de Workers AI (73 modelos revisados) **no tiene modelos de video**.

**Fábrica 24/7 dockerizada (sesión 2026-11-06, todo operativa y verificada)**:

- **Docker**: `docker compose up -d --build` levanta `pulso-factory` (imagen `python:3.13-slim` + ffmpeg + tesseract, deps del freeze exacto de `.venv`; puerto 8610) y `pulso-dashboard` (`nginx:alpine`). **Puerto ÚNICO del dashboard: 8611** (orden del dueño 2026-11-06 — los alias :8010/:8011 fueron eliminados). Proxy `/api` `/ws` `/img`. Cachés montadas: `state/imagen_cache`, `state/llm_cache`, modelos. El daemon corre **desde el bind-mount del repo** (`docker/factory/factoryd.py`): cambios de código sin rebuild. Branding: **PULSO** (Pulso Curioso) — NO es STECH (proyecto aparte del dueño).
- **factoryd**: daemon 24/7 (aiohttp, REST+WS) que ejecuta `python -m pipeline.run auto --no-publicar` en loop con cooldown y backoff. Control: `POST /api/control` (play/pausa/stop/skip); estado: `/api/estado` con métricas del sistema; eventos en vivo vía `/ws`. Loop verificado funcionando (research + fact-check + descarte honesto de ideas). **Desde 2026-11-06 (orden del dueño): `FACTORY_PUBLISH=1` — publica sola cada día a YouTube (`PulsoHumanoCurioso`) y Facebook (`Pulso Curioso`) vía Zernio; el QC del máster y los gates siguen como cinturón.** Primer episodio AUTO_PUBLISHED de punta a punta: `red-proxy-casa-blanca` (8 min 33 s) → YouTube `watch?v=yyuksUq4CyI` + Facebook reel. Dashboard en **8611 únicamente** (alias :8010/:8011 retirados por orden del dueño).
- **Reciclado de keyframes** (`KF_RECICLADO_CADA`, default 2): imagen nueva cada N beats, reuso de la última imagen válida del mismo escenario; el beat gancho, el cambio de escena y `renovar` fuerzan imagen nueva. Divide a la mitad las llamadas de cuota (objetivo del dueño: 20-30 imágenes por episodio, 24/7 sin pausa).
- **Motor del avatar: Babylon.js 9.33.3** (decisión del dueño, reemplaza a Three.js; UMD vendoreado en `factory/render/vendor/babylon/`; Three.js + página vieja **archivados** en `factory/render/vendor/legacy/`, no borrados). Contrato CDP intacto; A/B en cdp.mjs: paridad de velocidad (mediana ~1,0-1,3 s/frame en SwiftShader), 0 frames negros. El dashboard no usa plantillas SVG (circuito animado en CSS puro).
- **Extensión fábrica de cómics — comics.v2 (RECONSTRUIDA 2026-11-06 por orden del dueño)**: el cómic es un **LIBRO**: mínimo **15 viñetas por capítulo** en **páginas 1080×1620 con grillas reales de 3 bandas** (3/4/3, etc.), gancho flash-forward (cold open), **cliffhanger al cierre de cada página** (el silencio negro no lo pisa: retrocede al penúltimo), silencio tras el golpe, remate, y **humor negro de encuadre entre corchetes** (sin inventar hechos: todo cita LITERALMENTE el guion verificado — `ancla_guion` — con el claim más cercano si hay match). El guion necesita **≥ 13 oraciones** (si no, `SystemExit` honesto; el video sigue). Imágenes flux con variedad real (plano/luz/composición por rotación determinista; el silencio NO quema cuota: panel negro). Texto compuesto FUERA del generador (`componer.py`); footer por página con fuentes; exportación `pages/pag-NN.png` + `chapter_vertical.png` + `carrusel/pag-NN.png` (1 imagen por página) + `manifest.json`; QC v2 bloqueante (`≥15 viñetas`, 3 bandas de 1-4, fuentes en toda página, tamaños del libro). **APAGADA por defecto** (`COMICS_ENABLED=1`); métricas aparte en `state/metricas_comics.jsonl`. Prototipo real aprobado y enviado a Telegram: `projects/robo-gardner-13-obras/comics/` (15 viñetas / 2 páginas, grillas 3/3/3 + 2/2/2, QC aprobado). Camino LLM SMyCB para captions: fase siguiente.
- Suite completa: **170 passed** (5 fallas preexistentes: 4 en `tests/test_subtitles.py` del refactor que quitó subtítulos quemados + 1 en `tests/test_personaje_cara.py` por cambios del motor de imagen — ambos de sesiones previas del dueño/Qodex — NO revertir).

## 4. Contrato del personaje (no tocar a la ligera)

`state/estilo/personaje.json` es el contrato de prompt. Reglas que se probaron empíricamente:

1. El orden es fijo: `IDENTIDAD, ESTILO, escenario, acción, plano, negativos`. Si un beat redacta su prompt a mano, al beat 7 el personaje ya es otro.
2. La identidad es **silueta negra con contorno blanco grueso, cabeza redonda, sin cara**. Es consistente entre seeds *porque es una silueta*: cualquier detalle de rostro o ropa rompe la consistencia sin GPU ni LoRA.
3. **Prompts largos degradan la imagen.** Con dreamshaper (LCM de 4 pasos) un prompt de ~1000 caracteres devolvía cuerpos detallados, extremos de más y sin escenario. Con flux se toleran ~600 caracteres.
4. Vocabulario que **NO** funciona en SD1.5/dreamshaper: "stick figure silhouette + glowing outline" → entrega chicas anime de neón. "flat vector sticker" → entrega pegatinas tiradas en el suelo.
5. Las claves de acción/escenario/plano se resuelven contra la hoja. Una clave huérfana (ej. `senal_final`) cae al prompt como texto literal y condiciona casi nada: el modelo devolvía **el mismo byte** para beats distintos. Test que lo protege: `tests/test_keyframes.py::test_todas_las_claves_del_beats_existen_en_la_hoja`.

## 5. Comandos

```bash
# episodio completo con el motor viral
.venv/bin/python -m pipeline.run auto --historia "zombis: el día 1 del contagio" --slug dia-1-x

# por etapas
.venv/bin/python -m pipeline.run nuevo <slug> --titulo "..."
.venv/bin/python -m pipeline.run guion <slug>
.venv/bin/python -m pipeline.run narrar <slug>
.venv/bin/python -m pipeline.run keyframes <slug> --contacto   # placa, sin render
.venv/bin/python -m pipeline.run keyframes <slug>              # render completo
.venv/bin/python -m pipeline.run keyframes <slug> --forzar     # redrawea keyframes
.venv/bin/python -m pipeline.run enviar <slug>                 # Telegram

# pruebas
.venv/bin/python -m pytest tests -q
```

`--motor montaje` en `auto` conserva la ruta vieja (Ken Burns sobre imágenes descargadas) para comparar.

## 6. PENDIENTES, en orden de impacto

Cada uno con su criterio de aceptación. No marcar "hecho" sin la evidencia.

1. **Episodio real de punta a punta.** Corrida intentada y cortada a mano (por el fix de Bedrock): `dia-1-contagio`, nicho `zombis` (canal "Día Cero"). Aceptar: guion generado por la máquina → narración → placa de contactos aprobada → mp4 → **enviado por el bot de Telegram** con métricas.
2. **Motion blur por promedio de 4 submuestras** (el brief lo pide). Hoy está declarado PENDIENTE en `render_keyframes.json["pendientes"]`. Aceptar: medido el costo extra en el B950; si no se puede, decisión escrita y fundamentada (no eliminar la promesa en silencio).
3. **60 fps.** `KF_FPS=60` funciona; no está medido. Aceptar: número de segundos de render a 30 vs 60 sobre el mismo episodio y una recomendación.
4. **Paquete de publicación.** 3 prompts de miniatura a 1536×1024 + 5 títulos siguiendo a los ganadores del nicho + comparación de la miniatura propia contra las 6 mejores de los canales de referencia **a 320 px de ancho**, quedándose sólo con lo que aguanta. Aceptar: `publicacion/thumbnails.md` con la comparación real, no teórica.
5. **Voz.** Piper x_low funciona pero es baja calidad. Probar `kokoro-onnx` local (no instalado; onnxruntime sí está) y medir segundos de síntesis y calidad subjetiva contra Piper. Si la cadena no cierra, PENDIENTE con evidencia.
6. **Tiempos por palabra.** `faster-whisper` no está instalado. Sin él, los subtítulos van en chunks de ~6 palabras repartidos proporcionalmente. Aceptar: sincronía palabra-pantalla medida, o decisión de quedarse con el reparto actual.
7. **Investigación de canales de referencia.** YouTube MCP ya aporta títulos, vistas y fecha de videos relacionados al proponer cada idea; esa muestra no está normalizada por antigüedad/suscriptores y no sirve como evidencia factual. Sigue pendiente medir 6 canales del formato con score por vistas÷suscriptores, duración y miniaturas; analizar los 3 primeros videos y escribir `state/estilo/estilo.md` (personaje, color, luz, ritmo, cámara, texto, beats, narración, música y **qué no hacen los videos que pierden**). `yt-dlp` todavía no está instalado.
8. **Arco de escenarios.** El planificador asigna escenario por palabra clave: un guion sin topónimos tira los 18 beats a `calle`. Aceptar: variación de escenario por acto, con la placa de contactos mostrando al menos 3 escenarios por minuto.
9. **Variedad de poses.** El fallback alterna `quieto`/`camina` y aburre. Aceptar: ninguna acción repetida 3 veces seguidas en la placa.
10. **Wiring del orquestador.** `factory/orchestrador.py` sigue rutando a la etapa `avatar`. Aceptar: `motor="keyframe"` elegible y `estado()` reflejando la etapa nueva.
11. **`derivados` + checklist sobre la ruta keyframe.** `checklist()` exige `derivados-manifest.json`. Aceptar: cortes verticales 9:16 generados desde el mp4 keyframe y enviados por Telegram.
12. **Formato real del archivo de flux.** Workers AI devuelve **JPEG** y se guarda con extensión `.png`. Aceptar: extensión y contenido coherentes (o normalizar a PNG de verdad).
13. **Lazo de aprobación por Telegram de la placa** antes del render (regla del brief: revisar y recién después filmar). Aceptar: `contacto.png` llega al bot y el render espera el OK (o autoaprueba tras N minutos, documentado).
14. **Deuda de seguridad**: `stickman-studio-key.json` está en texto plano en el repo; el token de Kaggle no tiene username; `pipeline/llm.py` usa `datetime.utcnow()` deprecado. Aceptar: credenciales fuera del índice o cifradas, y el warning eliminado.
15. **Cómics — v2 ya Renderizada; sigue Fase 3 y siguientes** (`FABRICA-DE-COMICS.md`): el contrato comics.v2 está implementado y con prototipo aprobado (15 viñetas / 2 páginas, grillas 3/3/3 + 2/2/2). PENDIENTE: (a) camino LLM SMyCB para pulir captions/diálogos con guard de paridad factual (el determinista queda como base auditable); (b) testimonio con guiones largos reales (~60-70 oraciones → chunking `_agrupar` a 18 beats → 20 viñetas); (c) debate del orquestador con `COMICS_ENABLED`; (d) publicación de cómics (fase 6, luego de validar formato con el dueño). Nota de idioma: el caption SIEMPRE es el guion del canal (español) que cita el ancla — los claims EN/ES en `sources.json` solo alimentan el footer de fuentes; validar en el primer episodio real.
16. **`tests/test_subtitles.py`: 5 fallas preexistentes** (`AttributeError: module 'pipeline.stages.montaje' has no attribute '_ass'`): el refactor que quitó los subtítulos quemados (pedido del dueño) dejó el dead-code `_ass` o tests viejos. Aceptar: o tests actualizados al contrato nuevo o `_ass` eliminada — NO revertir el refactor.
17. **`headless_actor.py` es un borrador sin cablear** (nadie lo importa; se le agregaron los imports `os`/`json` que le faltaban para que compile, pero la lógica interna está a medio escribir). Aceptar: decidir con el dueño si se completa, se archiva o se borra.

## 7. Bugs que ya se arreglaron — no regressarlos

| Bug | Causa raíz | Test que lo protege |
|---|---|---|
| Tres beats devolvían el **mismo byte** | el test reutilizaba el mismo prompt; además las claves crudas no condicionaban nada | `test_todas_las_claves_del_beats_existen_en_la_hoja`, `test_huella_de_imagen_no_congela_prompts_distintos` |
| Planos de 4 s y texto desincronizado | `beats.plan` partía las duraciones sin partir el texto | `test_el_texto_se_reparte_con_el_tiempo`, `test_todos_los_beats_entran_en_la_banda` |
| ffmpeg: `No option name near '(iw-iw/zoom)*on/59'` | dentro de un filtro los parámetros se separan con `:`, la coma cierra el filtro | `test_camara_es_un_filtergraph_valido` |
| Subtítulos quemaban `,0,0,0,,palabra` | `Format:` declaraba 5 campos | `tests/test_subtitles.py` |
| −15,9 LUFS en vez de −14 | voz de Piper a 0 dBFS + loudnorm de una pasada | `test_loudnorm_lineal_clava_los_m14` |
| `chat()` multiplicaba intentos (5×3=15 por proveedor) | dos bucles de reintento superpuestos | `test_chat_no_multiplica_los_intentos` |
| La placa de contactos reventaba (exit 234) | `fps=30` en una salida de imagen única | `test_keyframes.py` (coberto por `hoja_contactos`) |
| El bot nunca mandaba el video final | `enviar_telegram` globbeaba sólo `derivados/` | ver §3 de `ROADMAP.md` |
| `AUTO_PUBLISH_FALLÓ` con posts VIVOS | Zernio devolvía `platformPostUrl: null` en la respuesta de creación y el contador pedía URL inmediata | `publicar_automatico` reconcilia contra `GET /posts/:postId` al vuelo; verificado con red-proxy-casa-blanca |

**Cómics a Telegram** (2026-11-06, actualizado a v2): `pipeline/comics/telegram.py::enviar_comic(ep)` manda el LIBRO (páginas `comics/pages/pag-NN.png`) con la leyenda "versión de revisión — NO está publicado". Reusable desde cualquier etapa.

## 8. Mapa de archivos

```
pipeline/imagen.py             cliente Workers AI + caché por huella + armar_prompt
state/estilo/personaje.json    hoja de personaje (contrato de prompt) — versionar al tocar
factory/acting/beats.py        guion -> beats de 1,35-2,20 s (densidad viral)
pipeline/stages/keyframes.py   keyframes -> cámara 2.5D -> placa -> concat -> audio -> QC
pipeline/stages/montaje.py     validar_ass / ASS_FORMAT (reutilizados por keyframes)
pipeline/stages/short.py       _cama: cama musical lavfi reutilizable
pipeline/stages/narracion.py   Piper + segmentación del guion
pipeline/stages/publicacion.py envío por Telegram (lee artifacts/render_*.json["archivo"])
pipeline/llm.py                cascada, reintento, limpieza de <reasoning>
pipeline/web.py                lector Scrapling/curl_cffi con fallback sin dependencias
pipeline/stages/descubrir.py   autodescubrimiento de fuentes (relevancia × prestigio)
docker/factory/factoryd.py     daemon 24/7 (REST+WS :8610) — corre desde el mount
docker-compose.yml             pulso-factory :8610 + pulso-dashboard :8611 (único puerto)
docker/dashboard/www/          Mission Control — sala de control sobria (vanilla, sin SVG, 1 archivo CSS)
factory/render/actor_page.html página del actor en Babylon.js (contrato CDP intacto)
factory/render/cdp.mjs         driver headless del actor (smoke test / benchmark)
pipeline/comics/               extensión historietas comics.v2 (off por defecto, QC honesto)
tests/test_comics.py           regresiones del contrato comics.v2 (15 viñetas, grillas 3 bandas)
tests/test_keyframes.py        regresiones del motor nuevo
DEPENDENCIAS.md                licencias de todo lo nuevo
VIABILIDAD.md                  qué es gratis de verdad y qué no
ROADMAP.md                     estado de la fábrica por fase
```

## 9. Cómo hablarle a CÓDEX en esta caja

- Prompt de arranque sugerido: `leé CODEX.md y seguí con el PENDIENTE 1`.
- Que ejecute con los comandos de §5, no con `python3` del sistema (el `pytest` está en `.venv`).
- Que no toque `projects/` ni `work/` en un `git add`; que no suba imágenes del usuario a servicios externos sin preguntar; que no borre episodios para "limpiar".
- Que reporte cada cierre con: archivo modificado y por qué, métricas del render, y salida real del comando.
