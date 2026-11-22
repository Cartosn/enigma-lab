"""Figuras del informe y su respaldo para las diapositivas, a partir de los resultados guardados.

No corre experimentos: lee ``results/summary.json`` y los Parquet de ``results/``.

- **Informe** (``report/figuras/``, estilo ``enigma_print``, PDF vectorial y PNG): las tres
  figuras de la sección de resultados, compactas para caber en 3 páginas (D-052):
  1. E4, la supervivencia de las alineaciones falsas frente a (25/26)^L;
  2. E5, las paradas falsas por orden frente a la tabla de Turing;
  3. E6, las letras que pide el SPRT frente a la aproximación de Wald.
- **Diapositivas** (``results/figures/slides/``, estilo ``enigma_slides``: 16:9, oscuro, letra
  grande): las mismas tres en formato de diapositiva, más E2 y E3 con la figura de su
  experimento. Son el respaldo de las diapositivas 6, 7, 15, 16 y 17; los gráficos de la
  presentación se dibujan con los CSV de ``results/presentacion/``.

Reglas de 8.1: el título dice el hallazgo con su número, los ejes llevan unidades, los IC
van como bigotes y la referencia publicada se dibuja en el gráfico.

Uso:  ``python -m enigma_lab.figuras``  (lo corre ``make reproduce``; ``make report``
llama a ``report_figures``).
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, LogLocator

from enigma_lab import paths
from enigma_lab.experiments.common import PNG_DPI, read_summary
from enigma_lab.viz.numfmt import fmt_dec, fmt_int, fmt_pct
from enigma_lab.viz.static_figs import es_number, es_percent, tokens
from enigma_lab.viz.theme import CATEGORICAL, Tokens, mpl_style_context

REPORT_FIGURES = paths.ROOT / "report" / "figuras"
"""Las figuras del informe, junto a ``report/informe.tex``."""

COMPACT: dict[str, Any] = {
    "font.size": 8,
    "axes.titlesize": 8.5,
    "axes.labelsize": 8,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7,
    "lines.linewidth": 1.3,
    "lines.markersize": 4,
}
"""En el informe las figuras van a la mitad o a todo el ancho de la columna (16 cm): letra de
8 pt, legible junto al texto de 11 pt sin escalar la figura."""

SIZES = {
    "enigma_print": {"half": (3.2, 2.3), "full": (6.5, 2.05)},
    "enigma_slides": {"half": (13.333, 7.5), "full": (13.333, 7.5)},
}
"""Tamaños en pulgadas: media columna o columna entera en el informe; 16:9 en diapositivas."""


@contextmanager
def _style(theme: str) -> Iterator[Tokens]:
    """El estilo Matplotlib del tema; en el informe, además, la letra compacta."""
    import matplotlib as mpl

    with mpl_style_context(theme):
        if theme == "enigma_print":
            compact: Any = COMPACT  # Matplotlib tipa las claves como literales
            with mpl.rc_context(compact):
                yield tokens(theme)
        else:
            yield tokens(theme)


def _new_figure(theme: str, size: str) -> tuple[Any, Any]:
    import matplotlib.pyplot as plt

    return plt.subplots(figsize=SIZES[theme][size])


def _short(value: float) -> str:
    """Un valor con los decimales justos: 678 · 26,3 · 0,99 · 0,11."""
    if value >= 100:
        return fmt_int(round(value))
    return fmt_dec(value, 1 if value >= 1 else 2)


def _halo(t: Tokens) -> list[Any]:
    """Borde del color del fondo alrededor de un texto, para leerlo sobre una línea."""
    from matplotlib.patheffects import withStroke

    return [withStroke(linewidth=2.5, foreground=t.background)]


def _log_ticks(value: float, _pos: Any) -> str:
    """Marcas de un eje logarítmico: 0,1 · 1 · 10 · 1.000 · 10.000."""
    return fmt_int(round(value)) if value >= 1 else fmt_dec(value, 2).rstrip("0").rstrip(",")


# ---------------------------------------------------------------- figura 1: E4


def crib_survival(table: pd.DataFrame, kappa: float, theme: str = "enigma_print") -> Any:
    """E4: alineaciones falsas que sobreviven al arrastre del crib, según su longitud L.

    Puntos con su IC 95 % para texto aleatorio y alemán real; líneas para la teoría
    (25/26)^L y para la teoría con el IC del alemán, (1 − (1 − κ)/25)^L.
    """
    random = table[table["texto"] == "aleatorio"].sort_values("L")
    german = table[table["texto"] == "aleman"].sort_values("L")
    at13 = {
        name: part.loc[part["L"] == 13, "p"].item() for name, part in (("r", random), ("g", german))
    }
    lengths = np.arange(int(table["L"].min()), int(table["L"].max()) + 1)
    with _style(theme) as t:
        fig, ax = _new_figure(theme, "half")
        ax.plot(lengths, (25 / 26) ** lengths, color=t.text_muted, label="Teoría: $(25/26)^L$")
        ax.plot(
            lengths,
            (1 - (1 - kappa) / 25) ** lengths,
            color=CATEGORICAL[1],
            linestyle="--",
            label=f"Teoría con κ = {fmt_dec(kappa, 4)}",
        )
        for part, color, label in (
            (random, CATEGORICAL[0], "Texto aleatorio"),
            (german, CATEGORICAL[1], "Alemán real"),
        ):
            ax.errorbar(
                part["L"],
                part["p"],
                yerr=[part["p"] - part["ic_bajo"], part["ic_alto"] - part["p"]],
                fmt="o",
                color=color,
                markeredgecolor=t.background,
                markeredgewidth=0.6,
                capsize=2,
                label=label,
                zorder=3,
            )
        ax.set_ylim(0, 1)
        ax.yaxis.set_major_formatter(es_percent())
        ax.set_xlabel("longitud del crib L (letras)")
        ax.set_ylabel("alineaciones falsas que sobreviven")
        ax.set_title(f"13 letras: sobrevive el {fmt_pct(at13['r'])} (alemán: {fmt_pct(at13['g'])})")
        ax.legend(loc="upper right", handlelength=1.6)
        fig.tight_layout()
    return fig


# ---------------------------------------------------------------- figura 2: E5


def bombe_stops(table: pd.DataFrame, letters: int = 12, theme: str = "enigma_print") -> Any:
    """E5: paradas falsas por orden de rotores según los lazos, con 12 letras en el menú.

    Medido con y sin diagonal board (modo Bletchley, media e IC 95 % de 100 menús) frente a
    la estimación de Turing, en escala logarítmica.
    """
    rows = table[(table["letras"] == letters) & (table["modo"] == "bletchley")]
    with_db = rows[rows["diagonal"] == "si"].sort_values("lazos")
    without_db = rows[rows["diagonal"] == "no"].sort_values("lazos")
    loops = with_db["lazos"].to_numpy()
    with _style(theme) as t:
        fig, ax = _new_figure(theme, "half")
        for part, color, marker, label in (
            (without_db, CATEGORICAL[2], "s", "Sin diagonal board"),
            (with_db, CATEGORICAL[0], "o", "Con diagonal board"),
        ):
            ax.errorbar(
                part["lazos"],
                part["paradas_media"],
                yerr=[
                    part["paradas_media"] - part["ic_bajo"],
                    part["ic_alto"] - part["paradas_media"],
                ],
                fmt=f"-{marker}",
                color=color,
                markeredgecolor=t.background,
                markeredgewidth=0.6,
                capsize=2,
                label=label,
                zorder=3,
            )
        ax.plot(
            with_db["lazos"],
            with_db["turing"],
            linestyle=":",
            marker="D",
            color=t.text_muted,
            markerfacecolor="none",
            label="Turing",
            zorder=2,
        )
        for x, y in zip(loops, with_db["paradas_media"], strict=True):
            # Con 2 y 3 lazos el rótulo va a la derecha: a la izquierda quedan la leyenda y
            # la línea de Turing.
            right = x >= 2
            ax.annotate(
                _short(y),
                (x, y),
                xytext=(6 if right else -6, -3),
                textcoords="offset points",
                ha="left" if right else "right",
                va="center",
                color=t.text,
                fontsize="small",
                path_effects=_halo(t),
            )
        ax.set_yscale("log")
        ax.yaxis.set_major_locator(LogLocator(base=10, numticks=12))
        ax.yaxis.set_major_formatter(FuncFormatter(_log_ticks))
        ax.set_xticks(loops)
        ax.set_xlim(loops.min() - 0.45, loops.max() + 0.5)
        ax.set_xlabel("lazos del menú")
        ax.set_ylabel("paradas falsas por orden (escala log)")
        first, last = with_db["paradas_media"].iloc[0], with_db["paradas_media"].iloc[-1]
        ax.set_title(
            f"{letters} letras: de {fmt_int(round(first))} a {fmt_dec(last, 2)} paradas por orden"
        )
        ax.legend(loc="lower left", handlelength=1.8)
        fig.tight_layout()
    return fig


# ---------------------------------------------------------------- figura 3: E6

SPRT_ROWS = (
    ("exacto", "Cálculo exacto, tasa 1/17"),
    ("tasa_1_17/letras_1_17", "Simulación, tasa 1/17"),
    ("aleman/letras_1_17", "Alemán real, pesos de Turing"),
    ("aleman/trigramas", "Alemán real, hasta trigramas"),
)


def sprt_letters(e6: dict[str, Any], theme: str = "enigma_print") -> Any:
    """E6: letras hasta que el SPRT decide (α = β = 1 %), en profundidad y al azar.

    Barras con la media e IC 95 % de 2.000 pares; el cálculo exacto no tiene IC. Las líneas
    punteadas son la aproximación de Wald con letras sueltas y tasas 1/17 y 1/26.
    """
    values: list[tuple[str, dict[str, tuple[float, float, float]]]] = []
    for key, label in SPRT_ROWS:
        by_hypothesis = {}
        for hypothesis in ("profundidad", "azar"):
            if key == "exacto":
                mean = e6["exacto"][hypothesis]["letras"]
                low = high = mean
            else:
                cell = e6["simulacion"][key][hypothesis]
                mean, (low, high) = cell["letras"], cell["ic"]
            by_hypothesis[hypothesis] = (mean, low, high)
        values.append((label, by_hypothesis))
    wald = e6["wald"]
    sim = e6["simulacion"]["tasa_1_17/letras_1_17"]["profundidad"]["letras"]
    with _style(theme) as t:
        fig, ax = _new_figure(theme, "full")
        rows = np.arange(len(values))
        height = 0.38
        for offset, hypothesis, color, label, side in (
            (-height / 2, "profundidad", CATEGORICAL[0], "En profundidad", -1),
            (height / 2, "azar", CATEGORICAL[1], "Al azar", 1),
        ):
            means = np.array([v[hypothesis][0] for _, v in values])
            lows = np.array([v[hypothesis][1] for _, v in values])
            highs = np.array([v[hypothesis][2] for _, v in values])
            ax.barh(
                rows + offset,
                means,
                height=height * 0.92,
                color=color,
                label=label,
                xerr=[means - lows, highs - means],
                error_kw={"ecolor": t.text_muted, "capsize": 2, "elinewidth": 0.9},
                zorder=2,
            )
            for y, mean, high in zip(rows + offset, means, highs, strict=True):
                ax.annotate(
                    fmt_int(round(mean)),
                    (high, y),
                    xytext=(4, 0),
                    textcoords="offset points",
                    va="center",
                    color=t.text,
                    fontsize="small",
                )
            ax.axvline(wald[hypothesis], color=color, linestyle=":", linewidth=1.2, zorder=1)
            ax.annotate(
                f"Wald: {fmt_int(round(wald[hypothesis]))}",
                (wald[hypothesis], 0),
                xycoords=("data", "axes fraction"),
                xytext=(3 * side, 3),
                textcoords="offset points",
                ha="left" if side > 0 else "right",
                va="bottom",
                color=t.text_muted,
                fontsize="small",
                path_effects=_halo(t),
            )
        ax.set_yticks(rows, [label for label, _ in values])
        ax.invert_yaxis()
        ax.set_xlim(0, max(wald.values()) * 1.45)
        ax.xaxis.set_major_formatter(es_number())
        ax.set_xlabel("letras comparadas hasta decidir (media e IC 95 %; α = β = 1 %)")
        ax.grid(axis="y", visible=False)
        ax.set_title(
            f"Wald estima {fmt_int(round(wald['profundidad']))} letras; la simulación pide "
            f"{fmt_int(round(sim))}"
        )
        ax.legend(loc="lower right", bbox_to_anchor=(1, 0.1), ncol=2)
        fig.tight_layout()
    return fig


# ---------------------------------------------------------------- generación


def _results(results_dir: Path | None = None) -> dict[str, Any]:
    """Lo que leen las figuras: el resumen de cifras y las tablas agregadas de E4 y E5."""
    folder = results_dir or paths.RESULTS
    return {
        "summary": read_summary(folder),
        "e4": pd.read_parquet(folder / "e4_cribs.parquet"),
        "e5": pd.read_parquet(folder / "e5_bombe.parquet"),
    }


def _figures(data: dict[str, Any], theme: str) -> dict[str, Any]:
    summary = data["summary"]
    return {
        "e4_cribs": crib_survival(data["e4"], summary["e4"]["kappa_aleman_x"], theme),
        "e5_bombe": bombe_stops(data["e5"], theme=theme),
        "e6_sprt": sprt_letters(summary["e6"], theme),
    }


def _save(fig: Any, folder: Path, name: str, formats: tuple[str, ...]) -> list[Path]:
    import matplotlib.pyplot as plt

    folder.mkdir(parents=True, exist_ok=True)
    saved = []
    for ext in formats:
        path = folder / f"{name}.{ext}"
        fig.savefig(path, dpi=PNG_DPI, bbox_inches="tight")
        saved.append(path)
    plt.close(fig)
    return saved


def report_figures(out_dir: Path = REPORT_FIGURES, results_dir: Path | None = None) -> list[Path]:
    """Las tres figuras del informe en PDF (vectorial, para LaTeX) y PNG."""
    figures = _figures(_results(results_dir), "enigma_print")
    return [p for name, fig in figures.items() for p in _save(fig, out_dir, name, ("pdf", "png"))]


def slide_figures(
    out_dir: Path = paths.SLIDE_FIGURES, results_dir: Path | None = None
) -> list[Path]:
    """Respaldo de las diapositivas: E4 a E6 en 16:9 y las figuras de E2 y E3 en tema oscuro."""
    from enigma_lab.experiments import e2_keyspace, e3_statistics

    folder = results_dir or paths.RESULTS
    data = _results(results_dir)
    figures = _figures(data, "enigma_slides")
    figures["e2_espacio_de_claves"] = e2_keyspace.figure(
        pd.read_parquet(folder / "e2_espacio_de_claves.parquet"), theme="enigma_slides"
    )
    pairs = pd.read_parquet(folder / "e3_pares.parquet")
    figures["e3_estadistica"] = e3_statistics.figure(
        pd.read_parquet(folder / "e3_estadistica.parquet"),
        theme="enigma_slides",
        pairs=pairs.pivot(index="plano", columns="cifrado", values="n").to_numpy(),
    )
    return [p for name, fig in figures.items() for p in _save(fig, out_dir, name, ("png", "svg"))]


def main() -> list[Path]:
    """Genera las figuras del informe y las de respaldo de las diapositivas."""
    import matplotlib

    matplotlib.use("Agg")  # solo archivos, sin ventanas
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    saved = report_figures() + slide_figures()
    for path in saved:
        print(f"  {path.relative_to(paths.ROOT).as_posix()}")
    print(json.dumps({"figuras": len(saved)}, ensure_ascii=False))
    return saved


if __name__ == "__main__":
    main()
