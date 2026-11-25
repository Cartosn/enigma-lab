"""Todas las páginas de la app corren sin errores (con el estado inicial y algunos botones)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from enigma_lab import paths
from ui.catalog import MODULES

PAGES = [paths.APP / m.page for m in MODULES if m.page]
WITH_HOME = [paths.APP / "Inicio.py", *PAGES]
"""Las páginas y la de Inicio, que corre desde el punto de entrada (usa ``st.navigation``)."""


@pytest.mark.parametrize("page", PAGES, ids=[p.stem for p in PAGES])
def test_page_runs(page) -> None:  # type: ignore[no-untyped-def]
    app = AppTest.from_file(str(page), default_timeout=120).run()
    assert not app.exception, app.exception


def test_experiments_page_without_the_full_corpus(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Docker y un clon sin ``make corpus`` no traen el corpus completo (D-071).

    Con los resultados guardados, Experimentos no lo lee: se dibujan las ocho pestañas, y las
    tablas de E3 y E4 son las de ``results/``, con la teoría calculada con el corpus completo.
    """
    import pandas as pd
    import streamlit as st

    from enigma_lab.stats import corpus

    def clear_caches() -> None:
        for cached in (corpus.load_text, corpus.load_letters, corpus.load_codes):
            cached.cache_clear()
        st.cache_data.clear()

    monkeypatch.setattr(corpus, "FULL_DIR", tmp_path)  # carpeta vacía: no hay corpus completo
    clear_caches()
    try:
        page = str(paths.APP / "pages" / "experimentos.py")
        app = AppTest.from_file(page, default_timeout=120).run()
        assert not app.exception, app.exception
        assert len([r for r in app.radio if r.label == "Resultados"]) == 8
        shown = [d.value for d in app.dataframe]
        for name, column in (
            ("e3_condiciones", "rechaza_cifrado_teoria"),
            ("e4_cribs", "teorico_kappa"),
        ):
            table = next(t for t in shown if column in t.columns).reset_index(drop=True)
            saved = pd.read_parquet(paths.RESULTS / f"{name}.parquet")
            pd.testing.assert_frame_equal(
                table, saved, check_dtype=False, check_column_type=False, check_index_type=False
            )
    finally:
        clear_caches()


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


def test_keyspace_page_parallel_attack() -> None:
    """La calculadora reparte la fuerza bruta: con 1.000 máquinas de 10⁹, unos 5,04 años."""
    app = AppTest.from_file(str(paths.APP / "pages" / "espacio.py"), default_timeout=60).run()
    label = "Probar las 1,6 × 10²⁰ claves"
    assert {m.label: m.value for m in app.metric}[label] == "5.037,2 años"
    app.select_slider[0].set_value(1_000).run()
    assert not app.exception
    assert {m.label: m.value for m in app.metric}[label] == "5,04 años"


@pytest.mark.parametrize("page", WITH_HOME, ids=[p.stem for p in WITH_HOME])
def test_pages_have_no_stray_strings(page) -> None:  # type: ignore[no-untyped-def]
    """En una página, Streamlit dibuja todo texto suelto («magia»): solo vale el docstring."""
    import ast

    tree = ast.parse(page.read_text(encoding="utf-8"))
    body = tree.body[1:] if ast.get_docstring(tree) else tree.body
    stray = [
        node.lineno
        for node in body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    assert not stray, f"{page.name}: textos sueltos en las líneas {stray}"


def _course_lines(app: AppTest) -> list[str]:
    return [str(m.value) for m in app.markdown if 'class="el-inclass"' in str(m.value)]


@pytest.mark.parametrize("page", WITH_HOME, ids=[p.stem for p in WITH_HOME])
def test_every_page_says_its_course_connection(page) -> None:  # type: ignore[no-untyped-def]
    """Debajo del título, la línea «En clase» con la etiqueta de su diapositiva (también en
    modo demo); en Experimentos, una por pestaña."""
    from ui.course import EXPERIMENTS
    from ui.course import PAGES as IN_CLASS

    key = page.stem.lower()
    expected = list(EXPERIMENTS.values()) if key == "experimentos" else IN_CLASS[key]
    for demo in (False, True):
        app = AppTest.from_file(str(page), default_timeout=120)
        app.session_state["demo_mode"] = demo
        app.run()
        assert not app.exception, app.exception
        lines = _course_lines(app)
        assert lines, page.stem
        shown = " ".join(lines)
        assert all(label in shown for label in expected), page.stem


def test_course_labels_follow_the_course_weeks() -> None:
    """Cada etiqueta empieza por la semana del curso, y toda página y pestaña tiene la suya."""
    from ui.course import EXPERIMENTS, SLIDES
    from ui.course import PAGES as IN_CLASS

    assert set(IN_CLASS) == {p.stem.lower() for p in WITH_HOME} - {"experimentos"}
    assert set(EXPERIMENTS) == {f"e{n}" for n in range(1, 9)}
    labels = [*SLIDES.values(), *EXPERIMENTS.values()] + [x for v in IN_CLASS.values() for x in v]
    assert all(label.startswith(("Semana ", "Semanas ")) and " · " in label for label in labels)


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


def test_rejewski_page_reconstructs_a_day_and_searches_the_catalog() -> None:
    page = str(paths.APP / "pages" / "rejewski.py")
    app = AppTest.from_file(page, default_timeout=180).run()
    assert not app.exception
    app.slider(key="rej_messages").set_value(150).run()
    assert not app.exception
    values = {m.label: m.value for m in app.metric}
    assert values["Letras de AD"] == "26 de 26"
    big = [m.value for m in app.markdown if 'class="el-result' in m.value]
    assert big and "configuraciones del catálogo" in big[0]
    app.toggle(key="rej_reveal").set_value(True).run()
    assert not app.exception


def test_attack_page_runs_the_three_phases() -> None:
    page = str(paths.APP / "pages" / "ataque.py")
    app = AppTest.from_file(page, default_timeout=300).run()
    assert not app.exception
    app.slider(key="att_length").set_value(800).run()
    app.radio(key="att_orders").set_value("I-III").run()
    next(b for b in app.button if b.label == "Atacar").click().run()
    assert not app.exception
    values = {m.label: m.value for m in app.metric}
    assert values["Ubicaciones de la fase 1"] == "105.456"


@pytest.mark.parametrize("page", PAGES, ids=[p.stem for p in PAGES])
def test_every_page_explains_itself_except_in_demo_mode(page) -> None:  # type: ignore[no-untyped-def]
    """Cada página tiene su «¿Qué estoy viendo?»; el modo demo lo oculta."""
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
