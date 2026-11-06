#!/usr/bin/env python3
"""Genera los 23 SKILL.md de la fábrica en .agents/skills/<nombre>/SKILL.md.

Cada skill documenta su contrato, punto funcional REAL (module.function),
criterios de calidad, validaciones y recuperación. Regenerable: si editas
registry.py, la parte operativa de estos docs se actualiza con este script.
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".agents" / "skills"
sys.path.insert(0, str(ROOT))

from factory.skills import registry as reg  # noqa: E402

EXTRA = {
    # instrucciones operativas propias por skill (lo que no se deriva del registro)
    "3d-character-director": textwrap.dedent("""\
        **Operación:** correr después de `narrar` (necesita `segment_durations_s`).
        1. Segmentar `artifacts/script.txt` igual que la voz (`narracion._segments`).
        2. Pedir partitura emocional al LLM (`pipeline.llm.chat_json`, task `direccion`); si
           el LLM falla usar fallback determinista y MARCARLO en el log.
        3. Compilar: transición suave prev->nuevo (0.45 s, smootherstep, escalada por
           intensidad) + gesto (anticipación en `gesto_t0`) + blinks + micro.
        4. Cámara con política por emoción; corte interior si el plano dura > 8 s.
        5. Escribir `artifacts/timeline_actuacion.json` y validar contra
           `factory/specs/timeline_actuacion.schema.json`.

        **Error y recuperación:** si Rhubarb no está instalado, el lip-sync cae a modo
        silábico (declarado); el director igualmente produce timeline y el orquestador
        decide si aceptarla. Si no hay narración: SystemExit con instrucción clara.

        **Ejemplo (CLI):** `python -c "from pathlib import Path; from
        factory.acting.director import construir_timeline; construir_timeline(Path('projects/<slug>'))"`"""),
    "facial-expression-animator": textwrap.dedent("""\
        **Operación:** leer la timeline del character-director (fuente única de verdad)
        y exponer los bloques de rig facial listos para el backend. Si no hay timeline,
        componer bloques desde la partitura con `estados.transicion_bloque`.

        **Reglas de calidad facial (pilar 1):** cejas independientes, micro-exposición
        ocular 0.85..1.4, mirada con intención (dx/dy), transiciones nunca lineales.
        Prohibido: valores fuera del contratado por `estados.PARAMS`; simpular
        "emoción" solo con boca abierta.

        **Ejemplo:** `factory.skills.registry.invocar('facial-expression-animator', ep)`"""),
    "phoneme-lipsync-engineer": textwrap.dedent("""\
        **Operación:** pasar el WAV de Piper a Rhubarb (`tools/rhubarb/rhubarb`,
        `-r phonetic --extendedShapes GHX`), recortar cues de visemas y guardar
        `artifacts/lipsync.json`. Para español, Rhubarb funciona sin diccionario
        (rutas fonéticas); NUNCA presentar cues silábicos como fonéticos — el motor
        `silabico` es fallback declarado y exige QC reforzado.

        **Criterios:** cues monótonos, visemas en {A B C D E F G H X}, densidad
        esperada 6..16 cues/s. Si el WAV no existe: fallar con instrucción ('narrar').

        **Ejemplo:** `tools/rhubarb/rhubarb -f json -r phonetic -o lipsync.json dialogo.wav`"""),
    "body-language-director": textwrap.dedent("""\
        **Operación:** de la timeline, construir plan de gestos con anticipación
        (0.08 s), settle (0.2 s) y duración escalada por `velocidad` del estado.
        Cada gesto debe tener propósito narrativo (explicar, advertir,
        mirar_atras...): sin gesticulación constante.

        **Prohibido:** penetrar geometría, deslizar pies, gestos duplicados en
        tramos < 1.5 s. La biblioteca vive en `factory/acting/estados.GESTOS`.

        **Ejemplo:** `factory.skills.registry.invocar('body-language-director', ep)`"""),
    "cinematic-camera-director": textwrap.dedent("""\
        **Operación:** por segmento elegir plano/movimiento desde CAMARA_POR_EMOCION
        (primer plano en miedo/suspenso, contrapicado en sorpresa, general en
        tranquilidad); corte interior en tramos largos. Composición: no cortar en
        el propio punto de énfasis (`enfatiza`).

        **Criterios:** movimientos suaves (sin sacudidas), densidad de cortes
        0..0.35 cortes/s en documental, motivación registrada en cada plano.

        **Ejemplo:** `factory.skills.registry.invocar('cinematic-camera-director', ep)`"""),
    "character-continuity-guardian": textwrap.dedent("""\
        **Operación:** persistir perfil del personaje en `state/personajes/`
        (paleta, iluminación, backend GLB, voz) y auditar cada episodio: backend
        estable, GLB idéntico, voz en allowlist. Bloquea aprobación con problemas.

        **Criterios (pilar 7):** un solo GLB por personaje; cambios de vestuario
        requieren registrarlos; iluminación del perfil nunca desviada.

        **Ejemplo:** `factory.skills.registry.invocar('character-continuity-guardian', ep)`"""),
    "viral-story-researcher": textwrap.dedent("""\
        **Operación:** `pipeline.tendencias.detectar` sobre semillas del nicho
        (Wikipedia热度, Hacker News, canales en vivo) + `pipeline.ideas.generar`
        para proponer episodios rankeados. No se adopta idea por grabbing viral
        aislado: exigir señal sostenida (demanda, comentarios reales).

        **Ejemplo:** `factory.skills.registry.invocar('viral-story-researcher')`"""),
    "retention-scriptwriter": textwrap.dedent("""\
        **Operación:** escribir el guion segmentado (`pipeline/stages/guion.guion`)
        con identidad del canal por nicho (`pipeline.nichos.canal_de`),
        hook < 15 s, escalada, giros y final. Respetar transformación de ideas
        (gate anti-duplicado contra los últimos 5 guiones).

        **Criterios:** bloques 20..120 palabras; preguntas abiertas repartidas;
        zero clickbait; cumplimiento del modo ficción/documental del nicho.

        **Ejemplo:** `factory.skills.registry.invocar('retention-scriptwriter', ep)`"""),
    "emotional-story-director": textwrap.dedent("""\
        **Operación:** partitura por segmento (emoción de los 13 estados,
        intensidad 0.2-1.0, gesto, enfásiz, sfx). La curva DEBE ser una curva
        (no uniformidad): escalar intensidad hacia el clímax. Fallback
        determinista si el LLM no responde, marcado en el log.

        **Ejemplo:** `factory.skills.registry.invocar('emotional-story-director', ep)`"""),
    "documentary-investigator": textwrap.dedent("""\
        **Operación:** descubrir fuentes (`stages.descubrir`), extraer contenido,
        redactar resumen con citas (`stages.research.research`) y verificar con
        proveedor INDEPENDIENTE (`factcheck`). Para historia/política/belico:
        fuentes因为它 identificables, fechas y no-inventar testimonios.

        **Gate 1:** < 4 fuentes únicas => SystemExit (no se publica sin research).

        **Ejemplo:** `factory.skills.registry.invocar('documentary-investigator', ep)`"""),
    "series-universe-builder": textwrap.dedent("""\
        **Operación:** consolidar episodios por categoría en `universo.json`
        (cast recurrente, continuidad, sugerencias de serie). Ampliar el cast
        con los perfiles creados por character-continuity-guardian.

        **Ejemplo:** `factory.skills.registry.invocar('series-universe-builder', ep)`"""),
    "storyboard-architect": textwrap.dedent("""\
        **Operación:** para cada segmento del guion materializar el visual:
        imágenes/archivo libre (Commons/Wikipedia/NASA filtrado por domínio) o
        clip propio; guardar en `assets/img|video/seg-NNN.*`. PROHIBIDO usar
        recreaciones como foto documental real; siempre score tree + crédito.

        **Ejemplo:** `factory.skills.registry.invocar('storyboard-architect', ep)`"""),
    "sound-design-engineer": textwrap.dedent("""\
        **Operación:** de la timeline, produzir `artifacts/plan_sonoro.json`
        (pistas amb/SFX con tiempo y ganancia, música -18 dB con ducking,
        silencios dramáticos en suspenso). Ejecutar mezcla en el montaje con
        FFmpeg amix; la música NUNCA competencia de la voz.

        **Ejemplo:** `factory.skills.registry.invocar('sound-design-engineer', ep)`"""),
    "cinematic-video-editor": textwrap.dedent("""\
        **Operación:** `stages.montaje.montar`: concat por segmentos (Ken Burns
        en imágenes, sub ass integrado, intro/outro, voz con adelay 3 s) + QC
        ffprobe automatizado (duración, streams). Reintentos por-parts opcionales:
        solo el segmento que falla, NO el video completo.

        **Ejemplo:** `factory.skills.registry.invocar('cinematic-video-editor', ep)`"""),
    "thumbnail-art-director": textwrap.dedent("""\
        **PENDING (backend futuro).** Contrato FIRMADO que el módulo debe cumplir:
        entradas = render principal + paleta + título; salida = `thumbnail.jpg`
        1280x720 con sujeto principal + <=3 palabras + contraste alto; QC =
        tamaño de texto relativo > 0.08 del alto y UI textual mínima. El
        orquestador NO debe llamarla hasta que exista el módulo real.
        Estado en registry: `pendiente_backend`."""),
    "youtube-growth-analyst": textwrap.dedent("""\
        **Operación:** registrar métricas por publicación
        (`stages.publicacion.registrar`): vistas, retención, CTR si disponible,
        recurrentes; aprender no solo por vistas sino por recurrencia y
        retención (spearching en `state/aprendizaje.json`). Experiments título/
        miniatura controlados.

        **Ejemplo:** `factory.skills.registry.invocar('youtube-growth-analyst', ep)`"""),
    "facebook-content-strategist": textwrap.dedent("""\
        **Operación:** publicar por conector OFICIAL (Zernio) el paquete de
        facebook.md. Nada de scraping de sesiones: solo API sin våra keys
        expuestas. Reintentos solo a operaciones seguras (POST idempotente).

        **Ejemplo:** `factory.skills.registry.invocar('facebook-content-strategist', ep)`"""),
    "community-manager-ai": textwrap.dedent("""\
        **PENDING (backend futuro).** Contrato FIRMADO: entrada = comentarios
        crudos; salida = {clasificación: pregunta|spam|idea|delicado,
        respuesta_genuina?, derivar_humano?}. Personalidad del canal, sin
        repetición automatizada, sin dedos falsos. Estado: `pendiente_backend`."""),
    "render-optimization-engineer": textwrap.dedent("""\
        **Operación:** publish config.limites() como fuente única: 1 render
        simultáneo, 720p/24fps para GLB, serializar FFmpeg, límite RAM
        configurable. Si la RAM se excede, reducir resolución antes que fps.

        **Ejemplo:** `factory.skills.registry.invocar('render-optimization-engineer')`"""),
    "visual-quality-inspector": textwrap.dedent("""\
        **Operación:** ffmpeg blackdetect (>= 0.3 s es defecto) + freezedetect
        sobre el render; guarda `artifacts/qc_visual.json`. Los photograms
        negros de la intro/outro son EXPECTED solo si duración < 0.3 s.

        **Ejemplo:** `factory.skills.registry.invocar('visual-quality-inspector', ep)`"""),
    "audio-quality-inspector": textwrap.dedent("""\
        **Operación:** ffmpeg ebur128: LUFS integrados (-16..-14 objetivo web,
        True Peak muestra), sincronía de duración vs video. Guardes
        `artifacts/qc_audio.json`; problema si < -22 LUFS (inaudible) o
        > -12 LUFS (peligro).

        **Ejemplo:** `factory.skills.registry.invocar('audio-quality-inspector', ep)`"""),
    "copyright-compliance-reviewer": textwrap.dedent("""\
        **Operación:** cada asset visual debe tener fuente (research/urls.txt)
        en bibliotecas de licencia verificable; música de biblioteca autorizada;
        recreaciones NO presentadas como material documental. Produce registro
        de licencias + problemas; bloquea publicación si hay asset sin fuente.

        **Ejemplo:** `factory.skills.registry.invocar('copyright-compliance-reviewer', ep)`"""),
    "monetization-policy-reviewer": textwrap.dedent("""\
        **Operación:** check `pipeline.gates.gate_publicacion` contra los
        requisitos oficiales YPP/Facebook (4,000 h + 1,000 subs", etc.). El
        sistema NO garantiza monetización: muestra progreso verificado y
        bloqueos de elegibilidad. Contenido sintético siempre declarado.

        **Ejemplo:** `factory.skills.registry.invocar('monetization-policy-reviewer', ep)`"""),
}


def render(md_name: str, meta: dict) -> str:
    punto = mod, fn = meta.get("punto", ("<pendiente>", "<pendiente>"))
    head = f"""---
name: {md_name}
grupo: {meta['grupo']}
estado: {meta['estado']}
punto_funcional: {punto[0]}.{punto[1]}
contrato_salida: {meta.get('contrato', '—')}
---

# {md_name}

## Objetivo y responsabilidades
{meta['rol']}
"""
    body = f"""
## Entradas (contrato de datos)
- Episodio: `projects/<slug>/` (clase `pipeline.episode.Episode`), con el pre-requisito: {meta.get('tz', '-')}
- Contexto compartido: `artifacts/` (script.txt, metadata.json, timeline_actuacion.json, lipsync.json)

## Salidas (contrato de datos)
- Contrato `{meta.get('contrato', '—')}` validado por `factory/skills/contratos.py`
- Artefactos escritos en `artifacts/` (ver Operación)

## Herramientas y repositorios compatibles
- pipeline/ (stages, llm multiproveedor con caché y rutas por tarea), factory/acting/ (estado/gestos/lipsync)
- Rhubarb Lip Sync (MIT, visemas), Piper TTS (VOX, voz del canal), FFmpeg (montaje y QC ebur128/blackdetect)
- mesh-avatar-studio / OpenMontage para representación visual y variante editorial

## Criterios de calidad
- Producto REAL medible (no placebo): la evaluación `registry.evaluar` marca pass/falla_N sobre el contrato.
- Hardware limitado: un solo render simultáneo, 720p/24fps GLB, serialización FFmpeg (config.limites).
- Siempre declarar el motor real usado (rhubarb/silabico, rhubarb debe ser el objetivo).

## Validaciones
- Entrada: exige episódio con pre-requisitos; contratos produccion (`contratos.py`) aplicados automáticamente.
- Salida: `evaluacion` en el retorno de `invocar` con problemas concretos.

## Condiciones de error y recuperación
- La skill NO mata la fábrica: `invocar` registra `status=error` en `state/skills_log.jsonl`
  con las últimas 2 líneas del traceback, y el orquestador decide reintentar o degradar.
- Fallbacks declarados en metadata (nunca se presenta un fallback como la vía óptima).

## Ejemplo de ejecución
```python
from pipeline import episode
from factory.skills import registry
ep = episode.Episode('<slug>')
out = registry.invocar('{md_name}', ep)   # -> {{estado, salida, evaluacion, duracion_s}}
```
"""
    extra = EXTRA.get(md_name)
    return head + "\n## Instrucciones operativas\n" + (extra or "Ver punto funcional y contrato en el registry.") + body


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, meta in reg.SKILLS.items():
        d = OUT / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(render(name, meta), encoding="utf-8")
    print(f"escritas {len(reg.SKILLS)} SKILL.md en {OUT}")


if __name__ == "__main__":
    main()
