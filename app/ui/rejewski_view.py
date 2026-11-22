"""Puente entre ``enigma_lab.rejewski`` y el dibujo de los ciclos de la página Rejewski.

El componente HTML solo dibuja: recibe aquí, como JSON, los ciclos cerrados, las cadenas
abiertas y las letras sin datos de AD, BE y CF que calcula Python, ya con sus coordenadas.
Si el teorema deja una sola completación, se dibuja la permutación completa y los arcos
deducidos (no vistos en ningún indicador) van punteados.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from enigma_lab.core.wiring import ALPHABET
from enigma_lab.rejewski.characteristic import DOUBLED_TYPES, PRODUCTS, cycles, format_type
from enigma_lab.rejewski.traffic import (
    completions,
    partial_cycles,
    possible_types,
    unique_completion,
)
from enigma_lab.viz.numfmt import fmt_int
from enigma_lab.viz.theme import CATEGORICAL
from ui.components import component_html as _html
from ui.components import theme_payload as _theme

WIDTH = 760
"""Ancho del dibujo (unidades del SVG); se escala al ancho de la página."""


def _sizes(demo: bool) -> dict[str, float]:
    """Radio de cada letra, paso entre letras (en cadenas y en ciclos), separación y encabezado."""
    if demo:
        return {"node": 15, "step": 34, "arc": 48, "gap": 18, "header": 66}
    return {"node": 13, "step": 30, "arc": 42, "gap": 16, "header": 58}


def product_state(known: np.ndarray) -> dict[str, Any]:
    """Qué se sabe de un producto: letras, si ya quedó determinado y qué estructuras admite."""
    found = completions(known, cap=2)
    types = possible_types(known) if len(found) > 1 else list(found)
    return {
        "letters": int((known >= 0).sum()),
        "types": types,
        "characteristic": len(types) == 1,
        "permutation": len(found) == 1 and next(iter(found.values())) == 1,
    }


def _colors(all_cycles: list[list[int]]) -> dict[int, str]:
    """Un color por longitud de ciclo: las parejas del teorema quedan del mismo color."""
    lengths = sorted({len(c) for c in all_cycles}, reverse=True)
    return {n: CATEGORICAL[i % len(CATEGORICAL)] for i, n in enumerate(lengths)}


def _structure(known: np.ndarray) -> tuple[dict[str, Any], np.ndarray | None, list, list]:
    """El estado de un producto y lo que se dibuja: la completación única o lo conocido."""
    state = product_state(known)
    full = unique_completion(known) if state["permutation"] else None
    if full is not None:
        return state, full, cycles(full), []
    closed, chains = partial_cycles(known)
    return state, None, closed, chains


def _panel(
    name: str, known: np.ndarray, top: float, demo: bool, colors: dict[int, str]
) -> tuple[dict[str, Any], float]:
    """Un producto con las coordenadas de todo lo que se dibuja; devuelve también su altura."""
    s = _sizes(demo)
    node, step, gap = s["node"], s["step"], s["gap"]
    state, full, closed, chains = _structure(known)
    if state["characteristic"]:
        status = format_type(DOUBLED_TYPES[state["types"][0]])
        deduced = 0 if full is None else int((known < 0).sum())
        caption = (
            f"permutación completa: {deduced} arcos deducidos con el teorema (punteados)"
            if full is not None and deduced
            else "permutación completa"
            if full is not None
            else f"{state['letters']} de 26 letras: la estructura ya no puede cambiar"
        )
    else:
        status = f"{state['letters']} de 26 letras"
        caption = f"{fmt_int(len(state['types']))} estructuras posibles con los ciclos en parejas"

    x, y, row = 10.0, top + s["header"], 0.0
    items = []
    for cycle in sorted(closed, key=len, reverse=True):
        n = len(cycle)
        r = node if n == 1 else max(2.2 * node, n * s["arc"] / (2 * math.pi))
        d = 2 * r + 2 * node + (26 if n == 1 else 0)
        if x + d > WIDTH - 10 and x > 10:
            x, y, row = 10.0, y + row + gap, 0.0
        items.append(
            {
                "letters": [ALPHABET[c] for c in cycle],
                "deduced": [bool(known[c] < 0) for c in cycle],
                "cx": x + d / 2,
                "cy": y + d / 2 + (12 if n == 1 else 0),
                "r": r,
                "color": colors[n],
            }
        )
        x, row = x + d + gap, max(row, d)
    y += row + (gap if items else 0)

    per_row = int((WIDTH - 40) // step)
    open_chains = []
    for chain in (c for c in chains if len(c) > 1):
        points = []
        for k in range(len(chain)):
            points.append(
                [10 + node + (k % per_row) * step, y + node + (k // per_row) * (step + 6)]
            )
        open_chains.append({"letters": [ALPHABET[c] for c in chain], "points": points})
        y += (math.ceil(len(chain) / per_row)) * (step + 6)
    loose_letters = [ALPHABET[c[0]] for c in chains if len(c) == 1]
    loose = None
    if loose_letters:
        start = 10 + (96 if demo else 80)
        per = int((WIDTH - start) // step)
        loose = {
            "label": [10, y + node],
            "letters": loose_letters,
            "points": [
                [start + (k % per) * step, y + node + (k // per) * step]
                for k in range(len(loose_letters))
            ],
        }
        y += math.ceil(len(loose_letters) / per) * step
    panel = {
        "name": name,
        "status": status,
        "caption": caption,
        "done": bool(state["characteristic"]),
        "top": top,
        "cycles": items,
        "chains": open_chains,
        "loose": loose,
    }
    return panel, y - top + gap


def cycles_payload(known: list[np.ndarray], demo: bool = False) -> dict[str, Any]:
    """Los tres productos, uno debajo del otro, con sus coordenadas y la altura total.

    Cada longitud de ciclo tiene el mismo color en los tres productos.
    """
    colors = _colors([c for part in known for c in _structure(part)[2]])
    panels, top = [], 0.0
    for name, part in zip(PRODUCTS, known, strict=True):
        panel, height = _panel(name, part, top, demo, colors)
        panels.append(panel)
        top += height
    return {
        "theme": _theme(),
        "demo": demo,
        "width": WIDTH,
        "height": top,
        "sizes": _sizes(demo),
        "products": panels,
    }


def render_cycles(payload: dict[str, Any]) -> None:
    """El componente, con la altura justa (el SVG se escala al ancho de la columna)."""
    scale = 1.15  # la columna de la página suele ser algo más ancha que el dibujo
    height = int(payload["height"] * scale) + 70
    st.iframe(_html("cycles.html", payload), height=height)


def indicators_table(indicators: np.ndarray, count: int = 12) -> pd.DataFrame:
    """Los primeros indicadores, con las parejas que aportan a AD, BE y CF."""
    rows = []
    for i, row in enumerate(indicators[:count], start=1):
        text = "".join(ALPHABET[int(v)] for v in row)
        rows.append(
            {
                "mensaje": i,
                "indicador": f"{text[:3]} {text[3:]}",
                "AD": f"{text[0]} → {text[3]}",
                "BE": f"{text[1]} → {text[4]}",
                "CF": f"{text[2]} → {text[5]}",
            }
        )
    return pd.DataFrame(rows)
