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


def test_banburismus_page_shows_turing_figures_and_finds_the_offset() -> None:
    """Cifras de las diapositivas 13 y 17; con 1.500 letras gana el desplazamiento verdadero."""
    page = str(paths.APP / "pages" / "banburismus.py")
    app = AppTest.from_file(page, default_timeout=120).run()
    assert not app.exception
    values = {m.label: m.value for m in app.metric}
    assert values["Repetición (1/17 frente a 1/26)"] == "+1,845 dB"
    assert values["No repetición"] == "−0,093 dB"
    assert values["Umbrales de Wald"] == "±19,96 dB"
    assert values["Wald con letras sueltas"] == "929 y 1.062"
    app.slider(key="banb_length").set_value(1500).run()
    app.toggle(key="banb_reveal").set_value(True).run()
    assert not app.exception
    assert any("es el verdadero" in str(block.value) for block in app.success)
    app.radio(key="banb_scoring").set_value("trigramas").run()
    assert not app.exception


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


@pytest.mark.parametrize("page", PAGES, ids=[p.stem for p in PAGES])
def test_every_page_explains_itself_except_in_demo_mode(page) -> None:  # type: ignore[no-untyped-def]
    """Spec 8.3: cada página tiene su «¿Qué estoy viendo?»; el modo demo lo oculta (8.2.11)."""
    label = "¿Qué estoy viendo?"
    app = AppTest.from_file(str(page), default_timeout=120).run()
    assert [e for e in app.expander if e.label == label], page.stem
    demo = AppTest.from_file(str(page), default_timeout=120)
    demo.session_state["demo_mode"] = True
    demo.run()
    assert not demo.exception, demo.exception
    assert not [e for e in demo.expander if e.label == label], page.stem


def test_bombe_companion_button_sets_the_recommended_demo_2() -> None:
    """Demo 2: «Cifrado del compañero» vacía el cifrado y deja la configuración del banco."""
    import json

    bench = json.loads((paths.RESULTS / "bench_demo2.json").read_text(encoding="utf-8"))
    chosen = next(c for c in bench["configuraciones"] if c["id"] == bench["recomendada"])
    app = AppTest.from_file(str(paths.APP / "pages" / "bombe.py"), default_timeout=300)
    app.session_state["demo_mode"] = True
    app.run()
    next(b for b in app.button if b.label == "Cifrado del compañero").click().run()
    assert not app.exception
    assert app.session_state["bombe_cipher"] == ""
    assert app.session_state["bombe_crib"] == chosen["crib"]
    assert any("Pega el texto cifrado" in str(block.value) for block in app.info)
    # El compañero pega su cifrado: los ajustes de la demo 2 siguen ahí, aunque los
    # controles no se dibujaron mientras el cifrado estaba vacío.
    data = json.loads((paths.DEMO / "respaldo_bombe.json").read_text(encoding="utf-8"))
    app.text_area(key="bombe_cipher").set_value(data["ciphertext"]).run()
    assert not app.exception
    assert app.radio(key="bombe_mode").value == chosen["modo"]
    assert app.toggle(key="bombe_diagonal").value is True
    assert app.selectbox(key="bombe_position").value == 0


def test_bombe_demo_mode_backup_case_shows_the_result_large() -> None:
    """Plan B en modo demo: sin tabla de paradas ni comparación, y el descifrado en grande."""
    import json

    from enigma_lab.core.machine import groups_of_five

    data = json.loads((paths.DEMO / "respaldo_bombe.json").read_text(encoding="utf-8"))
    app = AppTest.from_file(str(paths.APP / "pages" / "bombe.py"), default_timeout=300)
    app.session_state["demo_mode"] = True
    app.run()
    next(b for b in app.button if b.label == "Caso de respaldo").click().run()
    next(b for b in app.button if b.label == "Correr la Bombe").click().run()
    assert not app.exception
    assert not app.dataframe  # la tabla larga de paradas no se dibuja en modo demo
    next(b for b in app.button if b.label == "Verificar").click().run()
    assert not app.exception
    big = [m.value for m in app.markdown if 'class="el-result ok"' in m.value]
    assert big and groups_of_five(data["plaintext"]) in big[0]
    assert not [h for h in app.subheader if h.value == "Con y sin diagonal board"]
