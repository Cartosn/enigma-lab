"""Utilidades para las figuras de Matplotlib (informe y respaldo de diapositivas).

Las reglas de 8.1:
- el título dice el hallazgo, con su número;
- los ejes llevan unidades;
- los intervalos van como bandas o bigotes;
- la referencia publicada se dibuja en el gráfico.

Todo número sale con formato español (coma decimal), como en la app.
"""

from __future__ import annotations

from typing import Any

from matplotlib.axes import Axes
from matplotlib.ticker import FuncFormatter

from enigma_lab.viz.numfmt import fmt_dec, fmt_int
from enigma_lab.viz.theme import DARK, PRINT, Tokens

STYLE_FOR_THEME = {"enigma_print": PRINT, "enigma_slides": DARK}


def tokens(theme: str) -> Tokens:
    """Los colores del estilo: impreso (fondo blanco) o diapositivas (oscuro)."""
    return STYLE_FOR_THEME.get(theme, PRINT)


def es_number(decimals: int = 0) -> FuncFormatter:
    """Marcas de eje con formato español: 1.000 · 0,05."""

    def fmt(value: float, _pos: Any) -> str:
        if decimals == 0 and float(value).is_integer():
            return fmt_int(int(value))
        return fmt_dec(value, decimals)

    return FuncFormatter(fmt)


def es_percent(decimals: int = 0) -> FuncFormatter:
    """Marcas de eje para fracciones, en porcentaje: 0,6 → «60 %»."""
    return FuncFormatter(lambda value, _pos: f"{fmt_dec(100 * value, decimals)} %")


def reference_line(ax: Axes, y: float, label: str, theme: str, *, dashed: bool = True) -> None:
    """Línea horizontal de referencia con su etiqueta a la derecha, en tinta secundaria."""
    color = tokens(theme).text_muted
    ax.axhline(y, color=color, linewidth=1.2, linestyle="--" if dashed else "-", zorder=1)
    ax.annotate(
        label,
        xy=(1, y),
        xycoords=("axes fraction", "data"),
        xytext=(-4, 4),
        textcoords="offset points",
        ha="right",
        va="bottom",
        color=color,
        fontsize="small",
    )
