"""E8 · ¿Cuánto texto necesita el ataque moderno solo con texto cifrado?

**Mensajes.** Fragmentos alemanes del corpus (X como separador) de L letras, cifrados con
claves aleatorias de Enigma I (rotores I–V, reflector B, anillos y posiciones al azar) con k
cables. Factores: la longitud (25 a 1.500 letras) y los cables (6, 8 y 10).

**El ataque** (``attacks/gillogly.py``). Las tres fases de Gillogly (1995): IC con anillos
fijos sobre los órdenes y las 17.576 posiciones, los 676 anillos de las mejores ubicaciones y
el hill climbing del plugboard (IC y luego trigramas), con el reajuste de los anillos de
D-066. Éxito: el descifrado coincide con el texto en al menos el 90 % de las letras.

**Dónde falla.** Como se conoce la clave, se mide además:
- el puesto de la ubicación verdadera en la fase 1 (cuántas ubicaciones falsas tienen más IC);
- el hill climbing desde la ubicación verdadera (el «oráculo»), con el plugboard vacío como
  Gillogly y con la búsqueda parcial de la E de Ostwald y Weierud. Es lo que queda cuando la
  búsqueda de la ubicación no falla: Ostwald y Weierud la evitan haciendo el hill climbing en
  todas las ubicaciones, con días de cómputo.

**Estadística.** Tasa de éxito con intervalo de Wilson por celda y regresión logística
(statsmodels) del éxito contra log₁₀ L y los cables; de ella, la longitud con 50 % de éxito
para cada número de cables, con su IC por el método delta. Tiempo por mensaje.

**Referencias** (``data/reference/ostwald_weierud_2017.json``). Gillogly: unas 300 letras con 6
cables o menos, y un solo éxito con 10 cables, con 1.463 letras. Distancia de unicidad: unas 23
letras. Los mensajes reales no pasaban de 250 letras.

**Presupuesto:** menos de 40 min. D-067 explica N y los órdenes de cada modo.
"""

from __future__ import annotations

import json
import math
import time
import warnings
from typing import Any

import numpy as np
import pandas as pd

from enigma_lab import SEED, paths
from enigma_lab.attacks import gillogly, hillclimb
from enigma_lab.bombe.scrambler import rotor_orders
from enigma_lab.core.machine import encrypt
from enigma_lab.core.random_keys import random_config
from enigma_lab.core.wiring import ALPHABET
from enigma_lab.experiments.common import (
    Mode,
    RunInfo,
    output_dir,
    save_figure,
    save_table,
    update_summary,
)
from enigma_lab.stats.corpus import Source, random_excerpts
from enigma_lab.stats.inference import wilson_interval

PARAMS: dict[str, dict[str, Any]] = {
    "rapido": {
        "lengths": [50, 150, 400, 1_000],
        "cables": [6, 10],
        "n": 4,
        "rotors": ["I", "II", "III"],
        "top1": 200,
        "top2": 20,
        "source": "muestra",
    },
    "completo": {
        "lengths": [25, 50, 75, 100, 150, 200, 300, 400, 600, 800, 1_000, 1_500],
        "cables": [6, 8, 10],
        "n": 24,
        "rotors": ["I", "II", "III", "IV", "V"],
        "top1": 200,
        "top2": 20,
        "source": "completo",
    },
}
SUCCESS = 0.9
"""Fracción de letras correctas desde la que el mensaje se considera leído."""
REFERENCE_FILE = paths.REFERENCE / "ostwald_weierud_2017.json"


def references() -> dict[str, Any]:
    """Las cifras de Gillogly (según Ostwald y Weierud) y de Ostwald y Weierud, con su cita."""
    data: dict[str, Any] = json.loads(REFERENCE_FILE.read_text(encoding="utf-8"))
    return data


def to_codes(text: str) -> np.ndarray:
    return np.frombuffer(text.encode("ascii"), dtype=np.uint8).astype(np.int64) - 65


def true_location(config: Any) -> gillogly.Candidate:
    """La ubicación verdadera: orden, posición del núcleo al empezar y anillos central y derecho."""
    left, middle, right = (
        (p - r) % 26 for p, r in zip(config.positions, config.rings, strict=True)
    )
    return gillogly.Candidate(
        tuple(config.rotors), left * 676 + middle * 26 + right, config.rings[1], config.rings[2]
    )


