"""E6 · ¿Cuánto solapamiento necesita el Banburismus?

**Pares.** Dos mensajes cifrados con la máquina real, con la misma clave diaria (Enigma I,
rotores I–V, 10 cables) y claves de mensaje que solo difieren en el rotor derecho
(``banburismus/depth.py``). Cada mensaje mide el solapamiento máximo más 25 letras, así
que todo desplazamiento de −25 a +25 tiene las mismas columnas.

- *Profundidad (H1):* las columnas del desplazamiento verdadero.
- *Azar (H0):* las de otro desplazamiento del mismo par, elegido al azar.

**Dos fuentes de texto plano** (D-043):

- ``tasa_1_17``: texto sintético cuyas columnas en profundidad repiten con 1/17, una por
  una e independientes. Es el modelo de Turing, en el que valen la aproximación de Wald
  y el cálculo exacto.
- ``aleman``: dos fragmentos reales del corpus, con la X como separador.

**Puntuaciones** (``banburismus/scoring.py``, D-044):

- letras sueltas con la tasa 1/17 de Turing;
- letras sueltas con la tasa medida en el corpus;
- bigramas y trigramas;
- hasta tetragramas.

Las tres últimas usan el corpus, así que solo se aplican al texto alemán.

**La prueba** (``banburismus/sprt.py``). El SPRT con los umbrales de Wald para α = β de
5 %, 1 % y 0,1 %, sobre el solapamiento máximo. Con un solapamiento L más corto la prueba
es la misma, truncada: decide si cruzó un umbral en las primeras L letras.

**Medidas.**

- *Aciertos:* fracción de pares que decide bien dentro del solapamiento.
- *Letras hasta decidir:* media, con IC 95 %, de las letras leídas hasta cruzar un umbral,
  o de todas si no lo cruzó.
- *Identificación:* fracción de pares en que el desplazamiento verdadero saca el mayor
  puntaje de los 51 (así se usaba en Bletchley Park).
- *Curva ROC* del puntaje tras L letras, sin detenerse: profundidad contra azar.

**Referencia.** La aproximación de Wald con letras sueltas y 1/17: 929 letras en
profundidad y 1.062 al azar. Con la fuente ``tasa_1_17`` se compara además con el cálculo
exacto, que incluye el sobrepaso de los umbrales.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from enigma_lab import SEED
from enigma_lab.banburismus.depth import (
    MAX_OFFSET,
    OFFSETS,
    DepthPairs,
    TextSource,
    false_offsets,
    make_pairs,
    repeats,
)
from enigma_lab.banburismus.scoring import (
    P_DEPTH,
    P_RANDOM,
    TURING,
    RepeatModel,
    column_weights,
    ngram_coincidence,
    scoring_model,
    trajectory,
)
from enigma_lab.banburismus.sprt import (
    SPRTResult,
    exact_turing,
    run_sprt,
    thresholds,
    wald_gap,
    wald_letters,
)
from enigma_lab.experiments.common import (
    Mode,
    RunInfo,
    output_dir,
    save_figure,
    save_table,
    update_summary,
)
from enigma_lab.stats.corpus import Mode as TextMode
from enigma_lab.stats.corpus import Source
from enigma_lab.stats.inference import mean_ci, wilson_interval

PARAMS: dict[str, dict[str, Any]] = {
    "rapido": {
        "n": 300,
        "max_letters": 6_000,
        "overlaps": [25, 50, 100, 200, 400, 800, 1_600],
        "alphas": [0.05, 0.01, 0.001],
        "corpus": "muestra",
        "trajectories": 10,
        "trajectory_letters": 2_000,
    },
    "completo": {
        "n": 2_000,
        "max_letters": 10_000,
        "overlaps": [25, 50, 100, 200, 400, 800, 1_600],
        "alphas": [0.05, 0.01, 0.001],
        "corpus": "completo",
        "trajectories": 12,
        "trajectory_letters": 3_000,
    },
}
SOURCES: dict[TextSource, tuple[str, ...]] = {
    "tasa_1_17": ("letras_1_17",),
    "aleman": ("letras_1_17", "letras", "trigramas", "tetragramas"),
}
HYPOTHESES = ("profundidad", "azar")
TEXT_MODE: TextMode = "x"
MAIN_ALPHA = 0.01
ROC_OVERLAP = 200
"""El solapamiento de la curva ROC de la figura y de la app."""
TRAJECTORY_STEP = 10
"""Las trayectorias guardadas tienen un punto cada 10 letras."""


def alpha_tag(alpha: float) -> str:
    """El α en porcentaje, para nombrar columnas: 0,05 → «5», 0,01 → «1», 0,001 → «0_1»."""
    return f"{100 * alpha:g}".replace(".", "_")


def combo(text: str, key: str) -> str:
    """Clave de una fuente con una puntuación: «aleman/trigramas»."""
    return f"{text}/{key}"


def reference_letters(alpha: float = MAIN_ALPHA) -> dict[str, float]:
    """La aproximación de Wald con letras sueltas y 1/17: 929 y 1.062 letras con α = β = 1 %."""
    return {
        "profundidad": wald_letters(TURING.drift(True), True, alpha),
        "azar": wald_letters(TURING.drift(False), False, alpha),
    }


# ---------------------------------------------------------------- simulación


def _test_frame(
    text: str, key: str, tested: dict[str, np.ndarray], truth: np.ndarray, result: SPRTResult
) -> pd.DataFrame:
    """Una fila por par e hipótesis: letras, decisión y puntaje para cada α, y puntajes por L."""
    n = len(truth)
    frames = []
    for h, hypothesis in enumerate(HYPOTHESES):
        rows = slice(h * n, (h + 1) * n)
        data: dict[str, Any] = {
            "fuente": text,
            "puntuacion": key,
            "hipotesis": hypothesis,
            "par": np.arange(n, dtype=np.int32),
            "desplazamiento": tested[hypothesis].astype(np.int16),
            "verdadero": truth.astype(np.int16),
        }
        for t, alpha in enumerate(result.alphas):
            tag = alpha_tag(alpha)
            data[f"letras_{tag}"] = result.letters[rows, t].astype(np.float32)
            data[f"decision_{tag}"] = result.decision[rows, t]
            data[f"final_{tag}"] = result.final[rows, t].astype(np.float32)
        for c, mark in enumerate(result.checkpoints):
            data[f"db_{mark}"] = result.at[rows, c].astype(np.float32)
        frames.append(pd.DataFrame(data))
    return pd.concat(frames, ignore_index=True)


def _trajectory_frame(
    text: str, key: str, x: dict[str, np.ndarray], model: RepeatModel, params: dict[str, Any]
) -> pd.DataFrame:
    """Las primeras trayectorias de cada hipótesis, sin detenerse, un punto cada 10 letras."""
    count, letters = params["trajectories"], params["trajectory_letters"]
    marks = np.arange(TRAJECTORY_STEP, letters + 1, TRAJECTORY_STEP)
    frames = []
    for hypothesis in HYPOTHESES:
        paths = trajectory(x[hypothesis][:count, :letters], model)
        for i, path in enumerate(paths):
            frames.append(
                pd.DataFrame(
                    {
                        "fuente": text,
                        "puntuacion": key,
                        "hipotesis": hypothesis,
                        "par": i,
                        "letra": marks,
                        "decibanes": path[marks - 1].astype(np.float32),
                    }
                )
            )
    return pd.concat(frames, ignore_index=True)


def identification(pairs: DepthPairs, model: RepeatModel, lengths: list[int]) -> dict[str, float]:
    """Fracción de pares en que el desplazamiento verdadero saca el mayor puntaje de los 51.

    Así se usaba Banburismus: se corrían los dos mensajes uno sobre otro y se elegía el
    desplazamiento con más decibanes. Con k empatados en el primer lugar cuenta 1/k, el
    acierto esperado de un desempate al azar. Las claves son los solapamientos, en texto.
    """
    ordered = sorted(lengths)
    marks = np.array(ordered) - 1
    scores = np.empty((len(OFFSETS), len(pairs), len(marks)))
    for i, d in enumerate(OFFSETS):
        x = repeats(pairs.cipher1, pairs.cipher2, int(d), ordered[-1])
        scores[i] = np.cumsum(column_weights(x, model), axis=1)[:, marks]
    truth = scores[pairs.offsets + MAX_OFFSET, np.arange(len(pairs))]
    top = scores.max(axis=0)
    tied = (scores >= top - 1e-9).sum(axis=0)
    hits = (truth >= top - 1e-9) / tied
    return {str(length): float(hits[:, c].mean()) for c, length in enumerate(ordered)}


def _pair_rates(x: np.ndarray) -> list[float]:
    """Tasa de repetición: la media de las tasas de cada par, con su IC 95 % (media, bajo, alto)."""
    return list(mean_ci(x.mean(axis=1)))


def run_with_trajectories(
    params: dict[str, Any], seed: int = SEED
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Las pruebas (una fila por fuente, puntuación, par e hipótesis) y algunas trayectorias."""
    rngs = np.random.default_rng(seed).spawn(len(SOURCES))
    longest = params["max_letters"]
    marks = sorted({*params["overlaps"], longest})
    tests, paths = [], []
    rates: dict[str, Any] = {}
    found: dict[str, dict[str, float]] = {}
    for rng, (text, scorings) in zip(rngs, SOURCES.items(), strict=True):
        pairs = make_pairs(
            rng, params["n"], longest + MAX_OFFSET, text, params["corpus"], TEXT_MODE
        )
        tested = {"profundidad": pairs.offsets, "azar": false_offsets(rng, pairs.offsets)}
        x = {h: repeats(pairs.cipher1, pairs.cipher2, tested[h], longest) for h in HYPOTHESES}
        rates[text] = {h: _pair_rates(x[h]) for h in HYPOTHESES}
        rates[text]["desplazamiento_positivo"] = float((pairs.offsets > 0).mean())
        stacked = np.concatenate([x[h] for h in HYPOTHESES])
        for key in scorings:
            model = scoring_model(key, params["corpus"], TEXT_MODE)
            result = run_sprt(stacked, model, params["alphas"], marks)
            tests.append(_test_frame(text, key, tested, pairs.offsets, result))
            paths.append(_trajectory_frame(text, key, x, model, params))
            found[combo(text, key)] = identification(pairs, model, params["overlaps"])
    df = pd.concat(tests, ignore_index=True)
    for column in ("fuente", "puntuacion", "hipotesis"):
        df[column] = df[column].astype("category")
    df.attrs["tasas"] = rates
    df.attrs["identificacion"] = found
    return df, pd.concat(paths, ignore_index=True)


