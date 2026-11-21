"""Gráficos de Plotly para la app, con la plantilla ``enigma_dark``.

Siguen las reglas de 8.1:
- el título dice el hallazgo, con su número;
- los ejes llevan unidades;
- los IC van como bandas o bigotes;
- la referencia publicada se dibuja.

Cada función recibe datos ya calculados (DataFrames o arreglos) y devuelve una figura;
no calcula nada de Enigma.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from enigma_lab.core import keyspace as ks
from enigma_lab.viz.numfmt import fmt_dec, fmt_int, fmt_pct
from enigma_lab.viz.theme import CATEGORICAL, DARK, SEQUENTIAL_DARK, register_plotly_templates

LETTERS = [chr(65 + i) for i in range(26)]

# Las plantillas del tema deben existir antes de usar este módulo (también fuera de la app).
register_plotly_templates()


def _template(demo: bool) -> str:
    return "enigma_dark_demo" if demo else "enigma_dark"


def _rgba(hex_color: str, alpha: float) -> str:
    r, g, b = (int(hex_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def keyspace_bits(space: ks.KeySpace, model_name: str, demo: bool = False) -> go.Figure:
    """Barras horizontales de bits por componente; en ámbar, lo que barre la Bombe."""
    bits = space.component_bits()
    names = [ks.COMPONENT_LABELS[k] for k in bits]
    colors = [DARK.accent, DARK.accent, DARK.text_muted, DARK.border]
    fig = go.Figure(
        go.Bar(
            x=list(bits.values()),
            y=names,
            orientation="h",
            marker_color=colors,
            text=[fmt_dec(v) for v in bits.values()],
            textposition="outside",
            hovertemplate="%{y}: %{x:.2f} bits<extra></extra>",
        )
    )
    total = ks.bits(space.total_without_rings)
    fig.update_layout(
        template=_template(demo),
        title=f"Plugboard: {fmt_dec(bits['plugboard'], 1)} de {fmt_dec(total, 1)} bits",
        xaxis_title=f"bits (log₂ de las opciones), {model_name}",
        xaxis_range=[0, max(bits.values()) * 1.2],
        yaxis={"autorange": "reversed"},
        height=340,
        showlegend=False,
    )
    return fig


def plugboard_curve(cables: int, demo: bool = False) -> go.Figure:
    """N(k) para k = 0…13 en escala logarítmica, con el máximo y el valor elegido marcados."""
    k = np.arange(ks.max_cables() + 1)
    n = [ks.plugboard_settings(int(i)) for i in k]
    best = ks.best_cable_count()
    fig = go.Figure(
        go.Scatter(
            x=k,
            y=[float(v) for v in n],
            mode="lines+markers",
            line_color=CATEGORICAL[1],
            customdata=[fmt_int(v) for v in n],
            hovertemplate="%{x} cables: %{customdata} formas<extra></extra>",
        )
    )
    fig.add_annotation(
        x=best,
        y=np.log10(float(n[best])),
        yref="y",
        text=f"máximo: {best} cables",
        showarrow=True,
        arrowcolor=DARK.text_muted,
        ay=40,
    )
    fig.add_vline(x=cables, line_color=DARK.accent, line_dash="dot")
    fig.update_layout(
        template=_template(demo),
        title=f"N(k): máximo con {best} cables",
        xaxis_title=f"cables en el plugboard (con {cables}: {fmt_int(n[cables])})",
        yaxis_title="formas de conectarlos",
        yaxis={"type": "log", "exponentformat": "power", "dtick": 3},
        height=360,
        showlegend=False,
    )
    return fig


def frequency_comparison(plain: np.ndarray, cipher: np.ndarray, demo: bool = False) -> go.Figure:
    """Frecuencias de las 26 letras en el texto plano y en el cifrado."""
    fig = go.Figure()
    for values, name, color in (
        (plain, "Texto plano", CATEGORICAL[0]),
        (cipher, "Cifrado", CATEGORICAL[2]),
    ):
        fig.add_bar(
            x=LETTERS,
            y=values,
            name=name,
            marker_color=color,
            hovertemplate="%{x}: %{y:.1%}<extra>" + name + "</extra>",
        )
    fig.add_hline(
        y=1 / 26,
        line_dash="dot",
        line_color=DARK.text_muted,
        annotation_text="uniforme: 1/26",
        annotation_position="top right",
    )
    fig.update_layout(
        template=_template(demo),
        barmode="group",
        yaxis_tickformat=".0%",
        xaxis_title="letra",
        yaxis_title="frecuencia",
        height=360,
        title="El cifrado aplana las frecuencias del idioma",
    )
    return fig


def pair_heatmap(matrix: np.ndarray, demo: bool = False) -> go.Figure:
    """Matriz 26 × 26 plano × cifrado; la diagonal en cero queda en el color del fondo."""
    scale = [[0.0, DARK.background]] + [
        [0.001 + 0.999 * i / (len(SEQUENTIAL_DARK) - 1), c] for i, c in enumerate(SEQUENTIAL_DARK)
    ]
    diagonal = int(np.trace(matrix))
    fig = go.Figure(
        go.Heatmap(
            z=matrix,
            x=LETTERS,
            y=LETTERS,
            colorscale=scale,
            xgap=1,
            ygap=1,
            hovertemplate="plana %{y} → cifrada %{x}: %{z} veces<extra></extra>",
            colorbar={"title": "veces"},
        )
    )
    fig.update_layout(
        template=_template(demo),
        title=f"La diagonal suma {fmt_int(diagonal)}: ninguna letra se cifra a sí misma",
        xaxis_title="letra cifrada",
        yaxis_title="letra plana",
        yaxis={"autorange": "reversed", "scaleanchor": "x"},
        height=560,
    )
    return fig


def e3_ic(table: pd.DataFrame, demo: bool = False) -> go.Figure:
    """E3: IC del plano y del cifrado según la longitud, con su IC 95 % como banda."""
    from enigma_lab.stats.corpus import LANGUAGES
    from enigma_lab.stats.frequencies import GERMAN_IC_REFERENCE, RANDOM_IC

    fig = go.Figure()
    for color, language in zip(CATEGORICAL, LANGUAGES, strict=False):
        part = table[table["idioma"] == language].sort_values("L")
        for kind, dash in (("plano", "solid"), ("cifrado", "dot")):
            x = part["L"].tolist()
            fig.add_scatter(
                x=x + x[::-1],
                y=part[f"ic_{kind}_alto"].tolist() + part[f"ic_{kind}_bajo"].tolist()[::-1],
                fill="toself",
                fillcolor=_rgba(color, 0.15),
                line_width=0,
                hoverinfo="skip",
                showlegend=False,
            )
            fig.add_scatter(
                x=x,
                y=part[f"ic_{kind}"],
                mode="lines+markers",
                name=f"{LANGUAGES[language]}, {kind}",
                line={"color": color, "dash": dash},
                hovertemplate="L = %{x}: IC %{y:.4f}<extra></extra>",
            )
    fig.add_hline(
        y=GERMAN_IC_REFERENCE,
        line_dash="dash",
        line_color=DARK.text_muted,
        annotation_text="alemán, Pommerening: 0,0758",
    )
    fig.add_hline(
        y=RANDOM_IC,
        line_dash="dash",
        line_color=DARK.text_muted,
        annotation_text="al azar: 1/26 ≈ 0,0385",
        annotation_position="bottom right",
    )
    de = table[(table["idioma"] == "aleman")].sort_values("L").iloc[-1]
    fig.update_layout(
        template=_template(demo),
        xaxis_type="log",
        height=440,
        title=(
            f"El IC del alemán ({fmt_dec(de['ic_plano'], 4)}) cae a "
            f"{fmt_dec(de['ic_cifrado'], 4)} al cifrar"
        ),
        xaxis_title="longitud del mensaje (letras, escala log)",
        yaxis_title="índice de coincidencia",
    )
    return fig


def e4_survival(table: pd.DataFrame, demo: bool = False) -> go.Figure:
    """E4: alineaciones falsas que sobreviven, con IC 95 % y las dos curvas teóricas."""
    from enigma_lab.experiments.e4_cribs import TEXT_LABELS

    grid = np.arange(int(table["L"].min()), int(table["L"].max()) + 1)
    fig = go.Figure()
    fig.add_scatter(
        x=grid,
        y=(25 / 26) ** grid,
        mode="lines",
        name="Teoría: (25/26)^L",
        line={"color": DARK.text_muted, "width": 2},
        hoverinfo="skip",
    )
    german = table[table["texto"] == "aleman"]
    if not german.empty:
        fig.add_scatter(
            x=german["L"],
            y=german["teorico_kappa"],
            mode="lines",
            name="Teoría con el IC del alemán",
            line={"color": CATEGORICAL[1], "dash": "dash", "width": 1.5},
            hoverinfo="skip",
        )
    for color, text in zip(CATEGORICAL, ("aleatorio", "aleman"), strict=False):
        part = table[table["texto"] == text]
        fig.add_scatter(
            x=part["L"],
            y=part["p"],
            mode="markers",
            name=TEXT_LABELS[text],
            marker={"color": color, "size": 9},
            error_y={
                "type": "data",
                "symmetric": False,
                "array": part["ic_alto"] - part["p"],
                "arrayminus": part["p"] - part["ic_bajo"],
                "color": color,
            },
            hovertemplate="L = %{x}: %{y:.1%}<extra>" + TEXT_LABELS[text] + "</extra>",
        )
    title = "Alineaciones falsas que sobreviven al filtro"
    row13 = table[(table["texto"] == "aleatorio") & (table["L"] == 13)]
    if not row13.empty:
        title = (
            f"Con 13 letras sobrevive el {fmt_pct(float(row13['p'].iloc[0]))} de las "
            f"posiciones falsas (teoría {fmt_pct((25 / 26) ** 13)})"
        )
    fig.update_layout(
        template=_template(demo),
        title=title,
        height=440,
        xaxis_title="longitud del crib L (letras)",
        yaxis_title="alineaciones falsas que sobreviven",
        yaxis_tickformat=".0%",
        yaxis_range=[0, 1],
    )
    return fig


E5_FLOOR = 0.003
"""Piso de la escala logarítmica de E5: un promedio de 0 paradas se dibuja aquí."""


def e5_vs_turing(table: pd.DataFrame, demo: bool = False) -> go.Figure:
    """E5: paradas falsas por orden (con diagonal board) según letras y lazos, frente a Turing."""
    part = table[(table["diagonal"] == "si") & (table["modo"] == "bletchley")]
    fig = go.Figure()
    for color, loops in zip(CATEGORICAL, sorted(part["lazos"].unique()), strict=False):
        rows = part[part["lazos"] == loops].sort_values("letras")
        label = f"{loops} lazo{'s' if loops != 1 else ''}"
        fig.add_scatter(
            x=rows["letras"],
            y=np.maximum(rows["turing"], E5_FLOOR),
            mode="lines",
            line={"color": color, "dash": "dash", "width": 1.5},
            showlegend=False,
            hovertemplate=f"{label}, %{{x}} letras: %{{y}} (Turing)<extra></extra>",
        )
        fig.add_scatter(
            x=rows["letras"],
            y=np.maximum(rows["paradas_media"], E5_FLOOR),
            mode="markers",
            marker={"color": color, "size": 10},
            error_y={
                "type": "data",
                "symmetric": False,
                "array": rows["ic_alto"] - rows["paradas_media"],
                "arrayminus": np.maximum(rows["paradas_media"] - rows["ic_bajo"], 0),
                "color": color,
            },
            name=label,
            customdata=rows["paradas_media"],
            hovertemplate=f"{label}, %{{x}} letras: %{{customdata:.3g}} paradas falsas"
            "<extra>medido</extra>",
        )
    fig.add_scatter(
        x=[None],
        y=[None],
        mode="lines",
        line={"color": DARK.text_muted, "dash": "dash", "width": 1.5},
        name="Turing (discontinua)",
    )
    title = "Paradas falsas por orden de rotores frente a la tabla de Turing"
    row = part[(part["letras"] == 12) & (part["lazos"] == 3)]
    if not row.empty:
        r = row.iloc[0]
        title = (
            f"Con 12 letras y 3 lazos: {fmt_dec(r['paradas_media'], 2)} paradas por orden "
            f"(Turing: {fmt_dec(r['turing'], 2)})"
        )
    fig.update_layout(
        template=_template(demo),
        title=title,
        height=520,
        xaxis_title="letras (vértices) del menú",
        yaxis_title="paradas falsas por orden (escala log)",
        yaxis_type="log",
        xaxis={"dtick": 2},
        legend={"orientation": "h", "yanchor": "top", "y": -0.2, "x": 0, "xanchor": "left"},
        margin={"b": 120},
    )
    return fig


def _stops_text(value: float) -> str:
    """Paradas por orden para una celda: 17.575 · 678 · 26,3 · 0,11 · 0."""
    if np.isnan(value):
        return ""
    if value >= 100:
        return fmt_int(round(value))
    if value >= 1:
        return fmt_dec(value, 1)
    return "0" if value == 0 else fmt_dec(value, 2)


def e5_heatmap(table: pd.DataFrame, diagonal: str = "si", demo: bool = False) -> go.Figure:
    """E5: mapa de calor letras × lazos de las paradas falsas por orden (escala log)."""
    part = table[(table["diagonal"] == diagonal) & (table["modo"] == "bletchley")]
    letters = sorted(part["letras"].unique())
    loops = sorted(part["lazos"].unique())  # Plotly dibuja la primera categoría abajo
    grid = np.full((len(loops), len(letters)), np.nan)
    turing = np.full_like(grid, np.nan)
    for r in part.itertuples():
        y, x = loops.index(r.lazos), letters.index(r.letras)
        grid[y, x] = r.paradas_media
        turing[y, x] = r.turing
    fig = go.Figure(
        go.Heatmap(
            z=np.log10(np.maximum(grid, E5_FLOOR)),
            x=[str(v) for v in letters],
            y=[str(v) for v in loops],
            customdata=np.stack([grid, turing], axis=-1),
            text=[[_stops_text(v) for v in row] for row in grid],
            texttemplate="%{text}",
            textfont={"size": 13},
            colorscale=[[i / (len(SEQUENTIAL_DARK) - 1), c] for i, c in enumerate(SEQUENTIAL_DARK)],
            zmin=np.log10(E5_FLOOR),
            zmax=np.log10(20_000),
            xgap=2,
            ygap=2,
            colorbar={"title": "log₁₀"},
            hovertemplate="%{x} letras, %{y} lazos: %{customdata[0]:.3g} paradas "
            "(Turing: %{customdata[1]})<extra></extra>",
        )
    )
    fig.update_layout(
        template=_template(demo),
        title=f"Paradas falsas por orden, {'con' if diagonal == 'si' else 'sin'} diagonal board",
        height=340,
        xaxis_title="letras (vértices) del menú",
        yaxis_title="lazos",
        xaxis={"type": "category"},
        yaxis={"type": "category"},
    )
    return fig


def plotly_config() -> dict[str, Any]:
    """Configuración de la barra de herramientas (descarga de la imagen a 2x)."""
    from enigma_lab.viz.theme import PLOTLY_CONFIG

    return PLOTLY_CONFIG
