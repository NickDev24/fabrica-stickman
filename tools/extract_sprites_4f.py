# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "opencv-python-headless", "rapidocr-onnxruntime"]
# ///
"""SISTEMA PROFESIONAL DE EXTRACCIÓN DE SPRITES — AVATAR 4F (v2).

Localiza cada elemento por su RÓTULO (OCR), no por una cuadrícula: cada hoja es
un collage de paneles de tamaños distintos y el texto de cada panel nombra su
contenido. El nombre leído define la categoría y el nombre de archivo final.

Flujo por hoja:
  1. OCR de la hoja (cacheado en avatar_4f/_extractor/ocr_<hoja>.json).
  2. Agrupado de líneas -> bloques de rótulo (nombre + descripción).
  3. Región del elemento = espacio entre la fila anterior de rótulos y el rótulo.
  4. GrabCut dentro de la región -> alfa real (fondo transparente).
  5. Recorte ajustado al alfa + margen transparente de seguridad.
  6. Catálogo de palabras -> categoría, tipo de animación y nombre canónico.
  7. manifest.json + galería QA; sin datos suficientes -> PENDIENTE DE REVISIÓN.

Uso: .venv/bin/python tools/extract_sprites_4f.py [--forzar-ocr] [img ...]
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "avatar_4f"
QA = OUT / "_qa"
CACHE = OUT / "_extractor"
MAX_SIDE = 1800

# (palabras clave en el rótulo, categoría, nombre canónico, tipo para el motor)
CATALOGO = [
    # --- poses estáticas de cuerpo completo
    (("reposo neutral", "reposo", "idle"), "poses", "idle", "pose_completa"),
    (("frontal",), "poses", "frontal", "pose_completa"),
    (("lateral derecho", "profile-right", "perfil derecha"), "poses", "perfil_derecho", "pose_completa"),
    (("lateral izquierdo", "profile-left", "perfil izquierdo"), "poses", "perfil_izquierdo", "pose_completa"),
    (("tres cuartos", "3/4"), "poses", "tres_cuartos", "pose_completa"),
    (("espalda", "back", "vista posterior"), "poses", "espalda", "pose_completa"),
    (("agachado", "infiltracion"), "poses", "agachado", "pose_completa"),
    (("arrodillado", "rodilla"), "poses", "arrodillado", "pose_completa"),
    (("tumbado", "postura de observacion"), "poses", "tumbado", "pose_completa"),
    (("sentado", "silla", "escritorio"), "poses", "sentado", "pose_completa"),
    (("combate", "guarda"), "poses", "combate", "pose_completa"),
    # --- movimientos dinámicos
    (("carrera", "correr", "running"), "movimientos", "correr", "secuencia"),
    (("evasion",), "movimientos", "evasion", "secuencia"),
    (("salto", "jump"), "movimientos", "saltar", "secuencia"),
    (("caida",), "movimientos", "caida_controlada", "secuencia"),
    (("lanzamiento", "lanzar", "throw"), "movimientos", "lanzar_dispositivo", "secuencia"),
    # --- expresiones faciales
    (("neutral",), "expresiones", "neutral", "expresion"),
    (("alegria", "felicidad", "happy"), "expresiones", "alegria", "expresion"),
    (("tristeza", "sad", "triste"), "expresiones", "tristeza", "expresion"),
    (("enojo", "furioso", "furiously", "rabia"), "expresiones", "enojo", "expresion"),
    (("miedo", "fear", "scared", "terror"), "expresiones", "miedo", "expresion"),
    (("sorpresa", "surprised"), "expresiones", "sorpresa", "expresion"),
    (("confusion", "confuso", "skeptic", "duda"), "expresiones", "confusion", "expresion"),
    (("concentracion", "focused", "enfocado"), "expresiones", "concentracion", "expresion"),
    (("disgusto", "disappointed", "disgust"), "expresiones", "disgusto", "expresion"),
    (("cansancio", "exhausted", "exhausto", "fatiga"), "expresiones", "cansancio", "expresion"),
    (("aburrimiento", "apatia", "bored"), "expresiones", "aburrimiento", "expresion"),
    (("sarcasmo", "burla", "sarcastic"), "expresiones", "sarcasmo", "expresion"),
    (("inspiracion", "idea", "thinking", "pensativo"), "expresiones", "inspiracion", "expresion"),
    (("dolor", "esfuerzo", "pain"), "expresiones", "dolor", "expresion"),
    # --- gestos de manos
    (("mano abierta", "saludo abierto", "open hand"), "gestos", "mano_abierta", "gesto"),
    (("puno cerrado", "fist", "puno"), "gestos", "puno_cerrado", "gesto"),
    (("senalar", "senalar datos", "enfoque de datos"), "gestos", "senalar", "gesto"),
    (("contando", "dos dedos", "paz", "victoria", "peace"), "gestos", "contando_dedos", "gesto"),
    (("cap", "ajuste de equipo", "ajuste de gorra", "mano en el"), "gestos", "ajuste_gorra", "gesto"),
    (("carino", "holo-perro", "caricia"), "gestos", "gesto_carino", "gesto"),
    (("confirmacion", "pulgar", "thumbs", " ok"), "gestos", "confirmacion_ok", "gesto"),
    # --- acciones con objetos / interfaz
    (("escaneo", "escanear", "scan"), "acciones", "escanear_datos", "accion"),
    (("analisis", "analizar"), "acciones", "analizar_datos", "accion"),
    (("consola", "interfaz"), "acciones", "operar_consola", "accion"),
    (("carga de energia", "pose de poder", "energia"), "acciones", "cargar_energia", "accion"),
]

DESC_INICIO = ("utilizar", "uso", "reaccion", "determinacion", "estado", "falta",
               "derivado", "analisis de", "evaluacion", "entrada", "despliegue",
               "interaccion", "aprobacion", "muestra", "detalle", "punto", "dano",
               "evasion", "movimiento", "señala", "senala")
RUIDO = re.compile(r"^(4f|pulso|curioso|youtube|datos|#?[0-9a-f]{6}|[0-9.,\-\s]+)$", re.I)


def slug(txt: str) -> str:
    t = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "_", t).strip("_").lower()
    return re.sub(r"_+", "_", t)


def cargar_hoja(path: Path):
    bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if bgr is None:
        raise SystemExit(f"no pude leer {path}")
    h0, w0 = bgr.shape[:2]
    esc = MAX_SIDE / max(h0, w0)
    if esc < 1:
        bgr = cv2.resize(bgr, (int(w0 * esc), int(h0 * esc)), interpolation=cv2.INTER_AREA)
    return bgr, float(esc)


# --------------------------------------------------------------------- OCR
def ocr_hoja(path: Path, forzar: bool = False) -> list[dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    cache = CACHE / f"ocr_{path.stem}.json"
    if cache.exists() and not forzar:
        return json.loads(cache.read_text(encoding="utf-8"))
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    res, _ = ocr(str(path))
    items = []
    for r in res or []:
        box, txt, conf = r[0], r[1], float(r[2])
        xs, ys = [p[0] for p in box], [p[1] for p in box]
        items.append({"texto": txt.strip(), "conf": round(conf, 3),
                      "x": int(min(xs)), "y": int(min(ys)),
                      "w": int(max(xs) - min(xs)), "h": int(max(ys) - min(ys))})
    cache.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    return items


def es_util(items: list[dict]) -> list[dict]:
    out = []
    for it in items:
        t = it["texto"]
        if it["conf"] < 0.55 or len(t) < 3 or RUIDO.match(t):
            continue
        out.append(it)
    return sorted(out, key=lambda i: (i["y"], i["x"]))


def agrupar_bloques(items: list[dict]) -> list[dict]:
    """Agrupa líneas vecinas (nombre + descripción) en un rótulo por elemento."""
    bloques: list[dict] = []
    for it in items:
        asignado = False
        for b in bloques:
            solape_x = min(b["x1"], it["x"] + it["w"]) - max(b["x0"], it["x"])
            h_ult = b["lineas"][-1]["h"]
            cerca_y = 0 <= it["y"] - b["y1"] <= 0.75 * max(it["h"], h_ult)
            if solape_x > 0.35 * min(b["x1"] - b["x0"], it["w"]) and cerca_y:
                b["lineas"].append(it)
                b["x0"], b["x1"] = min(b["x0"], it["x"]), max(b["x1"], it["x"] + it["w"])
                b["y1"] = max(b["y1"], it["y"] + it["h"])
                asignado = True
                break
        if not asignado:
            bloques.append({"x0": it["x"], "x1": it["x"] + it["w"], "y0": it["y"],
                            "y1": it["y"] + it["h"], "lineas": [it]})
    for b in bloques:
        lineas = sorted(b["lineas"], key=lambda i: i["y"])
        nombre = lineas[0]["texto"]
        for extra in lineas[1:]:
            t = extra["texto"]
            if t.lower().startswith(DESC_INICIO) or len(t) > len(nombre) + 12:
                break
            nombre = f"{nombre} {t}"
        b["nombre"] = nombre
        b["texto_completo"] = " ".join(i["texto"] for i in lineas)
        b["h"] = max(i["h"] for i in lineas)
        b["conf"] = max(i["conf"] for i in lineas)
    return bloques


def descartar(b: dict) -> bool:
    """Títulos de sección, descripciones y textos de guía no son elementos."""
    n = b["nombre"].strip()
    if len(n) < 3:
        return True
    if n.lower().startswith(DESC_INICIO):
        return True
    letras = [c for c in n if c.isalpha()]
    if letras and sum(c.isupper() for c in letras) / len(letras) > 0.85 and len(n) > 9:
        return True
    if n.endswith(":"):
        return True
    return False


def mapear(nombre: str) -> tuple[str, str, str]:
    """Rótulo -> (categoría, nombre canónico, tipo). Fallback: sin_clasificar."""
    t = " " + nombre.lower() + " "
    for claves, cat, canon, tipo in CATALOGO:
        if any(k in t for k in claves):
            return cat, canon, tipo
    return "sin_clasificar", slug(nombre), "por_clasificar"


# -------------------------------------------------------------- geometría
def region_elemento(b: dict, bloques: list[dict], hoja_hw: tuple[int, int]) -> tuple[int, int, int, int]:
    """Franja entre el rótulo y el bloque de rótulos de arriba, en la misma columna."""
    hh, ww = hoja_hw
    y_fin = b["y0"] - max(2, int(0.25 * b["h"]))
    y_ini = int(hh * 0.04)
    for o in bloques:
        if o is b:
            continue
        solape = min(b["x1"], o["x1"]) - max(b["x0"], o["x0"])
        if solape > 0.25 * min(b["x1"] - b["x0"], o["x1"] - o["x0"]) and o["y1"] <= b["y0"]:
            y_ini = max(y_ini, o["y1"] + max(2, int(0.2 * o["h"])))
    ancho = b["x1"] - b["x0"]
    x0 = max(0, b["x0"] - int(0.12 * ancho))
    x1 = min(ww, b["x1"] + int(0.12 * ancho))
    if y_fin - y_ini < 20:
        y_ini = max(0, y_fin - int(hh * 0.25))
    y_ini = max(0, min(y_ini, hh - 2))
    y_fin = max(y_ini + 2, min(y_fin, hh))
    return x0, y_ini, max(2, x1 - x0), y_fin - y_ini


# -------------------------------------------------------------- GrabCut
def extraer_alfa(hoja: np.ndarray, region: tuple[int, int, int, int]) -> tuple[np.ndarray | None, dict]:
    x, y, w, h = region
    if w < 12 or h < 12:
        return None, {"motivo": "region_chica"}
    esc = min(1.0, 720.0 / max(w, h))
    crop = hoja[y:y + h, x:x + w]
    if esc < 1:
        crop = cv2.resize(crop, (max(12, int(w * esc)), max(12, int(h * esc))), interpolation=cv2.INTER_AREA)
    ch, cw = crop.shape[:2]
    gc = np.full((ch, cw), cv2.GC_BGD, np.uint8)
    m = int(0.06 * min(cw, ch))
    gc[m:ch - m, m:cw - m] = cv2.GC_PR_FGD
    # semilla segura: torso (centro, 45-75% de altura)
    cx0, cx1 = int(0.34 * cw), int(0.66 * cw)
    cy0, cy1 = int(0.42 * ch), int(0.78 * ch)
    gc[cy0:cy1, cx0:cx1] = cv2.GC_FGD
    gc[:max(2, m // 2), :] = cv2.GC_BGD
    gc[-max(2, m // 2):, :] = cv2.GC_BGD
    cv2.setRNGSeed(11)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    try:
        cv2.grabCut(crop, gc, None, bgd, fgd, 3, cv2.GC_INIT_WITH_MASK)
    except cv2.error:
        return None, {"motivo": "grabcut_fallo"}
    alpha = np.where((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(alpha, connectivity=8)
    if n > 1:
        mayor = 1 + int(np.argmax(stats[1:, 4]))
        alpha = np.where(lab == mayor, 255, 0).astype(np.uint8)
    cov = float(alpha.mean()) / 255.0
    ys, xs = np.where(alpha > 0)
    if len(xs) == 0:
        return None, {"motivo": "alfa_vacio", "cobertura": 0.0}
    bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
    mx, my = int(0.05 * (bx1 - bx0 + 1)), int(0.05 * (by1 - by0 + 1))
    bx0, by0 = max(0, bx0 - mx), max(0, by0 - my)
    bx1, by1 = min(cw - 1, bx1 + mx), min(ch - 1, by1 + my)
    rgba = cv2.cvtColor(crop[by0:by1 + 1, bx0:bx1 + 1], cv2.COLOR_BGR2BGRA)
    a = cv2.GaussianBlur(alpha[by0:by1 + 1, bx0:bx1 + 1].astype(np.float32) / 255.0, (3, 3), 0)
    rgba[:, :, 3] = (a * 255).astype(np.uint8)
    return rgba, {"cobertura": round(cov, 3), "recorte": [int(bx0), int(by0), int(bx1 - bx0 + 1), int(by1 - by0 + 1)],
                  "escala_analisis": round(esc, 3)}


def limpiar_fondo_conectado(rgba: np.ndarray) -> np.ndarray:
    """Quita restos de fondo uniforme que tocan el borde (círculos/paneles).

    Dentro del recorte ya extraído, cualquier región de color plano conectada al
    borde se hace transparente. Si eso destruye el sujeto, se descarta el cambio.
    """
    bgr = rgba[:, :, :3]
    alpha = rgba[:, :, 3]
    h, w = alpha.shape
    if h < 8 or w < 8:
        return rgba
    base = float((alpha > 40).mean())
    semillas = []
    for x in range(0, w, max(4, w // 24)):
        semillas += [(x, 0), (x, h - 1)]
    for y in range(0, h, max(4, h // 24)):
        semillas += [(0, y), (w - 1, y)]
    trabajo = bgr.copy()
    malla = np.zeros((h + 2, w + 2), np.uint8)
    marcas = np.zeros((h, w), np.uint8)
    for (sx, sy) in semillas:
        if marcas[sy, sx] or alpha[sy, sx] < 40:
            continue
        m2 = malla.copy()
        diff = (int(trabajo[sy, sx, 0]), int(trabajo[sy, sx, 1]), int(trabajo[sy, sx, 2]))
        n, im2, malla2, _ = cv2.floodFill(trabajo, m2, (sx, sy), (0, 0, 0),
                                          (16, 16, 16), (16, 16, 16), 4)
        if n > 0.03 * h * w:
            zona = np.zeros((h, w), np.uint8)
            zona[malla2[1:-1, 1:-1] > 0] = 1
            marcas |= zona
    if marcas.sum() == 0:
        return rgba
    propuesta = alpha.copy()
    propuesta[marcas > 0] = 0
    if (propuesta > 40).mean() < 0.55 * base:   # se comió al personaje: no tocar
        return rgba
    out = bgr[:, :, :3].copy()
    rgba2 = cv2.cvtColor(out, cv2.COLOR_BGR2BGRA) if bgr.shape[2] == 3 else rgba.copy()
    rgba2[:, :, 3] = propuesta
    return rgba2


def dhash(img: np.ndarray) -> bytes:
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, (9, 8), interpolation=cv2.INTER_AREA)
    return np.packbits((g[:, 1:] > g[:, :-1]).astype(np.uint8).flatten()).tobytes()


def hamming(a: bytes, b: bytes) -> int:
    return bin(int.from_bytes(a, "big") ^ int.from_bytes(b, "big")).count("1")


def guardar_png(rgba: np.ndarray, rel: str, thumb_dir: Path, thumb_rel: str) -> None:
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(p), rgba)
    t = max(rgba.shape[0], rgba.shape[1])
    th = cv2.resize(rgba, (max(1, rgba.shape[1] * 256 // t), max(1, rgba.shape[0] * 256 // t)),
                    interpolation=cv2.INTER_AREA)
    thumb_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUT / thumb_rel), th)


def galeria(elementos: list[dict]) -> None:
    cards = []
    for e in elementos:
        est = "⚠ PENDIENTE DE REVISIÓN HUMANA" if e["estado"] != "auto" else "✔ auto"
        dup = f" · DUP #{e['duplicado_de']}" if e["duplicado_de"] else ""
        cards.append(
            f'<div class="card {"warn" if e["estado"] != "auto" else ""}">'
            f'<img src="{e["thumb"]}" loading="lazy">'
            f'<div class="info"><b>{e["nombre"]}</b> <span class="cat">{e["categoria"]}</span><br>'
            f'<span class="rot">«{e["rotulo"]}»</span><br>'
            f'{e["ancho"]}x{e["alto"]}px · conf {e["confianza"]}{dup}<br>'
            f'<span class="st">{est}</span><br><span class="src">{e["imagen_origen"]}</span></div></div>')
    html = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>QA Sprites Avatar 4F</title><style>
body{background:#111;color:#ddd;font-family:system-ui;max-width:1280px;margin:24px auto;padding:0 16px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}
.card{background:#1b1b1f;border:1px solid #333;border-radius:10px;overflow:hidden}
.card img{width:100%;height:220px;object-fit:contain;background:repeating-conic-gradient(#2a2a2e 0 25%,#222 0 50%) 0 0/24px 24px}
.info{padding:8px 10px;font-size:.8rem;line-height:1.4}
.warn{border-color:#a33}.st{color:#ffb84d}.src{color:#777;font-size:.7rem}.cat{color:#0f0;font-size:.7rem}
.rot{color:#8cf;font-size:.72rem} h1{color:#0f0} small{color:#888}</style></head><body>
<h1>Galería QA — Sprites Avatar 4F</h1>
<small>Tablero gris = transparencia. Los ⚠ requieren revisión/renombrado humano.
manifest.json es la fuente de verdad del inventario.</small>
<div class="grid">%CARDS%</div></body></html>"""
    (QA / "galeria.html").write_text(html.replace("%CARDS%", "".join(cards)), encoding="utf-8")


