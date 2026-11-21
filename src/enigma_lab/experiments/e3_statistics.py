"""E3 · ¿Qué estadística se filtra y cuál no? (spec 7)

Para cada idioma (alemán, español) y longitud L se cifran N fragmentos reales del
corpus, cada uno con su propia clave aleatoria de Enigma I (10 cables). Por mensaje se
miden:

- el índice de coincidencia (IC) del texto plano y del cifrado;
- la prueba χ² de uniformidad de las 26 letras, en el plano y en el cifrado;
- los puntos fijos, que deben ser siempre 0.

**Lo que se espera.** El IC del plano queda en el del idioma (≈ 0,076 en alemán); el
del cifrado cae a 1/26, porque Enigma cambia de sustitución en cada letra. La χ²
rechaza la uniformidad del plano y no la del cifrado. Pero hay algo que se filtra
siempre: ninguna letra se cifra a sí misma, y la diagonal de la matriz plano × cifrado
es cero. Ese es el distinguidor: con L letras al azar, ningún punto fijo pasaría con
probabilidad (25/26)^L.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import pandas as pd

from enigma_lab import SEED
from enigma_lab.core.batch import encrypt_batch, random_key_batch
from enigma_lab.experiments.common import Mode, RunInfo, save_figure, save_table, update_summary
from enigma_lab.stats.corpus import ALL_LANGUAGES, LANGUAGES, Source, load_codes, random_excerpts
from enigma_lab.stats.frequencies import (
    GERMAN_IC_REFERENCE,
    RANDOM_IC,
    chi2_uniform,
    index_of_coincidence,
    pair_matrix,
)
from enigma_lab.stats.inference import mean_ci, no_fixed_point_probability

PARAMS: dict[str, dict[str, Any]] = {
    "rapido": {"n": 200, "lengths": [50, 100, 250, 500], "source": "muestra"},
    "completo": {"n": 1_000, "lengths": [25, 50, 100, 250, 500, 1_000], "source": "completo"},
}
ALPHA = 0.05


def run(params: dict[str, Any], seed: int = SEED) -> pd.DataFrame:
    """Una fila por mensaje (la matriz plano × cifrado la da :func:`run_with_pairs`)."""
    return run_with_pairs(params, seed)[0]


def run_with_pairs(params: dict[str, Any], seed: int = SEED) -> tuple[pd.DataFrame, np.ndarray]:
    """Los mensajes y la matriz 26 × 26 plano × cifrado del alemán con la mayor longitud."""
    conditions = [(lang, length) for lang in ALL_LANGUAGES for length in params["lengths"]]
    rngs = np.random.default_rng(seed).spawn(len(conditions))
    frames, pairs = [], np.zeros((26, 26), dtype=np.int64)
    source: Source = params["source"]
    for rng, (language, length) in zip(rngs, conditions, strict=True):
        plain = random_excerpts(rng, language, params["n"], length, source)
        keys, _ = random_key_batch(rng, params["n"], model="I", cables=10)
        cipher = encrypt_batch(keys, plain)
        _, p_plain = chi2_uniform(plain)
        _, p_cipher = chi2_uniform(cipher)
        frames.append(
            pd.DataFrame(
                {
                    "idioma": language,
                    "L": length,
                    "ic_plano": index_of_coincidence(plain),
                    "ic_cifrado": index_of_coincidence(cipher),
                    "p_plano": p_plain,
                    "p_cifrado": p_cipher,
                    "puntos_fijos": (plain == cipher).sum(axis=1),
                }
            )
        )
        if language == "aleman" and length == max(params["lengths"]):
            pairs += pair_matrix(plain, cipher)
    return pd.concat(frames, ignore_index=True), pairs


def by_condition(df: pd.DataFrame) -> pd.DataFrame:
    """Medias con IC 95 % y tasas de rechazo de la uniformidad, por idioma y longitud."""
    rows = []
    for (language, length), group in df.groupby(["idioma", "L"]):
        ic_p = mean_ci(group["ic_plano"].to_numpy())
        ic_c = mean_ci(group["ic_cifrado"].to_numpy())
        rows.append(
            {
                "idioma": language,
                "L": int(length),
                "n": len(group),
                "ic_plano": ic_p[0],
                "ic_plano_bajo": ic_p[1],
                "ic_plano_alto": ic_p[2],
                "ic_cifrado": ic_c[0],
                "ic_cifrado_bajo": ic_c[1],
                "ic_cifrado_alto": ic_c[2],
                "rechaza_plano": float((group["p_plano"] < ALPHA).mean()),
                "rechaza_cifrado": float((group["p_cifrado"] < ALPHA).mean()),
                "puntos_fijos": int(group["puntos_fijos"].sum()),
                "distinguidor": no_fixed_point_probability(int(length)),
            }
        )
    return pd.DataFrame(rows)


def pairs_table(matrix: np.ndarray) -> pd.DataFrame:
    """La matriz 26 × 26 en formato largo: plano, cifrado, n."""
    letters = [chr(65 + i) for i in range(26)]
    return pd.DataFrame(
        [(letters[i], letters[j], int(matrix[i, j])) for i in range(26) for j in range(26)],
        columns=["plano", "cifrado", "n"],
    )


def summary(df: pd.DataFrame, params: dict[str, Any]) -> dict[str, Any]:
    """Cifras clave de E3."""
    table = by_condition(df)
    longest = table[table["L"] == table["L"].max()].set_index("idioma")
    source: Source = params["source"]
    figures: dict[str, Any] = {
        "n_por_condicion": params["n"],
        "longitudes": params["lengths"],
        "fuente": source,
        "ic_referencia_aleman": GERMAN_IC_REFERENCE,
        "ic_azar": RANDOM_IC,
        "puntos_fijos": int(df["puntos_fijos"].sum()),
        "letras": int(df["L"].sum()),
    }
    for language in ALL_LANGUAGES:
        row = longest.loc[language]
        figures[language] = {
            "ic_corpus": index_of_coincidence(load_codes(language, source)),
            "L": int(row["L"]),
            "ic_plano": [row["ic_plano"], row["ic_plano_bajo"], row["ic_plano_alto"]],
            "ic_cifrado": [row["ic_cifrado"], row["ic_cifrado_bajo"], row["ic_cifrado_alto"]],
            "rechaza_plano": row["rechaza_plano"],
            "rechaza_cifrado": row["rechaza_cifrado"],
        }
    return figures


def figure(df: pd.DataFrame, theme: str = "enigma_print", pairs: np.ndarray | None = None) -> Any:
    """IC según la longitud (plano y cifrado, con IC 95 %) y la matriz plano × cifrado."""
    import matplotlib.pyplot as plt

    from enigma_lab.viz.numfmt import fmt_dec
    from enigma_lab.viz.static_figs import es_number, reference_line, tokens
    from enigma_lab.viz.theme import (
        CATEGORICAL,
        SEQUENTIAL_DARK,
        SEQUENTIAL_PRINT,
        mpl_style_context,
    )

    t = tokens(theme)
    table = by_condition(df)
    matrix = pairs
    with mpl_style_context(theme):
        fig, (left, right) = plt.subplots(1, 2, gridspec_kw={"width_ratios": [1.3, 1]})
        for color, language in zip(CATEGORICAL, ALL_LANGUAGES, strict=False):
            part = table[table["idioma"] == language]
            name = LANGUAGES[language]
            for kind, marker in (("plano", "o"), ("cifrado", "s")):
                left.plot(
                    part["L"],
                    part[f"ic_{kind}"],
                    marker=marker,
                    color=color,
                    linestyle="-" if kind == "plano" else ":",
                    label=f"{name}, {kind}",
                )
                left.fill_between(
                    part["L"],
                    part[f"ic_{kind}_bajo"],
                    part[f"ic_{kind}_alto"],
                    color=color,
                    alpha=0.15,
                    linewidth=0,
                )
        reference_line(left, GERMAN_IC_REFERENCE, "alemán, Pommerening: 0,0758", theme)
        reference_line(left, RANDOM_IC, "al azar: 1/26 ≈ 0,0385", theme)
        from matplotlib.ticker import NullFormatter

        left.set_xscale("log")
        left.set_xticks(sorted(table["L"].unique()))
        left.xaxis.set_minor_formatter(NullFormatter())
        left.set_xlabel("longitud del mensaje (letras, escala log)")
        left.set_ylabel("índice de coincidencia")
        left.xaxis.set_major_formatter(es_number())
        left.yaxis.set_major_formatter(es_number(3))
        de = table[(table["idioma"] == "aleman") & (table["L"] == table["L"].max())].iloc[0]
        left.set_title(
            f"Enigma lleva el IC de {fmt_dec(de['ic_plano'], 3)} a {fmt_dec(de['ic_cifrado'], 4)}"
        )
        left.legend(fontsize="x-small", loc="center right")

        if matrix is not None:
            ramp = SEQUENTIAL_PRINT if theme == "enigma_print" else SEQUENTIAL_DARK
            from matplotlib.colors import LinearSegmentedColormap

            cmap = LinearSegmentedColormap.from_list("ambar", [t.background, *ramp])
            image = right.imshow(matrix, cmap=cmap, interpolation="nearest")
            letters = [chr(65 + i) for i in range(26)]
            right.set_xticks(range(0, 26, 5), letters[::5])
            right.set_yticks(range(0, 26, 5), letters[::5])
            right.set_xlabel("letra cifrada")
            right.set_ylabel("letra plana")
            right.grid(visible=False)
            right.set_title("La diagonal es cero")
            fig.colorbar(image, ax=right, fraction=0.046, pad=0.04, format=es_number()).set_label(
                "veces"
            )
        fig.tight_layout()
    return fig


def main(mode: Mode = "completo", seed: int = SEED) -> dict[str, Any]:
    """Corre E3 y guarda sus resultados."""
    started = time.perf_counter()
    params = PARAMS[mode]
    df, pairs = run_with_pairs(params, seed)
    figures = summary(df, params) | {"segundos": round(time.perf_counter() - started, 1)}
    save_table(df, "e3_estadistica")
    save_table(by_condition(df), "e3_condiciones")
    save_table(pairs_table(pairs), "e3_pares")
    update_summary("e3", figures, RunInfo("e3", mode, seed))

    import matplotlib.pyplot as plt

    fig = figure(df, pairs=pairs)
    save_figure(fig, "e3_estadistica")
    plt.close(fig)
    return figures
