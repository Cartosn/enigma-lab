"""Enigma Lab: punto de entrada de la app (``streamlit run app/Inicio.py``).

Arma la navegación con las páginas que ya existen (``ui/catalog.py``), registra la
plantilla Plotly del tema y aplica el estilo común y el modo demo. El contenido de la
página Inicio está en ``paginas/inicio.py``.

Las páginas viven en ``paginas/`` y no en ``pages/``: con una carpeta ``pages/`` junto a este
archivo, Streamlit arranca en su modo antiguo de varias páginas, y la primera página que se
abre directo (``/bombe?demo=1`` con el servidor recién arrancado) corre sola, sin pasar por
aquí: sin modo demo ni estilos (D-079).
"""

from __future__ import annotations

import importlib

import streamlit as st

from enigma_lab.attacks.gillogly import warm_up as warm_up_attack
from enigma_lab.bombe.sweep import warm_up
from enigma_lab.viz.theme import register_plotly_templates
from ui.catalog import MODULES
from ui.layout import apply_global_style, demo_mode_toggle

st.set_page_config(
    page_title="Enigma Lab",
    page_icon=":material/lock:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Módulos pesados que las páginas importan: se cargan al arrancar, detrás del indicador,
# para que ninguna página quede en blanco más de 1 s al abrirla.
PRELOAD = (
    "scipy.stats",
    "pandas",
    "networkx",
    "enigma_lab.bombe.checker",
    "enigma_lab.experiments.e1_validation",
    "enigma_lab.experiments.e3_statistics",
    "enigma_lab.experiments.e4_cribs",
    "enigma_lab.experiments.e5_bombe",
    "enigma_lab.experiments.e6_banburismus",
    "enigma_lab.experiments.e7_rejewski",
    "enigma_lab.experiments.e8_coa",
)


@st.cache_resource(show_spinner="Preparando Enigma Lab: precalentando la Bombe…")
def _setup_once() -> bool:
    """Preparativos de una sola vez por proceso.

    Registra la plantilla de Plotly y precalienta la Bombe: compila los núcleos de Numba
    (o los carga de su caché en disco, ``cache=True``) y precalcula el aleatorizador de
    los 60 órdenes. Así la demo 2 no espera al compilador, aunque el salón no tenga red.
    Precalienta también los núcleos del ataque moderno y carga los módulos pesados de las
    demás páginas.
    """
    register_plotly_templates()
    warm_up(all_tables=True)
    warm_up_attack()
    for module in PRELOAD:
        importlib.import_module(module)
    return True


_setup_once()

pages = [st.Page("paginas/inicio.py", title="Inicio", icon=":material/home:", default=True)]
pages += [st.Page(m.page, title=m.title, icon=m.icon) for m in MODULES if m.page]
navigation = st.navigation(pages)

with st.sidebar:
    demo = demo_mode_toggle()
    st.caption("Enigma Lab · Criptografía · UNAL 2026")

apply_global_style(demo)
navigation.run()
