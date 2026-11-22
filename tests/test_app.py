"""La app arranca y la página Inicio muestra las cifras calculadas por el código."""

from __future__ import annotations

import tomllib

from streamlit.testing.v1 import AppTest

from enigma_lab import paths
from enigma_lab.core import keyspace as ks
from enigma_lab.viz import theme
from enigma_lab.viz.numfmt import fmt_dec, fmt_int

ENTRYPOINT = paths.APP / "Inicio.py"


def _run_app() -> AppTest:
    return AppTest.from_file(str(ENTRYPOINT), default_timeout=60).run()


def test_inicio_runs_without_errors() -> None:
    app = _run_app()
    assert not app.exception
    assert app.title[0].value == "Enigma Lab"


def test_inicio_shows_computed_figures() -> None:
    space = ks.keyspace(ks.ENIGMA_I)
    text = " ".join(block.value for block in _run_app().markdown)
    assert f'<span class="num">{round(ks.bits(space.total_without_rings))}</span>' in text
    assert f'<span class="num el-amber">{round(ks.bits(space.bombe_sweep))}</span>' in text
    assert fmt_int(space.bombe_sweep) in text
    assert fmt_dec(ks.bits(space.bombe_sweep)) in text


def test_demo_mode_scales_text() -> None:
    """Con el modo demo activo, el CSS común sube la letra base a 20 px.

    El estado se fija antes de la primera ejecución: al volver a ejecutar, AppTest
    corre directamente la página y no el punto de entrada, que es donde vive el
    interruptor de la barra lateral.
    """
    app = AppTest.from_file(str(ENTRYPOINT), default_timeout=60)
    app.session_state["demo_mode"] = True
    app.run()
    assert app.toggle(key="demo_mode").value is True
    styles = " ".join(block.value for block in app.markdown if "<style>" in block.value)
    assert "font-size: 20px" in styles


def test_streamlit_theme_matches_tokens() -> None:
    """Los colores de .streamlit/config.toml son los de enigma_lab.viz.theme.DARK."""
    config = tomllib.loads((paths.ROOT / ".streamlit" / "config.toml").read_text("utf-8"))
    t = config["theme"]
    d = theme.DARK
    assert t["primaryColor"] == d.accent
    assert t["backgroundColor"] == d.background
    assert t["secondaryBackgroundColor"] == d.surface
    assert t["textColor"] == d.text
    assert t["borderColor"] == d.border
    assert config["server"]["enableStaticServing"] is True
    for face in t["fontFaces"]:
        assert (paths.ROOT / face["url"]).is_file(), face["url"]


def test_demo_mode_survives_a_reload_through_the_url() -> None:
    """Con ?demo=1 en la URL la app abre en modo demo (una recarga no lo apaga)."""
    app = AppTest.from_file(str(ENTRYPOINT), default_timeout=60)
    app.query_params["demo"] = "1"
    app.run()
    assert not app.exception
    assert app.toggle(key="demo_mode").value is True
