"""E2 · ¿Cuánto aporta cada componente de la clave?

Es un cálculo exacto, sin azar, con enteros de Python (``core/keyspace.py``):
- los bits por componente de Enigma I y de la M3;
- N(k), las formas de conectar k cables, de 0 a 13, con el máximo en 11.

Los números grandes se guardan como texto en la columna ``opciones``, porque no caben
en un entero de 64 bits.
"""

from __future__ import annotations

import time
from typing import Any

import pandas as pd

from enigma_lab import SEED
from enigma_lab.core import keyspace as ks
from enigma_lab.experiments.common import (
    Mode,
    RunInfo,
    output_dir,
    save_figure,
    save_table,
    update_summary,
)
from enigma_lab.viz.numfmt import fmt_dec, fmt_int, fmt_pct, fmt_sci

MODELS = {"Enigma I": ks.ENIGMA_I, "Enigma M3": ks.M3}


def run(params: dict[str, Any] | None = None, seed: int = SEED) -> pd.DataFrame:
    """Tabla larga con los componentes de cada modelo y N(k) para k = 0…13."""
    rows: list[dict[str, Any]] = []
    for name, model in MODELS.items():
        space = ks.keyspace(model, cables=ks.DEFAULT_CABLES)
        options = {
            "orders": space.orders,
            "positions": space.positions,
            "rings": space.rings,
            "plugboard": space.plugboard,
        }
        for key, count in options.items():
            rows.append(
                {
                    "tabla": "componentes",
                    "modelo": name,
                    "componente": ks.COMPONENT_LABELS[key],
                    "cables": ks.DEFAULT_CABLES,
                    "opciones": str(count),
                    "bits": ks.bits(count),
                }
            )
        for label, count in (
            ("Total sin anillos", space.total_without_rings),
            ("Total con anillos", space.total_with_rings),
            ("Barrido de la Bombe", space.bombe_sweep),
        ):
            rows.append(
                {
                    "tabla": "totales",
                    "modelo": name,
                    "componente": label,
                    "cables": ks.DEFAULT_CABLES,
                    "opciones": str(count),
                    "bits": ks.bits(count),
                }
            )
    for k in range(ks.max_cables() + 1):
        count = ks.plugboard_settings(k)
        rows.append(
            {
                "tabla": "plugboard",
                "modelo": "",
                "componente": "Plugboard",
                "cables": k,
                "opciones": str(count),
                "bits": ks.bits(count),
            }
        )
    return pd.DataFrame(rows)


def summary(df: pd.DataFrame) -> dict[str, Any]:
    """Las cifras de 5.2."""
    space = ks.keyspace(ks.ENIGMA_I)
    years = ks.brute_force_years(space.total_without_rings, 1e9)
    total_bits = fmt_dec(ks.bits(space.total_without_rings))
    return {
        "total_sin_anillos": str(space.total_without_rings),
        "bits_sin_anillos": ks.bits(space.total_without_rings),
        "total_con_anillos": str(space.total_with_rings),
        "bits_con_anillos": ks.bits(space.total_with_rings),
        "bits_por_componente": {
            ks.COMPONENT_LABELS[k]: v for k, v in space.component_bits().items()
        },
        "fraccion_plugboard": space.plugboard_share,
        "barrido_bombe": space.bombe_sweep,
        "bits_barrido": ks.bits(space.bombe_sweep),
        "cables_maximo": ks.best_cable_count(),
        "n_maximo": str(ks.plugboard_settings(ks.best_cable_count())),
        "anos_a_1e9": years,
        "texto": (
            f"{fmt_sci(space.total_without_rings)} claves ({total_bits} bits); el plugboard "
            f"aporta el {fmt_pct(space.plugboard_share)}; la Bombe barre "
            f"{fmt_int(space.bombe_sweep)} configuraciones"
        ),
    }


def figure(df: pd.DataFrame, theme: str = "enigma_print") -> Any:
    """Bits por componente de Enigma I y N(k) con el máximo en 11 cables."""
    import matplotlib.pyplot as plt
    import numpy as np

    from enigma_lab.viz.static_figs import es_number, tokens
    from enigma_lab.viz.theme import mpl_style_context

    t = tokens(theme)
    comp = df[(df["tabla"] == "componentes") & (df["modelo"] == "Enigma I")]
    plug = df[df["tabla"] == "plugboard"]
    with mpl_style_context(theme):
        fig, (left, right) = plt.subplots(1, 2, gridspec_kw={"width_ratios": [1, 1.25]})
        colors = [t.accent, t.accent, t.text_muted, t.border]
        bars = left.barh(comp["componente"], comp["bits"], color=colors, height=0.55)
        left.invert_yaxis()
        left.bar_label(
            bars,
            labels=[fmt_dec(b) for b in comp["bits"]],
            padding=3,
            color=t.text,
            fontsize="small",
        )
        space = ks.keyspace(ks.ENIGMA_I)
        plug_bits = space.component_bits()["plugboard"]
        left.set_xlabel("bits (log₂ de las opciones)")
        left.set_title("Bits por componente, Enigma I", fontsize="medium")
        left.text(
            0.98,
            0.97,
            "ámbar: lo que barre la Bombe",
            transform=left.transAxes,
            ha="right",
            va="top",
            color=t.text_muted,
            fontsize="x-small",
        )
        left.grid(axis="y", visible=False)
        left.xaxis.set_major_formatter(es_number())

        k = plug["cables"].to_numpy()
        logs = np.array([np.log10(float(v)) for v in plug["opciones"]])
        right.plot(k, logs, marker="o", color=t.accent_2 if theme == "enigma_slides" else "#0072B2")
        best = int(k[np.argmax(logs)])
        right.annotate(
            f"máximo: {best} cables",
            xy=(best, logs.max()),
            xytext=(0, -26),
            textcoords="offset points",
            ha="center",
            color=t.text,
            fontsize="small",
            arrowprops={"arrowstyle": "-", "color": t.text_muted},
        )
        right.set_xlabel("cables en el plugboard")
        right.set_ylabel("log₁₀ N(k)")
        right.set_title("Formas de conectar k cables", fontsize="medium")
        right.xaxis.set_major_formatter(es_number())
        right.yaxis.set_major_formatter(es_number())
        fig.suptitle(
            f"El plugboard pone {fmt_dec(plug_bits, 1)} de los "
            f"{fmt_dec(ks.bits(space.total_without_rings), 1)} bits, con el máximo en "
            f"{best} cables",
            fontweight="semibold",
            x=0.02,
            ha="left",
        )
        fig.tight_layout()
    return fig


def main(mode: Mode = "completo", seed: int = SEED) -> dict[str, Any]:
    """Corre E2 (igual en los dos modos: es exacto) y guarda sus resultados."""
    folder = output_dir(mode)
    started = time.perf_counter()
    df = run()
    figures = summary(df) | {"segundos": round(time.perf_counter() - started, 2)}
    save_table(df, "e2_espacio_de_claves", folder)
    update_summary("e2", figures, RunInfo("e2", mode, seed), folder)

    import matplotlib.pyplot as plt

    fig = figure(df)
    save_figure(fig, "e2_espacio_de_claves", folder)
    plt.close(fig)
    return figures
