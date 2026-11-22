"""Puente entre ``enigma_lab.cribs`` y las animaciones de la página Cribs y menús.

Los componentes HTML solo dibujan: reciben aquí, como JSON, las alineaciones y el menú
que calcula Python.
"""

from __future__ import annotations

from typing import Any

import networkx as nx
import pandas as pd
import streamlit as st

from enigma_lab.cribs.dragging import Alignment
from enigma_lab.cribs.menu import layout, menu_edges, menu_stats
from ui.components import component_html as _html
from ui.components import theme_payload as _theme


def drag_payload(
    cipher: str, crib: str, aligned: list[Alignment], start: int = 0, demo: bool = False
) -> dict[str, Any]:
    """Datos del arrastre: el cifrado, el crib y los conflictos de cada alineación."""
    return {
        "theme": _theme(),
        "demo": demo,
        "cipher": cipher,
        "crib": crib,
        "start": start,
        "alignments": [{"position": a.position, "conflicts": list(a.conflicts)} for a in aligned],
    }


def menu_payload(graph: nx.MultiGraph, demo: bool = False) -> dict[str, Any]:
    """Datos del menú: letras con posición y grado, aristas con su paso y si están en un lazo."""
    stats = menu_stats(graph)
    positions = layout(graph)
    return {
        "theme": _theme(),
        "demo": demo,
        "nodes": [
            {
                "id": node,
                "x": x,
                "y": y,
                "degree": int(graph.degree(node)),
                "test": node == stats.test_letter,
            }
            for node, (x, y) in positions.items()
        ],
        "edges": [
            {"a": e.a, "b": e.b, "offset": e.offset, "in_loop": e.in_loop}
            for e in menu_edges(graph)
        ],
    }


def render_drag(payload: dict[str, Any]) -> None:
    height = 260 if payload.get("demo") else 220
    st.iframe(_html("crib_drag.html", payload), height=height)


def render_menu(payload: dict[str, Any]) -> None:
    height = 560 if payload.get("demo") else 520
    st.iframe(_html("menu_graph.html", payload), height=height)


def menu_table(graph: nx.MultiGraph) -> pd.DataFrame:
    """Las aristas del menú como tabla: los datos del grafo, para descargarlos (spec 8.3)."""
    return pd.DataFrame(
        {"letra_a": e.a, "letra_b": e.b, "paso": e.offset, "en_lazo": e.in_loop}
        for e in menu_edges(graph)
    )
