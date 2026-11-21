"""Enigma Lab: punto de entrada de la app (``streamlit run app/Inicio.py``).

Arma la navegación con las páginas que ya existen (``ui/catalog.py``), registra la
plantilla Plotly del tema y aplica el estilo común y el modo demo. El contenido de la
página Inicio está en ``pages/inicio.py``.
"""

from __future__ import annotations

import streamlit as st

from enigma_lab.viz.theme import register_plotly_templates
from ui.catalog import MODULES
from ui.layout import apply_global_style, demo_mode_toggle

st.set_page_config(
    page_title="Enigma Lab",
    page_icon=":material/lock:",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def _setup_once() -> bool:
    """Preparativos de una sola vez por proceso (en la fase 3, también precalentar Numba)."""
    register_plotly_templates()
    return True


_setup_once()

pages = [st.Page("pages/inicio.py", title="Inicio", icon=":material/home:", default=True)]
pages += [st.Page(m.page, title=m.title, icon=m.icon) for m in MODULES if m.page]
navigation = st.navigation(pages)

with st.sidebar:
    demo = demo_mode_toggle()
    st.caption("Enigma Lab · Criptografía · UNAL 2026")

apply_global_style(demo)
navigation.run()