def run(params: dict[str, Any], seed: int = SEED) -> pd.DataFrame:
    """Una fila por fuente, puntuación, par e hipótesis (profundidad o azar)."""
    return run_with_trajectories(params, seed)[0]


# ---------------------------------------------------------------- análisis


def alphas_in(df: pd.DataFrame) -> list[float]:
    """Los α de las columnas ``letras_*`` de la tabla de pruebas, de mayor a menor."""
    tags = [c.removeprefix("letras_") for c in df.columns if c.startswith("letras_")]
    return sorted((float(t.replace("_", ".")) / 100 for t in tags), reverse=True)


def marks_in(df: pd.DataFrame) -> list[int]:
    """Los solapamientos con puntaje anotado (columnas ``db_*``)."""
    return sorted(int(c.removeprefix("db_")) for c in df.columns if c.startswith("db_"))


def auc(positive: np.ndarray, negative: np.ndarray) -> float:
    """Área bajo la curva ROC: P(puntaje en profundidad > puntaje al azar), empates a medias.

    Es la U de Mann-Whitney dividida por n₁·n₀, con los rangos de todos los puntajes juntos.
    """
    ranks = rankdata(np.concatenate([positive, negative]))
    n1, n0 = len(positive), len(negative)
    return float((ranks[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def roc_points(positive: np.ndarray, negative: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """La curva ROC: para cada umbral t, de mayor a menor, (P(azar ≥ t), P(profundidad ≥ t))."""
    scores = np.concatenate([positive, negative])
    is_depth = np.r_[np.ones(len(positive), bool), np.zeros(len(negative), bool)]
    order = np.argsort(-scores, kind="mergesort")
    scores, is_depth = scores[order], is_depth[order]
    last_of_tie = np.r_[scores[1:] != scores[:-1], True]
    tpr = np.cumsum(is_depth)[last_of_tie] / len(positive)
    fpr = np.cumsum(~is_depth)[last_of_tie] / len(negative)
    return np.r_[0.0, fpr], np.r_[0.0, tpr]


ROC_GRID = np.unique(np.r_[np.linspace(0, 1, 101), np.geomspace(1e-3, 0.1, 25)])
"""Los falsos positivos en que se guarda cada curva ROC (más finos cerca de 0)."""


def scores_at(group: pd.DataFrame, mark: int) -> tuple[np.ndarray, np.ndarray]:
    """Puntajes tras ``mark`` letras: (en profundidad, al azar)."""
    depth = group.loc[group["hipotesis"] == "profundidad", f"db_{mark}"].to_numpy(float)
    chance = group.loc[group["hipotesis"] == "azar", f"db_{mark}"].to_numpy(float)
    return depth, chance


def roc_table(df: pd.DataFrame) -> pd.DataFrame:
    """Las curvas ROC por fuente, puntuación y solapamiento, en la rejilla ``ROC_GRID``."""
    rows = []
    for (text, key), group in df.groupby(["fuente", "puntuacion"], sort=False, observed=True):
        for mark in marks_in(df):
            depth, chance = scores_at(group, mark)
            fpr, tpr = roc_points(depth, chance)
            at_grid = tpr[np.searchsorted(fpr, ROC_GRID, side="right") - 1]
            area = auc(depth, chance)
            rows += [
                {
                    "fuente": text,
                    "puntuacion": key,
                    "solapamiento": mark,
                    "fpr": float(f),
                    "tpr": float(t),
                    "auc": area,
                }
                for f, t in zip(ROC_GRID, at_grid, strict=True)
            ]
    return pd.DataFrame(rows)


def _references(text: str, key: str, alpha: float, depth: bool, corpus: Source) -> dict[str, float]:
    """Wald con el modelo de la puntuación y, con la fuente de tasa 1/17, el cálculo exacto."""
    model = scoring_model(key, corpus, TEXT_MODE)
    out = {"wald": wald_letters(model.drift(depth), depth, alpha), "exacto": np.nan}
    if text == "tasa_1_17" and key == TURING.key:
        out["exacto"] = exact_turing(alpha, depth).letters
    return out


def _decisions(part: pd.DataFrame, alpha: float, wanted: int, mark: int) -> dict[str, Any]:
    """Aciertos, errores y letras leídas (con IC) de un grupo de pruebas, truncado en ``mark``."""
    tag = alpha_tag(alpha)
    letters = part[f"letras_{tag}"].to_numpy(float)
    decision = part[f"decision_{tag}"].to_numpy()
    decided = letters <= mark  # NaN (sin decidir) da False
    hits = int((decided & (decision == wanted)).sum())
    misses = int((decided & (decision == -wanted)).sum())
    mean, low, high = mean_ci(np.where(decided, letters, mark))
    hit_low, hit_high = wilson_interval(hits, len(part))
    return {
        "n": len(part),
        "aciertos": hits / len(part),
        "letras_media": mean,
        "ic_bajo": low,
        "ic_alto": high,
        "errores": misses / len(part),
        "sin_decidir": 1 - (hits + misses) / len(part),
        "aciertos_ic_bajo": hit_low,
        "aciertos_ic_alto": hit_high,
    }


def _overshoot(part: pd.DataFrame, alpha: float) -> dict[str, float]:
    """Sobrepaso medio de cada umbral y puntaje medio al decidir, E[S_N]."""
    tag = alpha_tag(alpha)
    upper, lower = thresholds(alpha)
    final = part[f"final_{tag}"].to_numpy(float)
    decision = part[f"decision_{tag}"].to_numpy()
    up, down = final[decision == 1], final[decision == -1]
    return {
        "sobrepaso_arriba_db": float((up - upper).mean()) if len(up) else np.nan,
        "sobrepaso_abajo_db": float((lower - down).mean()) if len(down) else np.nan,
        "puntaje_final_db": float(np.nanmean(final)) if len(up) + len(down) else np.nan,
    }


R4_COLUMNS = [
    "puntuacion",
    "solapamiento",
    "n",
    "aciertos",
    "letras_media",
    "ic_bajo",
    "ic_alto",
    "auc",
]


def aggregate(df: pd.DataFrame, corpus: Source = "completo") -> pd.DataFrame:
    """Tabla de la diapositiva 17 (``r4_banburismus.csv``).

    Una fila por fuente, puntuación, solapamiento, α e hipótesis, con las ocho columnas fijas
    primero. ``wald``, ``exacto``, los sobrepasos y ``wald_identidad`` (E[S_N] / deriva por
    letra) solo se llenan en el solapamiento máximo, el de la prueba sin truncar.
    """
    marks = marks_in(df)
    longest = marks[-1]
    found = df.attrs.get("identificacion", {})
    rows = []
    for (text, key), group in df.groupby(["fuente", "puntuacion"], sort=False, observed=True):
        areas = {mark: auc(*scores_at(group, mark)) for mark in marks}
        drift = {
            h: float(group.loc[group["hipotesis"] == h, f"db_{longest}"].mean()) / longest
            for h in HYPOTHESES
        }
        identified = found.get(combo(str(text), str(key)), {})
        for alpha in alphas_in(df):
            for hypothesis in HYPOTHESES:
                part = group[group["hipotesis"] == hypothesis]
                wanted = 1 if hypothesis == "profundidad" else -1
                depth = hypothesis == "profundidad"
                extra = _overshoot(part, alpha) | _references(
                    str(text), str(key), alpha, depth, corpus
                )
                extra["wald_identidad"] = extra["puntaje_final_db"] / drift[hypothesis]
                for mark in marks:
                    row = {
                        "puntuacion": key,
                        "solapamiento": mark,
                        **_decisions(part, alpha, wanted, mark),
                        "auc": areas[mark],
                        "fuente": text,
                        "hipotesis": hypothesis,
                        "alfa": alpha,
                        "umbral_db": thresholds(alpha)[0],
                        "identifica": identified.get(str(mark), np.nan),
                        "deriva_db": drift[hypothesis],
                    }
                    if mark == longest:
                        row |= extra
                    rows.append(row)
    table = pd.DataFrame(rows)
    return table[R4_COLUMNS + [c for c in table.columns if c not in R4_COLUMNS]]


def _cell(table: pd.DataFrame, text: str, key: str, hypothesis: str, mark: int) -> pd.Series:
    """La fila de la tabla con α = β = 1 % para una fuente, puntuación, hipótesis y solapamiento."""
    match = table[
        (table["fuente"] == text)
        & (table["puntuacion"] == key)
        & (table["hipotesis"] == hypothesis)
        & (table["solapamiento"] == mark)
        & np.isclose(table["alfa"], MAIN_ALPHA)
    ]
    return match.iloc[0]


def _model_entry(model: RepeatModel) -> dict[str, Any]:
    return {
        "probabilidades": [float(p) for p in model.probs],
        "repeticion_db": [float(v) for v in model.plus],
        "no_repeticion_db": [float(v) for v in model.minus],
        "por_letra_profundidad_db": model.drift(True),
        "por_letra_azar_db": model.drift(False),
    }


def summary(df: pd.DataFrame, params: dict[str, Any]) -> dict[str, Any]:
    """Cifras clave de E6."""
    corpus: Source = params["corpus"]
    table = aggregate(df, corpus)
    longest = marks_in(df)[-1]
    exact = {h: exact_turing(MAIN_ALPHA, h == "profundidad") for h in HYPOTHESES}
    out: dict[str, Any] = {
        "n_pares": params["n"],
        "letras_maximas": longest,
        "solapamientos": params["overlaps"],
        "alfas": params["alphas"],
        "corpus": corpus,
        "pesos": {
            "repeticion_db": float(TURING.plus[0]),
            "no_repeticion_db": float(TURING.minus[0]),
            "por_letra_profundidad_db": TURING.drift(True),
            "por_letra_azar_db": TURING.drift(False),
            "umbral_db": thresholds(MAIN_ALPHA)[0],
        },
        "wald": reference_letters(),
        "exacto": {
            h: {
                "letras": e.letters,
                "acepta_profundidad": e.accept_depth,
                "sobrepaso_arriba_db": e.overshoot_upper,
                "sobrepaso_abajo_db": e.overshoot_lower,
                "puntaje_final_db": e.mean_final,
            }
            for h, e in exact.items()
        },
        "brecha_wald": {h: wald_gap(MAIN_ALPHA, h == "profundidad") for h in HYPOTHESES},
        "por_alfa": {},
        "tasas": {
            "turing": P_DEPTH,
            "azar": P_RANDOM,
            "corpus_letras": ngram_coincidence(1, corpus, "letras"),
            "corpus_x": ngram_coincidence(1, corpus, "x"),
            "medidas": df.attrs.get("tasas", {}),
        },
        "simulacion": {},
        "solapamiento": {},
        "modelos": {
            key: _model_entry(scoring_model(key, corpus, TEXT_MODE)) for key in SOURCES["aleman"]
        },
    }
    for alpha in params["alphas"]:
        out["por_alfa"][alpha_tag(alpha)] = {
            "alfa": alpha,
            "umbral_db": thresholds(alpha)[0],
            "wald": reference_letters(alpha),
            "exacto": {
                h: {
                    "letras": exact_turing(alpha, h == "profundidad").letters,
                    "acepta_profundidad": exact_turing(alpha, h == "profundidad").accept_depth,
                }
                for h in HYPOTHESES
            },
        }
    for text, scorings in SOURCES.items():
        for key in scorings:
            cells = {h: _cell(table, text, key, h, longest) for h in HYPOTHESES}
            out["simulacion"][combo(text, key)] = {
                h: {
                    "letras": c["letras_media"],
                    "ic": [c["ic_bajo"], c["ic_alto"]],
                    "aciertos": c["aciertos"],
                    "errores": c["errores"],
                    "sin_decidir": c["sin_decidir"],
                    "wald": c["wald"],
                    "exacto": None if np.isnan(c["exacto"]) else c["exacto"],
                    "sobrepaso_arriba_db": c["sobrepaso_arriba_db"],
                    "sobrepaso_abajo_db": c["sobrepaso_abajo_db"],
                    "wald_identidad": c["wald_identidad"],
                }
                for h, c in cells.items()
            }
            out["solapamiento"][combo(text, key)] = {
                str(mark): {
                    "aciertos_profundidad": _cell(table, text, key, "profundidad", mark)[
                        "aciertos"
                    ],
                    "aciertos_azar": _cell(table, text, key, "azar", mark)["aciertos"],
                    "auc": _cell(table, text, key, "profundidad", mark)["auc"],
                    "identifica": _cell(table, text, key, "profundidad", mark)["identifica"],
                }
                for mark in params["overlaps"]
            }
    return out


# ---------------------------------------------------------------- figura

SHORT_LABELS = {
    "tasa_1_17/letras_1_17": "tasa 1/17, letras",
    "aleman/letras_1_17": "alemán, letras con 1/17",
    "aleman/letras": "alemán, letras con su tasa",
    "aleman/trigramas": "alemán, bigramas y trigramas",
    "aleman/tetragramas": "alemán, hasta tetragramas",
}
"""Etiquetas cortas para las leyendas."""


def _first_crossing(path: np.ndarray, upper: float, lower: float) -> int | None:
    """Índice del primer punto que cruza un umbral, o None si no cruza."""
    crossed = np.flatnonzero((path >= upper) | (path <= lower))
    return int(crossed[0]) if len(crossed) else None


def _below(ax: Any, columns: int) -> None:
    """Leyenda debajo del panel, para no tapar los datos."""
    ax.legend(fontsize="small", loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=columns)


def _hypothesis_label(hypothesis: str) -> str:
    return "en profundidad" if hypothesis == "profundidad" else "al azar"


def _trajectory_panel(ax: Any, paths: pd.DataFrame | None, theme: str, count: int = 8) -> None:
    """Trayectorias con tasa 1/17, cortadas donde cruzan un umbral (con un punto)."""
    from enigma_lab.viz.numfmt import fmt_dec
    from enigma_lab.viz.static_figs import es_number, tokens
    from enigma_lab.viz.theme import CATEGORICAL

    t = tokens(theme)
    upper, lower = thresholds(MAIN_ALPHA)
    if paths is not None and len(paths):
        part = paths[(paths["fuente"] == "tasa_1_17") & (paths["puntuacion"] == TURING.key)]
        for color, hypothesis in zip(CATEGORICAL, HYPOTHESES, strict=False):
            groups = part[part["hipotesis"] == hypothesis].groupby("par")
            for i, (_, path) in enumerate(groups):
                if i >= count:
                    break
                values, letters = path["decibanes"].to_numpy(), path["letra"].to_numpy()
                stop = _first_crossing(values, upper, lower)
                end = len(values) if stop is None else stop + 1
                ax.plot(
                    letters[:end],
                    values[:end],
                    color=color,
                    alpha=0.8,
                    linewidth=1.1,
                    label=_hypothesis_label(hypothesis) if i == 0 else None,
                )
                if stop is not None:
                    ax.plot(letters[stop], values[stop], "o", color=color, markersize=3.5)
    for y, label in ((upper, "aceptar profundidad"), (lower, "descartar")):
        ax.axhline(y, color=t.text_muted, linestyle="--", linewidth=1.1)
        sign = "+" if y > 0 else "−"
        ax.annotate(
            f"{label}: {sign}{fmt_dec(abs(y), 2)} dB",
            xy=(1, y),
            xycoords=("axes fraction", "data"),
            xytext=(-4, 4 if y > 0 else -12),
            textcoords="offset points",
            ha="right",
            color=t.text_muted,
            fontsize="small",
        )
    ax.set_title("Trayectorias con tasa 1/17")
    ax.set_xlabel("letras comparadas")
    ax.set_ylabel("decibanes acumulados")
    ax.xaxis.set_major_formatter(es_number())
    ax.yaxis.set_major_formatter(es_number())
    _below(ax, 2)


def _letters_panel(ax: Any, cells: pd.DataFrame, theme: str) -> None:
    """Letras hasta decidir por fuente y puntuación, con IC 95 % y las de Wald punteadas."""
    from enigma_lab.viz.numfmt import fmt_int
    from enigma_lab.viz.static_figs import es_number, tokens
    from enigma_lab.viz.theme import CATEGORICAL, ink_on

    t = tokens(theme)
    combos = [(text, key) for text, keys in SOURCES.items() for key in keys]
    y = np.arange(len(combos))
    for k, (color, hypothesis) in enumerate(zip(CATEGORICAL, HYPOTHESES, strict=False)):
        rows = [
            cells[
                (cells["fuente"] == a)
                & (cells["puntuacion"] == b)
                & (cells["hipotesis"] == hypothesis)
            ].iloc[0]
            for a, b in combos
        ]
        means = np.array([r["letras_media"] for r in rows])
        low = np.array([r["ic_bajo"] for r in rows])
        high = np.array([r["ic_alto"] for r in rows])
        place = y + (k - 0.5) * 0.4
        ax.barh(
            place,
            means,
            height=0.38,
            color=color,
            xerr=[means - low, high - means],
            error_kw={"ecolor": t.text_muted, "capsize": 2, "elinewidth": 1},
            label=_hypothesis_label(hypothesis),
        )
        for yy, m, lo in zip(place, means, low, strict=True):
            ax.annotate(
                fmt_int(round(m)),
                xy=(lo, yy),
                xytext=(-4, 0),
                textcoords="offset points",
                ha="right",
                va="center",
                fontsize="x-small",
                color=ink_on(color),
            )
    wald = reference_letters()
    for color, hypothesis in zip(CATEGORICAL, HYPOTHESES, strict=False):
        ax.axvline(wald[hypothesis], color=color, linestyle=":", linewidth=1.5)
        ax.annotate(
            f"Wald {fmt_int(round(wald[hypothesis]))}",
            xy=(wald[hypothesis], 1),
            xycoords=("data", "axes fraction"),
            xytext=(3, -10 if hypothesis == "profundidad" else -22),
            textcoords="offset points",
            color=color,
            fontsize="x-small",
        )
    ax.set_yticks(y, [SHORT_LABELS[combo(a, b)] for a, b in combos], fontsize="small")
    ax.invert_yaxis()
    ax.set_title("Letras hasta decidir con α = β = 1 %")
    ax.set_xlabel("letras (media e IC 95 %)")
    ax.xaxis.set_major_formatter(es_number())
    _below(ax, 2)


def _roc_panel(ax: Any, df: pd.DataFrame, theme: str) -> None:
    """Curvas ROC del puntaje tras ``ROC_OVERLAP`` letras, con su AUC en la leyenda."""
    from enigma_lab.viz.numfmt import fmt_dec
    from enigma_lab.viz.static_figs import es_number, tokens
    from enigma_lab.viz.theme import CATEGORICAL

    t = tokens(theme)
    mark = ROC_OVERLAP if ROC_OVERLAP in marks_in(df) else marks_in(df)[0]
    combos = [(text, key) for text, keys in SOURCES.items() for key in keys]
    for color, (text, key) in zip(CATEGORICAL, combos, strict=False):
        group = df[(df["fuente"] == text) & (df["puntuacion"] == key)]
        depth, chance = scores_at(group, mark)
        fpr, tpr = roc_points(depth, chance)
        ax.step(
            fpr,
            tpr,
            where="post",
            color=color,
            linewidth=1.5,
            label=f"{SHORT_LABELS[combo(text, key)]}: AUC {fmt_dec(auc(depth, chance), 3)}",
        )
    ax.plot([0, 1], [0, 1], color=t.text_muted, linestyle="--", linewidth=1)
    ax.set_title(f"Curva ROC con {mark} letras")
    ax.set_xlabel("falsos positivos")
    ax.set_ylabel("verdaderos positivos")
    ax.set_aspect("equal")
    ax.xaxis.set_major_formatter(es_number(1))
    ax.yaxis.set_major_formatter(es_number(1))
    ax.legend(fontsize="x-small", loc="lower right")  # bajo la diagonal no hay curvas


def figure(
    df: pd.DataFrame,
    theme: str = "enigma_print",
    trajectories: pd.DataFrame | None = None,
    corpus: Source = "completo",
) -> Any:
    """Trayectorias, letras hasta decidir frente a Wald y curvas ROC."""
    import matplotlib.pyplot as plt

    from enigma_lab.viz.numfmt import fmt_int
    from enigma_lab.viz.theme import mpl_style_context

    table = aggregate(df, corpus)
    longest = marks_in(df)[-1]
    cells = table[np.isclose(table["alfa"], MAIN_ALPHA) & (table["solapamiento"] == longest)]
    with mpl_style_context(theme):
        fig, axes = plt.subplots(
            1, 3, figsize=(17, 6), gridspec_kw={"width_ratios": [1.15, 1.2, 0.85]}
        )
        _trajectory_panel(axes[0], trajectories, theme)
        _letters_panel(axes[1], cells, theme)
        _roc_panel(axes[2], df, theme)
        first = _cell(table, "tasa_1_17", TURING.key, "profundidad", longest)
        fig.suptitle(
            f"Con letras sueltas y tasa 1/17, la profundidad se confirma en "
            f"{fmt_int(round(first['letras_media']))} letras (Wald: "
            f"{fmt_int(round(reference_letters()['profundidad']))})"
        )
        fig.tight_layout()
    return fig


def main(mode: Mode = "completo", seed: int = SEED) -> dict[str, Any]:
    """Corre E6 y guarda sus resultados."""
    folder = output_dir(mode)
    started = time.perf_counter()
    params = PARAMS[mode]
    df, paths = run_with_trajectories(params, seed)
    figures = summary(df, params) | {"segundos": round(time.perf_counter() - started, 1)}
    save_table(df, "e6_banburismus_pruebas", folder)
    save_table(aggregate(df, params["corpus"]), "e6_banburismus", folder)
    save_table(roc_table(df), "e6_banburismus_roc", folder)
    save_table(paths, "e6_banburismus_trayectorias", folder)
    update_summary("e6", figures, RunInfo("e6", mode, seed), folder)

    import matplotlib.pyplot as plt

    fig = figure(df, trajectories=paths, corpus=params["corpus"])
    save_figure(fig, "e6_banburismus", folder)
    plt.close(fig)
    return figures
