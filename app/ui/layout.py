"""Piezas comunes de las páginas: estilo global, modo demo y paneles explicativos."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from enigma_lab.viz.theme import DARK, MONO_STACK, ink_on

DEMO_KEY = "demo_mode"
DEMO_PARAM = "demo"
"""Parámetro de la URL que guarda el modo demo (``?demo=1``): sobrevive a una recarga."""
HIDDEN_IN_DEMO = "nodemo_"
"""Prefijo de las claves de los contenedores que el modo demo oculta con CSS."""

_CSS = f"""
.el-hero {{ padding: 0.5rem 0 1rem; }}
.el-question {{ font-size: 1.35rem; color: {DARK.text}; margin: 0 0 0.25rem; }}
.el-figure {{ display: flex; align-items: baseline; flex-wrap: wrap; gap: 0.4rem 1rem;
             line-height: 1.05; margin: 0.25rem 0 0.5rem; }}
.el-figure .num {{ font-size: clamp(3.5rem, 9vw, 6.5rem); font-weight: 650; }}
.el-figure .unit {{ font-size: 1.5rem; color: {DARK.text_muted}; }}
.el-figure .arrow {{ font-size: clamp(2.5rem, 6vw, 4.5rem); color: {DARK.text_muted}; }}
.el-amber {{ color: {DARK.accent}; }}
.el-sub {{ color: {DARK.text_muted}; max-width: 52rem; }}
.el-cipher {{ font-family: {MONO_STACK}; letter-spacing: 0.08em; color: {DARK.accent}; }}
.el-result {{ font-family: {MONO_STACK}; letter-spacing: 0.08em; line-height: 1.3;
              word-break: break-word; margin: 0.1rem 0 0.4rem; }}
.el-result.ok {{ color: {DARK.accent}; }}
.el-result.weak {{ color: {DARK.text_muted}; }}
.el-reading {{ color: {DARK.text}; line-height: 1.35; margin: 0 0 0.6rem; }}
.el-segbar {{ display: flex; gap: 2px; height: 28px; margin: 0.75rem 0 0.4rem; }}
.el-segbar .part {{ border-radius: 4px; display: flex; align-items: center;
                    padding: 0 0.5rem; font-size: 0.85rem; font-weight: 600;
                    white-space: nowrap; overflow: visible; }}
.el-legend {{ display: flex; flex-wrap: wrap; gap: 0.25rem 1.25rem; font-size: 0.9rem;
              color: {DARK.text_muted}; }}
.el-legend .key {{ display: inline-block; width: 0.75rem; height: 0.75rem;
                   border-radius: 2px; margin-right: 0.4rem; vertical-align: -0.05rem; }}
