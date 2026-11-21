"""Piezas comunes de las páginas: estilo global, modo demo y paneles explicativos."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape

import streamlit as st

from enigma_lab.viz.theme import DARK, MONO_STACK, ink_on

DEMO_KEY = "demo_mode"

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

_DEMO_CSS = """
html { font-size: 20px !important; }
"""


def demo_mode_toggle() -> bool:
    """Interruptor «Modo demo» de la barra lateral: letra de al menos 20 px para proyectar."""
    return st.toggle(
        "Modo demo",
        key=DEMO_KEY,
        help="Letra de al menos 20 px y resultados en grande, para proyectar en clase.",
    )


def is_demo() -> bool:
    """¿Está activo el modo demo? (el estado vive en ``st.session_state``)."""
    return bool(st.session_state.get(DEMO_KEY, False))


def apply_global_style(demo: bool) -> None:
    """Inyecta el CSS común y, en modo demo, la escala de letra de 20 px."""
    css = _CSS + (_DEMO_CSS if demo else "")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def what_am_i_seeing(*lines: str) -> None:
    """Panel plegable «¿Qué estoy viendo?» con 3 a 5 líneas (spec, sección 8.3)."""
    if not 3 <= len(lines) <= 5:
        raise ValueError("el panel «¿Qué estoy viendo?» lleva de 3 a 5 líneas")
    with st.expander("¿Qué estoy viendo?", icon=":material/help:"):
        st.markdown("\n".join(f"- {line}" for line in lines))


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
