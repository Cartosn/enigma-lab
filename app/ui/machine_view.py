"""Puente entre la traza de Python y la animación SVG de ``components/enigma_machine.html``.

El componente no sabe cifrar: recibe aquí, como JSON, la traza que calcula
``Enigma.trace`` y solo la anima (regla clave del spec, sección 3).
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import streamlit as st

from enigma_lab import paths
from enigma_lab.core.machine import EnigmaConfig, LetterTrace
from enigma_lab.viz.theme import DARK

COMPONENT = paths.APP / "components" / "enigma_machine.html"
MAX_ANIMATED = 200
"""Letras que se animan como máximo (el resto se cifra igual, pero no se anima)."""


def machine_payload(
    config: EnigmaConfig, traces: list[LetterTrace], demo: bool = False, autoplay: bool = True
) -> dict[str, Any]:
    """Los datos que necesita la animación: la clave, la traza y los colores del tema."""
    theme = {
        "background": DARK.background,
        "surface": DARK.surface,
        "border": DARK.border,
        "text": DARK.text,
        "text_muted": DARK.text_muted,
        "accent": DARK.accent,
        "accent_2": DARK.accent_2,
        "ink": "#111418",  # texto sobre rellenos ámbar y turquesa
    }
    return {
        "theme": theme,
        "demo": demo,
        "autoplay": autoplay,
        "rotors": list(config.rotors),
        "reflector": config.reflector,
        "rings": config.ring_letters,
        "start": config.position_letters,
        "plugboard": [list(pair) for pair in config.plugboard],
        "letters": [t.to_dict() for t in traces[:MAX_ANIMATED]],
        "truncated": len(traces) > MAX_ANIMATED,
        "total": len(traces),
    }


def machine_html(payload: dict[str, Any]) -> str:
    """El HTML del componente con los datos incrustados (sin romper la etiqueta <script>)."""
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return COMPONENT.read_text(encoding="utf-8").replace("__PAYLOAD__", data)


def render_machine(
    config: EnigmaConfig, traces: list[LetterTrace], demo: bool = False, autoplay: bool = True
) -> None:
    """Dibuja la animación de la máquina para la traza dada."""
    height = 720 if demo else 650
    st.iframe(machine_html(machine_payload(config, traces, demo, autoplay)), height=height)


def trace_table(traces: list[LetterTrace]) -> pd.DataFrame:
    """La traza como tabla: una fila por letra, con las ventanas y el camino de la corriente.

    Son los datos de la animación, para descargarlos (spec 8.3).
    """
    return pd.DataFrame(
        {
            "letra": t.index + 1,
            "tecla": t.key,
            "lampara": t.lamp,
            "ventanas_antes": t.positions_before,
            "ventanas": t.positions,
            "doble_paso": t.double_step,
            "camino": t.path(),
        }
        for t in traces
    )
