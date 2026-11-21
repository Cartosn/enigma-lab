"""Piezas comunes de los componentes HTML: los colores del tema y el JSON incrustado.

Los componentes de ``app/components/`` solo dibujan: reciben como JSON lo que calcula
Python, dentro de una etiqueta ``<script id="payload">``.
"""

from __future__ import annotations

import json
from typing import Any

from enigma_lab import paths
from enigma_lab.viz.theme import DARK

COMPONENTS = paths.APP / "components"


def theme_payload() -> dict[str, str]:
    """Los colores del tema «Bletchley nocturno» que usan los componentes."""
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


def component_html(name: str, payload: dict[str, Any]) -> str:
    """El HTML de un componente con sus datos incrustados (sin romper la etiqueta <script>)."""
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return (COMPONENTS / name).read_text(encoding="utf-8").replace("__PAYLOAD__", data)
