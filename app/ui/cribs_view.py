"""Puente entre ``enigma_lab.cribs`` y las animaciones de la página Cribs y menús.

Los componentes HTML solo dibujan: reciben aquí, como JSON, las alineaciones y el menú
que calcula Python.
"""

from __future__ import annotations

from typing import Any

import networkx as nx
import streamlit.components.v1 as components

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


def menu_payload(graph: nx.MultiGraph) -> dict[str, Any]:
    """Datos del menú: letras con posición y grado, aristas con su paso y si están en un lazo."""
    stats = menu_stats(graph)
    positions = layout(graph)
    return {
        "theme": _theme(),
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
    components.html(_html("crib_drag.html", payload), height=height, scrolling=True)


def render_menu(payload: dict[str, Any]) -> None:
    components.html(_html("menu_graph.html", payload), height=520)
