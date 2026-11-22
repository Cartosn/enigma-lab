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


# ---------------------------------------------------------------- Banburismus (fase 4)


def _signed(value: int) -> str:
    """Desplazamiento con signo: +8, −17, 0."""
    return f"+{value}" if value > 0 else fmt_int(value)


def banburismus_offsets(
    table: pd.DataFrame, upper: float, true_offset: int | None = None, demo: bool = False
) -> go.Figure:
    """Decibanes por desplazamiento, de −25 a +25: el mejor en ámbar; el verdadero, si se revela."""
    best_row = table.loc[table["decibanes"].idxmax()]
    best = int(best_row["desplazamiento"])
    colors = [DARK.accent if d == best else CATEGORICAL[1] for d in table["desplazamiento"]]
    fig = go.Figure(
        go.Bar(
            x=table["desplazamiento"],
            y=table["decibanes"],
            marker_color=colors,
            customdata=table[["repeticiones", "bigramas", "trigramas"]].to_numpy(),
            hovertemplate="desplazamiento %{x}: %{y:.1f} dB<br>%{customdata[0]} repeticiones, "
            "%{customdata[1]} bigramas y %{customdata[2]} trigramas<extra></extra>",
        )
    )
    fig.add_hline(
        y=upper,
        line_dash="dash",
        line_color=DARK.text_muted,
        annotation_text=f"aceptar profundidad: +{fmt_dec(upper, 2)} dB",
        annotation_position="top left",
    )
    if true_offset is not None:
        value = float(table.loc[table["desplazamiento"] == true_offset, "decibanes"].iloc[0])
        fig.add_annotation(
            x=true_offset,
            y=value,
            text="verdadero",
            showarrow=True,
            arrowcolor=DARK.success,
            font={"color": DARK.success},
            ay=-40 if value >= 0 else 40,
        )
    fig.update_layout(
        template=_template(demo),
        title=f"El desplazamiento {_signed(best)} suma "
        f"{fmt_dec(float(best_row['decibanes']), 1)} dB con "
        f"{fmt_int(int(best_row['repeticiones']))} repeticiones",
        xaxis_title="desplazamiento d (la letra j del mensaje 2 bajo la j + d del 1)",
        yaxis_title="decibanes en el solapamiento",
        xaxis={"dtick": 5},
        height=400,
        showlegend=False,
    )
    return fig


def banburismus_trajectories(
    paths: list[tuple[str, np.ndarray, str]], upper: float, lower: float, demo: bool = False
) -> go.Figure:
    """Decibanes acumulados letra a letra, con los umbrales de Wald y el punto donde se decide."""
    fig = go.Figure()
    for label, values, color in paths:
        letters = np.arange(1, len(values) + 1)
        fig.add_scatter(
            x=letters,
            y=values,
            mode="lines",
            name=label,
            line={"color": color, "width": 2},
            hovertemplate=f"{label}: letra %{{x}}, %{{y:.1f}} dB<extra></extra>",
        )
        crossed = np.flatnonzero((values >= upper) | (values <= lower))
        if len(crossed):
            k = int(crossed[0])
            fig.add_scatter(
                x=[k + 1],
                y=[values[k]],
                mode="markers",
                marker={"color": color, "size": 11, "symbol": "diamond"},
                showlegend=False,
                hovertemplate=f"{label}: decide en la letra {k + 1}<extra></extra>",
            )
    for y, text, position in (
        (upper, f"aceptar profundidad: +{fmt_dec(upper, 2)} dB", "top left"),
        (lower, f"descartar: {fmt_dec(lower, 2)} dB", "bottom left"),
    ):
        fig.add_hline(
            y=y,
            line_dash="dash",
            line_color=DARK.text_muted,
            annotation_text=text,
            annotation_position=position,
        )
    fig.update_layout(
        template=_template(demo),
        title="Trayectoria de la evidencia: se decide al cruzar un umbral",
        xaxis_title="letras comparadas",
        yaxis_title="decibanes acumulados",
        height=420,
        legend={"orientation": "h", "yanchor": "top", "y": -0.2, "x": 0, "xanchor": "left"},
        margin={"b": 110},
    )
    return fig


