"""_descubrir: URLs de Wikipedia bien formadas (regresión del 404 por %2B)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.stages import descubrir as d  # noqa: E402

RESP = {"query": {"search": [
    {"title": "Elecciones intermedias en los Estados Unidos"},
    {"title": "2026 United States elections"},
]}}


class _Resp:
    def json(self):
        return RESP


def test_wikipedia_nunca_emite_mas_en_las_urls(monkeypatch):
    monkeypatch.setattr(d.requests, "get", lambda *a, **k: _Resp())
    urls = [u for u, _t in d._wikipedia("elecciones")]
    assert urls, "esperaba resultados mockeados"
    for u in urls:
        assert "+" not in u
        assert " " not in u
        assert "%20" not in u
        assert "%2B" not in u
    assert any(u.startswith("https://en.wikipedia.org/wiki/2026_United_States_elections")
               for u in urls)


def test_fallback_sin_red_devuelve_la_consulta(monkeypatch):
    monkeypatch.setattr(d.llm, "chat", lambda *a, **k: "")  # sin JSON útil
    qs = d._queries("tema x", "ep-test")
    assert qs == ["tema x"]


def test_queries_dedup_y_recorte(monkeypatch):
    monkeypatch.setattr(d.llm, "chat",
                        lambda *a, **k: '{"queries":["uno", "dos", "", "tres", "cuatro", "cinco", "seis"]}')
    qs = d._queries("tema x", "ep-test")
    assert qs == ["uno", "dos", "tres", "cuatro", "cinco"]


# --- basura medida el 2026-11-05: el episodio del Congreso terminó con tres páginas de
# diccionario y un /wiki/U como "fuentes documentales" ---

def test_diccionarios_y_paginas_de_una_letra_no_son_fuentes():
    for url, titulo in [
        ("https://www.merriam-webster.com/dictionary/u", "U"),
        ("https://dictionary.cambridge.org/dictionary/english/u", "Meaning of U"),
        ("https://simple.wikipedia.org/wiki/U", "U"),
        ("https://en.wikipedia.org/wiki/2026_United_States_elections_in_Florida", "20"),
    ]:
        assert d._basura(url, titulo), f"entró basura: {url}"


def test_una_fuente_real_pasa_el_filtro():
    assert not d._basura("https://en.wikipedia.org/wiki/History_of_the_Republican_Party_(United_States)",
                         "History of the Republican Party (United States)")
    assert not d._basura("https://www.ssa.gov/history/1946.html", "1946 SSA annual report")


def test_consulta_de_una_palabra_no_se_busca(monkeypatch):
    monkeypatch.setattr(d.llm, "chat", lambda *a, **k: json.dumps(
        {"queries": ["u", "midterm", "congressional elections 2026 results"]}))
    qs = d._queries("elecciones de medio término 2026", "ep-basura")
    assert qs == ["congressional elections 2026 results"]
