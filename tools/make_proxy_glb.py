# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Genera un GLB de prueba REPRESENTATIVO (no es el avatar final) para el gate de viabilidad.

Medir el render de un avatar GLB en CPU sin un GLB disponible sería una suposición. Este script
arma un glTF binario con la complejidad que tendrá "cloak man": malla indexada de ~20k triángulos,
morph targets de boca (visemas) y un esqueleto con skinning, para que el benchmark mida también
las rutas que usa el motor (morphTargetInfluences y rotación de huesos vía rig_map).

Uso: python tools/make_proxy_glb.py /tmp/proxy_cloak.glb
"""
from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

# ---------------------------------------------------------------- icosaedro subdividido
def icosaedro():
    t = (1.0 + math.sqrt(5.0)) / 2.0
    v = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0),
         (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
         (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    v = [tuple(c / math.sqrt(sum(x * x for x in p)) for c in p) for p in v]
    f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
         (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
         (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
         (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    return list(v), list(f)


def subdividir(nivel):
    verts, faces = icosaedro()
    for _ in range(nivel):
        cache = {}

        def medio(a, b):
            key = (min(a, b), max(a, b))
            if key not in cache:
                p, q = verts[a], verts[b]
                m = tuple((p[i] + q[i]) / 2 for i in range(3))
                n = math.sqrt(sum(c * c for c in m))
                verts.append(tuple(c / n for c in m))
                cache[key] = len(verts) - 1
            return cache[key]

        nuevas = []
        for a, b, c in faces:
            ab, bc, ca = medio(a, b), medio(b, c), medio(c, a)
            nuevas += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        faces = nuevas
    return verts, faces


def escultor(puntos, caras):
    """Deforma la esfera en una figura con capa: cabeza, torso acampanado, base.

    No busca belleza: busca densidad de malla y cobertura de píxeles parecida a la real.
    """
    out = []
    for (x, y, z) in puntos:
        h = (y + 1) / 2.0                      # 0 abajo .. 1 arriba
        if h > 0.78:                            # cabeza
            r = 0.26 * math.sqrt(max(0.0, 1 - ((h - 0.78) / 0.22) ** 2))
            s = r / max(1e-6, math.sqrt(x * x + z * z))
            nx, nz = x * s * 1.0, z * s * 1.0
            ny = 0.78 + (h - 0.78) * 0.5
        elif h > 0.45:                          # torso
            s = 0.34
            nx, nz = x * s, z * s
            ny = h * 1.6
        else:                                   # capa: campana ancha
            w = 0.45 + 0.85 * (0.45 - h)
            s = w / max(1e-6, math.sqrt(x * x + z * z))
            nx, nz = x * s, z * s
            ny = h * 1.6
        out.append((nx, ny - 0.8, nz))
    return out


def main(salida: str):
    verts, faces = subdividir(5)                # 10242 verts / 20480 tris
    P = escultor(verts, faces)
    n = len(P)

    # normales por acumulación en vértice
    N = [[0.0, 0.0, 0.0] for _ in range(n)]
    for a, b, c in faces:
        pa, pb, pc = P[a], P[b], P[c]
        u = [pb[i] - pa[i] for i in range(3)]
        w = [pc[i] - pa[i] for i in range(3)]
        cr = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]]
        for idx in (a, b, c):
            for i in range(3):
                N[idx][i] += cr[i]
    norm = []
    for v in N:
        m = math.sqrt(sum(c * c for c in v)) or 1.0
        norm.append((v[0] / m, v[1] / m, v[2] / m))

    # morph targets: 3 visemas (abrir boca, redondear, estirar) aplicados en la zona media
    def morph(modo):
        d = []
        for (x, y, z) in P:
            banda = math.exp(-((y + 0.15) ** 2) / 0.06)
            if z < 0:
                d.append((0.0, 0.0, 0.0))
                continue
            if modo == 0:
                d.append((0.0, -0.12 * banda, 0.05 * banda))
            elif modo == 1:
                d.append((0.03 * banda * math.copysign(1, x), -0.06 * banda, 0.04 * banda))
            else:
                d.append((0.0, 0.05 * banda, -0.03 * banda))
        return d

    morphs = [morph(i) for i in range(3)]

    # esqueleto de 4 huesos + skinning por altura
    huesos = ["hips", "spine", "chest", "head"]
    joints, weights = [], []
    for (x, y, z) in P:
        f = (y + 0.8) / 1.6
        i0 = min(3, max(0, int(f * 3.999)))
        i1 = min(3, i0 + 1)
        mix = (f * 3.999) - i0
        joints.append((i0, i1, 0, 0))
        weights.append((round(1 - mix, 4), round(mix, 4), 0.0, 0.0))

    # ------------------------------------------------------------- buffer binario
    bloques, offset = [], 0

    def push(data: bytes, align=4):
        nonlocal offset
        pad = (-len(data)) % align
        blob = data + b"\x00" * pad
        bloques.append(blob)
        start = offset
        offset += len(blob)
        return start, len(data)

    # el motor apunta la cámara a y≈1.0; el proxy se traslada al final (los deltas de
    # morph/normales son invariantes a traslación, así que se calculan sobre P sin desplazar)
    P = [(x, y + 0.9, z) for (x, y, z) in P]

    ident = struct.pack("<16f", *[1 if i % 5 == 0 else 0 for i in range(16)])
    ibm = ident * len(huesos)

    pos_bytes = b"".join(struct.pack("<3f", *p) for p in P)
    mn = [min(p[i] for p in P) for i in range(3)]
    mx = [max(p[i] for p in P) for i in range(3)]
    off_pos, len_pos = push(pos_bytes)

    nrm_bytes = b"".join(struct.pack("<3f", *v) for v in norm)
    off_nrm, len_nrm = push(nrm_bytes)

    idx_bytes = b"".join(struct.pack("<3H", *f) for f in faces)
    off_idx, len_idx = push(idx_bytes, 2)
    if len_idx % 4:
        pad = 4 - (len_idx % 4)
        bloques[-1] += b"\x00" * pad
        offset += pad

    jt_bytes = b"".join(struct.pack("<4H", *j) for j in joints)
    off_jt, len_jt = push(jt_bytes)

    wt_bytes = b"".join(struct.pack("<4f", *w) for w in weights)
    off_wt, len_wt = push(wt_bytes)

    offs_morph = []
    for m in morphs:
        b = b"".join(struct.pack("<3f", *d) for d in m)
        offs_morph.append(push(b))

    off_ibm, len_ibm = push(ibm)
    binario = b"".join(bloques)

    bvs = []

    def bufferview(off, ln, target=None):
        d = {"buffer": 0, "byteOffset": off, "byteLength": ln}
        if target is not None:
            d["target"] = target
        bvs.append(d)
        return len(bvs) - 1

    acc = []

    def accessor(bv, comp, ctype, count, amin=None, amax=None, target=None):
        d = {"bufferView": bv, "componentType": comp, "type": ctype, "count": count}
        if amin is not None:
            d["min"], d["max"] = amin, amax
        if target is not None:
            d["target"] = target
        acc.append(d)
        return len(acc) - 1

    bv_pos = bufferview(off_pos, len_pos, 34962)
    bv_nrm = bufferview(off_nrm, len_nrm, 34962)
    bv_idx = bufferview(off_idx, len_idx, 34963)
    bv_jt = bufferview(off_jt, len_jt, 34962)
    bv_wt = bufferview(off_wt, len_wt, 34962)
    bv_morph = [bufferview(o, l, 34962) for o, l in offs_morph]
    bv_ibm = bufferview(off_ibm, len_ibm)

    a_pos = accessor(bv_pos, 5126, "VEC3", n, mn, mx, 34962)
    a_nrm = accessor(bv_nrm, 5126, "VEC3", n, target=34962)
    a_idx = accessor(bv_idx, 5123, "SCALAR", len(faces) * 3, target=34963)
    a_jt = accessor(bv_jt, 5123, "VEC4", n, target=34962)
    a_wt = accessor(bv_wt, 5126, "VEC4", n, target=34962)
    def bounds(m):
        return ([min(d[i] for d in m) for i in range(3)], [max(d[i] for d in m) for i in range(3)])

    # glTF exige min/max en los accessors de morph target (POSITION deltas)
    a_morph = [accessor(b, 5126, "VEC3", n, *bounds(m), target=34962)
               for b, m in zip(bv_morph, morphs)]
    a_ibm = accessor(bv_ibm, 5126, "MAT4", len(huesos))

    # cadena de huesos: hips -> spine -> chest -> head
    nodos = []
    for i, nombre in enumerate(huesos):
        node = {"name": nombre, "translation": [0.0, 0.0 if i == 0 else 0.4, 0.0]}
        if i + 1 < len(huesos):
            node["children"] = [i + 1]
        nodos.append(node)
    nodos.append({"name": "cloak_proxy", "mesh": 0, "skin": 0})

    gltf = {
        "asset": {"version": "2.0", "generator": "make_proxy_glb"},
        "scene": 0,
        "scenes": [{"nodes": [0, len(nodos) - 1]}],
        "nodes": nodos,
        "meshes": [{
            "name": "cloak",
            "primitives": [{
                "attributes": {"POSITION": a_pos, "NORMAL": a_nrm, "JOINTS_0": a_jt, "WEIGHTS_0": a_wt},
                "indices": a_idx,
                "material": 0,
                "targets": [{"POSITION": a_morph[0]}, {"POSITION": a_morph[1]}, {"POSITION": a_morph[2]}],
            }],
            "extras": {"targetNames": ["mouthOpen", "mouthRound", "mouthWide"]},
        }],
        "materials": [{"name": "tela", "pbrMetallicRoughness": {
            "baseColorFactor": [0.11, 0.12, 0.15, 1.0], "metallicFactor": 0.0, "roughnessFactor": 0.7}}],
        "skins": [{"joints": list(range(len(huesos))), "skeleton": 0, "inverseBindMatrices": a_ibm}],
        "accessors": acc,
        "bufferViews": bvs,
        "buffers": [{"byteLength": len(binario)}],
    }

    js = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    js += b" " * ((-len(js)) % 4)
    chunk_json = struct.pack("<II", len(js), 0x4E4F534A) + js
    bn = binario + b"\x00" * ((-len(binario)) % 4)
    chunk_bin = struct.pack("<II", len(bn), 0x004E4942) + bn
    header = struct.pack("<III", 0x46546C67, 2, 12 + len(chunk_json) + len(chunk_bin))
    Path(salida).write_bytes(header + chunk_json + chunk_bin)

    # autovalidación: estos tres errores hacen que GLTFLoader falle con mensajes opacos
    crudo = Path(salida).read_bytes()
    m, v, total = struct.unpack("<III", crudo[:12])
    assert (m, v, total) == (0x46546C67, 2, len(crudo)), "cabecera GLB inconsistente"
    assert gltf["buffers"][0].get("uri") is None, "el buffer de un GLB no declara uri"
    for t in gltf["meshes"][0]["primitives"][0]["targets"]:
        a = gltf["accessors"][t["POSITION"]]
        assert "min" in a and "max" in a, "morph target sin min/max"

    print(f"{salida}: {n} vértices, {len(faces)} triángulos, 3 morph targets, "
          f"{len(huesos)} huesos, {Path(salida).stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/proxy_cloak.glb")
