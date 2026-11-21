"""Puente entre ``enigma_lab.cribs`` y las animaciones de la página Cribs y menús.

Los componentes HTML solo dibujan: reciben aquí, como JSON, las alineaciones y el menú
que calcula Python.
"""

from __future__ import annotations

import json
from typing import Any

import networkx as nx
import streamlit.components.v1 as components

from enigma_lab import paths
from enigma_lab.cribs.dragging import Alignment
from enigma_lab.cribs.menu import layout, menu_edges, menu_stats
from enigma_lab.viz.theme import DARK

COMPONENTS = paths.APP / "components"


def _theme() -> dict[str, str]:
    return {
        "background": DARK.background,
        "surface": DARK.surface,
        "border": DARK.border,
        "text": DARK.text,
        "text_muted": DARK.text_muted,
        "accent": DARK.accent,
        "accent_2": DARK.accent_2,
        "error": DARK.error,
        "success": DARK.success,
        "ink": "#111418",
    }


def _html(name: str, payload: dict[str, Any]) -> str:
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return (COMPONENTS / name).read_text(encoding="utf-8").replace("__PAYLOAD__", data)


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
