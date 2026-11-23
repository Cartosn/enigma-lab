"""Identidad visual «Bletchley nocturno».

Un solo lugar para los colores de la app, de las figuras del informe y de las figuras
de respaldo de las diapositivas:

* tokens de interfaz (fondo, superficies, bordes, texto, acentos, error y éxito) en
  versión oscura (app y diapositivas) e impresa (informe, fondo blanco);
* paleta categórica Okabe-Ito, apta para daltonismo, en un orden fijo;
* rampas secuenciales de un solo tono (el ámbar de las lámparas de Enigma);
* plantillas Plotly ``enigma_dark`` y ``enigma_dark_demo`` (nada bajo 20 px);
* estilos Matplotlib ``enigma_print`` (fondo blanco) y ``enigma_slides`` (oscuro, 16:9).

Plotly y Matplotlib se importan dentro de las funciones: importar este módulo es
barato y no exige ninguna de las dos bibliotecas.

Cómo se eligieron el orden de la paleta y las rampas: ``docs/DECISIONES.md``.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FONT_DIR = Path(__file__).resolve().parent / "fonts"
"""Fuentes TTF para Matplotlib (las WOFF2 de la app están en ``app/static/fonts``)."""

FONT_STACK = "Inter, system-ui, 'Segoe UI', Roboto, sans-serif"
MONO_STACK = "'JetBrains Mono', ui-monospace, Consolas, monospace"


@dataclass(frozen=True)
class Tokens:
    """Colores con nombre de la interfaz y de las figuras (hex sRGB)."""

    background: str
    surface: str
    border: str
    grid: str
    text: str
    text_muted: str
    accent: str
    accent_2: str
    error: str
    success: str


DARK = Tokens(
    background="#0F1216",
    surface="#171B21",
    border="#2A3038",
    grid="#2A3038",
    text="#E8E6E3",
    text_muted="#9AA3AD",
    accent="#F2B134",  # ámbar: las lámparas de Enigma
    accent_2="#4FB3BF",  # turquesa
    error="#E5534B",  # conflicto o error
    success="#57AB5A",
)
"""Tema oscuro por defecto: la app y las figuras de respaldo de diapositivas."""

PRINT = Tokens(
    background="#FFFFFF",
    surface="#F6F7F8",
    border="#D0D7DE",
    grid="#E6E9EC",
    text="#1F2328",
    text_muted="#59636E",
    accent="#A47300",  # ámbar oscurecido: paso 5 de SEQUENTIAL_PRINT, 4,2:1 sobre blanco
    accent_2="#0072B2",  # azul Okabe-Ito
    error="#E5534B",
    success="#57AB5A",
)
"""Variante para imprimir (informe): fondo blanco con la misma paleta de datos."""

OKABE_ITO = {
    "bluish_green": "#009E73",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "sky_blue": "#56B4E9",
    "orange": "#E69F00",
    "reddish_purple": "#CC79A7",
    "yellow": "#F0E442",
}
"""Paleta Okabe-Ito sin el negro (invisible sobre el fondo oscuro), en el orden de uso."""

CATEGORICAL: tuple[str, ...] = tuple(OKABE_ITO.values())
"""Series de datos, siempre en este orden y sin ciclar.

