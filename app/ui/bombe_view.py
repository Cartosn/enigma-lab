"""Puente entre ``enigma_lab.bombe`` y la página La Bombe: tambores y tablas.

El componente ``bombe_drums.html`` solo dibuja: recibe aquí, como JSON, las conexiones
del menú y, al terminar, las letras de cada tambor en la parada elegida.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from enigma_lab.bombe.checker import Hypotheses
from enigma_lab.bombe.scrambler import order_label, position_letters
from enigma_lab.bombe.sweep import BombeRun, Stop
from enigma_lab.bombe.wiring import BombeWiring
from enigma_lab.core.wiring import ALPHABET
from ui.components import component_html, theme_payload


def drum_letters(stop: Stop, offset: int) -> str:
    """Las letras de la tripleta de la conexión con paso i en una parada.

    Izquierdo y central como en la parada (el central + 1 si la variante dice que ya
    avanzó); el derecho, la posición de la parada más i + 1.
    """
    left, middle, right = stop.position // 676, (stop.position // 26) % 26, stop.position % 26
    if 0 < stop.turn <= offset:
        middle += 1
    return ALPHABET[left] + ALPHABET[middle % 26] + ALPHABET[(right + offset + 1) % 26]


def drums_payload(
    wiring: BombeWiring,
    state: str,
    title: str,
    subtitle: str = "",
    stop: Stop | None = None,
    demo: bool = False,
) -> dict[str, Any]:
    """Datos de los tambores: una tripleta por conexión del menú (estado «running» o «done»)."""
    columns = []
    for i in (int(v) for v in wiring.edge_offset):
        column: dict[str, Any] = {
            "offset": i,
            "pair": f"{wiring.crib[i]}–{wiring.cipher[i]}",
            "shift": i + 1,
        }
        if stop is not None:
            column["drums"] = drum_letters(stop, i)
        columns.append(column)
    return {
        "theme": theme_payload(),
        "demo": demo,
        "state": state,
        "title": title,
        "subtitle": subtitle,
        "position": stop.position_letters if stop else "",
        "columns": columns,
    }


def render_drums(payload: dict[str, Any]) -> None:
    height = 300 if payload.get("demo") else 250
    st.iframe(component_html("bombe_drums.html", payload), height=height)


def stops_frame(run: BombeRun, hypotheses: Hypotheses | None, limit: int = 300) -> pd.DataFrame:
    """Tabla de paradas para mostrar: primero las consistentes y luego las demás (``limit``)."""
    test = run.wiring.test_letter
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    if hypotheses is not None:
        # Se recorren todas las hipótesis, no solo las primeras: así toda parada consistente
        # sale en este primer bloque, y las de abajo son de verdad las que no pasaron.
        for k in range(len(hypotheses)):
            if len(rows) >= limit:
                break
            h = hypotheses.get(k)
            key = (order_label(h.stop.order), h.stop.position, h.stop.turn)
            if key in seen:
                continue
            seen.add(key)
            rows.append(_row(h.stop, test, True, h.pairs()))
    for order_run in run.runs:
        if len(rows) >= limit:
            break
        for k in range(len(order_run)):
            if len(rows) >= limit:
                break
            stop = order_run.stop(k)
            if (order_label(stop.order), stop.position, stop.turn) not in seen:
                rows.append(_row(stop, test, False, ""))
    return pd.DataFrame(rows)


def _row(stop: Stop, test: str, consistent: bool, pairs: str) -> dict[str, Any]:
    return {
        "Orden": order_label(stop.order),
        "Posición": position_letters(stop.position),
        "Vuelta del central": f"letra {stop.turn}" if stop.turn else "—",
        "Hilos encendidos": stop.lit,
        "Stecker candidato": stop.stecker_label(test),
        "Consistente": "sí" if consistent else "no",
        "Steckers deducidos": pairs,
    }