def trial(
    rng: np.random.Generator,
    length: int,
    cables: int,
    params: dict[str, Any],
    logp3: np.ndarray,
) -> dict[str, Any]:
    """Un mensaje: la clave, el ataque completo y el hill climbing desde la ubicación verdadera."""
    config = random_config(rng, cables=cables, rotors=params["rotors"])
    source: Source = params["source"]
    plain = random_excerpts(rng, "aleman", 1, length, source, "x")[0].astype(np.int64)
    cipher = to_codes(encrypt(config, "".join(ALPHABET[c] for c in plain)))
    orders = tuple(rotor_orders(tuple(params["rotors"])))
    truth = true_location(config)

    started = time.perf_counter()
    result = gillogly.attack(cipher, orders, params["top1"], params["top2"])
    seconds = time.perf_counter() - started
    accuracy = float((result.best.plaintext == plain).mean())
    rank = result.rank_of(truth.order, truth.start)
    # Diagnóstico: el IC de la ubicación verdadera con sus anillos verdaderos, frente a las
    # ubicaciones de la fase 1 (anillos AAA). Si la fase 1 probara también los anillos, la
    # competencia crecería en proporción (D-067).
    right_rings = gillogly.ic_at(cipher, truth.order, truth.start, truth.ring_m, truth.ring_r)
    rank_rings = int(sum(int((v > right_rings).sum()) for v in result.scores.values()))
    oracle = gillogly.climb_at(cipher, truth, logp3)
    oracle_e = gillogly.climb_at(cipher, truth, logp3, partial=True)
    best = result.best.candidate
    return {
        "L": length,
        "cables": cables,
        "orden": "-".join(config.rotors),
        "aciertos": accuracy,
        "exito": accuracy >= SUCCESS,
        "orden_correcto": best.order == truth.order,
        "fase1_puesto": rank,
        "fase1_encontrada": rank < params["top1"],
        "fase1_puesto_anillos_verdaderos": rank_rings,
        "top1": params["top1"],
        "ic_verdadera": float(
            max(result.scores[truth.order][s] for s in gillogly.neighbours(truth.start, both=True))
        ),
        "ic_verdadera_anillos": right_rings,
        "ic_mejor": result.phase1[0].ic,
        "trigramas_por_letra": result.best.score,
        "oraculo_aciertos": float((oracle.plaintext == plain).mean()),
        "oraculo_e_aciertos": float((oracle_e.plaintext == plain).mean()),
        "segundos": seconds,
        "segundos_fase1": result.seconds["fase1"],
        "segundos_fase2": result.seconds["fase2"],
        "segundos_fase3": result.seconds["fase3"],
    }


def run(params: dict[str, Any], seed: int = SEED, progress: bool = False) -> pd.DataFrame:
    """Una fila por mensaje, con N mensajes por longitud y número de cables."""
    gillogly.warm_up()
    logp3 = hillclimb.trigram_table()
    cells = [(length, cables) for cables in params["cables"] for length in params["lengths"]]
    rngs = np.random.default_rng(seed).spawn(len(cells))
    rows = []
    for rng, (length, cables) in zip(rngs, cells, strict=True):
        started = time.perf_counter()
        for _ in range(params["n"]):
            rows.append(trial(rng, length, cables, params, logp3))
        if progress:
            done = [r["exito"] for r in rows[-params["n"] :]]
            print(
                f"  E8 · {cables} cables, {length} letras: {sum(done)} de {len(done)} "
                f"({time.perf_counter() - started:.0f} s)",
                flush=True,
            )
    df = pd.DataFrame(rows)
    df["oraculo_exito"] = df["oraculo_aciertos"] >= SUCCESS
    df["oraculo_e_exito"] = df["oraculo_e_aciertos"] >= SUCCESS
    return df