def roc_curves(
    curves: list[tuple[str, np.ndarray, np.ndarray, float]], length: int, demo: bool = False
) -> go.Figure:
    """Curvas ROC (falsos positivos contra verdaderos), con su AUC y la diagonal del azar."""
    fig = go.Figure()
    for color, (label, fpr, tpr, area) in zip(CATEGORICAL, curves, strict=False):
        fig.add_scatter(
            x=fpr,
            y=tpr,
            mode="lines",
            line={"color": color, "width": 2, "shape": "hv"},
            name=f"{label}: AUC {fmt_dec(area, 3)}",
            hovertemplate="falsos %{x:.1%}, verdaderos %{y:.1%}<extra></extra>",
        )
    fig.add_scatter(
        x=[0, 1],
        y=[0, 1],
        mode="lines",
        line={"color": DARK.text_muted, "dash": "dash", "width": 1},
        name="azar: AUC 0,5",
        hoverinfo="skip",
    )
    best = max(curves, key=lambda c: c[3]) if curves else None
    fig.update_layout(
        template=_template(demo),
        title=f"Curva ROC con {fmt_int(length)} letras"
        + (f": AUC {fmt_dec(best[3], 3)} en la mejor" if best else ""),
        xaxis_title="falsos positivos (azar tomado por profundidad)",
        yaxis_title="verdaderos positivos",
        xaxis={"range": [0, 1], "tickformat": ".0%"},
        yaxis={"range": [0, 1.02], "tickformat": ".0%"},
        height=480,
        legend={"orientation": "h", "yanchor": "top", "y": -0.2, "x": 0, "xanchor": "left"},
        margin={"b": 140},
    )
    return fig


def _e6_combos() -> list[tuple[str, str, str]]:
    from enigma_lab.experiments.e6_banburismus import SHORT_LABELS, SOURCES, combo

    return [
        (text, key, SHORT_LABELS[combo(text, key)])
        for text, keys in SOURCES.items()
        for key in keys
    ]


def e6_letters(table: pd.DataFrame, demo: bool = False) -> go.Figure:
    """E6: letras hasta decidir (α = β = 1 %) por fuente y puntuación, con IC 95 % y Wald."""
    from enigma_lab.experiments.e6_banburismus import MAIN_ALPHA, reference_letters

    longest = int(table["solapamiento"].max())
    part = table[np.isclose(table["alfa"], MAIN_ALPHA) & (table["solapamiento"] == longest)]
    combos = _e6_combos()
    fig = go.Figure()
    wald = reference_letters()
    for color, hypothesis, name in zip(
        CATEGORICAL, ("profundidad", "azar"), ("en profundidad", "al azar"), strict=False
    ):
        rows = [
            part[
                (part["fuente"] == t)
                & (part["puntuacion"] == k)
                & (part["hipotesis"] == hypothesis)
            ]
            for t, k, _ in combos
        ]
        present = [
            (label, r.iloc[0]) for (_, _, label), r in zip(combos, rows, strict=True) if len(r)
        ]
        fig.add_bar(
            y=[label for label, _ in present],
            x=[r["letras_media"] for _, r in present],
            orientation="h",
            name=name,
            marker_color=color,
            error_x={
                "type": "data",
                "symmetric": False,
                "array": [r["ic_alto"] - r["letras_media"] for _, r in present],
                "arrayminus": [r["letras_media"] - r["ic_bajo"] for _, r in present],
                "color": DARK.text_muted,
            },
            text=[fmt_int(round(r["letras_media"])) for _, r in present],
            textposition="inside",
            hovertemplate="%{y}: %{x:.0f} letras<extra>" + name + "</extra>",
        )
        fig.add_vline(
            x=wald[hypothesis],
            line_dash="dot",
            line_color=color,
            annotation_text=f"Wald {fmt_int(round(wald[hypothesis]))}",
            annotation_position="top left" if hypothesis == "profundidad" else "top right",
        )
    base = part[(part["fuente"] == "tasa_1_17") & (part["hipotesis"] == "profundidad")]
    title = "Letras hasta decidir frente a la aproximación de Wald"
    if len(base):
        letters = fmt_int(round(base["letras_media"].iloc[0]))
        title = (
            f"Con tasa 1/17 la profundidad se confirma en {letters} letras "
            f"(Wald: {fmt_int(round(wald['profundidad']))})"
        )
    fig.update_layout(
        template=_template(demo),
        title=title,
        barmode="group",
        xaxis_title="letras hasta decidir (α = β = 1 %, media e IC 95 %)",
        yaxis={"autorange": "reversed"},
        height=460,
    )
    return fig


