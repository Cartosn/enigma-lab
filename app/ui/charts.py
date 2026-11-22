"""Gráficos de la app y su exportación (spec 8.3: «todo gráfico se puede exportar»).

- **La figura:** el botón de la cámara en la barra de Plotly la baja en PNG a 2x.
- **Los datos:** el botón «Datos (CSV)» baja las series de la propia figura
  (``figure_table``), o la tabla que se le pase.

Las descargas son diferidas: el CSV se arma solo cuando alguien pulsa el botón, así que
dibujar la página no cuesta más. En modo demo no se dibujan los botones de descarga.
"""

from __future__ import annotations

import io
from collections.abc import Callable
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from enigma_lab.viz.plotly_figs import figure_table, plotly_config


def csv_bytes(table: pd.DataFrame) -> bytes:
    """Una tabla en CSV (UTF-8, con punto decimal, como los CSV de ``results/``)."""
    return table.to_csv(index=False).encode("utf-8")


def csv_button(
    label: str,
    table: Callable[[], pd.DataFrame],
    name: str,
    where: Any = st,
    icon: str = ":material/table:",
) -> None:
    """Botón de descarga de una tabla en CSV, calculada solo al pulsarlo."""
    where.download_button(
        label,
        data=lambda: csv_bytes(table()),
        file_name=f"{name}.csv",
        mime="text/csv",
        icon=icon,
        key=f"csv_{name}",
        on_click="ignore",
    )


def chart(
    fig: go.Figure,
    name: str,
    demo: bool = False,
    where: Any = st,
    data: pd.DataFrame | None = None,
) -> None:
    """Dibuja un gráfico de Plotly con el tema y, fuera del modo demo, su botón de datos.

    ``name`` es el nombre del archivo CSV (sin extensión) y la clave del botón, así que
    debe ser único en la página. ``data`` reemplaza a las series de la figura cuando la
    tabla original dice más (por ejemplo, con sus IC).
    """
    where.plotly_chart(fig, theme=None, config=plotly_config(), width="stretch")
    if demo:
        return
    csv_button(
        "Datos (CSV)",
        (lambda: data) if data is not None else (lambda: figure_table(fig)),
        name,
        where,
    )


def figure_bytes(make_figure: Callable[[], Any], fmt: str) -> bytes:
    """Dibuja una figura de Matplotlib (estilo ``enigma_print``) y la devuelve en PNG o SVG."""
    import matplotlib.pyplot as plt

    fig = make_figure()
    buffer = io.BytesIO()
    fig.savefig(buffer, format=fmt)
    plt.close(fig)
    return buffer.getvalue()


def figure_downloads(
    name: str, table: Callable[[], pd.DataFrame], make_figure: Callable[[], Any]
) -> None:
    """Tres botones: los datos en CSV y la figura del informe en PNG y en SVG.

    La figura se dibuja solo cuando alguien pulsa su botón (descarga diferida), así que
    la página no paga el costo de Matplotlib al abrirse.
    """
    cols = st.columns(3)
    csv_button("Datos (CSV)", table, name, cols[0])
    for col, fmt, mime, icon in (
        (cols[1], "png", "image/png", ":material/image:"),
        (cols[2], "svg", "image/svg+xml", ":material/draw:"),
    ):
        col.download_button(
            f"Figura ({fmt.upper()})",
            data=lambda fmt=fmt: figure_bytes(make_figure, fmt),
            file_name=f"{name}.{fmt}",
            mime=mime,
            icon=icon,
            key=f"{name}_{fmt}",
            on_click="ignore",
        )