# ---------------------------------------------------------------- análisis


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """Una fila por longitud y cables: éxito con IC de Wilson, por fase, y tiempo."""
    rows = []
    for (length, cables), part in df.groupby(["L", "cables"], sort=True):
        n = len(part)
        hits = int(part["exito"].sum())
        low, high = wilson_interval(hits, n)
        row = {
            "L": int(length),
            "cables": int(cables),
            "n": n,
            "exitos": hits,
            "exito": hits / n,
            "ic_bajo": low,
            "ic_alto": high,
        }
        for column, name in (
            ("fase1_encontrada", "fase1"),
            ("oraculo_exito", "oraculo"),
            ("oraculo_e_exito", "oraculo_e"),
        ):
            k = int(part[column].sum())
            lo, hi = wilson_interval(k, n)
            row |= {name: k / n, f"{name}_ic_bajo": lo, f"{name}_ic_alto": hi}
        with_rings = part["fase1_puesto_anillos_verdaderos"] < part["top1"]
        row |= {
            "fase1_con_anillos_verdaderos": float(with_rings.mean()),
            "aciertos_media": float(part["aciertos"].mean()),
            "fase1_puesto_mediana": float(part["fase1_puesto"].median()),
            "fase1_puesto_anillos_mediana": float(part["fase1_puesto_anillos_verdaderos"].median()),
            "segundos_media": float(part["segundos"].mean()),
            "segundos_fase1_media": float(part["segundos_fase1"].mean()),
        }
        rows.append(row)
    return pd.DataFrame(rows)


def logistic(df: pd.DataFrame, column: str = "exito") -> dict[str, Any] | None:
    """Regresión logística: logit P(éxito) = β₀ + β₁·log₁₀ L + β₂·cables (statsmodels).

    Devuelve los coeficientes con su IC 95 % y, para cada número de cables, la longitud con
    50 % de éxito, L₅₀ = 10^(−(β₀ + β₂·cables)/β₁), con su IC por el método delta. ``None`` si
    el modelo no se puede ajustar (por ejemplo, con éxito o fracaso en todos los mensajes).
    """
    import statsmodels.api as sm

    y = df[column].astype(float).to_numpy()
    if y.min() == y.max():
        return None
    x = np.column_stack([np.ones(len(df)), np.log10(df["L"].to_numpy(float)), df["cables"]])
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fit = sm.Logit(y, x).fit(disp=0)
    except Exception:
        return None
    beta = np.asarray(fit.params, dtype=float)
    cov = np.asarray(fit.cov_params(), dtype=float)
    ci = np.asarray(fit.conf_int(), dtype=float)
    names = ("constante", "log10_L", "cables")
    out: dict[str, Any] = {
        "coeficientes": {
            name: {"valor": float(beta[i]), "ic": [float(ci[i, 0]), float(ci[i, 1])]}
            for i, name in enumerate(names)
        },
        "n": len(df),
        "pseudo_r2": float(fit.prsquared),
        "l50": {},
    }
    low, high = np.log10(df["L"].min()), np.log10(df["L"].max())
    for cables in sorted(df["cables"].unique()):
        g = -(beta[0] + beta[2] * cables) / beta[1]
        grad = np.array(
            [-1 / beta[1], (beta[0] + beta[2] * cables) / beta[1] ** 2, -cables / beta[1]]
        )
        sd = float(math.sqrt(max(grad @ cov @ grad, 0.0)))
        inside = beta[1] > 0 and low <= g <= high and math.isfinite(sd) and sd < 2
        # Fuera de las longitudes medidas, L₅₀ sería una extrapolación: no se reporta.
        out["l50"][str(int(cables))] = (
            {
                "letras": float(10**g),
                "ic": [float(10 ** (g - 1.96 * sd)), float(10 ** (g + 1.96 * sd))],
            }
            if inside
            else None
        )
    return out


def predicted(fit: dict[str, Any], lengths: np.ndarray, cables: int) -> np.ndarray:
    """La curva logística ajustada para esas longitudes y ese número de cables."""
    c = fit["coeficientes"]
    z = c["constante"]["valor"] + c["log10_L"]["valor"] * np.log10(lengths)
    z = z + c["cables"]["valor"] * cables
    curve: np.ndarray = 1 / (1 + np.exp(-z))
    return curve