def e6_identification(table: pd.DataFrame, demo: bool = False) -> go.Figure:
    """E6: fracción de pares en que el desplazamiento verdadero gana, según el solapamiento."""
    from enigma_lab.experiments.e6_banburismus import MAIN_ALPHA

    longest = int(table["solapamiento"].max())
    part = table[
        np.isclose(table["alfa"], MAIN_ALPHA)
        & (table["hipotesis"] == "profundidad")
        & (table["solapamiento"] < longest)
    ]
    fig = go.Figure()
    for color, (text, key, label) in zip(CATEGORICAL, _e6_combos(), strict=False):
        rows = part[(part["fuente"] == text) & (part["puntuacion"] == key)].sort_values(
            "solapamiento"
        )
        if rows.empty:
            continue
        fig.add_scatter(
            x=rows["solapamiento"],
            y=rows["identifica"],
            mode="lines+markers",
            name=label,
            line={"color": color},
            hovertemplate=f"{label}, %{{x}} letras: %{{y:.1%}}<extra></extra>",
        )
    fig.add_hline(
        y=1 / 51,
        line_dash="dot",
        line_color=DARK.text_muted,
        annotation_text="al azar: 1 de 51",
        annotation_position="bottom right",
    )
    fig.update_layout(
        template=_template(demo),
        title="Con más solapamiento, el desplazamiento verdadero gana más veces",
        xaxis_title="solapamiento (letras, escala log)",
        yaxis_title="pares en que el verdadero gana entre los 51",
        xaxis={
            "type": "log",
            "tickvals": sorted(part["solapamiento"].unique()),
            "ticktext": [fmt_int(int(v)) for v in sorted(part["solapamiento"].unique())],
        },
        yaxis={"tickformat": ".0%", "range": [0, 1.02]},
        height=440,
        legend={"orientation": "h", "yanchor": "top", "y": -0.22, "x": 0, "xanchor": "left"},
        margin={"b": 130},
    )
    return fig