@media (prefers-reduced-motion: reduce) {{
  * {{ animation: none !important; transition: none !important; }}
}}
"""

# Modo demo: la letra base sube a 20 px, y lo que Streamlit dibuja más pequeño que la
# letra base (pies de texto, etiquetas, métricas, tablas) se lleva a 1rem, así que nada
# queda bajo 20 px. Los contenedores con clave «nodemo_…» desaparecen sin perder el
# estado de sus controles.
_DEMO_CSS = f"""
html {{ font-size: 20px !important; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] *,
[data-testid="stWidgetLabel"] p, [data-testid="stMetricLabel"] p,
[data-testid="stMetricDelta"] div, [data-testid="stExpander"] summary p,
[data-testid="stMarkdownContainer"] small, [data-testid="stTooltipIcon"],
[data-testid="stSidebarNav"] span, [data-testid="stSidebar"] p,
[data-testid="stTab"] p, button p, [data-baseweb="select"] div,
[data-testid="stRadio"] label p, [data-testid="stAlert"] p,
[data-testid="stProgress"] p, [data-testid="stSpinner"] p,
[data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input, [data-testid="stCode"] code,
[data-baseweb="select"] input, [data-testid="stMarkdownContainer"] code,
[data-testid="stSliderThumbValue"], [data-testid="stSliderTickBarMin"],
[data-testid="stSliderTickBarMax"], [data-testid="stSliderTickBarMin"] *,
[data-testid="stSliderTickBarMax"] *, [data-testid="stPageLink"] p,
[data-testid="stMarkdownBadge"], [data-testid="stDownloadButton"] p,
.el-legend, .el-segbar .part {{ font-size: 1rem !important; }}
[data-testid="stMetricValue"] div {{ font-size: 2rem !important; }}
[class*="st-key-{HIDDEN_IN_DEMO}"] {{ display: none !important; }}
"""


def demo_mode_toggle() -> bool:
    """Interruptor «Modo demo» de la barra lateral, para proyectar en clase.

    El estado vive en ``st.session_state`` y se refleja en la URL (``?demo=1``): así una
    recarga de la página, o abrir directamente ``http://localhost:8501/?demo=1``, deja la
    app en modo demo.
    """
    if DEMO_KEY not in st.session_state:
        st.session_state[DEMO_KEY] = st.query_params.get(DEMO_PARAM) == "1"
    demo = st.toggle(
        "Modo demo",
        key=DEMO_KEY,
        help="Letra de al menos 20 px, sin los paneles que la demo no usa y con el resultado "
        "en grande. Se guarda en la URL (?demo=1).",
    )
    if demo:
        st.query_params[DEMO_PARAM] = "1"
    elif DEMO_PARAM in st.query_params:
        del st.query_params[DEMO_PARAM]
    return demo


def is_demo() -> bool:
    """¿Está activo el modo demo? (el estado vive en ``st.session_state``)."""
    return bool(st.session_state.get(DEMO_KEY, False))


def apply_global_style(demo: bool) -> None:
    """Inyecta el CSS común y, en modo demo, la escala de letra de 20 px."""
    css = _CSS + (_DEMO_CSS if demo else "")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def hidden_in_demo(name: str) -> DeltaGenerator:
    """Contenedor que el modo demo oculta con CSS.

    Sirve para los paneles con controles (por ejemplo, la clave de la página Máquina):
    si no se dibujaran, Streamlit borraría su estado; ocultos, lo conservan.
    """
    return st.container(key=HIDDEN_IN_DEMO + name)


def what_am_i_seeing(*lines: str) -> None:
    """Panel plegable «¿Qué estoy viendo?» con 3 a 5 líneas.

    En modo demo no se dibuja: es de los paneles que la demo no usa.
    """
    if not 3 <= len(lines) <= 5:
        raise ValueError("el panel «¿Qué estoy viendo?» lleva de 3 a 5 líneas")
    if is_demo():
        return
    with st.expander("¿Qué estoy viendo?", icon=":material/help:"):
        st.markdown("\n".join(f"- {line}" for line in lines))


def big_result(text: str, reading: str = "", ok: bool = True, demo: bool = False) -> None:
    """El resultado de la página en letra grande (en modo demo, más grande todavía).

    ``text`` va en monoespaciada (el texto en grupos de 5); ``reading``, debajo, es la
    lectura para personas, por ejemplo con la X como espacio.
    """
    size = "3rem" if demo else "1.8rem"
    tone = "ok" if ok else "weak"
    html = f'<div class="el-result {tone}" style="font-size: {size};">{escape(text) or "—"}</div>'
    if reading:
        reading_size = "1.6rem" if demo else "1.05rem"
        html += f'<p class="el-reading" style="font-size: {reading_size};">{escape(reading)}</p>'
    st.markdown(html, unsafe_allow_html=True)


def x_as_space(text: str) -> str:
    """La lectura habitual de un texto militar: la X separa palabras."""
    return " ".join(word for word in text.split("X") if word)


def segmented_bar(parts: Sequence[tuple[str, float, str, str]], label: str) -> str:
    """HTML de una barra segmentada: un todo dividido en partes proporcionales.

    Cada parte es (nombre, valor, texto que va dentro, color de relleno). Los nombres
    van en la leyenda, en el mismo orden que los bloques; el texto interior usa blanco
    o casi negro según el relleno.
    """
    total = sum(value for _, value, _, _ in parts)
    blocks = "".join(
        f'<div class="part" style="flex: {value / total:.6f} 1 0; background: {fill};'
        f' color: {ink_on(fill)};">{escape(inside)}</div>'
        for _, value, inside, fill in parts
    )
    legend = "".join(
        f'<span><span class="key" style="background: {fill};"></span>{escape(name)}</span>'
        for name, _, _, fill in parts
    )
    return (
        f'<div class="el-segbar" role="img" aria-label="{escape(label)}">{blocks}</div>'
        f'<div class="el-legend">{legend}</div>'
    )