def summary(df: pd.DataFrame, params: dict[str, Any]) -> dict[str, Any]:
    """Cifras clave de E8."""
    table = aggregate(df)
    ref = references()
    cells = {
        f"{int(r['cables'])}/{int(r['L'])}": {
            "exito": r["exito"],
            "ic": [r["ic_bajo"], r["ic_alto"]],
            "fase1": r["fase1"],
            "oraculo": r["oraculo"],
            "oraculo_e": r["oraculo_e"],
            "segundos": r["segundos_media"],
        }
        for _, r in table.iterrows()
    }
    by_cables = {}
    for cables, part in df.groupby("cables"):
        by_cables[str(int(cables))] = {
            "mensajes": len(part),
            "exito": float(part["exito"].mean()),
            "segundos_media": float(part["segundos"].mean()),
        }
    return {
        "longitudes": params["lengths"],
        "cables": params["cables"],
        "n_por_celda": params["n"],
        "rotores": params["rotors"],
        "ordenes": len(rotor_orders(tuple(params["rotors"]))),
        "ubicaciones_fase1": len(rotor_orders(tuple(params["rotors"]))) * 17_576,
        "top1": params["top1"],
        "top2": params["top2"],
        "umbral_exito": SUCCESS,
        "corpus": params["source"],
        "mensajes": len(df),
        "celdas": cells,
        "por_cables": by_cables,
        "logistica": logistic(df),
        "logistica_fase1": logistic(df, "fase1_encontrada"),
        "oraculo": float(df["oraculo_exito"].mean()),
        "oraculo_e": float(df["oraculo_e_exito"].mean()),
        "segundos_por_mensaje": float(df["segundos"].mean()),
        "referencias": {
            "gillogly_letras_hasta_6_cables": ref["gillogly_1995"]["letras_hasta_6_cables"],
            "gillogly_letras_10_cables": ref["gillogly_1995"]["letras_unico_exito_10_cables"],
            "unicidad_letras": ref["unicidad"]["letras"],
            "limite_reglamentario": ref["limite_reglamentario_letras"],
            "mensaje_real_mas_corto": ref["mensaje_real_mas_corto"]["letras"],
        },
    }


# ---------------------------------------------------------------- figura


def _success_panel(ax: Any, df: pd.DataFrame, theme: str) -> None:
    """Éxito por longitud y cables, con IC de Wilson, la logística y las referencias."""
    from enigma_lab.viz.numfmt import fmt_int
    from enigma_lab.viz.static_figs import es_number, es_percent, tokens
    from enigma_lab.viz.theme import CATEGORICAL

    t = tokens(theme)
    table = aggregate(df)
    fit = logistic(df)
    grid = np.geomspace(table["L"].min(), table["L"].max(), 200)
    levels = sorted(table["cables"].unique())
    for k, (color, cables) in enumerate(zip(CATEGORICAL, levels, strict=False)):
        part = table[table["cables"] == cables].sort_values("L")
        dodge = 1 + 0.035 * (k - (len(levels) - 1) / 2)  # separa los bigotes de cada serie
        # Con 0 o N éxitos, el límite de Wilson sale a un error de redondeo de la proporción:
        # sin recortar, el bigote puede quedar en −1e-17 y Matplotlib no lo acepta.
        below = np.clip(part["exito"] - part["ic_bajo"], 0, None)
        above = np.clip(part["ic_alto"] - part["exito"], 0, None)
        ax.errorbar(
            part["L"] * dodge,
            part["exito"],
            yerr=[below, above],
            fmt="o",
            color=color,
            markersize=4,
            capsize=2,
            elinewidth=1,
            label=f"{cables} cables",
        )
        if fit is not None:
            ax.plot(grid, predicted(fit, grid, int(cables)), color=color, linewidth=1.3)
        ax.plot(part["L"], part["oraculo"], color=color, linestyle=":", linewidth=1.2)
    ref = references()
    marks = (
        (ref["unicidad"]["letras"], "unicidad ≈ 23"),
        (ref["limite_reglamentario_letras"], "límite real: 250"),
        (ref["gillogly_1995"]["letras_hasta_6_cables"], "Gillogly, ≤ 6 cables: ~300"),
        (ref["gillogly_1995"]["letras_unico_exito_10_cables"], "Gillogly, 10 cables: 1.463"),
    )
    for k, (x, label) in enumerate(marks):
        ax.axvline(x, color=t.text_muted, linestyle="--", linewidth=0.9)
        # Los rótulos van sobre el marco, en dos alturas: abajo hay datos.
        ax.annotate(
            label,
            xy=(x, 1),
            xycoords=("data", "axes fraction"),
            xytext=(0, 3 + 10 * (k % 2)),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize="x-small",
            color=t.text_muted,
        )
    ax.set_xscale("log")
    ax.set_xlim(min(20, table["L"].min() * 0.8), max(1_800, table["L"].max() * 1.15))
    ax.set_ylim(-0.03, 1.03)
    ax.set_xlabel("longitud del mensaje (letras, escala log)")
    ax.set_ylabel("mensajes leídos (≥ 90 % de las letras)")
    ax.xaxis.set_major_formatter(es_number())
    ax.yaxis.set_major_formatter(es_percent())
    ax.legend(
        fontsize="small",
        loc="upper left",
        title="punteado: con la ubicación dada",
        title_fontsize="x-small",
    )
    per_cell = int(df.groupby(["L", "cables"]).size().min())
    ax.set_title(f"Éxito del ataque de Gillogly ({fmt_int(per_cell)} mensajes por punto)", pad=26)