def rejewski_class_sizes(
    table: pd.DataFrame, kuhl_largest: tuple[str, int] | None = None, demo: bool = False
) -> go.Figure:
    """E7: cuántas características tienen cada tamaño de clase (log-log), frente a Kuhl.

    ``table`` es ``Catalog.distribution()`` con la columna ``kuhl`` (su tabla 2).
    """
    fig = go.Figure()
    fig.add_scatter(
        x=table["tamano"],
        y=table["caracteristicas"],
        mode="markers",
        name="este catálogo (E7)",
        marker={"color": CATEGORICAL[0], "size": 7},
        hovertemplate="clases de %{x} configuraciones: %{y}<extra>E7</extra>",
    )
    if "kuhl" in table:
        ref = table.dropna(subset=["kuhl"])
        fig.add_scatter(
            x=ref["tamano"],
            y=ref["kuhl"].astype(float),
            mode="markers",
            name="Kuhl (2007), tabla 2",
            marker={
                "color": CATEGORICAL[2],
                "size": 11,
                "symbol": "diamond-open",
                "line": {"width": 2},
            },
            hovertemplate="clases de %{x} configuraciones: %{y}<extra>Kuhl</extra>",
        )
    if kuhl_largest is not None:
        label, size = kuhl_largest
        fig.add_scatter(
            x=[size],
            y=[1],
            mode="markers",
            name=f"Kuhl: la mayor, {label}",
            marker={
                "color": CATEGORICAL[2],
                "size": 11,
                "symbol": "diamond-open",
                "line": {"width": 2},
            },
            showlegend=False,
            hovertemplate=f"{label}: %{{x}} configuraciones<extra>Kuhl</extra>",
        )
    unique = int(table.loc[table["tamano"] == 1, "caracteristicas"].sum())
    total = int(table["caracteristicas"].sum())
    fig.update_layout(
        template=_template(demo),
        title=f"{fmt_int(unique)} de {fmt_int(total)} características señalan una configuración",
        xaxis={
            "type": "log",
            "dtick": 1,
            "tickformat": ",d",
            "title": "tamaño de la clase (configuraciones con la misma característica)",
        },
        yaxis={
            "type": "log",
            "dtick": 1,
            "tickformat": ",d",
            "title": "características con ese tamaño",
        },
        height=440,
        legend={"orientation": "h", "yanchor": "top", "y": -0.22, "x": 0, "xanchor": "left"},
        margin={"b": 120},
    )
    return fig


def rejewski_messages(days: pd.DataFrame, theory: np.ndarray, demo: bool = False) -> go.Figure:
    """E7: mensajes del día hasta reconstruir AD, BE y CF, por nivel, con la teoría y Rejewski."""
    from enigma_lab.rejewski.traffic import LEVEL_LABELS

    fig = go.Figure()
    order = ("caracteristica", "permutacion", "eliminacion", "todas")
    for color, level in zip(CATEGORICAL, order, strict=False):
        values = days[level].to_numpy()
        fig.add_histogram(
            x=values,
            xbins={"start": 0, "end": 320, "size": 5},
            histnorm="probability",
            name=f"{LEVEL_LABELS[level]}: {fmt_dec(float(values.mean()), 1)}",
            marker_color=color,
            opacity=0.55,
            hovertemplate="%{x} mensajes: %{y:.1%} de los días<extra></extra>",
        )
    n = np.arange(len(theory))
    binned = np.add.reduceat(theory, np.arange(0, len(theory), 5))
    fig.add_scatter(
        x=n[::5][: len(binned)] + 2.5,
        y=binned,
        mode="lines",
        name="teoría de las 26 letras (coleccionista de cupones)",
        line={"color": DARK.text_muted, "dash": "dash", "width": 2},
        hoverinfo="skip",
    )
    for value, label in ((60, "Rejewski: unos 60"), (80, "unos 80")):
        fig.add_vline(
            x=value,
            line_dash="dot",
            line_color=DARK.text_muted,
            annotation_text=label,
            annotation_position="top right",
        )
    perm = float(days["permutacion"].mean())
    fig.update_layout(
        template=_template(demo),
        barmode="overlay",
        title=f"Con el teorema, AD, BE y CF quedan determinadas en {fmt_dec(perm, 1)} mensajes",
        xaxis={"title": "mensajes del día", "range": [0, 320]},
        yaxis={"title": "fracción de los días", "tickformat": ".0%"},
        height=460,
        legend={"orientation": "h", "yanchor": "top", "y": -0.2, "x": 0, "xanchor": "left"},
        margin={"b": 150},
    )
    return fig