def procesar(imagenes: list[Path], forzar_ocr: bool = False) -> None:
    QA.mkdir(parents=True, exist_ok=True)
    (QA / "thumbs").mkdir(parents=True, exist_ok=True)
    elementos: list[dict] = []
    hashes: list[bytes] = []
    for src in imagenes:
        print(f"== {src.name}")
        hoja, esc = cargar_hoja(src)
        hh, ww = hoja.shape[:2]
        items = es_util(ocr_hoja(src, forzar_ocr))
        bloques = agrupar_bloques(items)
        print(f"   rótulos: {len(bloques)}")
        nuevos = 0
        regiones_usadas: list[tuple[int, int, int, int]] = []

        def iou(a, b):
            ax2, ay2, bx2, by2 = a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3]
            ox = max(0, min(ax2, bx2) - max(a[0], b[0]))
            oy = max(0, min(ay2, by2) - max(a[1], b[1]))
            inter = ox * oy
            return inter / max(1, a[2] * a[3] + b[2] * b[3] - inter)

        if not [b for b in bloques if not descartar(b)]:
            # hoja de una sola vista (sin rótulos): elemento = personaje completo
            stem = src.stem.lower()
            pistas = ("frente", "frontal", "dorso", "espalda", "perfil", "pose", "vista")
            if any(p in stem for p in pistas):
                canon, cat, tipo = mapear(stem.replace("_", " ").replace("-", " "))
                region = (int(ww * 0.04), int(hh * 0.04), int(ww * 0.92), int(hh * 0.92))
                rgba, meta = extraer_alfa(hoja, region)
                ok = rgba is not None and meta.get("cobertura", 0) > 0.10
                if rgba is None:
                    rgba = cv2.cvtColor(hoja, cv2.COLOR_BGR2BGRA)
                    rgba[:, :, 3] = 255
                    meta = {}
                elif ok:
                    rgba = limpiar_fondo_conectado(rgba)
                idx = len(elementos) + 1
                rel = f"{cat}/{canon}.png"
                if (OUT / rel).exists() or any(e["ruta"] == rel for e in elementos):
                    rel = f"{cat}/{canon}_{idx}.png"
                if not ok:
                    rel = f"{cat}/_revision_{idx}_{canon}.png"
                trel = f"_qa/thumbs/{Path(rel).stem}_{idx}.png"
                guardar_png(rgba, rel, QA / "thumbs", trel)
                hsh = dhash(rgba)
                dup = next((e["id"] for e, x in zip(elementos, hashes) if hamming(hsh, x) < 5), None)
                hashes.append(hsh)
                elementos.append({
                    "id": idx, "nombre": canon, "rotulo": f"(sin rótulo) {src.name}",
                    "categoria": cat if ok else "pendiente_revision", "tipo_animacion": tipo,
                    "imagen_origen": src.name, "coords_rotulo": None,
                    "region_busqueda": {"x": region[0], "y": region[1], "w": region[2], "h": region[3]},
                    "recorte": meta.get("recorte"), "cobertura_alfa": meta.get("cobertura"),
                    "ancho": int(rgba.shape[1]), "alto": int(rgba.shape[0]),
                    "anchor": {"poses": [0.5, 1.0], "movimientos": [0.5, 1.0],
                               "expresiones": [0.5, 0.55], "gestos": [0.5, 0.5],
                               "acciones": [0.5, 0.85]}.get(cat, [0.5, 0.5]),
                    "estado": "auto" if ok else "pendiente_revision",
                    "confianza": 0.8 if ok else 0.3, "duplicado_de": dup, "ruta": rel,
                    "thumb": trel, "extractor": "extract_sprites_4f v2 (vista única)",
                    "ts": datetime.now().isoformat(timespec="seconds"),
                })
                print("   -> 1 elemento (vista única, sin rótulos)")
            continue

        for b in bloques:
            if descartar(b):
                continue
            if b["x1"] - b["x0"] > 0.55 * ww:      # rótulo que cruza la hoja = título
                continue
            cat, canon, tipo = mapear(b["nombre"])
            region = region_elemento(b, bloques, (hh, ww))
            if region[3] < 16 or region[2] < 16:
                continue
            if any(iou(region, r) > 0.62 for r in regiones_usadas):
                continue
            regiones_usadas.append(region)
            rgba, meta = extraer_alfa(hoja, region)
            # si el sujeto toca el borde de la región, ampliar y reintentar
            for _ in range(2):
                rec = (meta or {}).get("recorte")
                if not rec:
                    break
                toca_arriba = rec[1] <= 2
                toca_izq = rec[0] <= 2
                x, y, w, h = region
                toca_der = rec[0] + rec[2] >= w - 2
                if not (toca_arriba or toca_izq or toca_der):
                    break
                if toca_arriba:
                    y = max(0, y - int(h * 0.45))
                if toca_izq:
                    x = max(0, x - int(w * 0.22))
                    w = w + int(region[2] * 0.22)
                if toca_der:
                    w = min(ww - x, w + int(region[2] * 0.22))
                region = (x, y, w, max(16, region[1] + region[3] - y))
                nuevo, meta2 = extraer_alfa(hoja, region)
                if nuevo is not None:
                    rgba, meta = nuevo, meta2
                else:
                    break
            ok = rgba is not None and meta.get("cobertura", 0) > 0.10
            conf = round(min(0.95, 0.45 + 0.5 * min(1.0, meta.get("cobertura", 0) / 0.35)), 2) if ok else 0.3
            if rgba is None:
                x, y, w, h = region
                rgba = cv2.cvtColor(hoja[y:y + h, x:x + w], cv2.COLOR_BGR2BGRA)
                rgba[:, :, 3] = 255
            elif ok:
                rgba = limpiar_fondo_conectado(rgba)
            # geometría: una "cabeza" cuadrada no puede ser pose de cuerpo entero
            ar = rgba.shape[1] / max(rgba.shape[0], 1)
            if 0.55 <= ar <= 1.75 and rgba.shape[0] < 0.22 * hh and cat == "poses":
                cat, tipo = "expresiones", "expresion"
                canon = f"perfil_{canon}" if "perfil" in canon else canon
            idx = len(elementos) + 1
            rel = f"{cat}/{canon}.png"
            if (OUT / rel).exists() or any(e["ruta"] == rel for e in elementos):
                rel = f"{cat}/{canon}_{idx}.png"
            rl = f"{cat}/_revision_{idx}_{canon}.png"
            if not ok:
                rel = rl
            trel = f"_qa/thumbs/{Path(rel).stem}_{idx}.png"
            guardar_png(rgba, rel, QA / "thumbs", trel)
            hsh = dhash(rgba)
            dup = next((e["id"] for e, x in zip(elementos, hashes) if hamming(hsh, x) < 5), None)
            hashes.append(hsh)
            elementos.append({
                "id": idx,
                "nombre": canon if ok else f"pendiente_{canon}",
                "rotulo": b["texto_completo"][:120],
                "categoria": cat if ok else "pendiente_revision",
                "tipo_animacion": tipo,
                "imagen_origen": src.name,
                "coords_rotulo": {"x": b["x0"], "y": b["y0"],
                                  "w": b["x1"] - b["x0"], "h": b["y1"] - b["y0"]},
                "region_busqueda": {"x": region[0], "y": region[1], "w": region[2], "h": region[3]},
                "recorte": meta.get("recorte"),
                "cobertura_alfa": meta.get("cobertura"),
                "ancho": int(rgba.shape[1]), "alto": int(rgba.shape[0]),
                "anchor": {"poses": [0.5, 1.0], "movimientos": [0.5, 1.0],
                           "expresiones": [0.5, 0.55], "gestos": [0.5, 0.5],
                           "acciones": [0.5, 0.85]}.get(cat, [0.5, 0.5]),
                "estado": "auto" if ok else "pendiente_revision",
                "confianza": conf,
                "duplicado_de": dup,
                "ruta": rel,
                "thumb": trel,
                "extractor": "extract_sprites_4f v2 (ocr+grabcut)",
                "ts": datetime.now().isoformat(timespec="seconds"),
            })
            nuevos += 1
        print(f"   -> {nuevos} elementos")

    resumen: dict[str, int] = {}
    for e in elementos:
        resumen[e["categoria"]] = resumen.get(e["categoria"], 0) + 1
    manifest = {
        "avatar": "4F Pulso Curioso",
        "version": 2,
        "generado": datetime.now().isoformat(timespec="seconds"),
        "categorias": {"poses": "vistas completas estáticas", "movimientos": "movimientos dinámicos",
                       "expresiones": "cabezas/rostros", "gestos": "manos aisladas",
                       "acciones": "objetos/interfaz", "pendiente_revision": "requiere revisión humana"},
        "resumen": resumen,
        "pendientes": sum(1 for e in elementos if e["estado"] != "auto"),
        "elementos": elementos,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    galeria(elementos)
    print(f"OK: {len(elementos)} elementos ({manifest['pendientes']} pendientes) -> {OUT/'manifest.json'}")


def fuentes_por_defecto() -> list[Path]:
    """Hojas de referencia en assets/ + vistas sueltas nuevas en avatar_4f/."""
    hojas = sorted(ROOT.glob("assets/Gemini_Generated_Image_*.jpeg"))
    hojas = [p for p in hojas if "mousob" not in p.stem]   # logo circular, no es hoja
    vistas = sorted(p for p in ROOT.glob("avatar_4f/*.jpeg")
                    if any(k in p.stem.lower() for k in
                           ("frente", "dorso", "perfil", "frontal", "espalda")))
    return hojas + vistas


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    forzar = "--forzar-ocr" in sys.argv
    rutas = [Path(a) for a in args] or fuentes_por_defecto()
    procesar(rutas, forzar)