def _time_panel(ax: Any, df: pd.DataFrame, theme: str) -> None:
    """Segundos por mensaje según la longitud, por cables."""
    from enigma_lab.viz.static_figs import es_number
    from enigma_lab.viz.theme import CATEGORICAL

    table = aggregate(df)
    for color, cables in zip(CATEGORICAL, sorted(table["cables"].unique()), strict=False):
        part = table[table["cables"] == cables].sort_values("L")
        ax.plot(
            part["L"],
            part["segundos_media"],
            "o-",
            color=color,
            markersize=4,
            label=f"{cables} cables",
        )
    ax.set_xscale("log")
    ax.set_xlabel("longitud del mensaje (letras, escala log)")
    ax.set_ylabel("segundos por mensaje (media)")
    ax.xaxis.set_major_formatter(es_number())
    ax.yaxis.set_major_formatter(es_number(1))
    ax.legend(fontsize="small")
    ax.set_title("Tiempo del ataque")


def figure(df: pd.DataFrame, theme: str = "enigma_print") -> Any:
    """Éxito según la longitud (con IC, logística y referencias) y tiempo por mensaje."""
    import matplotlib.pyplot as plt

    from enigma_lab.viz.numfmt import fmt_int
    from enigma_lab.viz.theme import mpl_style_context

    fit = logistic(df)
    with mpl_style_context(theme):
        size = None if theme == "enigma_slides" else (13, 5)  # 16:9 en las diapositivas
        fig, (left, right) = plt.subplots(
            1, 2, figsize=size, gridspec_kw={"width_ratios": [1.7, 1]}
        )
        _success_panel(left, df, theme)
        _time_panel(right, df, theme)
        title = "Éxito del ataque moderno según la longitud del mensaje"
        if fit is not None and fit["l50"].get("6"):
            title = (
                f"Con 6 cables, el ataque lee la mitad de los mensajes desde unas "
                f"{fmt_int(round(fit['l50']['6']['letras']))} letras"
            )
        fig.suptitle(title)
        fig.tight_layout()
    return fig


def main(mode: Mode = "completo", seed: int = SEED) -> dict[str, Any]:
    """Corre E8 y guarda sus resultados."""
    folder = output_dir(mode)
    started = time.perf_counter()
    params = PARAMS[mode]
    df = run(params, seed, progress=True)
    figures = summary(df, params) | {"segundos": round(time.perf_counter() - started, 1)}
    save_table(df, "e8_coa_mensajes", folder)
    save_table(aggregate(df), "e8_coa", folder)
    update_summary("e8", figures, RunInfo("e8", mode, seed), folder)

    import matplotlib.pyplot as plt

    fig = figure(df)
    save_figure(fig, "e8_coa", folder)
    plt.close(fig)
    return figures