Las tres primeras pasan las comprobaciones de color de la guía de visualización
(banda de luminosidad, croma, separación con daltonismo y contraste ≥ 3:1) sobre los
dos fondos; de la cuarta en adelante, cada gráfico lleva leyenda y etiquetas directas.
"""

SEQUENTIAL_DARK: tuple[str, ...] = (
    "#5F4100",
    "#7F5800",
    "#A07000",
    "#C38900",
    "#E4A41E",
    "#FFC257",
    "#FFE4B9",
)
"""Magnitud sobre fondo oscuro: tono del ámbar, de apagado (poco) a brillante (mucho)."""

SEQUENTIAL_PRINT: tuple[str, ...] = (
    "#FFE4B9",
    "#FFC257",
    "#E7A724",
    "#C68C00",
    "#A47300",
    "#835B00",
    "#634400",
)
"""Magnitud sobre blanco: de claro (poco) a oscuro (mucho). Para categorías ordenadas
discretas, usa los pasos 3 a 7 (los dos primeros quedan bajo 2:1 sobre blanco)."""


# ------------------------------------------------------------------ contraste


def _channel_to_linear(c: float) -> float:
    """Canal sRGB en [0, 1] a luz lineal (curva de transferencia de sRGB)."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    """Luminancia relativa WCAG 2: 0,2126 R + 0,7152 G + 0,0722 B en luz lineal."""
    h = hex_color.lstrip("#")
    r, g, b = (_channel_to_linear(int(h[i : i + 2], 16) / 255) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: str, b: str) -> float:
    """Contraste WCAG 2 entre dos colores: (L₁ + 0,05) / (L₂ + 0,05), con L₁ ≥ L₂."""
    la, lb = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def ink_on(fill: str) -> str:
    """Color de texto legible dentro de un relleno: blanco o casi negro, el de más contraste."""
    white, black = "#FFFFFF", "#111418"
    return white if contrast_ratio(white, fill) >= contrast_ratio(black, fill) else black


# ------------------------------------------------------------------ Plotly


def _colorscale(ramp: tuple[str, ...]) -> list[list[Any]]:
    """Rampa de colores como escala continua de Plotly: pares [posición, color]."""
    last = len(ramp) - 1
    return [[i / last, color] for i, color in enumerate(ramp)]


def plotly_template(tokens: Tokens = DARK, font_size: int = 16) -> Any:
    """Plantilla Plotly del tema: fondos, tipografía, ejes discretos y paleta.

    Sigue las reglas de 8.1 y de la guía de visualización: rejilla fina y sólida,
    líneas de 2 px, marcadores de 8 px con un anillo del color del fondo, barras con
    la punta redondeada y coma decimal (``separators=",."``).
    """
    import plotly.graph_objects as go

    axis = {
        "gridcolor": tokens.grid,
        "gridwidth": 1,
        "griddash": "solid",
        "linecolor": tokens.border,
        "showline": True,
        "zeroline": False,
        "ticks": "outside",
        "tickcolor": tokens.border,
        "ticklen": 4,
        "tickfont": {"color": tokens.text_muted, "size": font_size - 2},
        "title": {"font": {"color": tokens.text_muted, "size": font_size - 1}, "standoff": 10},
        "automargin": True,
    }
    layout = go.Layout(
        font={"family": FONT_STACK, "size": font_size, "color": tokens.text},
        paper_bgcolor=tokens.background,
        plot_bgcolor=tokens.background,
        colorway=list(CATEGORICAL),
        separators=",.",
        title={
            "x": 0,
            "xanchor": "left",
            "font": {"size": round(font_size * 1.25), "color": tokens.text},
        },
        xaxis=axis,
        yaxis=axis,
        legend={
            "bgcolor": "rgba(0,0,0,0)",
            "font": {"color": tokens.text, "size": font_size - 2},
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
        hoverlabel={
            "bgcolor": tokens.surface,
            "bordercolor": tokens.border,
            "font": {"family": FONT_STACK, "color": tokens.text, "size": font_size - 2},
        },
        margin={"l": 16, "r": 16, "t": 72, "b": 16},
        barcornerradius=4,
        bargap=0.35,
        colorscale={"sequential": _colorscale(SEQUENTIAL_DARK)},
    )
    data = {
        "scatter": [
            go.Scatter(
                line={"width": 2},
                marker={"size": 8, "line": {"width": 2, "color": tokens.background}},
            )
        ],
        "bar": [go.Bar(marker={"line": {"width": 0}})],
        "heatmap": [go.Heatmap(colorscale=_colorscale(SEQUENTIAL_DARK))],
    }
    return go.layout.Template(layout=layout, data=data)


def register_plotly_templates() -> None:
    """Registra ``enigma_dark`` (16 px) y ``enigma_dark_demo`` en Plotly.

    La de modo demo parte de 22 px para que también las marcas de los ejes, que van 2 px
    por debajo de la letra base, queden en 20 px, el mínimo del modo demo.
    """
    import plotly.io as pio

    pio.templates["enigma_dark"] = plotly_template(DARK, font_size=16)
    pio.templates["enigma_dark_demo"] = plotly_template(DARK, font_size=22)


PLOTLY_CONFIG: dict[str, Any] = {
    "displaylogo": False,
    "toImageButtonOptions": {"format": "png", "scale": 2},
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}
"""Configuración de los gráficos de la app: descarga en PNG a 2x desde la barra."""


# ------------------------------------------------------------------ Matplotlib

_fonts_registered = False


def register_fonts() -> None:
    """Registra en Matplotlib las fuentes TTF del paquete (Inter y JetBrains Mono)."""
    global _fonts_registered
    if _fonts_registered:
        return
    import logging

    from matplotlib import font_manager

    for path in sorted(FONT_DIR.glob("*.ttf")):
        font_manager.fontManager.addfont(str(path))
    # DejaVu Sans es solo el respaldo para glifos que Inter no tenga; sin esto,
    # Matplotlib avisa en cada título que DejaVu no tiene peso «semibold».
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    _fonts_registered = True


def mpl_style(name: str) -> dict[str, Any]:
    """Parámetros (rcParams) de los estilos ``enigma_print`` y ``enigma_slides``.

    ``enigma_print`` es para el informe: fondo blanco, 6,3 × 3,6 pulgadas (el ancho de
    una columna a 11 pt) y letra de 9-10 pt. ``enigma_slides`` es el respaldo de las
    diapositivas: fondo oscuro, 16:9 y letra grande.
    """
    from cycler import cycler

    if name == "enigma_print":
        tokens, size, figsize, line, marker = PRINT, 10, (6.3, 3.6), 1.5, 5.0
    elif name == "enigma_slides":
        tokens, size, figsize, line, marker = DARK, 20, (13.333, 7.5), 3.0, 10.0
    else:
        raise ValueError(f"estilo desconocido: {name!r} (usa enigma_print o enigma_slides)")
    return {
        "figure.facecolor": tokens.background,
        "figure.figsize": figsize,
        "figure.dpi": 100,
        "savefig.facecolor": tokens.background,
        "savefig.edgecolor": tokens.background,
        "savefig.dpi": 200,  # PNG a 2x
        "savefig.bbox": "tight",
        "svg.fonttype": "none",  # el texto del SVG queda como texto
        "pdf.fonttype": 42,  # TrueType incrustada en el PDF
        "font.family": ["Inter", "DejaVu Sans"],
        "font.size": size,
        "text.color": tokens.text,
        "axes.facecolor": tokens.background,
        "axes.edgecolor": tokens.border,
        "axes.linewidth": 0.8,
        "axes.labelcolor": tokens.text_muted,
        "axes.labelsize": size,
        "axes.titlesize": round(size * 1.2),
        "axes.titleweight": "semibold",
        "axes.titlelocation": "left",
        "axes.titlecolor": tokens.text,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "axes.prop_cycle": cycler(color=list(CATEGORICAL)),
        "grid.color": tokens.grid,
        "grid.linewidth": 0.6,
        "grid.linestyle": "-",
        "xtick.color": tokens.border,
        "ytick.color": tokens.border,
        "xtick.labelcolor": tokens.text_muted,
        "ytick.labelcolor": tokens.text_muted,
        "xtick.labelsize": size - 1,
        "ytick.labelsize": size - 1,
        "lines.linewidth": line,
        "lines.markersize": marker,
        "lines.solid_capstyle": "round",
        "lines.solid_joinstyle": "round",
        "legend.frameon": False,
        "legend.fontsize": size - 1,
    }


@contextmanager
def mpl_style_context(name: str) -> Iterator[None]:
    """Aplica un estilo Matplotlib solo dentro del bloque ``with``."""
    import matplotlib as mpl

    register_fonts()
    # Matplotlib tipa las claves como literales; el diccionario se valida al aplicarlo.
    params: Any = mpl_style(name)
    with mpl.rc_context(params):
        yield
