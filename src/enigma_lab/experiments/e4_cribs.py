"""E4 · ¿Cuántas posiciones descarta un crib? (spec 7)

Para cada longitud L del crib se cifran N mensajes de 250 letras con claves aleatorias
de Enigma I (10 cables). En cada mensaje se toma como crib el tramo de L letras que
empieza en una posición al azar t, y se arrastra sobre el cifrado. La alineación
verdadera (t) sobrevive siempre; se mide qué fracción de las falsas sobrevive.

**Dos textos.**
- *Aleatorio:* letras uniformes, como el piloto. La teoría es (25/26)^L.
- *Alemán real:* fragmentos del corpus con la X como separador, al estilo militar.

**La teoría con alemán.** En una alineación falsa, la letra j del crib (p_{t+j}) choca
con la cifrada en s + j solo si es distinta de la letra plana de esa posición
(p_{s+j}), y entonces con probabilidad 1/25, porque el cifrado es uniforme entre las 25
letras distintas de la plana. Con κ, la probabilidad de que dos letras del texto
coincidan (el IC):

    P(sobrevive) ≈ (1 − (1 − κ)/25)^L,

que con κ = 1/26 vuelve a dar (25/26)^L. En alemán, κ ≈ 0,08 > 1/26, así que se espera
que sobrevivan un poco más alineaciones falsas que con texto aleatorio.

**IC 95 %.** Las alineaciones de un mismo mensaje no son independientes. Por eso el
intervalo se calcula con la media de las fracciones por mensaje: media ± 1,96 · s/√N.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import pandas as pd

from enigma_lab import SEED
from enigma_lab.core.batch import encrypt_batch, random_key_batch
from enigma_lab.cribs.dragging import survival_probability, survives
from enigma_lab.experiments.common import Mode, RunInfo, save_figure, save_table, update_summary
from enigma_lab.stats.corpus import Source, load_codes, random_excerpts
from enigma_lab.stats.frequencies import index_of_coincidence
from enigma_lab.stats.inference import mean_ci

PARAMS: dict[str, dict[str, Any]] = {
    "rapido": {
        "n": 200,
        "lengths": [5, 10, 13, 20, 30, 50],
        "message_length": 250,
        "source": "muestra",
    },
    "completo": {
        "n": 1_000,
        "lengths": [5, 8, 10, 13, 15, 20, 25, 30, 40, 50],
        "message_length": 250,
        "source": "completo",
    },
}
TEXTS = ("aleatorio", "aleman")
TEXT_LABELS = {"aleatorio": "Texto aleatorio", "aleman": "Alemán real (X como separador)"}
PILOT_L13 = 0.600
"""Referencia del piloto (spec, tabla de E4): 60,0 % con L = 13, texto aleatorio."""


def kappa(text: str, source: Source) -> float:
    """Probabilidad de que dos letras del texto coincidan: 1/26 al azar, el IC en alemán."""
    if text == "aleatorio":
        return 1 / 26
    return float(index_of_coincidence(load_codes("aleman", source, "x")))


def theory(length: int, k: float) -> float:
    """(1 − (1 − κ)/25)^L, la supervivencia esperada de una alineación falsa."""
    return float((1 - (1 - k) / 25) ** length)


def _messages(
    rng: np.random.Generator, text: str, n: int, length: int, source: Source
) -> np.ndarray:
    if text == "aleatorio":
        return rng.integers(0, 26, size=(n, length), dtype=np.uint8)
    return random_excerpts(rng, "aleman", n, length, source, mode="x")


def run(params: dict[str, Any], seed: int = SEED) -> pd.DataFrame:
    """Una fila por mensaje: cuántas alineaciones falsas sobrevivieron."""
    conditions = [(text, length) for text in TEXTS for length in params["lengths"]]
    rngs = np.random.default_rng(seed).spawn(len(conditions))
    m, n = params["message_length"], params["n"]
    frames = []
    for rng, (text, length) in zip(rngs, conditions, strict=True):
        plain = _messages(rng, text, n, m, params["source"])
        keys, _ = random_key_batch(rng, n, model="I", cables=10)
        cipher = encrypt_batch(keys, plain)
        starts = rng.integers(0, m - length + 1, size=n)
        cribs = plain[np.arange(n)[:, None], starts[:, None] + np.arange(length)]
        ok = survives(cipher, cribs)
        true_ok = ok[np.arange(n), starts]
        false_total = m - length  # todas las alineaciones menos la verdadera
        surviving = ok.sum(axis=1) - true_ok
        frames.append(
            pd.DataFrame(
                {
                    "texto": text,
                    "L": length,
                    "falsas": false_total,
                    "sobreviven": surviving,
                    "fraccion": surviving / false_total,
                    "verdadera_sobrevive": true_ok,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def aggregate(df: pd.DataFrame, source: Source) -> pd.DataFrame:
    """Tabla de la diapositiva 15 (``r2_cribs.csv``): una fila por texto y longitud."""
    rows = []
    for (text, length), group in df.groupby(["texto", "L"], sort=False):
        mean, low, high = mean_ci(group["fraccion"].to_numpy())
        rows.append(
            {
                "L": int(length),
                "texto": text,
                "n": int(group["falsas"].sum()),
                "sobreviven": int(group["sobreviven"].sum()),
                "p": mean,
                "ic_bajo": low,
                "ic_alto": high,
                "teorico": survival_probability(int(length)),
                "teorico_kappa": theory(int(length), kappa(str(text), source)),
                "mensajes": len(group),
            }
        )
    return pd.DataFrame(rows)


def summary(df: pd.DataFrame, params: dict[str, Any]) -> dict[str, Any]:
    """Cifras clave de E4."""
    table = aggregate(df, params["source"])
    inside = (table["ic_bajo"] <= table["teorico"]) & (table["teorico"] <= table["ic_alto"])
    inside_k = (table["ic_bajo"] <= table["teorico_kappa"]) & (
        table["teorico_kappa"] <= table["ic_alto"]
    )
    out: dict[str, Any] = {
        "n_por_L": params["n"],
        "longitudes": params["lengths"],
        "letras_por_mensaje": params["message_length"],
        "fuente": params["source"],
        "verdadera_sobrevive_siempre": bool(df["verdadera_sobrevive"].all()),
        "kappa_aleman_x": kappa("aleman", params["source"]),
        "referencia_piloto_L13": PILOT_L13,
    }
    for text in TEXTS:
        part = table[table["texto"] == text]
        out[text] = {
            "teoria_25_26_dentro_del_ic": f"{int(inside[part.index].sum())} de {len(part)}",
            "teoria_kappa_dentro_del_ic": f"{int(inside_k[part.index].sum())} de {len(part)}",
            "por_L": {
                str(r.L): {
                    "p": r.p,
                    "ic": [r.ic_bajo, r.ic_alto],
                    "teorico": r.teorico,
                    "teorico_kappa": r.teorico_kappa,
                }
                for r in part.itertuples()
            },
        }
    return out


def figure(df: pd.DataFrame, theme: str = "enigma_print", source: Source = "completo") -> Any:
    """Supervivencia de las alineaciones falsas según L, con la teoría (25/26)^L."""
    import matplotlib.pyplot as plt

    from enigma_lab.viz.numfmt import fmt_pct
    from enigma_lab.viz.static_figs import es_number, es_percent, tokens
    from enigma_lab.viz.theme import CATEGORICAL, mpl_style_context

    t = tokens(theme)
    table = aggregate(df, source)
    with mpl_style_context(theme):
        fig, ax = plt.subplots()
        grid = np.arange(int(table["L"].min()), int(table["L"].max()) + 1)
        ax.plot(
            grid,
            (25 / 26) ** grid,
            color=t.text_muted,
            linewidth=1.5,
            zorder=1,
            label=r"Teoría: $(25/26)^L$",
        )
        for color, text in zip(CATEGORICAL, TEXTS, strict=False):
            part = table[table["texto"] == text]
            ax.errorbar(
                part["L"],
                part["p"],
                yerr=[part["p"] - part["ic_bajo"], part["ic_alto"] - part["p"]],
                fmt="o",
                color=color,
                capsize=3,
                label=TEXT_LABELS[text],
                zorder=3,
            )
            if text == "aleman":
                k = kappa("aleman", source)
                ax.plot(
                    grid,
                    [theory(int(x), k) for x in grid],
                    color=color,
                    linestyle="--",
                    linewidth=1.2,
                    zorder=2,
                    label="Teoría con el IC del alemán",
                )
        random13 = table[(table["texto"] == "aleatorio") & (table["L"] == 13)]
        title = "Las alineaciones falsas sobreviven como predice la teoría"
        if not random13.empty:
            p13 = float(random13["p"].iloc[0])
            title = f"Con 13 letras sobrevive el {fmt_pct(p13)} de las posiciones falsas"
        ax.set_title(title)
        ax.text(
            0.99,
            0.97,
            f"teoría con 13 letras: {fmt_pct(survival_probability(13))}",
            transform=ax.transAxes,
            ha="right",
            va="top",
            color=t.text_muted,
            fontsize="small",
        )
        ax.set_xlabel("longitud del crib L (letras)")
        ax.set_ylabel("alineaciones falsas que sobreviven")
        ax.set_ylim(0, 1)
        ax.yaxis.set_major_formatter(es_percent())
        ax.xaxis.set_major_formatter(es_number())
        ax.legend(fontsize="small", loc="lower left")
        fig.tight_layout()
    return fig


def main(mode: Mode = "completo", seed: int = SEED) -> dict[str, Any]:
    """Corre E4 y guarda sus resultados."""
    started = time.perf_counter()
    params = PARAMS[mode]
    df = run(params, seed)
    figures = summary(df, params) | {"segundos": round(time.perf_counter() - started, 1)}
    save_table(df, "e4_cribs_mensajes")
    save_table(aggregate(df, params["source"]), "e4_cribs")
    update_summary("e4", figures, RunInfo("e4", mode, seed))

    import matplotlib.pyplot as plt

    fig = figure(df, source=params["source"])
    save_figure(fig, "e4_cribs")
    plt.close(fig)
    return figures
