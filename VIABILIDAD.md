# FASE 0 — Gate de viabilidad de render 3D headless

Medido en la máquina real (Pentium B950, 2 núcleos, 11 GiB, HDD, sin GPU), Chrome 155 +
SwiftShader (WebGL por software), motor Three.js r169 vendorizado en `factory/render/`.
Driver: `factory/render/cdp.mjs` (CDP puro, sin npm).

## Escena de prueba

Como **no existe ningún GLB en la máquina** (verificado con `find ~ -iname '*.glb'` → 0 resultados),
se midió contra dos escenas:

1. **procedural**: la figura de respaldo de `actor_page.html` (~15 primitivas livianas).
2. **GLB proxy**: `tools/make_proxy_glb.py` genera un glTF binario con la complejidad esperada del
   "cloak man": 10 242 vértices, 20 480 triángulos, 3 morph targets de boca, esqueleto de 4 huesos
   con skinning. El motor reportó `modo=glb`, `morfos=3`, `huesos=4` → las rutas reales de
   actuación (morph + rig_map sobre huesos) están ejercitadas en la medición.

## Números (mediana sin warmup, descarta los primeros frames)

| escena | resolución | ms/frame | fps real | RAM pico | 30 s @24 fps | 90 s @24 fps |
|---|---|---|---|---|---|---|
| procedural | 1280×720 | 1 164 | 0,86 | 2 277 MB | ~14 min | ~42 min |
| GLB proxy | 1280×720 | 1 986 | 0,50 | 2 259 MB | ~24 min | ~71 min |
| GLB proxy | 960×540 | **998** | **1,00** | 2 261 MB | **~12 min** | **~36 min** |

Carga inicial del motor + escena: 5–9 s (se paga una sola vez por sesión de render).
Sin crash, sin OOM, sin frames negros sospechosos en ninguna corrida.

## DECISIÓN

**El render 3D headless es VIABLE en este hardware. Se sigue con la animación en vivo (FASE 2),
no se pivotea a 2.5D.**

Criterios que se cumplieron:
- RAM: 2,26 GB de 11 GB disponibles, y es casi todo Chrome, no la escena → no crece con el modelo.
- Estabilidad: 75 frames renderizados en 3 corridas, cero caídas.
- Tiempo: 12 min por 30 s de video a 540p es un render por lotes aceptable en una caja sin GPU.

Condiciones que la decisión impone (no son opcionales):
- **Render a 960×540 y upscale a 1280×720 en el mezclado final.** Bajar de 720p nativo a 540p
  casi divide el tiempo por 2 (1 986 → 998 ms/frame); el costo es software rasterization pura,
  dominado por píxeles, no por triángulos.
- **Una sola sesión de Chrome por video**, todos los frames en el mismo proceso (la carga inicial
  de 5–9 s se paga una vez, no por frame).
- **24 fps, no 30 ni 60.** `factory/acting/director.py` ya fija `FPS = 24`; a 30 fps el costo
  sube 25 % sin beneficio visible en este tipo de plano.
- El pipeline **nunca** debe quedarse solo en 3D: si una escena falla se regenera esa escena
  (FASE 2, evaluación automática), no el video entero.

## Confirmación en producción real (no benchmark)

La decisión se validó después con una pieza completa, con timeline real del director
(6 segmentos, partitura por LLM, 391 cues de Rhubarb, 11 planos de cámara) y audio real de Piper:

| corrida | duración | frames | ms/frame (mediana) | min de frames | RAM pico Chrome | peso final |
|---|---|---|---|---|---|---|
| smoke 2 s @540p | 2,04 s | 49 | 415 | 0,8 | — | 0,10 MB |
| pieza completa @540p→720p (proxy `/tmp`) | 58,38 s | 1 401 | 577 | 14,2 | 2 303 MB | 1,51 MB |
| **aceptación 30 s con `cloakman.glb` del repo** | **28,40 s** | **682** | **397** | **8,1** | **2 343 MB** | **1,06 MB** |

El 577 ms/frame real es la mitad de los 998 ms del benchmark: la escena de prueba corría con la
timeline sintética de 2 segmentos; la real es más barata por frame porque el costo está dominado
por píxeles (SwiftShader) y no por la rigging. O sea: **~7 min por cada 30 s de video**, no 12.
La corrida de aceptación baja además a **397 ms/frame** con el personaje definitivo (7 144
triángulos) contra el proxy de referencia (~20 k): el costo sigue siendo el píxel, y el modelo
cuesta menos de lo que costaba el proxy. Cero frames negros (`blackdetect`: 0 s), cero caídas,
cero OOM, y el presupuesto de RAM sigue siendo el mismo con 49 que con 1 401 frames.

## Qué queda como fallback documentado (no activado)

La ruta 2.5D por sprites + FFmpeg (la que ya funciona en `anime-argento`) sigue siendo la opción
de emergencia si el GLB real del "cloak man" resulta ser mucho más pesado que el personaje actual.
Antes de activar ese pivote hay que medir el GLB real con esta misma herramienta:

```sh
node factory/render/cdp.mjs --frames 15 --w 960 --h 540 --glb assets/<cloak>.glb --out /tmp/b
```

## Límite honesto de esta medición

Desde la corrida de aceptación el pipeline **ya no depende de un proxy en `/tmp`**: renderiza
`assets/characters/cloakman.glb`, que vive en el repo. Pero ese archivo **lo generamos nosotros**
(`tools/make_character_glb.py`, 31 piezas, 7 144 triángulos, rig por nodos nombrados) porque el
GLB real del "cloak man" del usuario **no existe en esta máquina** (`find ~ -iname '*.glb'` = 0
resultados; `state/personajes/principal.json` apuntaba a `assets/4F/pulso-4f.glb`, inexistente).
Cuando llegue el archivo real, `--glb` o un `.glb` en `assets/` lo toman sin tocar código, y la
tabla de arriba se recalcula con el comando de medición. Si el modelo real trae morph targets o
skinning, el motor ya los soporta por la otra ruta (`aplicarAGlb`): el sidecar de rig por nodos
es el complemento para personajes sin cara animable, no un reemplazo.