def attack_ic_histogram(
    counts: np.ndarray, edges: np.ndarray, marks: list[tuple[str, float, str]], demo: bool = False
) -> go.Figure:
    """Fase 1 del ataque: cuántas ubicaciones dan cada IC, con las marcas de referencia.

    ``counts`` y ``edges`` son el histograma de los IC (escala log en y); cada marca es
    (rótulo, IC, color).
    """
    centers = (edges[:-1] + edges[1:]) / 2
    fig = go.Figure(
        go.Bar(
            x=centers,
            y=np.where(counts > 0, counts, np.nan),
            width=np.diff(edges),
            marker_color=DARK.text_muted,
            name="ubicaciones",
            hovertemplate="IC %{x:.4f}: %{y} ubicaciones<extra></extra>",
        )
    )
    for k, (label, value, color) in enumerate(marks):
        fig.add_vline(
            x=value,
            line_color=color,
            line_dash="dot" if k else "solid",
            annotation_text=label,
            annotation_position="top left" if k % 2 else "top right",
        )
    total = int(counts.sum())
    fig.update_layout(
        template=_template(demo),
        title=f"Fase 1: el IC de las {fmt_int(total)} ubicaciones, sin plugboard",
        xaxis_title="índice de coincidencia del descifrado",
        yaxis={"type": "log", "title": "ubicaciones", "dtick": 1, "tickformat": ",d"},
        bargap=0,
        height=420,
        showlegend=False,
    )
    return fig


def attack_climb(trace: np.ndarray, demo: bool = False) -> go.Figure:
    """Fase 3: la subida del hill climbing, cambio por cambio (IC y trigramas por letra)."""
    from plotly.subplots import make_subplots

    steps = np.arange(1, len(trace) + 1)
    stage = np.where(trace[:, 0] == 0, "IC", "trigramas")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_scatter(
        x=steps,
        y=trace[:, 1],
        mode="lines+markers",
        name="IC del texto",
        line={"color": CATEGORICAL[0]},
        customdata=np.stack([trace[:, 3], stage], axis=1),
        hovertemplate="cambio %{x} (%{customdata[1]}): IC %{y:.4f}, %{customdata[0]} cables"
        "<extra></extra>",
    )
    fig.add_scatter(
        x=steps,
        y=trace[:, 2],
        mode="lines+markers",
        name="log₁₀ p por trigrama",
        line={"color": CATEGORICAL[2]},
        secondary_y=True,
        hovertemplate="cambio %{x}: %{y:.3f}<extra></extra>",
    )
    switch = int((trace[:, 0] == 0).sum())
    final = int(trace[-1, 3]) if len(trace) else 0
    if 0 < switch < len(trace):
        fig.add_vline(
            x=switch + 0.5,
            line_dash="dot",
            line_color=DARK.text_muted,
            annotation_text="del IC a los trigramas",
            annotation_position="top left",
        )
    fig.add_hline(y=1 / 26, line_dash="dash", line_color=DARK.text_muted, annotation_text="1/26")
    fig.update_layout(
        template=_template(demo),
        title=f"Fase 3: {len(trace)} cambios de cable aceptados hasta {final} cables",
        xaxis_title="cambio aceptado",
        height=420,
        legend={"orientation": "h", "yanchor": "top", "y": -0.22, "x": 0, "xanchor": "left"},
        margin={"b": 110},
    )
    fig.update_yaxes(title_text="índice de coincidencia", secondary_y=False)
    fig.update_yaxes(title_text="log₁₀ p por trigrama", secondary_y=True, showgrid=False)
    return fig


