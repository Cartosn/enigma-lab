"""Todas las páginas de la app corren sin errores (con el estado inicial y algunos botones)."""

from __future__ import annotations

import re

import pytest
from streamlit.testing.v1 import AppTest

from enigma_lab import paths
from ui.catalog import MODULES

PAGES = [paths.APP / m.page for m in MODULES if m.page]


@pytest.mark.parametrize("page", PAGES, ids=[p.stem for p in PAGES])
def test_page_runs(page) -> None:  # type: ignore[no-untyped-def]
    app = AppTest.from_file(str(page), default_timeout=120).run()
    assert not app.exception, app.exception


def test_cribs_page_shows_slide_11_menu() -> None:
    app = AppTest.from_file(str(paths.APP / "pages" / "cribs.py"), default_timeout=60).run()
    values = {m.label: m.value for m in app.metric}
    assert values["Letras"] == "11" and values["Aristas"] == "13" and values["Lazos"] == "3"
    assert values["Letra de prueba"] == "T"


def test_cribs_page_backup_case() -> None:
    app = AppTest.from_file(str(paths.APP / "pages" / "cribs.py"), default_timeout=60).run()
    next(b for b in app.button if b.label == "Caso de respaldo").click().run()
    assert not app.exception
    values = {m.label: m.value for m in app.metric}
    assert values["Lazos"] == "3" and values["Letra de prueba"] == "T"


def test_keyspace_page_figures() -> None:
    app = AppTest.from_file(str(paths.APP / "pages" / "espacio.py"), default_timeout=60).run()
    values = {m.label: m.value for m in app.metric}
    assert values["Barrido de la Bombe"] == "1.054.560"
    assert re.match(r"70,2\s%", values["Parte del plugboard"])


def test_bombe_page_backup_case_decrypts() -> None:
    """La Bombe con el caso de respaldo: menú de 3 lazos, barrido, «Verificar» y las 78 letras."""
    import json

    from enigma_lab.core.machine import groups_of_five

    data = json.loads((paths.DEMO / "respaldo_bombe.json").read_text(encoding="utf-8"))
    app = AppTest.from_file(str(paths.APP / "pages" / "bombe.py"), default_timeout=300).run()
    assert not app.exception
    values = {m.label: m.value for m in app.metric}
    assert values["Lazos"] == "3" and values["Letra de prueba"] == "T"
    next(b for b in app.button if b.label == "Correr la Bombe").click().run()
    assert not app.exception
    next(b for b in app.button if b.label == "Verificar").click().run()
    assert not app.exception
    text = " ".join(str(block.value) for block in app.markdown)
    assert groups_of_five(data["plaintext"]) in text
