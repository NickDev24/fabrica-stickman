# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Genera el GLB del personaje "cloak man" (victoriano/gótico) con cara y rig por NODOS.

A diferencia de tools/make_proxy_glb.py (densidad de malla para el benchmark de FASE 0),
este archivo produce un actor presentable: cada parte de la cara y del cuerpo es un nodo
glTF nombrado, así que el motor puede moverlo sin skinning ni pesos de vértice.

Salidas:
  <glb>                          el personaje
  <rigmap>                       mapa de rig (nodos + visemas) que consume el motor
  el sidecar state/personajes/rig_<stem>.json que lee pipeline/stages/avatar.py

Uso:
  python3 tools/make_character_glb.py assets/characters/cloakman.glb

No requiere red ni dependencias: escribe el contenedor glTF 2.0 binario a mano.
"""
from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

# ----------------------------------------------------------------------------- primitivas
def _restar(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def _producto(p, q):
    return (p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0])


def winding_correcto(verts, faces, centro=None):
    """Cara convexa: si la normal apunta hacia adentro, se invierte el orden de índices.

    Three.js renderiza solo la cara frontal; un winding invertido hace que la oreja o el
    labio desaparezcan según el ángulo de cámara (y el frame sale "mordido").
    """
    if centro is None:
        centro = tuple(sum(v[k] for v in verts) / len(verts) for k in range(3))
    out = []
    for a, b, c in faces:
        pa, pb, pc = verts[a], verts[b], verts[c]
        n = _producto(_restar(pb, pa), _restar(pc, pa))
        cx = (pa[0] + pb[0] + pc[0]) / 3 - centro[0]
        cy = (pa[1] + pb[1] + pc[1]) / 3 - centro[1]
        cz = (pa[2] + pb[2] + pc[2]) / 3 - centro[2]
        if n[0] * cx + n[1] * cy + n[2] * cz < 0:
            out.append((a, c, b))
        else:
            out.append((a, b, c))
    return out


def normals(verts, faces):
    acc = [[0.0, 0.0, 0.0] for _ in verts]
    for a, b, c in faces:
        pa, pb, pc = verts[a], verts[b], verts[c]
        cr = _producto(_restar(pb, pa), _restar(pc, pa))
        for i in (a, b, c):
            for k in range(3):
                acc[i][k] += cr[k]
    out = []
    for v in acc:
        m = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0
        out.append((v[0] / m, v[1] / m, v[2] / m))
    return out


def revolucion(perfil, seg=24, escala=(1.0, 1.0, 1.0)):
    """Superficie de revolución alrededor de Y. perfil = [(radio, y), ...] de un extremo al otro.

    Radio 0 en un extremo cierra la pieza (cono/esfera).
    """
    verts, faces = [], []
    for (r, y) in perfil:
        rx, ry, rz = r * escala[0], y * escala[1], r * escala[2]
        for j in range(seg):
            th = 2 * math.pi * j / seg
            verts.append((rx * math.cos(th), ry, rz * math.sin(th)))
    for i in range(len(perfil) - 1):
        for j in range(seg):
            a, b = i * seg + j, i * seg + (j + 1) % seg
            c, d = (i + 1) * seg + j, (i + 1) * seg + (j + 1) % seg
            faces += [(a, c, b), (b, c, d)]
    return verts, winding_correcto(verts, faces)


def malla(perfil, seg=24, escala=(1.0, 1.0, 1.0)):
    verts, faces = revolucion(perfil, seg, escala)
    return verts, normals(verts, faces), faces


def esfera(r, seg=20, ring=12, escala=(1.0, 1.0, 1.0)):
    perfil = [(r * math.sin(math.pi * i / ring), r * math.cos(math.pi * i / ring))
              for i in range(ring + 1)]
    verts, faces = revolucion(perfil, seg, escala)
    return verts, normals(verts, faces), faces


def caja(w, h, d):
    x, y, z = w / 2, h / 2, d / 2
    caras = [(((-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z))),
             ((x, -y, -z), (-x, -y, -z), (-x, y, -z), (x, y, -z)),
             ((x, -y, z), (x, -y, -z), (x, y, -z), (x, y, z)),
             ((-x, -y, -z), (-x, -y, z), (-x, y, z), (-x, y, -z)),
             ((-x, y, z), (x, y, z), (x, y, -z), (-x, y, -z)),
             ((x, -y, z), (-x, -y, z), (-x, -y, -z), (x, -y, -z))]
    verts, faces, k = [], [], 0
    for quad in caras:
        verts += list(quad)
        faces += [(k, k + 1, k + 2), (k, k + 2, k + 3)]
        k += 4
    return verts, normals(verts, faces), faces


def cono_z(r, h, seg=16):
    """Cono con el ápice mirando a +Z (nariz): se construye la geometría orientada, no el nodo."""
    verts = [(0.0, 0.0, h)]
    for j in range(seg):
        th = 2 * math.pi * j / seg
        verts.append((r * math.cos(th), r * math.sin(th), 0.0))
    verts.append((0.0, 0.0, 0.0))
    base, caras = len(verts) - 1, []
    for j in range(seg):
        a, b = 1 + j, 1 + (j + 1) % seg
        caras += [(0, a, b), (base, b, a)]
    faces = winding_correcto(verts, caras)
    return verts, normals(verts, faces), faces


# ----------------------------------------------------------------------------- personaje
# (nombre, padre, traslación, geometría, material).  geometría=None -> nodo puro (pivote).
#
# Silueta: gabardina larga victoriana CEÑIDA (no campana: una capa ancha se come el torso y
# el personaje queda como un peón de ajedrez), hombros y brazos POR FUERA del paño, cuello
# alto rígido detrás de la nuca y cabeza grande para que la cara se lea a 540p.
def partes():
    P = []
    add = lambda *a: P.append(a)

    add("personaje", None, (0, 0, 0), None, "raiz")
    add("cuerpo", "personaje", (0, 0, 0), None, None)

    # Abrigo: recto desde el hombro hasta el suelo, apenas evasé. El borde nace ANCHO para
    # que el hombro no asome como una bola suelta sobre el paño.
    add("abrigo", "cuerpo", (0, 0.0, -0.01),
        malla([(0.215, 1.50), (0.225, 1.25), (0.235, 0.90), (0.265, 0.42), (0.315, 0.0)], seg=28),
        "capa")
    add("abrigo_borde", "cuerpo", (0, 0.06, -0.01),
        malla([(0.320, 0.0), (0.300, 0.06)], seg=28), "forro")
    # Capa al hombro: paño plano detrás, asoma como alas en el plano medio (silueta gótica).
    add("capa_trasera", "cuerpo", (0, 0.86, -0.185), caja(0.56, 1.34, 0.045), "capa")

    add("chest", "cuerpo", (0, 1.34, 0), None, None)
    add("torso", "chest", (0, 0.02, 0),
        malla([(0.155, 0.16), (0.185, 0.04), (0.175, -0.14), (0.15, -0.30)], seg=22), "tela")
    # Cuello alto: une torso y cabeza SIN hueco (el cono anterior dejaba ver el fondo).
    add("cuello_v", "chest", (0, 0.16, -0.02),
        malla([(0.105, 0.26), (0.145, 0.10), (0.175, 0.0)], seg=20), "solapa")
    add("cuello_piel", "chest", (0, 0.16, 0.01), malla([(0.062, 0.24), (0.070, 0.0)], seg=14), "piel")
    # (Sin solapas sueltas: dos cajas sobre un paño cilíndrico leían como stickers rojos.)

    for lad, s in (("L", -1), ("R", 1)):
        add(f"hombro{lad}", "chest", (s * 0.185, 0.12, 0), esfera(0.095, escala=(1, 0.85, 0.9)), "tela")
        add(f"brazo{lad}", "chest", (s * 0.215, 0.06, 0),
            malla([(0.048, -0.32), (0.058, -0.14), (0.070, 0.0)], seg=16), "tela")
        add(f"codo{lad}", f"brazo{lad}", (0, -0.32, 0),
            malla([(0.040, -0.28), (0.048, -0.12), (0.052, 0.0)], seg=16), "tela")
        add(f"mano{lad}", f"codo{lad}", (0, -0.28, 0), esfera(0.052, escala=(0.85, 1.15, 0.9)), "piel")

    add("neck", "chest", (0, 0.26, 0), None, None)
    add("head", "neck", (0, 0.14, 0), None, None)
    add("craneo", "head", (0, 0.13, 0), esfera(0.162, escala=(1.0, 1.12, 0.98)), "piel")

    # Mandíbula como pivote: mentón y boca cuelgan de ella, un solo grado de libertad
    # para el visema. El mentón va PEGADO al cráneo, no protruyendo (hocico).
    add("mandibula", "head", (0, 0.055, 0.01), None, None)
    add("menton", "mandibula", (0, -0.035, 0.085), esfera(0.075, escala=(0.80, 0.48, 0.55)), "piel")
    add("boca", "mandibula", (0, 0.005, 0.128), esfera(0.030, escala=(1.0, 0.22, 0.22)), "boca")
    add("labio_sup", "mandibula", (0, 0.026, 0.126), caja(0.062, 0.011, 0.016), "labio")

    # Cabello: casquete liso + tupé alto (esferas achatadas, nunca cajas: un box flota
    # como un ladrillo sobre la frente).
    add("pelo", "head", (0, 0.215, -0.012), esfera(0.162, escala=(1.0, 0.55, 1.0)), "pelo")
    add("peinado_alto", "head", (0, 0.285, 0.045), esfera(0.135, escala=(0.85, 0.42, 0.72)), "pelo")
    add("patilla_izq", "head", (-0.145, 0.09, 0.02), caja(0.018, 0.06, 0.04), "pelo")
    add("patilla_der", "head", (0.145, 0.09, 0.02), caja(0.018, 0.06, 0.04), "pelo")

    for lad, s in (("L", -1), ("R", 1)):
        add(f"ojo{lad}", "head", (s * 0.058, 0.145, 0.128), esfera(0.030, escala=(1, 1, 0.7)), "blanco")
        add(f"iris{lad}", f"ojo{lad}", (0, 0, 0.019), esfera(0.0145, escala=(1, 1, 0.62)), "iris")
        add(f"ceja{lad}", "head", (s * 0.060, 0.200, 0.135), caja(0.062, 0.016, 0.018), "pelo")
    add("nariz", "head", (0, 0.105, 0.145), cono_z(0.019, 0.048), "piel")
    return P


MATERIALES = {
    "piel":    {"base": (0.80, 0.68, 0.60, 1), "rough": 0.72, "metal": 0.0},
    "pelo":    {"base": (0.055, 0.05, 0.055, 1), "rough": 0.55, "metal": 0.1},
    "tela":    {"base": (0.085, 0.088, 0.105, 1), "rough": 0.88, "metal": 0.0},
    "capa":    {"base": (0.062, 0.062, 0.078, 1), "rough": 0.92, "metal": 0.0},
    "forro":   {"base": (0.20, 0.055, 0.07, 1), "rough": 0.75, "metal": 0.0},
    "solapa":  {"base": (0.10, 0.10, 0.12, 1), "rough": 0.6, "metal": 0.15},
    "blanco":  {"base": (0.92, 0.93, 0.95, 1), "rough": 0.35, "metal": 0.0},
    "iris":    {"base": (0.28, 0.62, 0.60, 1), "rough": 0.25, "metal": 0.0, "emis": (0.05, 0.16, 0.15)},
    "boca":    {"base": (0.055, 0.028, 0.035, 1), "rough": 0.5, "metal": 0.0},
    "labio":   {"base": (0.44, 0.24, 0.25, 1), "rough": 0.6, "metal": 0.0},
    "raiz":    None,
}

# Mapa de rig: parámetro del actor -> [[nodo, operación, eje, factor, modo], ...]
#   rot  -> grados por unidad de parámetro      pos -> metros por unidad (sobre la base)
#   esc  -> escala relativa (base + v*factor)   modo "fija" -> escala = v
RIG_NODOS = {
    "cabeza_pitch":   [["head", "rot", "x", 1.0]],
    "cabeza_yaw":     [["head", "rot", "y", 1.0]],
    "cabeza_roll":    [["head", "rot", "z", 1.0]],
    "postura_roll":   [["chest", "rot", "z", 0.55]],
    "peso":           [["chest", "rot", "x", 0.5]],
    "mirada_dx":      [["ojoL", "rot", "y", 16], ["ojoR", "rot", "y", 16]],
    "mirada_dy":      [["ojoL", "rot", "x", 11], ["ojoR", "rot", "x", 11]],
    "ojo_apertura":   [["ojoL", "esc", "y", 1.0, "fija"], ["ojoR", "esc", "y", 1.0, "fija"]],
    "ceja_izq":       [["cejaL", "pos", "y", 0.022], ["cejaL", "rot", "z", 9]],
    "ceja_der":       [["cejaR", "pos", "y", 0.022], ["cejaR", "rot", "z", -9]],
    "brazo_izq":      [["brazoL", "rot", "x", -42]],
    "brazo_der":      [["brazoR", "rot", "x", -42]],
    "codo_izq":       [["codoL", "rot", "x", -55]],
    "codo_der":       [["codoR", "rot", "x", -55]],
    "manos_levantadas": [["brazoL", "rot", "z", 16], ["brazoR", "rot", "z", -16]],
    "boca_base":      [["mandibula", "rot", "x", 10]],
}
VISEMA_NODOS = [["mandibula", "rot", "x", 17], ["boca", "esc", "y", 1.7]]
RESPIRACION_NODO = "torso"
CABEZA_NODO = "head"


# ----------------------------------------------------------------------------- glTF
def construir(glb_path: Path, rig_path: Path):
    P = partes()
    bloques, offset = [], 0

    def push(data: bytes):
        nonlocal offset
        blob = data + b"\x00" * ((-len(data)) % 4)
        bloques.append(blob)
        start = offset
        offset += len(blob)
        return start, len(data)

    bvs, acc = [], []

    def bufferview(off, ln, target=None):
        d = {"buffer": 0, "byteOffset": off, "byteLength": ln}
        if target is not None:
            d["target"] = target
        bvs.append(d)
        return len(bvs) - 1

    def accessor(bv, comp, ctype, count, amin=None, amax=None, target=None):
        d = {"bufferView": bv, "componentType": comp, "type": ctype, "count": count}
        if amin is not None:
            d["min"], d["max"] = amin, amax
        if target is not None:
            d["target"] = target
        acc.append(d)
        return len(acc) - 1

    meshes, nodes, nombre_ind = [], [], {}
    mat_index = {k: i for i, k in enumerate([n for n, v in MATERIALES.items() if v is not None])}
    for i, (nombre, padre, pos, geom, mat) in enumerate(P):
        node = {"name": nombre, "translation": list(pos)}
        nombre_ind[nombre] = len(nodes)
        nodes.append(node)
        if padre is not None:
            nodes[nombre_ind[padre]].setdefault("children", []).append(len(nodes) - 1)
        if geom is None:
            continue
        verts, nrm, faces = geom
        off_p, len_p = push(b"".join(struct.pack("<3f", *v) for v in verts))
        off_n, len_n = push(b"".join(struct.pack("<3f", *v) for v in nrm))
        off_i, len_i = push(b"".join(struct.pack("<3H", *f) for f in faces))
        mn = [min(v[k] for v in verts) for k in range(3)]
        mx = [max(v[k] for v in verts) for k in range(3)]
        a_p = accessor(bufferview(off_p, len_p, 34962), 5126, "VEC3", len(verts), mn, mx, 34962)
        a_n = accessor(bufferview(off_n, len_n, 34962), 5126, "VEC3", len(verts), target=34962)
        a_i = accessor(bufferview(off_i, len_i, 34963), 5123, "SCALAR", len(faces) * 3, target=34963)
        meshes.append({"name": nombre, "primitives": [{
            "attributes": {"POSITION": a_p, "NORMAL": a_n}, "indices": a_i,
            "material": mat_index[mat]}]})
        node["mesh"] = len(meshes) - 1

    mats = []
    for nombre, spec in MATERIALES.items():
        if spec is None:
            continue
        m = {"name": nombre, "pbrMetallicRoughness": {
            "baseColorFactor": list(spec["base"]),
            "metallicFactor": spec["metal"], "roughnessFactor": spec["rough"]}}
        if spec.get("emis"):
            m["emissiveFactor"] = list(spec["emis"])
        mats.append(m)

    gltf = {
        "asset": {"version": "2.0", "generator": "make_character_glb"},
        "scene": 0, "scenes": [{"nodes": [0]}], "nodes": nodes, "meshes": meshes,
        "materials": mats, "accessors": acc, "bufferViews": bvs,
    }
    binario = b"".join(bloques)
    gltf["buffers"] = [{"byteLength": len(binario)}]

    js = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    js += b" " * ((-len(js)) % 4)
    chunk_json = struct.pack("<II", len(js), 0x4E4F534A) + js
    bn = binario + b"\x00" * ((-len(binario)) % 4)
    chunk_bin = struct.pack("<II", len(bn), 0x004E4942) + bn
    header = struct.pack("<III", 0x46546C67, 2, 12 + len(chunk_json) + len(chunk_bin))
    glb_path.parent.mkdir(parents=True, exist_ok=True)
    glb_path.write_bytes(header + chunk_json + chunk_bin)

    crudo = glb_path.read_bytes()
    magic, ver, total = struct.unpack("<III", crudo[:12])
    assert (magic, ver, total) == (0x46546C67, 2, len(crudo)), "cabecera GLB inconsistente"
    assert gltf["buffers"][0].get("uri") is None, "el buffer de un GLB no declara uri"
    for m in meshes:
        for k, a in m["primitives"][0]["attributes"].items():
            assert 0 <= a < len(acc), f"{m['name']}.{k} apunta accessor inexistente"

    rig_map = {"nodos": RIG_NODOS, "visema_nodos": VISEMA_NODOS,
               "cabeza_nodo": CABEZA_NODO, "respiracion_nodo": RESPIRACION_NODO,
               "morfos": {}, "huesos": {}, "visema_morphs": []}
    rig_path.parent.mkdir(parents=True, exist_ok=True)
    rig_path.write_text(json.dumps(rig_map, ensure_ascii=False), encoding="utf-8")

    nv = sum(len(p[3][0]) for p in P if p[3])
    nt = sum(len(p[3][2]) for p in P if p[3])
    print(f"{glb_path}: {len(meshes)} partes, {nv} vértices, {nt} triángulos, "
          f"{glb_path.stat().st_size / 1e6:.2f} MB | rig: {len(RIG_NODOS)} parámetros")
    return gltf, rig_map


def main(argv):
    glb = Path(argv[0]) if argv else Path("assets/characters/cloakman.glb")
    rig = Path(argv[1]) if len(argv) > 1 else Path("state/personajes") / f"rig_{glb.stem}.json"
    construir(glb, rig)


if __name__ == "__main__":
    main(sys.argv[1:])