def e8_success(
    table: pd.DataFrame,
    curves: dict[int, tuple[np.ndarray, np.ndarray]],
    references: list[tuple[float, str]],
    demo: bool = False,
) -> go.Figure:
    """E8: mensajes leídos según la longitud y los cables, con IC de Wilson y la logística.

    ``curves`` es la logística ajustada por número de cables (x, y); el punteado es el hill
    climbing con la ubicación dada (el «oráculo»).
    """
    fig = go.Figure()
    for color, cables in zip(CATEGORICAL, sorted(table["cables"].unique()), strict=False):
        part = table[table["cables"] == cables].sort_values("L")
        label = f"{cables} cables"
        fig.add_scatter(
            x=part["L"],
            y=part["exito"],
            mode="markers",
            name=label,
            marker={"color": color, "size": 9},
            error_y={
                "type": "data",
                "symmetric": False,
                "array": part["ic_alto"] - part["exito"],
                "arrayminus": part["exito"] - part["ic_bajo"],
                "color": color,
            },
            legendgroup=label,
            hovertemplate="%{x} letras: %{y:.0%}<extra>" + label + "</extra>",
        )
        if int(cables) in curves:
            x, y = curves[int(cables)]
            fig.add_scatter(
                x=x,
                y=y,
                mode="lines",
                line={"color": color, "width": 2},
                name=f"{label}: logística",
                legendgroup=label,
                showlegend=False,
                hoverinfo="skip",
            )
        fig.add_scatter(
            x=part["L"],
            y=part["oraculo"],
            mode="lines",
            line={"color": color, "dash": "dot", "width": 1.5},
            name=f"{label}, con la ubicación dada",
            legendgroup=label,
            hovertemplate="%{x} letras: %{y:.0%}<extra>con la ubicación dada</extra>",
        )
    for k, (value, label) in enumerate(references):
        fig.add_vline(
            x=value,
            line_dash="dash",
            line_color=DARK.text_muted,
            annotation_text=label,
            annotation_position="bottom right" if k % 2 else "top right",
        )
    fig.update_layout(
        template=_template(demo),
        title="Mensajes que lee el ataque de Gillogly, según su longitud",
        xaxis={
            "type": "log",
            "title": "longitud del mensaje (letras, escala log)",
            "range": [np.log10(20), np.log10(1_800)],
        },
        yaxis={
            "title": "mensajes leídos (≥ 90 % de las letras)",
            "tickformat": ".0%",
            "range": [-0.03, 1.05],
        },
        height=480,
        legend={"orientation": "h", "yanchor": "top", "y": -0.2, "x": 0, "xanchor": "left"},
        margin={"b": 140},
    )
    return fig


def plotly_config() -> dict[str, Any]:
    """Configuración de la barra de herramientas (descarga de la imagen a 2x)."""
    from enigma_lab.viz.theme import PLOTLY_CONFIG

    return PLOTLY_CONFIG


def _values(data: Any) -> list[Any]:
    """Los valores de un eje de una serie de Plotly como lista (vacía si no hay)."""
    if data is None:
        return []
    return [v.item() if isinstance(v, np.generic) else v for v in np.asarray(data).ravel()]


def figure_table(fig: go.Figure) -> pd.DataFrame:
    """Los datos de una figura de Plotly en formato largo, para descargarlos (spec 8.3).

    Una fila por punto de cada serie, con las columnas «serie», «x» e «y»; los mapas de
    calor agregan «z», con una fila por celda, y los bigotes de error, «error_y». Las
    bandas de IC salen como series propias (el contorno de la banda).
    """
    rows: list[dict[str, Any]] = []
    for k, trace in enumerate(fig.data):
        name = trace.name or f"serie {k + 1}"
        z = getattr(trace, "z", None)
        if z is not None:
            matrix = np.asarray(z)
            xs = _values(trace.x) or list(range(matrix.shape[1]))
            ys = _values(trace.y) or list(range(matrix.shape[0]))
            rows += [
                {"serie": name, "x": x, "y": y, "z": matrix[i, j].item()}
                for i, y in enumerate(ys)
                for j, x in enumerate(xs)
            ]
            continue
        xs, ys = _values(getattr(trace, "x", None)), _values(getattr(trace, "y", None))
        if not xs and not ys:
            continue
        xs = xs or list(range(len(ys)))
        ys = ys or [None] * len(xs)
        error = getattr(trace, "error_y", None)
        errors = _values(error.array) if error is not None and error.array is not None else []
        for i, (x, y) in enumerate(zip(xs, ys, strict=False)):
            row = {"serie": name, "x": x, "y": y}
            if errors:
                row["error_y"] = errors[i] if i < len(errors) else None
            rows.append(row)
    return pd.DataFrame(rows)
